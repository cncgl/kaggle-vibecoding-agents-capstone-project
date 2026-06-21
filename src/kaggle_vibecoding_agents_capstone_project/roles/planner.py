"""Planner agent — drafts and repairs the itinerary.

This is the one creative role: the LLM lives here, the deterministic Verifier stays
the source of truth. Two interchangeable backends sit behind the same signatures:

* **Gemini via Google ADK** (``planner_llm``) — used automatically when a Gemini key
  is configured. This is the real multi-agent demonstration.
* **Deterministic mock** (``_mock_*`` below) — the offline fallback. It intentionally
  drafts a plan with a couple of real-world violations (a Monday-closed museum, an
  outdoor stop during afternoon rain) so the loop is fully demonstrable with no key,
  and it is the safety net if any LLM call fails (no key, network, bad JSON).

So `draft`/`repair` are thin dispatchers: try the LLM, fall back to the mock.
"""

from __future__ import annotations

import logging
from dataclasses import replace

from ..models import Itinerary, ItineraryStep, Place, TripRequest, Violation
from . import planner_llm

_log = logging.getLogger(__name__)


def active_mode() -> str:
    """Which backend ``draft``/``repair`` will use: gemini / local / mock."""

    return planner_llm.mode_label()


def draft(request: TripRequest, places: dict[str, Place]) -> Itinerary:
    """Draft an initial itinerary (LLM if configured, else the mock sketch)."""

    if planner_llm.available():
        try:
            return planner_llm.llm_draft(request, places)
        except Exception as exc:  # noqa: BLE001 — never let the demo crash
            _log.warning("LLM draft unavailable (%s); using offline mock", planner_llm.short_reason(exc))
    return _mock_draft(request, places)


def repair(
    itinerary: Itinerary,
    violations: list[Violation],
    request: TripRequest,
    places: dict[str, Place],
    rainy_hours: set[int],
) -> tuple[Itinerary, list[str]]:
    """Repair an itinerary against the Verifier's violations (LLM if configured)."""

    if planner_llm.available():
        try:
            return planner_llm.llm_repair(itinerary, violations, request, places, rainy_hours)
        except Exception as exc:  # noqa: BLE001 — never let the demo crash
            _log.warning("LLM repair unavailable (%s); using offline mock", planner_llm.short_reason(exc))
    return _mock_repair(itinerary, violations, request, places, rainy_hours)


def _mock_draft(request: TripRequest, places: dict[str, Place]) -> Itinerary:
    """Offline draft: a fixed sketch with two deliberate, demonstrable violations."""

    steps = [
        ItineraryStep("knm", 9.5, 2.0),       # museum — CLOSED on Monday (weekday 0)
        ItineraryStep("nishiki", 12.0, 1.0),  # lunch — fine
        ItineraryStep("botanical", 14.0, 2.0),  # outdoor — clashes with afternoon rain
    ]
    return Itinerary(date_weekday=request.date_weekday, steps=steps)


def _mock_repair(
    itinerary: Itinerary,
    violations: list[Violation],
    request: TripRequest,
    places: dict[str, Place],
    rainy_hours: set[int],
) -> tuple[Itinerary, list[str]]:
    """Offline repair: swap each violating step for a suitable alternative place."""

    bad_steps = {v.step_index for v in violations if v.step_index >= 0}
    used = {s.place_id for i, s in enumerate(itinerary.steps) if i not in bad_steps}
    new_steps: list[ItineraryStep] = []
    changes: list[str] = []

    for i, step in enumerate(itinerary.steps):
        if i in bad_steps:
            alt = _find_alternative(step, request, places, rainy_hours, used)
            if alt is not None:
                changes.append(
                    f"swapped {places[step.place_id].name} → {alt.name} "
                    f"(step {i}, {_why(violations, i)})"
                )
                step = replace(step, place_id=alt.id)
                used.add(alt.id)
            else:
                changes.append(f"could not fix step {i} ({_why(violations, i)})")
        new_steps.append(step)

    return Itinerary(date_weekday=itinerary.date_weekday, steps=new_steps), changes


def _find_alternative(
    step: ItineraryStep,
    request: TripRequest,
    places: dict[str, Place],
    rainy_hours: set[int],
    used: set[str],
) -> Place | None:
    start, end = step.start_hour, step.start_hour + step.duration_h
    need_indoor = any(h in rainy_hours for h in range(int(start), int(end) + 1))
    current = places.get(step.place_id)
    want_interest = current.interest if current else None

    def ok(p: Place) -> bool:
        return (
            p.id not in used
            and p.id != step.place_id
            and request.date_weekday in p.open_days
            and p.open_from <= start
            and end <= p.open_to
            and (p.indoor if need_indoor else True)
        )

    candidates = [p for p in places.values() if ok(p)]
    # Prefer same interest, then cheaper, then stable by name.
    candidates.sort(key=lambda p: (p.interest != want_interest, p.cost_jpy, p.name))
    return candidates[0] if candidates else None


def _why(violations: list[Violation], step_index: int) -> str:
    kinds = sorted({v.kind for v in violations if v.step_index == step_index})
    return ", ".join(kinds) or "unknown"
