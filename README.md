---
title: FeasiblePlan
emoji: 🗺️
colorFrom: green
colorTo: blue
sdk: docker
app_port: 8000
pinned: false
---

# FeasiblePlan — a travel concierge that returns itineraries you can *actually run*

> 日本語: [README-ja.md](README-ja.md) · Full writeup: [docs/WRITEUP.md](docs/WRITEUP.md)

Capstone submission for the **5-Day AI Agents: Intensive Vibe Coding Course with Google**
(Concierge Agents track). FeasiblePlan plans a day out and **proves it's doable** — a
deterministic Verifier checks every step against real constraints and a repair loop fixes
any violations, so the plan you get isn't just *plausible*, it actually works.

- package: `kaggle_vibecoding_agents_capstone_project` · python 3.12

## The idea

Most AI travel planners hand you a *plausible* itinerary that breaks in the real world:
a museum that's **closed on Mondays**, an outdoor stop **in the afternoon rain**, a
transfer with **no time to make it**, a day that's **over budget**. FeasiblePlan splits
the work so that can't happen:

- A **Planner** (LLM) does the creative part — proposing an interesting day.
- A **Verifier** (plain, deterministic code) is the source of truth — it checks opening
  days/hours, weather, travel time, budget and the day window. It never hallucinates.
- An **Orchestrator** runs a **plan → verify → repair** loop: the Verifier's violations
  go back to the Planner until the itinerary is feasible.

```text
[Orchestrator]              (root agent — owns the control flow)
  ├─ Profiler / Memory      load long-term preferences
  ├─ Planner (LLM)          draft an itinerary   ← creativity lives ONLY here
  ├─ Tools                  weather · places · travel time   (future: Maps MCP)
  └─ Verifier (code)        check open-days/hours, weather, travel, budget, day-window
        ↑↓  repair loop: violations → Planner → re-verify  (≤3 iterations)
  → a verified itinerary + a "feasibility report"
```

**Does it work?** Measured across 5 scenarios: a raw planner's plans are feasible **40%**
of the time; after verify→repair, **100%** — a +60-point lift that reproduces on both
Gemini and a local model. (See `eval.py`.)

## Course concepts demonstrated (≥3 required → six here)

- **Multi-agent orchestration (Google ADK)** — Planner is an ADK `LlmAgent`; Orchestrator,
  Verifier and Profiler are distinct roles (`roles/`).
- **Tool use** — weather, curated places, travel-time estimator (`tools/`).
- **Sessions & Memory** — user preferences persist across runs (`memory.py`).
- **Security & human-in-the-loop** — PII redaction in logs + booking gated behind explicit
  human approval (`security.py`, `orchestrator.book`).
- **Evaluation** — the feasibility metric above (`eval.py`).
- **Deployability** — one-page web UI + single-container `Dockerfile`.

No vendor lock-in: the Planner runs on **Gemini**, a **local LLM** (Ollama / LM Studio via
ADK's `LiteLlm`), or a deterministic **mock** — auto-selected, with safe fallback to the
mock on any LLM failure, so it can run **completely offline**.

## Setup & run

```bash
uv sync

# Offline (no key, deterministic mock) — runs end to end:
uv run python -m kaggle_vibecoding_agents_capstone_project.agent   # plan → verify → repair → booking gate
uv run python -m kaggle_vibecoding_agents_capstone_project.eval    # BEFORE→AFTER feasibility
uv run python -m kaggle_vibecoding_agents_capstone_project.web     # web UI at http://localhost:8000
```

To use a real LLM, create a `.env` (gitignored — never commit it; see `.env.example`):

- **Cloud (Gemini):** `GOOGLE_API_KEY=...` — free key from <https://aistudio.google.com/apikey>
- **Local (Ollama / LM Studio):** `FEASIBLEPLAN_BACKEND=local` + a base URL + a model you've
  loaded — no key, no quota, fully offline (via ADK's `LiteLlm`).

The Verifier is always deterministic; feasibility never depends on the LLM.

## Web UI & deployment

Click **Plan my day** to see the whole story on one screen: the raw plan's problems (red)
→ auto-repairs (green) → a verified itinerary with a ✓ feasible badge → a **Confirm & Book**
human-in-the-loop button.

![FeasiblePlan web UI](docs/ui.png)

HTML and API ship in **one container**, so it deploys as-is (Deployability):

```bash
docker build -t feasibleplan . && docker run -p 8000:8000 feasibleplan   # http://localhost:8000
# Cloud Run:        gcloud run deploy feasibleplan --source .
# Hugging Face:     bash scripts/deploy-hf.sh   (Docker Space; config is in this README's frontmatter)
```

A public deploy defaults to `FEASIBLEPLAN_BACKEND=mock`: no API key, no quota, **no external
API calls**, no model cost — yet it tells the same verify→repair story and never breaks.

## Submission checklist

- [x] Joined the competition · track = **Concierge Agents**
- [x] Agent implemented (ADK: orchestrator + planner + verifier + profiler)
- [x] ≥3 concepts (multi-agent · tool use · memory · **security/HITL** · **eval** · **deployability**)
- [x] Public repo + setup + **web UI (FastAPI) + Dockerfile (Cloud Run / HF Spaces)**
- [x] 5-minute video (YouTube): <https://www.youtube.com/watch?v=iZKr5ak4n2I>
- [x] **Submitted** — Writeup (≤2,500 words + cover) on Kaggle ✅

## Links

- Competition: <https://www.kaggle.com/competitions/vibecoding-agents-capstone-project>
- Submitted Writeup: <https://www.kaggle.com/competitions/vibecoding-agents-capstone-project/writeups/feasibleplan-itineraries-you-can-actually-run>
- Live demo: <https://concigel-feasibleplan.hf.space> · Video: <https://www.youtube.com/watch?v=iZKr5ak4n2I>
- Writeup source: [docs/WRITEUP.md](docs/WRITEUP.md) · Video script: [docs/VIDEO_SCRIPT.md](docs/VIDEO_SCRIPT.md)
- 日本語版 README: [README-ja.md](README-ja.md)
