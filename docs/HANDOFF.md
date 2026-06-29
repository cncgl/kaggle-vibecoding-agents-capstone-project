# HANDOFF — FeasiblePlan（次セッション用の引き継ぎ）

最終更新: 2026-06-29 / 作業者メモ。別セッションで続きをやるための「構想」と「現状」。

> ✅ **提出済み（2026-06-29）**。Kaggle Writeup を Submit 完了（締切 2026-07-06 より前）。
> - Writeup: <https://www.kaggle.com/competitions/vibecoding-agents-capstone-project/writeups/feasibleplan-itineraries-you-can-actually-run>
> - 動画(YouTube公開): <https://www.youtube.com/watch?v=iZKr5ak4n2I>
> - 公開デモ(HF Spaces, mock固定): <https://concigel-feasibleplan.hf.space>
> - 公開リポ: <https://github.com/cncgl/kaggle-vibecoding-agents-capstone-project>
> 締切までは Writeup の編集可。残タスクは任意のブラッシュアップのみ（必須作業なし）。

## 1. 構想（何を作るか・なぜ勝てるか）

**FeasiblePlan** = "plausibleではなく **doable** な旅程を出す" 旅行/外出コンシェルジュ。
提出トラックは **Concierge Agents**（公式説明に "planning" が明記、ど真ん中）。

差別化の核：多くの旅行エージェントのデモは*もっともらしいが現実に破綻した*旅程を出す
（休館・移動不能・雨天の屋外・予算超過）。FeasiblePlanは **Verifierエージェント** が各ステップを
実データ（営業時間・移動時間・天気・予算）に照合し、違反があれば **自動修正（repairループ）** する。

設計の全体像・10時間プラン・評価ルーブリックは
`../kaggle-5-day-ai-agents-intensive-vibecoding-course-with-google/capstone.md` に集約。

## 2. 現状（どこまでできているか）

✅ **動く骨格が完成**。APIキー不要・オフラインで end-to-end 実行できる。

```
uv run python -m kaggle_vibecoding_agents_capstone_project.agent
```

実行すると、サンプル（京都・月曜）で **plan → verify → repair** が走る:

- 初期違反を検出: 「Kyoto National Museum は月曜休館」「Botanical Garden は屋外×午後の雨」
- 自動修正: Sanjusangen-do（室内・月曜営業）/ Kyoto Aquarium（室内）へスワップ
- 結果: feasible な旅程（1イテレーションで解決）
- 出力1行目に `Planner backend: mock | gemini (...)` を表示

→ アーキテクチャと"自己検証・自己修正"の価値はこの時点で実証済み。

✅ **Planner を Google ADK に配線済み**（2026-06-21）。`roles/planner_llm.py` が ADK `LlmAgent` で
draft/repair を実装。**3バックエンドを自動選択**（`backend()`）:

- **gemini** … Gemini API（要キー）。`output_schema`で構造化出力。実機検証済（live 40%→100%）。
- **local** … Ollama / LM Studio（OpenAI互換）を ADK `LiteLlm` 経由で。**キー・課金不要・完全オフライン**。
  JSON指示＋防御パース（配列/単一ステップ/think/末尾ゴミを吸収、max_output_tokens=2048）。
  **LM Studio `qwen/qwen3.6-27b` で実機検証済（フォールバック0・初手feasible）**。小型3Bは収束不安定→mock救済。
- **mock** … 決定論フォールバック。`FEASIBLEPLAN_BACKEND=mock` で明示強制も可。

`planner.py` がディスパッチし、**LLM失敗（無キー/429/壊れJSON）時は常にmockへフォールバック**＝デモは絶対に落ちない。
切替は `.env`（`FEASIBLEPLAN_BACKEND` / `FEASIBLEPLAN_LLM_*`）。**残:** Maps MCP / live weather は未（mock/curated）。

**セットアップ（実LLMを使う場合）**:

```bash
cp .env.example .env   # GOOGLE_API_KEY を https://aistudio.google.com/apikey で発行して貼る
uv run python -m kaggle_vibecoding_agents_capstone_project.agent  # backend が gemini (...) になる
```

キーは `.env`（gitignore済み）にのみ置く。**絶対コミットしない**。

## 3. ファイル構成（どこに何があるか）

