# vibecoding-agents-capstone-project（日本語版）

> English: [README.md](README.md)

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

```text
[Orchestrator]
  ├─ Profiler/Memory  … 嗜好を長期記憶から読込・更新
  ├─ Planner (LLM)    … 候補旅程をドラフト（gemini / local / mock）
  ├─ Tools            … 天気 / 場所 / 移動時間（将来: Maps MCP）
  └─ Verifier/Critic  … 制約照合 → 違反検出（決定論コード＝信頼の源）
        ↑↓ repair loop（違反があればPlannerへ差し戻し）
  → 検証済み旅程 ＋「実行可能性レポート」
```

→ Concierge要件「個人情報を安全に保つ」に合わせ、PII配慮（`security.redact`）と予約前の human-in-the-loop を組み込み。

## 提出物・評価（公式）

提出物（「New Writeup」→保存→右上「Submit」）:

1. **Kaggle Writeup** — トラック選択必須、**2,500語以内**、**カバー画像 必須**（下書き: [docs/WRITEUP.md](docs/WRITEUP.md)）
2. **動画** — Media Galleryに添付、**5分以内・YouTube公開**（必須）（台本: [docs/VIDEO_SCRIPT.md](docs/VIDEO_SCRIPT.md)）
3. **プロジェクトリンク** — 公開デモURL。無理なら**公開リポジトリ＋詳細セットアップ手順**

**評価（100点）**: Pitch 30（コンセプト10＋動画10＋Writeup10）＋ Implementation 70。デプロイは必須でない（加点的）。

## 提出チェックリスト

- [x] コンペに Join
- [x] トラック決定（**Concierge Agents**）
- [x] エージェント実装（ADK：orchestrator＋planner(ADK LlmAgent)＋verifier＋profiler）
- [x] ≥3コンセプトを実証（multi-agent(ADK) / Tool use / Memory / **Security・HITL** / **Eval** / **Deployability**）
- [x] 公開リポジトリ＋手順 ＋ **Web UI（FastAPI）＋ Dockerfile（Cloud Run / HF Spaces 可）**
- [ ] 5分動画（YouTube）… 台本済（撮影/UP は要作業）
- [ ] Writeup（≤2,500語・カバー画像）→ **Submit**（下書き＋カバー済・最終Submit は要作業）

## セットアップ／実行

```bash
uv sync

# オフライン（キー不要・mock）で end-to-end 実行
uv run python -m kaggle_vibecoding_agents_capstone_project.agent   # plan → verify → repair → 予約ゲート
uv run python -m kaggle_vibecoding_agents_capstone_project.eval    # 実行可能性 BEFORE→AFTER
uv run python -m kaggle_vibecoding_agents_capstone_project.web     # Web UI: http://localhost:8000
```

実LLMを使う場合は `.env` を用意（gitignore済み・絶対コミットしない。雛形: `.env.example`）:

- **クラウド（Gemini）**: `GOOGLE_API_KEY=...`（<https://aistudio.google.com/apikey> で無料発行）
- **ローカル（Ollama / LM Studio）**: `FEASIBLEPLAN_BACKEND=local` ＋ base URL ＋ ロード済みモデル名
  （キー・課金不要・完全オフライン。ADKの`LiteLlm`経由）

Planner は **gemini / local / mock** の3バックエンドを自動選択し、LLMが失敗しても**mockに自動フォールバック**（落ちない）。
Verifier は常に決定論的で、実行可能性の判定は LLM に依存しない。

## Web UI（デモ画面）

「Plan my day」で **素案の問題（赤）→ 自動修正（緑）→ ✓ feasible な旅程 → Confirm & Book（HITL）** が一画面で見えます。

![FeasiblePlan Web UI](docs/ui.png)

**Deployability**: HTML＋APIを**1コンテナ**に同梱（`Dockerfile`）。

```bash
docker build -t feasibleplan . && docker run -p 8000:8000 feasibleplan
# Cloud Run:  gcloud run deploy feasibleplan --source .
# 公開デモは mock 固定 → キー不要・外部通信ゼロ・課金0・落ちない
```

## リンク

- コンペ: <https://www.kaggle.com/competitions/vibecoding-agents-capstone-project>
- 設計/提出ドキュメント: [docs/WRITEUP.md](docs/WRITEUP.md) / [docs/VIDEO_SCRIPT.md](docs/VIDEO_SCRIPT.md)
