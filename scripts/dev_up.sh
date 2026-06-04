#!/usr/bin/env bash
# Phase 0 local bootstrap (run from repo root).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> uv sync"
uv sync

if [[ ! -f .env ]]; then
  echo "==> cp .env.example .env"
  cp .env.example .env
  echo "    Edit .env for Langfuse keys after signing up at http://localhost:3001"
fi

if [[ ! -f evals/eval_set.jsonl ]]; then
  echo "==> load BIRD data (~500MB download)"
  uv run python scripts/load_data.py
else
  echo "==> eval_set.jsonl exists, skipping load_data (delete evals/eval_set.jsonl to re-download)"
fi

echo "==> docker compose up -d"
docker compose up -d

echo ""
echo "Next steps:"
echo "  1. Langfuse: http://localhost:3001 → create project → paste keys into .env"
echo "  2. vLLM (CPU dev):  ./scripts/start_vllm_cpu.sh"
echo "     vLLM (H100):     ./scripts/start_vllm_h100.sh"
echo "  3. Agent:           uv run uvicorn agent.server:app --host 0.0.0.0 --port 8001"
echo "  4. Smoke test:      ./scripts/smoke_test.sh"
echo "  5. Eval (3 q):      uv run python evals/run_eval.py --limit 3"
