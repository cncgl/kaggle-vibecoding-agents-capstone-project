"""Core data models for FeasiblePlan.

Plain dataclasses, no external deps — these are the contract shared across the
agent roles (planner / verifier / orchestrator) and the tools.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Weekday convention: 0 = Monday ... 6 = Sunday (matches datetime.weekday()).


@dataclass
class UserPreferences:
    """Long-term, learned preferences for one user (persisted by memory.py)."""

    pace: str = "moderate"  # relaxed | moderate | packed
    budget_jpy: int = 10_000
    interests: list[str] = field(default_factory=lambda: ["history", "food", "nature"])
    mobility: str = "normal"  # normal | limited
    party: str = "solo"


@dataclass
class TripRequest:
    """A single day-out request to plan."""

    city: str
    date_weekday: int  # 0=Mon .. 6=Sun
    start_hour: int = 9
    end_hour: int = 18
    prefs: UserPreferences = field(default_factory=UserPreferences)


@dataclass
class Place:
    """A candidate place. In the MVP this comes from a curated dataset;

    later it should be backed by the Maps MCP server (see tools/places.py).
    """

    id: str
    name: str
    category: str  # museum | temple | park | market | restaurant | aquarium ...
    indoor: bool
    lat: float
    lon: float
    open_days: set[int]  # weekdays the place is open
    open_from: int  # hour (24h)
    open_to: int  # hour (24h)
    cost_jpy: int
    interest: str  # history | food | nature | art ...


@dataclass
class ItineraryStep:
    place_id: str
    start_hour: float  # 24h, fractional allowed
    duration_h: float


@dataclass
class Itinerary:
    date_weekday: int
    steps: list[ItineraryStep] = field(default_factory=list)

    def total_cost(self, places: dict[str, Place]) -> int:
        return sum(places[s.place_id].cost_jpy for s in self.steps if s.place_id in places)


@dataclass
class Violation:
    """One reason a step is not doable."""

    step_index: int  # -1 = whole-trip level (e.g. budget)
    kind: str  # closed | hours | weather | travel | budget
    detail: str


@dataclass
class FeasibilityReport:
    """The artifact that makes the value visible (great for the demo video)."""

    feasible: bool
    iterations: int
    initial_violations: list[Violation] = field(default_factory=list)
    remaining_violations: list[Violation] = field(default_factory=list)
    changes: list[str] = field(default_factory=list)
    planner_mode: str = "mock"  # which Planner backend ran: 'mock' | 'gemini (...)'
