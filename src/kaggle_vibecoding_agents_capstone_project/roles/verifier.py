"""Verifier / Critic agent — the differentiator.

Checks every itinerary step against real-world constraints and returns the list
of violations. This is deterministic on purpose: trustworthy checks are the value
proposition. (The Planner is where the LLM creativity lives, not here.)
"""

from __future__ import annotations

import math

from ..models import Itinerary, Place, TripRequest, Violation
from ..tools import places as places_tool


def verify(
    itinerary: Itinerary,
    request: TripRequest,
    places: dict[str, Place],
    rainy_hours: set[int],
) -> list[Violation]:
    violations: list[Violation] = []
    steps = itinerary.steps

    for i, step in enumerate(steps):
        place = places.get(step.place_id)
        if place is None:
            violations.append(Violation(i, "closed", f"unknown place '{step.place_id}'"))
            continue

        start, end = step.start_hour, step.start_hour + step.duration_h

        # 1) Open on this weekday?
        if request.date_weekday not in place.open_days:
            violations.append(
                Violation(i, "closed", f"{place.name} is closed on weekday {request.date_weekday}")
            )

        # 2) Within opening hours?
        if start < place.open_from or end > place.open_to:
            violations.append(
                Violation(
                    i,
                    "hours",
                    f"{place.name} open {place.open_from}:00–{place.open_to}:00, "
                    f"but step is {start:.1f}–{end:.1f}",
                )
            )

        # 3) Weather-appropriate? (outdoor place during a rainy hour)
        if not place.indoor and _overlaps_rain(start, end, rainy_hours):
            violations.append(
                Violation(i, "weather", f"{place.name} is outdoor and it rains during {start:.0f}:00")
            )

    # 4) Travel time feasible between consecutive steps?
    for i in range(len(steps) - 1):
        a, b = places.get(steps[i].place_id), places.get(steps[i + 1].place_id)
        if a is None or b is None:
            continue
        end_a = steps[i].start_hour + steps[i].duration_h
        gap_min = (steps[i + 1].start_hour - end_a) * 60.0
        need = places_tool.travel_minutes(a, b)
        if gap_min < need:
            violations.append(
                Violation(
                    i + 1,
                    "travel",
                    f"only {gap_min:.0f} min before {b.name}, need ~{need:.0f} min from {a.name}",
                )
            )

    # 5) Budget
    total = itinerary.total_cost(places)
    if total > request.prefs.budget_jpy:
        violations.append(
            Violation(-1, "budget", f"total ¥{total} over budget ¥{request.prefs.budget_jpy}")
        )

    return violations


def _overlaps_rain(start: float, end: float, rainy_hours: set[int]) -> bool:
    return any(h in rainy_hours for h in range(int(math.floor(start)), int(math.ceil(end))))