```
src/kaggle_vibecoding_agents_capstone_project/
  agent.py            # 入口: サンプル実行＋実行可能性レポート表示
  models.py           # データモデル（全役割の共通契約: dataclass）
  memory.py           # 長期記憶（preferences）JSON永続
  roles/
    orchestrator.py   # ★ plan→verify→repair ループ（root agent）。# trace: 印あり
    planner.py        # ★ ディスパッチャ: キーあれば planner_llm、無ければ _mock_* へ
    planner_llm.py    # ★ ADK LlmAgent + 構造化出力で draft/repair（Gemini本体）
    verifier.py       # 制約チェック→違反リスト（決定論的＝信頼の源）
    profiler.py       # 嗜好の load/更新（memory のラッパ）
  tools/
    weather.py        # demo: 午後雨。real open-meteo 関数も同梱（キー不要）
    places.py         # curated 京都データ。TODO: Maps MCP サーバに差し替え
.env.example          # GOOGLE_API_KEY のひな形（コピーして .env に）
docs/HANDOFF.md       # このファイル
```

設計判断: **Verifierは決定論的**（信頼性が価値）、**LLMの創造性はPlannerだけ**に閉じ込める。
MVPは曜日ベース（実日付でなく）で決定論的に動く。コアはstdlibのみ（依存はLLM配線時に追加）。

## 4. 次にやること（優先順）

1. **【配線済→残ライブ検証】Planner を Gemini/ADK に**（`planner_llm.py`）。シグネチャ維持・violationsを
   プロンプトでrepairに渡す・mockフォールバック完備。**残: 実キーで1回走らせ** `Planner backend: gemini (...)`
   を確認し、LLM出力の質・違反パターンを見てプロンプト微調整。
2. **places を Maps MCP サーバに差し替え**（Day 2）。`get_places`/`travel_minutes` の戻り値型を保てば他は無改修。
3. **天気を live に**: `weather.get_rainy_hours` → `fetch_precipitation_hours` に切替（実座標/日付を request から）。
4. **Profiler を本実装**: 保存prefsの実マージ＋旅行後フィードバックで学習（memoryは"ヒント"扱い）。
5. **Observability**: orchestrator の `# trace:` 箇所に OpenTelemetry トレースを入れる（Day 4。ADKで依存導入済）。
6. ✅ **済: Concierge/Security 要件**: `security.redact`（PIIマスク）＋`orchestrator.book`（予約=不可逆操作の
   前に human-in-the-loop 承認）。`agent.py`が y/N で承認、非TTY時は安全側で拒否。
7. ✅ **済: Web UI＋デプロイ足場**: `web.py`（FastAPI）＋`static/index.html`（1枚・ビルド工程なし）で
   plan→verify→repair→HITL予約を一画面表示（スクショ `docs/ui.png`）。`Dockerfile`同梱で1コンテナ＝
   Cloud Run可（`gcloud run deploy --source .`）。**残: 実デプロイ（任意・課金）して公開URLを取得**。
8. **提出物**: ✅下書き済（[WRITEUP.md](WRITEUP.md) / [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md) / [cover.png](cover.png)）。
   **残: 動画撮影→YouTube公開 / Kaggle WriteupにペーストしてSubmit**。

## 5. 提出ルーブリックとの対応（≥3コンセプト）

| コンセプト | 本実装での担保 | 状態 |
| --- | --- | --- |
| マルチエージェント(ADK) | orchestrator＋planner(ADK LlmAgent)＋verifier＋profiler | 骨格✅ / ADK配線✅(ライブ検証残) |
| Tool use / MCP | weather＋Maps MCP | weather✅(mock) / MCP TODO |
| Sessions & Memory | preferences 永続 | ✅(JSON) |
| Observability | trace points | 印のみ / 実装TODO |
| Security | PII配慮＋human-in-the-loop | ✅ `security.redact`＋`orchestrator.book`(予約前HITLゲート) |
| Eval | 実行可能性% 指標 | ✅ `eval.py`（実Gemini 40%→100% / mock 20%→100% / 27B 40%→100%） |
| Deployability | UI＋コンテナ | ✅ `web.py`(FastAPI)＋`static/index.html`＋`Dockerfile`（Cloud Run可）/ 実デプロイは残 |

→ 3つ縛りに対し**6コンセプト**で余裕。実証済: multi-agent(ADK)・Tool use・Memory・Security/HITL・Eval・Deployability。

## 6. 未決事項（決めたら進む）

- [ ] 最終デモの都市/範囲（MVPは京都固定。Maps MCPなら任意都市可）
- [ ] 個人 or チーム（最大4人）
- [ ] Day 5デプロイをやるか（課金 or read-along）
- [ ] 「今から行ける」当日プラン（現在地＋今の天気）を後付けするか（デモ映え）

## 7. 参考リンク

- 提出コンペ（要Join済み）: <https://www.kaggle.com/competitions/vibecoding-agents-capstone-project>
- 設計doc: `../kaggle-5-day-ai-agents-intensive-vibecoding-course-with-google/capstone.md`
- ADK/Agents CLI/MCP/skills は Day 2–5 の codelab（同コースの day*.md にリンク）
