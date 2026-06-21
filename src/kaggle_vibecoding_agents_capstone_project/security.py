"""Security — keep the traveler's personal info safe (a Concierge-track requirement).

Two cheap, demonstrable guards:

* ``redact`` — mask PII (email / phone / precise coordinates) before anything is
  written to a log or trace. We log *derived* facts, never raw personal data.
* ``request_summary`` — a log-safe one-line description of a TripRequest that
  carries no PII (counts and buckets only).

The human-in-the-loop gate (don't finalize an irreversible action without explicit
approval) lives next to the control flow in ``roles/orchestrator.book``.
"""

from __future__ import annotations

import re

from .models import TripRequest

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"\+?\d[\d\s-]{7,}\d")
_COORD = re.compile(r"\b\d{1,3}\.\d{3,}\b")  # precise lat/lon → coarsened


def redact(text: str) -> str:
    """Mask emails, phone numbers and precise coordinates in free text."""

    text = _EMAIL.sub("[email]", text)
    text = _PHONE.sub("[phone]", text)
    text = _COORD.sub("[geo]", text)
    return text


def request_summary(request: TripRequest) -> str:
    """A log-safe summary: derived counts/buckets only, no raw preferences."""

    prefs = request.prefs
    budget_bucket = "low" if prefs.budget_jpy < 5_000 else "mid" if prefs.budget_jpy < 15_000 else "high"
    return (
        f"city={request.city} weekday={request.date_weekday} "
        f"interests={len(prefs.interests)} budget={budget_bucket} party={prefs.party}"
    )
