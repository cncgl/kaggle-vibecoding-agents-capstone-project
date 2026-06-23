# Slide deck for the 5-minute demo video

Branded 1920×1080 slides for every scene except the live demo (Scene 3, which is a
screen recording). PNGs are ready to use; the `.svg` files are the editable source
(re-render with headless Chrome — see below). Narration text is in
[../VIDEO_SCRIPT.md](../VIDEO_SCRIPT.md) / [../VIDEO_SCRIPT-ja.md](../VIDEO_SCRIPT-ja.md).

| Scene | Time | Asset |
| --- | --- | --- |
| 1 — The hook | 0:00–0:30 | `slide1-problem.png` |
| 2 — Idea & architecture | 0:30–1:10 | `slide2-architecture.png` |
| 3 — Live demo | 1:10–2:40 | **screen recording** of the web UI (real local LLM) |
| 4 — Eval | 2:40–3:30 | `slide4-eval.png` |
| 5 — Concepts & deployed | 3:30–4:20 | `slide5-concepts.png` + ~5s screen capture of the HF URL |
| 6 — Close | 4:20–5:00 | `slide6-close.png` |

## Assembling the video (Mac)

1. Open **iMovie** (free) or **CapCut** / **ScreenFlow**.
2. Drop the slide PNGs on the timeline in order; set each to its scene length above.
3. Insert the **Scene 3 screen recording** between slide 2 and slide 4; speed up / cut the
   LLM wait so the plan→repair→feasible beat stays snappy.
4. Add narration: record a voiceover track (read the English lines from the script) and
   line it up with each slide, or narrate live while recording Scene 3.
5. Export **1080p** and upload to YouTube (public). Paste the link into the Writeup.

## Re-rendering a slide after editing its SVG

```bash
google-chrome --headless=new --disable-gpu --screenshot=slideX.png \
  --window-size=1920,1080 --default-background-color=00000000 slideX.svg
```
