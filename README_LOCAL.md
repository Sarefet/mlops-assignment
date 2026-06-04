# Local development guide

Repo: [GlebBerjoskin/mlops-assignment](https://github.com/GlebBerjoskin/mlops-assignment)

## One-time setup

```bash
cd /Users/idan.shafat/my-repos/ml_ops_hw/inference-o11y
chmod +x scripts/*.sh
./scripts/dev_up.sh
```

**Mac note:** We pin `transformers<5` in `pyproject.toml` (vLLM breaks on transformers 5.x).
Local vLLM uses `facebook/opt-125m` on CPU; first LLM call can take 1–3 minutes.

**Faster local option:** Uncomment the OpenAI block in `.env` and skip vLLM entirely for agent/eval wiring.

## Run stack (4 terminals)

```bash
# T1 — observability (if not already up)
docker compose up -d

# T2 — vLLM (CPU on Mac)
./scripts/start_vllm_cpu.sh

# T3 — agent
uv run uvicorn agent.server:app --host 0.0.0.0 --port 8001

# T4 — smoke / eval
./scripts/smoke_test.sh
uv run python evals/run_eval.py --limit 3 --out results/eval_smoke.json
```

## Langfuse (Phase 4)

1. Open http://localhost:3001 → sign up locally
2. Create project → copy public/secret keys into `.env`
3. Restart agent server; POST with `"tags": {"phase": "eval", "run": "baseline"}`

## H100 slot (submission)

### 1. Push your work to GitHub (do this on Mac, once)

`origin` is the course template (`GlebBerjoskin/mlops-assignment`). You cannot push there.

```bash
# On github.com: Fork GlebBerjoskin/mlops-assignment → YOUR_USER/mlops-assignment
cd ~/my-repos/ml_ops_hw/inference-o11y
git remote add mine https://github.com/YOUR_GITHUB_USER/mlops-assignment.git
git add -A && git commit -m "HW2: agent, evals, grafana, local scripts"
git push -u mine main
```

Replace `YOUR_GITHUB_USER`. Course hand-in = link to **your** fork (or zip of this folder).

### 2. On the H100 VM (clone + env)

```bash
git clone https://github.com/YOUR_GITHUB_USER/mlops-assignment.git inference-o11y
cd inference-o11y
uv sync
uv run python scripts/load_data.py
docker compose up -d
cp .env.example .env
# Edit .env: HF_TOKEN, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY
# LANGFUSE_HOST=http://localhost:3001
# VLLM_MODEL=Qwen/Qwen3-30B-A3B-Instruct-2507
```

Langfuse keys: copy from your Mac `.env` (same project) or create a new project on the VM UI at http://localhost:3001.

### 3. Port forwards from laptop

**Cursor/VS Code:** Remote-SSH to VM → Ports → forward `3000`, `9090`, `3001`, `8000`, `8001`.

**Or SSH:**

```bash
ssh -L 3000:localhost:3000 -L 9090:localhost:9090 -L 3001:localhost:3001 \
    -L 8000:localhost:8000 -L 8001:localhost:8001 USER@VM_IP
```

Open on laptop: Grafana :3000 (`admin`/`admin`), Prometheus :9090, Langfuse :3001.

### 4. Run + Langfuse tags

```bash
./scripts/start_vllm_h100.sh          # terminal 1
uv run uvicorn agent.server:app --host 0.0.0.0 --port 8001   # terminal 2

# Baseline eval (tags: phase=eval, run=baseline)
uv run python evals/run_eval.py --out results/eval_baseline.json --run baseline

# After tuning
uv run python evals/run_eval.py --out results/eval_after_tuning.json --run after_tuning

# Load test (tags: phase=load_test, run=...)
uv run python load_test/driver.py --rps 10 --duration 300 --run baseline_load
```

Filter traces in Langfuse by metadata `run` for `langfuse_tags.png`.

## What's already implemented

- `agent/graph.py` — verify → revise loop (max 3 iterations)
- `agent/prompts.py` — generate / verify / revise prompts
- `evals/run_eval.py` — execution accuracy + per-iteration pass rate
- `infra/grafana/.../serving.json` — latency, throughput, KV cache panels
