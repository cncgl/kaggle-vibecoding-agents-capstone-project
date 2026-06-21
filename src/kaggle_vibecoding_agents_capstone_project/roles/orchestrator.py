"""Orchestrator — runs the plan → verify → repair loop.

This is the root agent. It owns the control flow; the LLM work lives in Planner.
Observability hook points are marked `# trace:` — wire these to OpenTelemetry
(Day 4 learning) so the whole trajectory is inspectable.
"""

from __future__ import annotations

import logging
from typing import Callable

from .. import security
from ..models import FeasibilityReport, Itinerary, Place, TripRequest
from ..tools import places as places_tool
from ..tools import weather as weather_tool
from . import planner, verifier
from .profiler import Profiler

_log = logging.getLogger(__name__)

MAX_ITERS = 3


def plan_trip(
    request: TripRequest,
    *,
    places: dict[str, Place] | None = None,
    rainy_hours: set[int] | None = None,
) -> tuple[Itinerary, FeasibilityReport, dict[str, Place]]:
    """Plan a doable day trip.

    `places` / `rainy_hours` are optional injection points (used by eval and tests
    to vary the world per scenario); when omitted they come from the live tools.
    """

    # 0) Profiler / memory: merge stored prefs (request prefs win if set explicitly).
    profiler = Profiler()
    _stored = profiler.load()  # trace: memory.load  (TODO: actually merge)

    # 1) Gather tool context (or use the injected world).
    places = places if places is not None else places_tool.get_places(request.city)
    rainy = (
        rainy_hours
        if rainy_hours is not None
        else weather_tool.get_rainy_hours(lat=34.99, lon=135.77)  # TODO: per-place coords/date
    )

    # 2) Draft.
    itinerary = planner.draft(request, places)  # trace: planner.draft
    initial = verifier.verify(itinerary, request, places, rainy)  # trace: verifier

    # 3) Repair loop.
    all_changes: list[str] = []
    iterations = 0
    violations = initial
    while violations and iterations < MAX_ITERS:
        iterations += 1
        itinerary, changes = planner.repair(itinerary, violations, request, places, rainy)
        all_changes.extend(changes)
        violations = verifier.verify(itinerary, request, places, rainy)  # trace: verifier

    report = FeasibilityReport(
        feasible=not violations,
        iterations=iterations,
        initial_violations=initial,
        remaining_violations=violations,
        changes=all_changes,
        planner_mode=planner.active_mode(),
    )
    return itinerary, report, places


def book(
    itinerary: Itinerary,
    places: dict[str, Place],
    *,
    approver: Callable[[str], bool],
    traveler_contact: str = "",
) -> bool:
    """Human-in-the-loop gate: finalize the trip only with explicit approval.

    Booking is the one irreversible action, so the agent must never do it on its
    own — it presents a summary and waits for a human yes/no (`approver`). Anything
    we log is run through `security.redact`, so the traveler's contact details never
    land in logs/traces (a Concierge "keep personal info safe" requirement).
    Returns True iff the trip was approved (in the MVP "booking" is a no-op stub;
    a real impl would call a reservation API here).
    """

    summary = _booking_summary(itinerary, places)
    if traveler_contact:
        _log.info("booking requested for %s", security.redact(traveler_contact))

    if not approver(summary):
        _log.info("booking declined by human reviewer")
        return False

    _log.info("booking confirmed by human reviewer")  # real impl: call reservation API
    return True


def _booking_summary(itinerary: Itinerary, places: dict[str, Place]) -> str:
    lines = ["Confirm & book this itinerary?"]
    for s in itinerary.steps:
        name = places[s.place_id].name if s.place_id in places else s.place_id
        lines.append(f"  {s.start_hour:>4.1f}  {name}")
    lines.append(f"  total ¥{itinerary.total_cost(places)}")
    return "\n".join(lines)
