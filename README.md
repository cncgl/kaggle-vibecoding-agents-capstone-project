# vibecoding-agents-capstone-project

**AI Agents: Intensive Vibe Coding Capstone Project** の提出用リポジトリ。
5-Day AI Agents: Intensive Vibe Coding Course With Google（2026/06/15–19）の集大成。

- slug: `vibecoding-agents-capstone-project`
- package: `kaggle_vibecoding_agents_capstone_project`
- python: 3.12

## コンペ概要

| 項目 | 内容 |
| --- | --- |
| コンペ | <https://www.kaggle.com/competitions/vibecoding-agents-capstone-project> |
| 種別 / 報酬 | Community（hackathon）/ **12 Swag**（各トラック上位3×4） |
| 締切 | **2026/07/06（月）23:59 PT**（= 07/07 06:59 UTC）。早期提出推奨（draftは審査対象外） |
| バッジ/証明書 | **Capstone参加者全員**に付与（2026年7月末まで） |
| 提出形式 | Kaggle **Writeup**（このリポジトリはコード/デモリンク用） |

コースで学んだ**主要コンセプトを3つ以上実証**する、実世界向けAIエージェントを構築する。

## 我々の作品: FeasiblePlan（Concierge Agents トラック）

**"plausibleではなく doable な旅程を出す" 旅行/外出コンシェルジュ。**

差別化の核：多くの旅行エージェントは*もっともらしいが現実に破綻した*旅程を出す（休館・移動不能・雨天の屋外・予算超過）。
FeasiblePlanは **Verifierエージェント** が各ステップを実データ（営業時間・移動時間・天気・予算）に照合し、
違反を見つけたら **自動修正（repairループ）** する。だから出てくる旅程は**実際に回せる**。

```
[Orchestrator]
  ├─ Profiler/Memory  … 嗜好を長期記憶から読込・更新
  ├─ Planner          … 候補旅程をドラフト (Gemini)
  ├─ Recon (Tools/MCP)… Maps MCP / 天気 / Web検索
  └─ Verifier/Critic  … 制約照合 → 違反検出
        ↑↓ repair loop（違反があればPlannerへ差し戻し）
  → 検証済み旅程 ＋「実行可能性レポート」
```

→ Concierge要件「個人情報を安全に保つ」に合わせ、PII配慮（trajectory eval / human-in-the-loop）を組み込む。

**詳細な設計ドキュメント**（10時間プラン・概念マッピング・writeup骨子）はコース側リポジトリに集約:
`../kaggle-5-day-ai-agents-intensive-vibecoding-course-with-google/capstone.md`

## 提出物・評価（公式）

提出物（「New Writeup」→保存→右上「Submit」）:

1. **Kaggle Writeup** — トラック選択必須、**2,500語以内**、**カバー画像 必須**
2. **動画** — Media Galleryに添付、**5分以内・YouTube公開**（必須）
3. **プロジェクトリンク** — 公開デモURL。無理なら**公開リポジトリ＋詳細セットアップ手順**

**≥3コンセプトの実証（提示場所）**: Antigravity→動画 / Security→コード or 動画 / Deployability→動画 / Agent skills(Agents CLI)→コード or 動画 / ほか multi-agent(ADK)・MCP。

**評価（100点）**: Pitch 30（コンセプト10＋動画10＋Writeup10）＋ Implementation 70（アーキ/コード/agent活用・tool use 50＋残り20）。デプロイは必須でない（加点的）。

## 提出チェックリスト

- [x] コンペに Join
- [ ] トラック決定（**Concierge Agents** 予定）
- [ ] エージェント実装（ADK / Agents CLI / Antigravity）
- [ ] ≥3コンセプトを実証（Antigravity / Agent skills / Security / Deployability …）
- [ ] デモ or 公開リポジトリ＋手順
- [ ] 5分動画（YouTube）
- [ ] Writeup（≤2,500語・カバー画像）→ **Submit**

## setup

```bash
uv sync
```

## 開発（予定）

本コンペは**データセットDL不要**（Writeup提出型）。実装は ADK / Agents CLI を用いたエージェントを `src/` 配下に構築する。

```bash
# オフライン（キー不要・mock Planner）で end-to-end 実行
uv run python -m kaggle_vibecoding_agents_capstone_project.agent
```

実LLM（Gemini via Google ADK）を使う場合は `.env` にキーを置く（gitignore済み・絶対コミットしない）:

```bash
cp .env.example .env   # GOOGLE_API_KEY を https://aistudio.google.com/apikey で発行して貼る
uv run python -m kaggle_vibecoding_agents_capstone_project.agent
# → 出力1行目が `Planner backend: gemini (gemini-2.5-flash, adk)` になる
```

Gemini無料枠が尽きた等でクラウドを使いたくない場合は、**ローカルLLM（Ollama / LM Studio）**にも切替可（キー・課金不要・完全オフライン）。ADKの`LiteLlm`経由で接続:

```bash
ollama pull llama3.2:3b   # 例（7-8Bモデルの方が安定）
# .env に:  FEASIBLEPLAN_BACKEND=local  /  FEASIBLEPLAN_LLM_MODEL=llama3.2:3b
uv run python -m kaggle_vibecoding_agents_capstone_project.agent
# → `Planner backend: local (llama3.2:3b @ http://localhost:11434/v1, adk+litellm)`
```

Planner は **gemini / local / mock** の3バックエンドを自動選択し、LLMが失敗しても**mockに自動フォールバック**（落ちない）。Verifier は常に決定論的で、実行可能性の判定は LLM に依存しない。

## リンク

- コンペ: <https://www.kaggle.com/competitions/vibecoding-agents-capstone-project>
- コース本体（教材/各日ログ/設計doc）: `../kaggle-5-day-ai-agents-intensive-vibecoding-course-with-google/`
- ADK / Agents CLI / Antigravity は Day 3–5 の codelab 参照
