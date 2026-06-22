#!/usr/bin/env bash
# Deploy the current `main` to the Hugging Face Space.
#
# Why a snapshot instead of `git push hf main`? HF Spaces rejects in-repo binary
# files unless they're in Git LFS. We keep the screenshots (docs/*.png) as normal
# files on GitHub (no LFS), so for HF we push a clean snapshot with the PNGs removed
# and the README image pointed at GitHub's raw URL (so it still renders on the Space).
# docs/ isn't needed to build the app anyway (it's in .dockerignore).
#
# One-time setup (already done if you've pushed before):
#   git remote add hf https://huggingface.co/spaces/<your-user>/feasibleplan
# Usage:
#   bash scripts/deploy-hf.sh      # enter your HF *write* token when prompted
set -euo pipefail

RAW="https://raw.githubusercontent.com/cncgl/kaggle-vibecoding-agents-capstone-project/main/docs"

git remote get-url hf >/dev/null 2>&1 || {
  echo "✗ No 'hf' remote. Add it first:"
  echo "    git remote add hf https://huggingface.co/spaces/<your-user>/feasibleplan"
  exit 1
}
git diff --quiet && git diff --cached --quiet || {
  echo "✗ Working tree not clean. Commit or stash changes first."
  exit 1
}

git checkout -q main
git branch -D hf-deploy >/dev/null 2>&1 || true

# Build a clean orphan snapshot of main without the binary PNGs.
git checkout -q --orphan hf-deploy
git rm -q --cached docs/cover.png docs/ui.png
sed -i "s#(docs/\(cover\|ui\)\.png)#(${RAW}/\1.png)#g" README.md
git add README.md
git commit -q -m "HF Spaces deploy snapshot (PNGs via raw GitHub URL; HF rejects in-repo binaries)"

echo "→ Pushing snapshot to HF (enter your HF write token when prompted)…"
git push hf hf-deploy:main --force

# Restore main and clean up.
git checkout -qf main
git branch -D hf-deploy >/dev/null 2>&1 || true
echo "✅ Pushed. Watch the build at your Space page; it serves on app_port 8000 (mock backend)."
