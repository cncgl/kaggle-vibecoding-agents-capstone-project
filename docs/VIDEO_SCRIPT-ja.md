# FeasiblePlan — 5分デモ動画 台本＆絵コンテ（日本語版）

> English: [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md)
> ナレーションは**英語で話す**ので、各シーンに「英語（実際に読む文）＋日本語訳」を併記します。

**目標:** ≤5:00 / YouTube公開 / ナレーション英語（約700語 ≈ 150wpm）。
**狙い:** 「plausible（もっともらしい）」と「doable（実際に回せる）」のギャップを*見える化*し、エージェントがそれを埋める様子を見せる。

## 撮影セットアップ（録画はMac、LLM推論はUbuntu）

- **メインデモは実ローカルLLM**を使う。画面の **`backend: local (qwen…)` バッジ**が「本物のエージェント」の証拠。repairは**自然言語**で返る（定型文ではない）。
- LLMはUbuntu（LM Studio）に置いたまま。軽快に見せるなら高速モデル（`qwen3-4b-instruct-2507`）。`qwen/qwen3.6-27b`でも可だが1プラン〜1〜2分なので**待ち時間は編集でカット/早送り**。
- **Ubuntu側**でUIをLAN公開（撮影中は起動したまま）:

  ```bash
  # .env: FEASIBLEPLAN_BACKEND=local / FEASIBLEPLAN_LLM_BASE_URL=http://localhost:1234/v1 / FEASIBLEPLAN_LLM_MODEL=qwen3-4b-instruct-2507
  HOST=0.0.0.0 uv run python -m kaggle_vibecoding_agents_capstone_project.web
  ```

- **Mac側**で `http://192.168.24.67:8000`（または `…24.55`）を開き画面録画（QuickTime）。ブラウザを全画面にしてLAN URLを隠す。ズーム約110%・ダークテーマ。
- **本番前に一度ウォームアップ**（初回のLLM呼び出しはモデルロードで遅い）。
- 何テイクか録り、**Plannerが見える形でミス→Verifierが検出**する良い回を採用（実LLMは回ごとに違い、一発で正解する回もある）。
- 公開URL（Hugging Faceの**mock**版）は常時稼働のデモURL。Scene 5で一瞬見せる。

---

## Scene 1 — つかみ（0:00–0:30）

**画面:** 4ステップの“きれいな”AI旅程（スライド）。そこに赤いスタンプが落ちる：「CLOSED MONDAY（月曜休館）」「RAINING ☔」「NO TIME TO TRANSFER（乗継不能）」「OVER BUDGET（予算超過）」。

**ナレーション（英語＝実際に話す）:**
> Ask any AI for a day in Kyoto and you get a beautiful plan. Then reality hits. The
> museum is closed on Mondays. The garden is outdoor — and it's raining at 3pm. The
> transfer is impossible. You're over budget. It was *plausible*. It just wasn't
> *doable*. That gap is the default failure of AI planners — and it's what FeasiblePlan
> fixes.

**訳:** どんなAIに京都の1日を頼んでも、きれいなプランが返ってくる。でも現実にぶつかる——博物館は月曜休館、庭園は屋外で午後3時は雨、乗継は不可能、予算オーバー。*もっともらしい*が*実際には回せない*。このギャップこそAIプランナーの典型的な失敗で、FeasiblePlanが直すものです。

## Scene 2 — アイデアとアーキテクチャ（0:30–1:10）

**画面:** アーキテクチャ図（README/カバー）。Planner（創造）と Verifier（信頼の源）、repairループの矢印を強調。

**ナレーション（英語）:**
> FeasiblePlan splits the work. A Planner — an LLM on Google's ADK — does the creative
> part: proposing an interesting day. A Verifier — plain, deterministic code — is the
> source of truth: it checks every step against opening hours, weather, travel time,
> budget, and your time window. An Orchestrator runs a plan-verify-repair loop: the
> Verifier's violations go back to the Planner until the plan is actually feasible.
> Crucially, the Planner is never told the weather — so, like a real LLM, it can make a
> genuine mistake. Catching that mistake is the whole point.

**訳:** FeasiblePlanは仕事を分けます。Planner（Google ADK上のLLM）は創造を担当し、面白い1日を提案。Verifier（素の決定論コード）は信頼の源で、各ステップを営業時間・天気・移動時間・予算・時間枠に照合。Orchestratorが plan→verify→repair ループを回し、Verifierの違反をPlannerに戻して、実際にfeasibleになるまで繰り返す。肝心なのは、**Plannerには天気を渡さない**こと——だから実LLMらしく本当にミスをし得る。そのミスを捕まえるのが核心です。

## Scene 3 — Web UIで実ローカルLLMの実演（1:10–2:40）

**画面:** Web UI（MacブラウザからUbuntu LAN）。まず **`backend: local (qwen…)` バッジ**を指し示す（＝スクリプトでなく実LLM）。**Monday**を選び **Plan my day** をクリック。結果が表示：赤の「Raw plan had N problems」→ 緑の「Auto-repaired」（**自然言語**の修正、例「Replaced … due to rain」に注目）→ **✓ feasible** バッジ付きの旅程タイムライン。（カーソルで バッジ→赤→緑→✓ をなぞる。）

**ナレーション（英語）:** *(採用テイクに合わせて読む——違反内容は回ごとに変わる)*
> Let's plan a Monday in Kyoto — and notice the badge: this is a real local LLM. The
> Planner drafts a day, and instantly the Verifier flags real problems, in red — here a
> venue that's closed today and an outdoor stop that runs into the afternoon rain. Now
> watch the repair loop: those violations go back to the LLM, which swaps in open, indoor
> alternatives — and tells you why, in plain language. The result is a verified, feasible
> itinerary. Not a plausible plan. A doable one — and you can see exactly what was wrong
> and how it was fixed.

