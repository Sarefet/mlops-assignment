#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -f evals/eval_set.jsonl ]]; then
  echo "Run scripts/dev_up.sh first (need eval_set.jsonl)"
  exit 1
fi

QUESTION=$(python3 -c "
import json
print(json.loads(open('evals/eval_set.jsonl').readline())['question'])
")
DB=$(python3 -c "
import json
print(json.loads(open('evals/eval_set.jsonl').readline())['db_id'])
")

echo "==> health"
curl -sf http://localhost:8001/health | jq .

echo "==> answer (first eval question)"
curl -sf -X POST http://localhost:8001/answer \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg q "$QUESTION" --arg db "$DB" \
    '{question: $q, db: $db, tags: {phase: "smoke", source: "local"}}')" | jq .

echo "OK"
