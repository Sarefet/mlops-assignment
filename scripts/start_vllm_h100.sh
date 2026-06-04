#!/usr/bin/env bash
# H100 production run — tune flags here for Phase 1 & 6, document in REPORT.md.
# Reference: https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html
set -euo pipefail

MODEL="${VLLM_MODEL:-Qwen/Qwen3-30B-A3B-Instruct-2507}"

# First knobs to try on H100 (one change per load-test iteration; log in REPORT.md):
#   --max-num-seqs N          more concurrent agent requests
#   --gpu-memory-utilization  0.85–0.95
#   --max-model-len           4096 vs 8192 (shorter = more KV headroom)
#   drop --enable-prefix-caching if memory-bound
# Docs: https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html

exec uv run python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL" \
  --host 0.0.0.0 \
  --port 8000 \
  --tensor-parallel-size 1 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90 \
  --enable-prefix-caching
