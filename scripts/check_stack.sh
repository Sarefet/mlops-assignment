#!/usr/bin/env bash
# Quick health check for all assignment services (run on your Mac).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== Docker ==="
docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null | head -12 || echo "docker compose not running"

echo ""
echo "=== vLLM :8000 ==="
curl -sf --max-time 5 http://127.0.0.1:8000/health && echo " OK" || echo " NOT REACHABLE (is ./scripts/start_vllm_cpu.sh running?)"

echo ""
echo "=== Agent :8001 ==="
curl -sf --max-time 5 http://127.0.0.1:8001/health && echo " OK" || echo " NOT REACHABLE (start: uv run uvicorn agent.server:app --port 8001)"

echo ""
echo "=== Prometheus :9090 ==="
curl -sf --max-time 5 http://127.0.0.1:9090/-/healthy && echo " OK" || echo " NOT REACHABLE"

echo ""
echo "=== Grafana :3000 ==="
curl -sf --max-time 5 http://127.0.0.1:3000/api/health && echo " OK" || echo " NOT REACHABLE"

echo ""
echo "=== Langfuse :3001 ==="
curl -sf --max-time 5 http://127.0.0.1:3001/api/public/health && echo " OK" || echo " NOT REACHABLE"

echo ""
echo "=== Langfuse keys in .env ==="
grep -q '^LANGFUSE_PUBLIC_KEY=pk-' .env 2>/dev/null && echo "public key set" || echo "MISSING public key"
grep -q '^LANGFUSE_SECRET_KEY=sk-' .env 2>/dev/null && echo "secret key set" || echo "MISSING secret key"
