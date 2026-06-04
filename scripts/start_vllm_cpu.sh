#!/usr/bin/env bash
# Local dev: small model on CPU (no GPU). Use for agent/eval wiring on a laptop.
set -euo pipefail

# Must be an *instruct/chat* model (ChatOpenAI API needs a chat template).
# OPT/completion-only models (opt-125m) fail with HTTP 400 on /v1/chat/completions.
MODEL="${VLLM_MODEL:-Qwen/Qwen2.5-0.5B-Instruct}"

# vLLM 0.10+ auto-detects CPU when no CUDA; do not pass --device (removed).
export VLLM_TARGET_DEVICE="${VLLM_TARGET_DEVICE:-cpu}"
export VLLM_HOST_IP="${VLLM_HOST_IP:-127.0.0.1}"
export GLOO_SOCKET_IFNAME="${GLOO_SOCKET_IFNAME:-lo0}"
export VLLM_CPU_KVCACHE_SPACE="${VLLM_CPU_KVCACHE_SPACE:-4}"

exec uv run python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL" \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 2048 \
  --max-num-batched-tokens 2048 \
  --enforce-eager \
  --trust-remote-code
