#!/usr/bin/env bash
# Run after vLLM + agent are healthy (./scripts/check_stack.sh).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Smoke test (1 question, may take 1-3 min on CPU vLLM)"
./scripts/smoke_test.sh

echo ""
echo "==> Mini eval (3 questions)"
uv run python evals/run_eval.py --limit 3 --out results/eval_smoke.json

echo ""
echo "==> Langfuse: open http://localhost:3001 and confirm a trace appeared"
echo "==> Grafana:  open http://localhost:3000 (admin/admin) → vLLM serving dashboard"
