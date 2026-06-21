# FeasiblePlan — 5-minute demo video script & storyboard

**Target:** ≤ 5:00, public on YouTube. **Narration:** English (~700 words ≈ 150 wpm).
**Goal:** make the "plausible vs. doable" gap *visible*, then show the agent close it.

Recording tips
- **Main demo is the web UI** (`uv run python -m kaggle_vibecoding_agents_capstone_project.web`
  → http://localhost:8000). Browser zoom ~110%, dark theme.
- For a **snappy, reproducible** UI use the deterministic mock (`FEASIBLEPLAN_BACKEND=mock`) —
  instant. Show a **local LLM** (`qwen/qwen3.6-27b`) or **Gemini** run once to prove it's
  real, then cut. (27B takes ~1–2 min/plan — record, then speed up/cut.)
- Keep a terminal handy for the eval (Scene 4); large font (≥ 18pt).

---

## Scene 1 — The hook (0:00–0:30)

**On screen:** A pretty AI itinerary (slide) with four stops. Then red stamps drop on it:
"CLOSED MONDAY", "RAINING ☔", "NO TIME TO TRANSFER", "OVER BUDGET".

**Narration:**
> Ask any AI for a day in Kyoto and you get a beautiful plan. Then reality hits. The
> museum is closed on Mondays. The garden is outdoor — and it's raining at 3pm. The
> transfer is impossible. You're over budget. It was *plausible*. It just wasn't
> *doable*. That gap is the default failure of AI planners — and it's what FeasiblePlan
> fixes.

## Scene 2 — The idea & architecture (0:30–1:10)

**On screen:** The architecture diagram (from the README / cover). Highlight Planner
("creativity") vs Verifier ("source of truth") and the repair loop arrow.

**Narration:**
> FeasiblePlan splits the work. A Planner — an LLM on Google's ADK — does the creative
> part: proposing an interesting day. A Verifier — plain, deterministic code — is the
> source of truth: it checks every step against opening hours, weather, travel time,
> budget, and your time window. An Orchestrator runs a plan-verify-repair loop: the
> Verifier's violations go back to the Planner until the plan is actually feasible.
> Crucially, the Planner is never told the weather — so, like a real LLM, it can make a
> genuine mistake. Catching that mistake is the whole point.

## Scene 3 — Live demo in the web UI (1:10–2:40)

**On screen:** The web UI at localhost:8000. Pick **Monday**, keep the defaults, click
**Plan my day**. The result panel fills in: a red "Raw plan had 2 problems" block, then
a green "Auto-repaired" block, then the verified timeline with a **✓ feasible** badge.
(Cursor-trace red → green → ✓.)

**Narration:**
> Let's plan a Monday in Kyoto. The Planner drafts a day — and instantly the Verifier
> flags two real problems, in red: the National Museum is closed on Mondays, and an
> outdoor stop collides with afternoon rain. Now watch: the repair loop hands those
> violations back, and the Planner swaps in an open, indoor alternative for each — in
> green. The result is a verified, feasible itinerary. Not a plausible plan. A doable
> one — and you can see exactly what was wrong and how it was fixed.

**On screen (2:20–2:40):** Click **Confirm & Book**; the "✓ Booked — contact redacted in
logs" message appears.

**Narration:**
> And because a concierge takes real actions, booking is gated: it only happens when a
> human clicks confirm — and the traveler's contact details are redacted from the logs.
> The agent never books on its own.

## Scene 4 — Proof, not vibes: the eval (2:40–3:30)

**On screen:** Run `uv run python -m kaggle_vibecoding_agents_capstone_project.eval`.
Hold on the final table; highlight **40% → 100%**.

**Narration:**
> A claim deserves a number. Across five scenarios — different days, weather, and
> budgets — we measure feasibility before and after our loop. The raw planner's plans
> are feasible only forty percent of the time. After verify-and-repair: one hundred
> percent. A sixty-point lift. And this reproduces on both Gemini and a fully local
> model — a capable LLM still ships broken plans on hard days; the self-verification
> loop is what closes the gap.

## Scene 5 — Concepts & no lock-in (3:30–4:20)

**On screen:** Quick bullets appear as narrated. Then show `.env` toggling backends:
`FEASIBLEPLAN_BACKEND=local` → run shows `local (qwen/qwen3.6-27b …)`.

**Narration:**
> Under the hood it brings together the course concepts: multi-agent orchestration on
> ADK, tool use for ground truth, persistent memory for preferences, security with PII
> redaction and human-in-the-loop, and a real evaluation. And there's no vendor
> lock-in: the same agent runs on Gemini, on a local model through Ollama or LM Studio,
> or on a deterministic offline mock — and any LLM failure falls back safely, so it
> never crashes. It can run completely offline.

## Scene 6 — Close (4:20–5:00)

**On screen:** Repo URL + "FeasiblePlan — doable, not just plausible." Cover image.

**Narration:**
> FeasiblePlan is an honest MVP: next is real map data over MCP, live weather, and a
> learning profiler. But the core idea already works — a concierge that *proves its
> plans are runnable* before handing them to you. Code's public, linked below. Thanks
> for watching.

---

### Shot checklist
- [ ] Problem slide with red "broken" stamps (Scene 1)
- [ ] Architecture diagram still (Scene 2) — reuse `docs/cover.svg` / README diagram
- [ ] **Web UI**: Monday → Plan my day → red problems → green repairs → ✓ feasible → Confirm & Book (Scene 3)
- [ ] Terminal: `eval` run, 40%→100% table (Scene 4)
- [ ] Backend badge in the UI (mock / gemini / local) — or `.env` toggle (Scene 5)
- [ ] Close card with repo URL + tagline (Scene 6)
