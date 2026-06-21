"""Eval — quantify FeasiblePlan's core claim.

    uv run python -m kaggle_vibecoding_agents_capstone_project.eval

The pitch is "other planners produce *plausible* but *broken* itineraries; we
produce *doable* ones." This harness turns that into a number: across a set of
scenarios it compares

  * BEFORE — the Planner's raw draft (what a normal trip-AI would hand you), vs
  * AFTER  — FeasiblePlan's plan after the verify → repair loop.

and reports the feasibility rate of each. The BEFORE→AFTER lift is the headline
figure for the writeup and the demo video. Runs with whichever Planner backend is
active (offline mock, or live Gemini if a key is configured).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .models import TripRequest, UserPreferences
from .roles import orchestrator, planner, planner_llm


@dataclass
class Scenario:
    name: str
    request: TripRequest
    rainy_hours: set[int]


def _scenarios() -> list[Scenario]:
    def req(weekday: int, budget: int, interests: list[str]) -> TripRequest:
        return TripRequest(
            city="Kyoto",
            date_weekday=weekday,
            prefs=UserPreferences(budget_jpy=budget, interests=interests),
        )

    rain_pm = {14, 15, 16}
    rain_allday = {10, 11, 12, 13, 14, 15, 16}
    sunny: set[int] = set()
    return [
        Scenario("Mon · rain PM · ¥10k", req(0, 10_000, ["history", "food", "nature"]), rain_pm),
        Scenario("Wed · rain PM · ¥10k", req(2, 10_000, ["history", "food", "nature"]), rain_pm),
        Scenario("Sat · sunny · ¥10k", req(5, 10_000, ["nature", "food"]), sunny),
        Scenario("Mon · sunny · ¥3k", req(0, 3_000, ["history", "art"]), sunny),
        Scenario("Sun · rain all day · ¥8k", req(6, 8_000, ["nature", "food", "history"]), rain_allday),
    ]


@dataclass
class Row:
    name: str
    draft_feasible: bool
    final_feasible: bool
    initial_violations: int
    iterations: int


def run() -> list[Row]:
    rows: list[Row] = []
    for sc in _scenarios():
        _, report, _ = orchestrator.plan_trip(sc.request, rainy_hours=sc.rainy_hours)
        rows.append(
            Row(
                name=sc.name,
                draft_feasible=len(report.initial_violations) == 0,
                final_feasible=report.feasible,
                initial_violations=len(report.initial_violations),
                iterations=report.iterations,
            )
        )
    return rows


def _pct(n: int, total: int) -> str:
    return f"{n}/{total} ({100 * n // total if total else 0}%)"


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    planner_llm.quiet_sdk_logs()  # mute ADK's traceback spew on handled LLM fallbacks

    rows = run()
    total = len(rows)

    print("=== FeasiblePlan — feasibility eval ===")
    print(f"Planner backend: {planner.active_mode()}\n")
    print(f"{'scenario':<26} {'draft':>7} {'final':>7} {'viol':>5} {'iters':>6}")
    print("-" * 54)
    for r in rows:
        print(
            f"{r.name:<26} {('✓' if r.draft_feasible else '✗'):>7} "
            f"{('✓' if r.final_feasible else '✗'):>7} "
            f"{r.initial_violations:>5} {r.iterations:>6}"
        )

    draft_ok = sum(r.draft_feasible for r in rows)
    final_ok = sum(r.final_feasible for r in rows)
    lift = (final_ok - draft_ok) * 100 // total if total else 0
    print("-" * 54)
    print(f"Raw planner (BEFORE) feasibility: {_pct(draft_ok, total)}")
    print(f"FeasiblePlan (AFTER)  feasibility: {_pct(final_ok, total)}")
    print(f"Lift from verify→repair loop:     +{lift} points")


if __name__ == "__main__":
    main()
