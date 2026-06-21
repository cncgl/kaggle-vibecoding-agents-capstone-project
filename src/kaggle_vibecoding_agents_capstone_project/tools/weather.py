"""Weather tool.

MVP returns a deterministic forecast (rain in the afternoon) so the verify/repair
loop is demonstrable offline. A real open-meteo fetch is included below (no API
key required) — switch `get_rainy_hours` to call it once you want live data.
"""

from __future__ import annotations

import json
import urllib.request

# Deterministic demo forecast: rain 14:00–16:59.
_DEMO_RAINY_HOURS: set[int] = {14, 15, 16}


def get_rainy_hours(lat: float, lon: float, date_iso: str | None = None) -> set[int]:
    """Return the set of hours (0–23) with meaningful precipitation.

    MVP: deterministic demo value. TODO: call `fetch_precipitation_hours` for live
    data once we wire real coordinates/dates through the request.
    """

    return set(_DEMO_RAINY_HOURS)


def fetch_precipitation_hours(
    lat: float, lon: float, date_iso: str, threshold_mm: float = 0.2
) -> set[int]:
    """Live open-meteo lookup (free, no key). Returns hours with precip > threshold.

    Falls back to the demo value on any network error so the scaffold never crashes.
    """

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&hourly=precipitation&forecast_days=3&timezone=auto"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310 (trusted host)
            data = json.load(resp)
        hours: set[int] = set()
        times = data["hourly"]["time"]
        precip = data["hourly"]["precipitation"]
        for t, p in zip(times, precip):
            # t like "2026-07-06T14:00"
            day, hm = t.split("T")
            if day == date_iso and p is not None and p > threshold_mm:
                hours.add(int(hm[:2]))
        return hours
    except Exception:  # noqa: BLE001 — graceful offline fallback
        return set(_DEMO_RAINY_HOURS)
