"""Long-term memory (preferences) — JSON-backed for the MVP.

This is the "Sessions & Memory" course concept in its simplest durable form.
NEXT: swap for ADK Memory / Memory Bank if time allows.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import UserPreferences

_DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "preferences.json"


class Memory:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _DEFAULT_PATH

    def load(self) -> UserPreferences:
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            raw["interests"] = list(raw.get("interests", []))
            return UserPreferences(**raw)
        return UserPreferences()

    def save(self, prefs: UserPreferences) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(prefs), ensure_ascii=False, indent=2), encoding="utf-8")
