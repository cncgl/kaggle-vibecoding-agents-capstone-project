"""Places tool.

MVP: a small curated Kyoto dataset so the loop runs offline. The opening days/
hours are illustrative, not authoritative.

NEXT (Day 2 learning): replace this with the **Maps MCP server** — one of the 50+
Google-managed MCP servers — to get real opening hours, locations and travel
times. Keep this module's function signatures so the rest of the code is unchanged.
"""

from __future__ import annotations

import math

from ..models import Place

# weekdays: 0=Mon .. 6=Sun
_ALL_DAYS = {0, 1, 2, 3, 4, 5, 6}
_TUE_TO_SUN = {1, 2, 3, 4, 5, 6}  # closed Monday (typical museum)

_KYOTO: dict[str, Place] = {
    p.id: p
    for p in [
        # interest=history/art
        Place("knm", "Kyoto National Museum", "museum", True, 34.990, 135.773,
              _TUE_TO_SUN, 9, 17, 700, "history"),
        Place("sanjusangendo", "Sanjusangen-do", "temple", True, 34.988, 135.771,
              _ALL_DAYS, 8, 17, 600, "history"),
        Place("manga", "Kyoto Int'l Manga Museum", "museum", True, 35.012, 135.759,
              {0, 2, 3, 4, 5, 6}, 10, 18, 900, "art"),
        # interest=food
        Place("nishiki", "Nishiki Market", "market", True, 35.005, 135.764,
              _ALL_DAYS, 9, 18, 2000, "food"),
        Place("pontocho", "Pontocho Dinner", "restaurant", True, 35.004, 135.770,
              _ALL_DAYS, 17, 23, 5000, "food"),
        # interest=nature
        Place("maruyama", "Maruyama Park", "park", False, 35.003, 135.781,
              _ALL_DAYS, 0, 24, 0, "nature"),
        Place("botanical", "Kyoto Botanical Garden", "park", False, 35.050, 135.764,
              _ALL_DAYS, 9, 17, 200, "nature"),
        Place("aquarium", "Kyoto Aquarium", "aquarium", True, 34.988, 135.747,
              _ALL_DAYS, 10, 18, 2400, "nature"),
    ]
}


def get_places(city: str) -> dict[str, Place]:
    """Return candidate places for a city keyed by id.

    TODO: back this with the Maps MCP server instead of the curated dict.
    """

    # MVP ignores `city` and always returns the Kyoto set.
    return dict(_KYOTO)


def travel_minutes(a: Place, b: Place, kmph: float = 15.0) -> float:
    """Rough urban travel time (walking + transit average) between two places."""

    return _haversine_km(a.lat, a.lon, b.lat, b.lon) / kmph * 60.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))
