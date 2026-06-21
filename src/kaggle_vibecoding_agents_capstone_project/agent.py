"""Entrypoint: run FeasiblePlan end-to-end on a sample request and print a report.

    uv run python -m kaggle_vibecoding_agents_capstone_project.agent

This runs fully offline (mock planner + curated places + demo weather). It exists
to prove the architecture works; the real value comes from swapping the Planner
for Gemini/ADK and `places` for the Maps MCP server (see docs/HANDOFF.md).
"""

from __future__ import annotations

import logging

from .models import Itinerary, Place, TripRequest, UserPreferences
from .roles import orchestrator, planner_llm

# A simulated stored contact for the traveler — stands in for real PII. The point
# of the demo is that this never reaches a log un-redacted (see security.redact).
_TRAVELER_CONTACT = "aki.tanaka@example.com / +81 90-1234-5678"


def _interactive_approver(summary: str) -> bool:
    """Ask a human to approve booking. Declines safely when there's no TTY."""

    print("\n--- human-in-the-loop ---")
    print(summary)
    try:
        answer = input("Approve & book? [y/N] ").strip().lower()
    except EOFError:
        print("(no interactive input — declining by default)")
        return False
    return answer in {"y", "yes"}


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
    # INFO logs make the PII redaction in the booking step visible in the demo.
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    planner_llm.quiet_sdk_logs()  # mute ADK's traceback spew on handled LLM fallbacks

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

    # Security / human-in-the-loop: only a feasible plan is offered for booking,
    # and booking (the irreversible step) requires explicit human approval.
    if report.feasible:
        booked = orchestrator.book(
            itinerary,
            places,
            approver=_interactive_approver,
            traveler_contact=_TRAVELER_CONTACT,
        )
        print(f"\nBooked: {booked}")


if __name__ == "__main__":
    main()
