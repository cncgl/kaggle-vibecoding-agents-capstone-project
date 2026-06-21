"""FeasiblePlan web UI — a thin FastAPI layer over the existing agent.

    uv run python -m kaggle_vibecoding_agents_capstone_project.web
    # then open http://localhost:8000

The core multi-agent logic (orchestrator.plan_trip / orchestrator.book) is reused
unchanged; this module only serializes it for a single-page UI and serves that page.
It is deliberately one self-contained app (HTML + API) so it deploys as one container
(e.g. Cloud Run) — the "Deployability" concept — with no build step.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .models import Itinerary, ItineraryStep, Place, TripRequest, UserPreferences
from .roles import orchestrator, planner_llm
from .tools import places as places_tool

app = FastAPI(title="FeasiblePlan")
planner_llm.quiet_sdk_logs()  # keep server logs clean on handled LLM fallbacks

_INDEX = Path(__file__).parent / "static" / "index.html"


class PlanRequest(BaseModel):
    date_weekday: int = 0
    start_hour: int = 9
    end_hour: int = 18
    budget_jpy: int = 10_000
    interests: list[str] = Field(default_factory=lambda: ["history", "food", "nature"])


class BookStep(BaseModel):
    place_id: str
    start_hour: float
    duration_h: float


class BookRequest(BaseModel):
    steps: list[BookStep]
    traveler_contact: str = ""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _INDEX.read_text(encoding="utf-8")


@app.post("/plan")
def plan(req: PlanRequest) -> dict:
    request = TripRequest(
        city="Kyoto",
        date_weekday=req.date_weekday,
        start_hour=req.start_hour,
        end_hour=req.end_hour,
        prefs=UserPreferences(budget_jpy=req.budget_jpy, interests=req.interests),
    )
    itinerary, report, places = orchestrator.plan_trip(request)
    return _serialize(itinerary, report, places)


@app.post("/book")
def book(req: BookRequest) -> dict:
    # The user clicking "Confirm & Book" in the UI *is* the human-in-the-loop approval,
    # so the approver returns True; orchestrator.book still redacts the contact in logs.
    places = places_tool.get_places("Kyoto")
    itinerary = Itinerary(
        date_weekday=0,
        steps=[ItineraryStep(s.place_id, s.start_hour, s.duration_h) for s in req.steps],
    )
    booked = orchestrator.book(
        itinerary, places, approver=lambda _summary: True, traveler_contact=req.traveler_contact
    )
    return {"booked": booked}


def _serialize(itinerary: Itinerary, report, places: dict[str, Place]) -> dict:
    def step(s: ItineraryStep) -> dict:
        p = places.get(s.place_id)
        return {
            "place_id": s.place_id,
            "name": p.name if p else s.place_id,
            "category": p.category if p else None,
            "indoor": p.indoor if p else None,
            "cost": p.cost_jpy if p else None,
            "start": s.start_hour,
            "end": s.start_hour + s.duration_h,
        }

    def viol(v) -> dict:
        return {"kind": v.kind, "detail": v.detail, "step_index": v.step_index}

    return {
        "backend": report.planner_mode,
        "feasible": report.feasible,
        "iterations": report.iterations,
        "initial_violations": [viol(v) for v in report.initial_violations],
        "remaining_violations": [viol(v) for v in report.remaining_violations],
        "changes": report.changes,
        "steps": [step(s) for s in itinerary.steps],
        "total_cost": itinerary.total_cost(places),
    }


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
