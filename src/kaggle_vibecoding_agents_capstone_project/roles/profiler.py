"""Profiler agent — loads/updates the user's long-term preferences.

Thin wrapper over memory.py for now. NEXT: have it learn from feedback (after a
trip, update interests/pace), and treat memory as a *hint* not an instruction
(the "memory is episodic, skills are procedural" point from Day 3/4).
"""

from __future__ import annotations

from ..memory import Memory
from ..models import UserPreferences


class Profiler:
    def __init__(self, memory: Memory | None = None) -> None:
        self.memory = memory or Memory()

    def load(self) -> UserPreferences:
        return self.memory.load()

    def remember(self, prefs: UserPreferences) -> None:
        self.memory.save(prefs)
