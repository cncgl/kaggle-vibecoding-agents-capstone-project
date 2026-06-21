# HANDOFF — FeasiblePlan（次セッション用の引き継ぎ）

最終更新: 2026-06-21 / 作業者メモ。別セッションで続きをやるための「構想」と「現状」。

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

✅ **Planner を Google ADK（Gemini）に配線済み**（2026-06-21）。`roles/planner_llm.py` が
ADK `LlmAgent`＋構造化出力（`output_schema=_PlanResult`）で draft/repair を実装。
`planner.py` は「キーがあればGemini／無ければmock」に自動ディスパッチ。**キー無し・オフラインでも
常に動く**設計（LLM失敗時もmockへフォールバックしデモは絶対に落ちない）。
構造検証（schema往復・prompt生成・ADK構築・ハルシネid除去）は **済**。
**残:** 実キーでのライブ検証（下記セットアップ）。Maps MCP / live weather はまだ mock/curated。

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
7. **デプロイ（任意・加点）**: Agent Runtime / Cloud Run ＋ 簡易UI（Day 5、課金注意）。
8. **提出物**: 5分動画（before/after の実行可能性を見せる）＋ Writeup ≤2,500語＋公開リポリンク。

## 5. 提出ルーブリックとの対応（≥3コンセプト）

| コンセプト | 本実装での担保 | 状態 |
| --- | --- | --- |
| マルチエージェント(ADK) | orchestrator＋planner(ADK LlmAgent)＋verifier＋profiler | 骨格✅ / ADK配線✅(ライブ検証残) |
| Tool use / MCP | weather＋Maps MCP | weather✅(mock) / MCP TODO |
| Sessions & Memory | preferences 永続 | ✅(JSON) |
| Observability | trace points | 印のみ / 実装TODO |
| Security | PII配慮＋human-in-the-loop | ✅ `security.redact`＋`orchestrator.book`(予約前HITLゲート) |
| Eval | 実行可能性% 指標 | ✅ `eval.py`（実Gemini 40%→100% / mock 20%→100%） |

→ 3つ縛りに対し余裕。動画でAntigravity/Deployability、コードでskills/securityを見せる構成。

## 6. 未決事項（決めたら進む）

- [ ] 最終デモの都市/範囲（MVPは京都固定。Maps MCPなら任意都市可）
- [ ] 個人 or チーム（最大4人）
- [ ] Day 5デプロイをやるか（課金 or read-along）
- [ ] 「今から行ける」当日プラン（現在地＋今の天気）を後付けするか（デモ映え）

## 7. 参考リンク

- 提出コンペ（要Join済み）: <https://www.kaggle.com/competitions/vibecoding-agents-capstone-project>
- 設計doc: `../kaggle-5-day-ai-agents-intensive-vibecoding-course-with-google/capstone.md`
- ADK/Agents CLI/MCP/skills は Day 2–5 の codelab（同コースの day*.md にリンク）