**訳:** 京都の月曜を計画してみましょう——バッジに注目、これは実物のローカルLLMです。Plannerが1日を下書きすると、Verifierが即座に実際の問題を赤で指摘——ここでは今日休館の施設と、午後の雨にかかる屋外スポット。さあrepairループを見て：違反がLLMに戻され、開いている屋内の代替に入れ替え、しかも理由を平易な言葉で教えてくれる。結果は検証済みのfeasibleな旅程。もっともらしいプランではなく、実際に回せるもの——どこが問題で、どう直したかも一目で分かります。

**画面（2:20–2:40）:** **Confirm & Book** をクリック → 「✓ Booked — contact redacted in logs」表示。

**ナレーション（英語）:**
> And because a concierge takes real actions, booking is gated: it only happens when a
> human clicks confirm — and the traveler's contact details are redacted from the logs.
> The agent never books on its own.

**訳:** そしてコンシェルジュは実際の行動を取るので、予約にはゲートがある：人間がconfirmを押したときだけ実行され、旅行者の連絡先はログでマスクされる。エージェントが勝手に予約することはありません。

## Scene 4 — 雰囲気でなく証拠：Eval（2:40–3:30）

**画面:** Evalの表 **40% → 100%**。Mac画面に出すには、Macから `ssh <user>@192.168.24.67` してMacのターミナルで `uv run python -m kaggle_vibecoding_agents_capstone_project.eval` を実行するか、表のスクショ/スライドを差し込む。（同じローカルLLMで 40%→100% を再現。27Bは数分かかるのでスライドでも可。）

**ナレーション（英語）:**
> A claim deserves a number. Across five scenarios — different days, weather, and
> budgets — we measure feasibility before and after our loop. The raw planner's plans
> are feasible only forty percent of the time. After verify-and-repair: one hundred
> percent. A sixty-point lift. And this reproduces on both Gemini and a fully local
> model — a capable LLM still ships broken plans on hard days; the self-verification
> loop is what closes the gap.

**訳:** 主張には数字を。曜日・天気・予算の異なる5シナリオで、ループ前後のfeasibility（実行可能率）を測ります。素のPlannerのプランは40%しかfeasibleでない。verify＋repairの後は100%。+60ポイント。これはGeminiでも完全ローカルモデルでも再現する——優秀なLLMでも難しい日には破綻プランを出す。その差を埋めるのが自己検証ループです。

## Scene 5 — コンセプト・ロックインなし・そして公開済み（3:30–4:20）

**画面:** 箇条書きをナレーションに合わせて表示。続いて新しいタブで**公開URL** `https://concigel-feasibleplan.hf.space` を開く——同じUIがHugging Faceで稼働（バッジは `backend: mock`）。バッジの違いを一言：local＝実LLM、deploy＝決定論mock。

**ナレーション（英語）:**
> Under the hood it brings together the course concepts: multi-agent orchestration on
> ADK, tool use for ground truth, persistent memory for preferences, security with PII
> redaction and human-in-the-loop, and a real evaluation. There's no vendor lock-in —
> the same agent runs on Gemini, on a local model, or on a deterministic offline mock,
> with safe fallback so it never crashes. And it's already deployed: here it is live on
> Hugging Face, running the mock so the public demo needs no keys and never breaks.

**訳:** 内部ではコースのコンセプトが集約：ADK上のマルチエージェント、地に足のついた情報のためのツール使用、嗜好の永続メモリ、PIIマスク＋human-in-the-loopのセキュリティ、そして本物のEval。ベンダーロックインも無し——同じエージェントがGeminiでも、ローカルモデルでも、決定論オフラインmockでも動き、安全にフォールバックして落ちない。しかも既にデプロイ済み：ほら、Hugging Faceで稼働中——mockで動くので公開デモはキー不要・絶対に落ちません。

## Scene 6 — 締め（4:20–5:00）

**画面:** リポジトリURL ＋「FeasiblePlan — doable, not just plausible.」＋カバー画像。

**ナレーション（英語）:**
> FeasiblePlan is an honest MVP: next is real map data over MCP, live weather, and a
> learning profiler. But the core idea already works — a concierge that *proves its
> plans are runnable* before handing them to you. Code's public, linked below. Thanks
> for watching.

**訳:** FeasiblePlanは誠実なMVP：次はMCP経由の実地図データ、ライブ天気、学習するProfiler。でも核心は既に動いています——**プランが実際に回せると証明してから手渡す**コンシェルジュ。コードは公開、下にリンク。ご視聴ありがとうございました。

---

## ショット・チェックリスト

- [ ] 赤い“破綻”スタンプの問題スライド（Scene 1）
- [ ] アーキテクチャ図の静止画（Scene 2）— `docs/cover.svg` / README図を流用
- [ ] **Web UI（実ローカルLLM）**：`backend: local (qwen…)` バッジ提示 → Monday → Plan my day → 赤い問題 → 緑の自然言語repair → ✓ feasible → Confirm & Book（Scene 3）
- [ ] Eval 40%→100% の表 — Macからssh実行 or スライド（Scene 4）
- [ ] **公開URL** `concigel-feasibleplan.hf.space`（バッジ＝mock）（Scene 5）
- [ ] 締めカード：リポURL＋タグライン（Scene 6）
- [ ] 本番テイク前にLLMを一度ウォームアップ
