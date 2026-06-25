"""LLM-backed Planner — the real "brain" of FeasiblePlan (Google ADK).

This is the piece that makes the multi-agent story real: an ADK ``LlmAgent`` drafts
the itinerary (creative work) while the deterministic Verifier remains the source of
truth. We keep ``planner.py``'s public ``draft``/``repair`` signatures.

Two interchangeable LLM backends behind ADK (see ``backend()``):
  * **gemini** — Gemini via the Gemini API (needs a key); schema-constrained output.
  * **local**  — any OpenAI-compatible local server (Ollama / LM Studio) via ADK's
    LiteLlm; no key, no quota, fully offline. We instruct the JSON shape and parse it.
Anything that fails (no key, quota/network, bad JSON) falls back to the offline mock,
so the demo always runs.

Honest-demo design: the Planner is **not** told the live weather forecast, so it can
genuinely pick an outdoor stop that later turns out to clash with afternoon rain —
exactly the kind of "plausible but not doable" mistake the Verifier exists to catch.
On repair it *is* given the violations (and the rainy hours) as feedback to fix.

Env (loaded from a project-root ``.env`` by ``load_dotenv``):
    # cloud (Gemini)
    GOOGLE_GENAI_USE_VERTEXAI=FALSE
    GOOGLE_API_KEY=<from https://aistudio.google.com/apikey>
    FEASIBLEPLAN_MODEL=gemini-2.5-flash        # optional Gemini model override
    # local (Ollama / LM Studio) — quota-free fallback
    FEASIBLEPLAN_BACKEND=local                 # or: gemini | mock
    FEASIBLEPLAN_LLM_BASE_URL=http://localhost:11434/v1   # Ollama; LM Studio = :1234/v1
    FEASIBLEPLAN_LLM_MODEL=llama3.2:3b         # a model you've pulled/loaded
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from ..models import Itinerary, ItineraryStep, Place, TripRequest, Violation

load_dotenv()  # idempotent; lets `.env` configure the Gemini key + model

_log = logging.getLogger(__name__)

_APP = "feasibleplan"
_USER = "local"
_SESSION = "plan"
_WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Free-tier rate-limit handling: retry a 429 a couple of times, honoring the
# server's suggested delay (capped, so a daily-quota exhaustion degrades to the
# mock fallback quickly instead of hanging the demo).
_MAX_RETRIES = 2
_MAX_WAIT_S = 30.0


def model_name() -> str:
    return os.environ.get("FEASIBLEPLAN_MODEL", "gemini-2.5-flash")


# --- backend selection: gemini (cloud) | local (Ollama/LM Studio) | mock --------

_DEFAULT_LOCAL_BASE_URL = "http://localhost:11434/v1"  # Ollama; LM Studio = :1234/v1


def _has_gemini_key() -> bool:
    return bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"))


def backend() -> str:
    """Resolve which Planner backend to use: 'gemini' | 'local' | 'mock'.

    Precedence: an explicit ``FEASIBLEPLAN_BACKEND`` wins (mock/local/gemini), else
    auto-detect — a local endpoint URL → local, a Gemini key → gemini, else mock.
    """

    forced = os.environ.get("FEASIBLEPLAN_BACKEND", "").strip().lower()
    if forced == "mock":
        return "mock"
    if forced == "local":
        return "local"
    if forced == "gemini":
        return "gemini" if _has_gemini_key() else "mock"
    if os.environ.get("FEASIBLEPLAN_LLM_BASE_URL"):
        return "local"
    if _has_gemini_key():
        return "gemini"
    return "mock"


def available() -> bool:
    """True when an LLM backend (gemini or local) should run, i.e. not mock."""

    return backend() != "mock"


def _local_model() -> str:
    return os.environ.get("FEASIBLEPLAN_LLM_MODEL", "llama3.2:3b")


def _local_base_url() -> str:
    return os.environ.get("FEASIBLEPLAN_LLM_BASE_URL", _DEFAULT_LOCAL_BASE_URL)


def mode_label() -> str:
    """Human-readable label of the active backend (for the feasibility report)."""

    b = backend()
    if b == "gemini":
        return f"gemini ({model_name()}, adk)"
    if b == "local":
        return f"local ({_local_model()} @ {_local_base_url()}, adk+litellm)"
    return "mock"


def quiet_sdk_logs() -> None:
    """Silence ADK/genai ERROR tracebacks for *handled* fallbacks.

    When an LLM call fails we catch it and fall back to the mock, but ADK still
    logs the exception+traceback at ERROR. That's alarming noise for a working
    demo, so entrypoints call this to mute the SDK loggers; our own concise
    'using offline mock' warning remains the signal.
    """

    for name in ("google_adk", "google.adk", "google_genai", "google.genai"):
        logging.getLogger(name).setLevel(logging.CRITICAL)
    # httpx / LiteLLM log every request at INFO (incl. 429 and completion lines);
    # demote to WARNING so the demo output stays clean.
    for name in ("httpx", "LiteLLM", "litellm"):
        logging.getLogger(name).setLevel(logging.WARNING)


def short_reason(exc: Exception) -> str:
    """One-line, human-readable cause for a failed LLM call (for warnings)."""

    text = str(exc)
    if "429" in text or "RESOURCE_EXHAUSTED" in text:
        if re.search(r"per\s*day|RequestsPerDay", text, re.IGNORECASE):
            return "Gemini free-tier daily quota exhausted (429)"
        return "Gemini rate limit (429)"
    if "503" in text or "UNAVAILABLE" in text:
        return "Gemini temporarily overloaded (503)"
    if "500" in text or "INTERNAL" in text:
        return "Gemini server error (500)"
    return f"{type(exc).__name__}: {text[:120]}"


# --- structured output contract (what the LLM must return) -------------------


class _PlanStep(BaseModel):
    place_id: str = Field(description="an id taken verbatim from the candidate list")
    start_hour: float = Field(description="24h clock, fractional allowed, e.g. 9.5")
    duration_h: float = Field(description="hours spent at this place, e.g. 1.5")


class _PlanResult(BaseModel):
    steps: list[_PlanStep] = Field(description="2-4 ordered stops for the day")
    changes: list[str] = Field(
        default_factory=list,
        description="repair only: one short human-readable note per fix made",
    )


# --- public API (mirrors planner.draft / planner.repair) ---------------------


def llm_draft(request: TripRequest, places: dict[str, Place]) -> Itinerary:
    instruction = (
        "You are a day-trip planner. Given a request and a list of candidate places, "
        "design ONE feasible single-day itinerary of 2-4 ordered stops. "
        "Use ONLY place ids from the candidate list. Keep every stop inside the time "
        "window, match the visitor's interests, and stay within budget. "
        "You are NOT given the weather; just plan sensibly. "
        "Return JSON matching the schema."
    )
    prompt = _draft_prompt(request, places)
    result = _run(instruction, prompt)
    return _to_itinerary(result, request, places)


def llm_repair(
    itinerary: Itinerary,
    violations: list[Violation],
    request: TripRequest,
    places: dict[str, Place],
    rainy_hours: set[int],
) -> tuple[Itinerary, list[str]]:
    instruction = (
        "You are repairing a day-trip itinerary that a verifier found infeasible. "
        "Fix EVERY listed violation by swapping in suitable alternative places (use "
        "ONLY ids from the candidate list) or adjusting times. For weather violations, "
        "prefer indoor places during rainy hours. Keep the rest of the plan stable. "
        "Fill `changes` with one short note per fix. Return JSON matching the schema."
    )
    prompt = _repair_prompt(itinerary, violations, request, places, rainy_hours)
    result = _run(instruction, prompt)
    new_it = _to_itinerary(result, request, places)
    changes = list(result.changes) or ["LLM re-planned the itinerary"]
    return new_it, changes


# --- prompt construction -----------------------------------------------------


def _places_table(places: dict[str, Place]) -> str:
    header = "id | name | category | indoor? | open_days(0=Mon..6=Sun) | hours | cost_jpy | interest"
    rows = [header]
    for p in places.values():
        days = ",".join(str(d) for d in sorted(p.open_days))
        rows.append(
            f"{p.id} | {p.name} | {p.category} | "
            f"{'indoor' if p.indoor else 'outdoor'} | {days} | "
            f"{p.open_from}-{p.open_to} | {p.cost_jpy} | {p.interest}"
        )
    return "\n".join(rows)


def _request_block(request: TripRequest) -> str:
    prefs = request.prefs
    wd = _WEEKDAYS[request.date_weekday]
    return (
        f"City: {request.city}\n"
        f"Day: {wd} (weekday {request.date_weekday})\n"
        f"Window: {request.start_hour}:00-{request.end_hour}:00\n"
        f"Budget: ¥{prefs.budget_jpy}\n"
        f"Interests: {', '.join(prefs.interests)}\n"
        f"Pace: {prefs.pace} | Party: {prefs.party} | Mobility: {prefs.mobility}"
    )


def _draft_prompt(request: TripRequest, places: dict[str, Place]) -> str:
    return (
        f"REQUEST\n{_request_block(request)}\n\n"
        f"CANDIDATE PLACES\n{_places_table(places)}\n\n"
        "Draft the itinerary now."
    )


def _repair_prompt(
    itinerary: Itinerary,
    violations: list[Violation],
    request: TripRequest,
    places: dict[str, Place],
    rainy_hours: set[int],
) -> str:
    cur_lines = []
    for i, s in enumerate(itinerary.steps):
        nm = places[s.place_id].name if s.place_id in places else s.place_id
        cur_lines.append(
            f"  step {i}: {s.place_id} ({nm}) {s.start_hour:.1f}-{s.start_hour + s.duration_h:.1f}"
        )
    viol_lines = [f"  - [{v.kind}] step {v.step_index}: {v.detail}" for v in violations]
    rainy = ", ".join(f"{h}:00" for h in sorted(rainy_hours)) or "none"
    return (
        f"REQUEST\n{_request_block(request)}\n\n"
        f"RAINY HOURS TODAY: {rainy}\n\n"
        f"CURRENT ITINERARY\n" + "\n".join(cur_lines) + "\n\n"
        f"VIOLATIONS TO FIX\n" + "\n".join(viol_lines) + "\n\n"
        f"CANDIDATE PLACES\n{_places_table(places)}\n\n"
        "Return the corrected itinerary."
    )


# --- ADK plumbing ------------------------------------------------------------


def _run(instruction: str, prompt: str) -> _PlanResult:
    """Run a one-shot ADK LlmAgent constrained to the _PlanResult schema.

    Retries on a 429 (free-tier rate limit) honoring the server's suggested wait;
    if it still fails the caller falls back to the deterministic mock.
    """

    for attempt in range(_MAX_RETRIES + 1):
        try:
            return asyncio.run(_run_async(instruction, prompt))
        except Exception as exc:  # noqa: BLE001 — inspect, maybe retry, else re-raise
            wait = _retry_wait(exc)
            if wait is None or attempt == _MAX_RETRIES:
                raise
            _log.info("transient API error; retrying in %.0fs", wait)
            time.sleep(wait)
    raise RuntimeError("unreachable")  # pragma: no cover


def _retry_wait(exc: Exception) -> float | None:
    """Seconds to wait before retrying a transient API error, or None if not worth it.

    Retryable: a per-*minute* 429 throttle (honor the server's suggested delay) and
    a transient 503/500 overload (short backoff). NOT retryable: a per-*day* free-tier
    exhaustion — waiting seconds can't clear it, so we fall back to the mock at once.
    """

    text = str(exc)
    if "429" in text or "RESOURCE_EXHAUSTED" in text:
        if re.search(r"per\s*day|RequestsPerDay", text, re.IGNORECASE):
            return None
        m = re.search(r"retry(?:Delay)?[\"']?[:\s]+['\"]?([\d.]+)s", text, re.IGNORECASE)
        return min((float(m.group(1)) if m else 5.0) + 1.0, _MAX_WAIT_S)
    if "503" in text or "UNAVAILABLE" in text or "500" in text or "INTERNAL" in text:
        return 4.0
    return None


# Local (Ollama/LM Studio) models don't get ADK's `output_schema` constraint, so we
# spell out the JSON shape and parse defensively instead.
_JSON_SHAPE_INSTRUCTION = (
    "/no_think\n"
    "Do NOT write any analysis, reasoning, or 'thinking process'. Your entire reply "
    "must be ONE JSON object and nothing else — no prose, no markdown fences, no "
    "<think>. Start at '{' and end at '}'. Top-level keys MUST be \"steps\" and "
    '"changes" (not a bare array, not a single step). '
    'Shape: {"steps": [{"place_id": "<an id from the candidate list>", '
    '"start_hour": 9.5, "duration_h": 1.5}], "changes": ["<short note per fix>"]}. '
    "Use 2-4 steps; `changes` may be an empty list."
)


def _build_model() -> tuple[object, bool]:
    """Return (model arg for LlmAgent, whether to use ADK's output_schema).

    Gemini supports schema-constrained output; local OpenAI-compatible models go
    through LiteLLM where we instruct the JSON shape and parse it ourselves.
    """

    if backend() == "local":
        from google.adk.models.lite_llm import LiteLlm

        model = LiteLlm(
            model=f"openai/{_local_model()}",
            api_base=_local_base_url(),
            api_key=os.environ.get("FEASIBLEPLAN_LLM_API_KEY", "not-needed"),
        )
        return model, False
    return model_name(), True


async def _run_async(instruction: str, prompt: str) -> _PlanResult:
    # Imported lazily so the package imports fine even if ADK is unavailable.
    from google.adk.agents import LlmAgent
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    model, use_schema = _build_model()
    kwargs = {"output_schema": _PlanResult, "output_key": "plan"} if use_schema else {}
    instr = instruction if use_schema else f"{instruction}\n\n{_JSON_SHAPE_INSTRUCTION}"
    user_text = prompt if use_schema else f"{prompt}\n\n/no_think Return ONLY the JSON object."
    # Low temperature for stable JSON; large token budget so even a chatty/thinking
    # local model still reaches and completes the JSON.
    config = types.GenerateContentConfig(temperature=0.2, max_output_tokens=4096)

    agent = LlmAgent(
        name="planner", model=model, instruction=instr, generate_content_config=config, **kwargs
    )
    runner = InMemoryRunner(agent=agent, app_name=_APP)
    await runner.session_service.create_session(app_name=_APP, user_id=_USER, session_id=_SESSION)

    message = types.Content(role="user", parts=[types.Part(text=user_text)])
    texts: list[str] = []
    async for event in runner.run_async(
        user_id=_USER, session_id=_SESSION, new_message=message
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if getattr(part, "text", None):
                    texts.append(part.text)

    final_text = texts[-1] if texts else ""
    if os.environ.get("FEASIBLEPLAN_DEBUG_RAW"):
        _log.warning("RAW: %d part(s), last len=%d", len(texts), len(final_text))
        _log.warning("RAW FULL: %r", final_text[:4000])

    return _PlanResult.model_validate(_extract_plan(final_text))


def _extract_plan(text: str) -> dict:
    """Find the best JSON plan in a model response.

    Scans every '{'/'[' position, decodes the JSON value there, and keeps the richest
    valid plan (most steps). This tolerates chain-of-thought prose, markdown fences,
    trailing text, and — crucially — stray brackets like `[closed]` that appear when a
    model echoes the violations before (or instead of) the real JSON.
    """

    t = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    t = re.sub(r"<think>.*$", "", t, flags=re.DOTALL | re.IGNORECASE)  # unclosed/truncated
    dec = json.JSONDecoder()
    best: dict | None = None
    for m in re.finditer(r"[\[{]", t):
        try:
            value, _ = dec.raw_decode(t[m.start() :])
        except json.JSONDecodeError:
            continue  # stray bracket (e.g. `[closed]`) or partial JSON — skip
        plan = _coerce_plan(value)
        steps = plan.get("steps") if isinstance(plan, dict) else None
        if isinstance(steps, list) and steps and all(isinstance(s, dict) for s in steps):
            if best is None or len(steps) > len(best["steps"]):
                best = plan  # prefer the full itinerary over a single-step example
    if best is None:
        raise ValueError("no usable JSON plan in model output")
    return best


def _coerce_plan(value) -> dict:
    """Normalize common LLM shapes into the {"steps": [...], "changes": [...]} object.

    Some models ignore the wrapper and return a bare list of steps, or a single
    step object; accept those rather than failing to the mock unnecessarily.
    """

    if isinstance(value, list):
        return {"steps": value, "changes": []}
    if isinstance(value, dict):
        if "steps" in value:
            return value
        if "place_id" in value:  # a single bare step
            return {"steps": [value], "changes": []}
    return value  # leave anything else for pydantic to reject with a clear error


def _to_itinerary(
    result: _PlanResult, request: TripRequest, places: dict[str, Place]
) -> Itinerary:
    steps = [
        ItineraryStep(s.place_id, float(s.start_hour), float(s.duration_h))
        for s in result.steps
        if s.place_id in places  # drop hallucinated ids; verifier guards the rest
    ]
    if not steps:
        raise ValueError("LLM returned no usable steps")
    return Itinerary(date_weekday=request.date_weekday, steps=steps)
