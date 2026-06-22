# FeasiblePlan — 5-minute demo video script & storyboard

**Target:** ≤ 5:00, public on YouTube. **Narration:** English (~700 words ≈ 150 wpm).
**Goal:** make the "plausible vs. doable" gap *visible*, then show the agent close it.

Recording setup (record on the Mac; the LLM runs locally on the Ubuntu box)
- **Main demo uses the REAL local LLM** — the `backend: local (qwen…)` badge on screen is the
  proof it's a genuine agent, and the repairs come back in *natural language* (not templated).
- LLM stays on Ubuntu (LM Studio). For a snappy take use a fast model
  (`qwen3-4b-instruct-2507`); `qwen/qwen3.6-27b` also works but is ~1–2 min/plan — record then
  speed-up/cut the wait.
- On **Ubuntu**, expose the UI on the LAN (keep it running through the whole shoot):
  ```bash
  # .env: FEASIBLEPLAN_BACKEND=local / FEASIBLEPLAN_LLM_BASE_URL=http://localhost:1234/v1 / FEASIBLEPLAN_LLM_MODEL=qwen3-4b-instruct-2507
  HOST=0.0.0.0 uv run python -m kaggle_vibecoding_agents_capstone_project.web
  ```
- On the **Mac**, open `http://192.168.24.67:8000` (or `…24.55`) and screen-record (QuickTime).
  Browser full-screen to hide the LAN URL; zoom ~110%, dark theme.
- **Warm up once** before recording (the first LLM call loads the model and is slow).
- Do a few takes and keep one where the Planner makes a *visible* mistake the Verifier catches
  (a real LLM varies — sometimes it nails it first try).
- The public **mock** deploy on Hugging Face is the always-on demo URL, shown briefly in Scene 5.

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

## Scene 3 — Live demo in the web UI, real local LLM (1:10–2:40)

**On screen:** The web UI (Mac browser → Ubuntu LAN). Point out the **`backend: local
(qwen…)`** badge first — this is a real LLM, not a script. Pick **Monday**, click **Plan
my day**. The result fills in: a red "Raw plan had N problems" block, then a green
"Auto-repaired" block (note the **natural-language** fixes, e.g. "Replaced … due to rain"),
then the verified timeline with a **✓ feasible** badge. (Cursor-trace badge → red → green → ✓.)

**Narration:** *(narrate to match your take — the exact violations vary run to run)*
> Let's plan a Monday in Kyoto — and notice the badge: this is a real local LLM. The
> Planner drafts a day, and instantly the Verifier flags real problems, in red — here a
> venue that's closed today and an outdoor stop that runs into the afternoon rain. Now
> watch the repair loop: those violations go back to the LLM, which swaps in open, indoor
> alternatives — and tells you why, in plain language. The result is a verified, feasible
> itinerary. Not a plausible plan. A doable one — and you can see exactly what was wrong
> and how it was fixed.

**On screen (2:20–2:40):** Click **Confirm & Book**; the "✓ Booked — contact redacted in
logs" message appears.

**Narration:**
> And because a concierge takes real actions, booking is gated: it only happens when a
> human clicks confirm — and the traveler's contact details are redacted from the logs.
> The agent never books on its own.

## Scene 4 — Proof, not vibes: the eval (2:40–3:30)

**On screen:** The eval table, **40% → 100%**. To get it on the Mac screen, either `ssh
<user>@192.168.24.67` and run `uv run python -m kaggle_vibecoding_agents_capstone_project.eval`
in the Mac terminal, or drop in a captured screenshot/slide of the table. (Runs on the same
local LLM — it reproduces 40%→100%; the 27B run takes a few minutes, so a slide is fine.)

**Narration:**
> A claim deserves a number. Across five scenarios — different days, weather, and
> budgets — we measure feasibility before and after our loop. The raw planner's plans
> are feasible only forty percent of the time. After verify-and-repair: one hundred
> percent. A sixty-point lift. And this reproduces on both Gemini and a fully local
> model — a capable LLM still ships broken plans on hard days; the self-verification
> loop is what closes the gap.

## Scene 5 — Concepts, no lock-in & it's deployed (3:30–4:20)

**On screen:** Quick bullets appear as narrated. Then open the **live public URL**
`https://concigel-feasibleplan.hf.space` in a new tab — same UI, running on Hugging Face
(its badge reads `backend: mock`). Briefly note the badge difference: local = real LLM,
deploy = deterministic mock.

**Narration:**
> Under the hood it brings together the course concepts: multi-agent orchestration on
> ADK, tool use for ground truth, persistent memory for preferences, security with PII
> redaction and human-in-the-loop, and a real evaluation. There's no vendor lock-in —
> the same agent runs on Gemini, on a local model, or on a deterministic offline mock,
> with safe fallback so it never crashes. And it's already deployed: here it is live on
> Hugging Face, running the mock so the public demo needs no keys and never breaks.

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
- [ ] **Web UI (real local LLM)**: show `backend: local (qwen…)` badge → Monday → Plan my day →
      red problems → green natural-language repairs → ✓ feasible → Confirm & Book (Scene 3)
- [ ] Eval 40%→100% table — ssh-run on Mac or a slide (Scene 4)
- [ ] **Live public URL** `concigel-feasibleplan.hf.space` (badge = mock) (Scene 5)
- [ ] Close card with repo URL + tagline (Scene 6)
- [ ] Warm up the LLM once before the real takes
