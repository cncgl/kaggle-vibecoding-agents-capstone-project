"""Entrypoint: run FeasiblePlan end-to-end on a sample request and print a report.

    uv run python -m kaggle_vibecoding_agents_capstone_project.agent

This runs fully offline (mock planner + curated places + demo weather). It exists
to prove the architecture works; the real value comes from swapping the Planner
for Gemini/ADK and `places` for the Maps MCP server (see docs/HANDOFF.md).
"""

from __future__ import annotations

from .models import Itinerary, Place, TripRequest, UserPreferences
from .roles import orchestrator


def _fmt_itinerary(it: Itinerary, places: dict[str, Place]) -> str:
    lines = []
    for s in it.steps:
        p = places.get(s.place_id)
        name = p.name if p else s.place_id
        end = s.start_hour + s.duration_h
        tag = "indoor" if (p and p.indoor) else "outdoor"
        cost = f"¥{p.cost_jpy}" if p else "?"
        lines.append(f"  {s.start_hour:>4.1f}–{end:<4.1f}  {name}  ({tag}, {cost})")
    return "\n".join(lines)


def main() -> None:
    # Monday (weekday 0) trips up the closed museum; afternoon rain trips the garden.
    request = TripRequest(
        city="Kyoto",
        date_weekday=0,
        start_hour=9,
        end_hour=18,
        prefs=UserPreferences(budget_jpy=10_000, interests=["history", "food", "nature"]),
    )

    itinerary, report, places = orchestrator.plan_trip(request)

    print("=== FeasiblePlan — sample run (Kyoto, Monday) ===")
    print(f"Planner backend: {report.planner_mode}\n")
    print(f"Initial violations ({len(report.initial_violations)}):")
    for v in report.initial_violations:
        print(f"  - [{v.kind}] {v.detail}")
    print("\nRepairs:")
    for c in report.changes or ["  (none)"]:
        print(f"  - {c}")
    print(f"\nFinal itinerary (feasible={report.feasible}, iterations={report.iterations}):")
    print(_fmt_itinerary(itinerary, places))
    if report.remaining_violations:
        print("\n⚠️ remaining violations:")
        for v in report.remaining_violations:
            print(f"  - [{v.kind}] {v.detail}")


if __name__ == "__main__":
    main()
