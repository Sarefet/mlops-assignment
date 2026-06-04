# MLOps Assignment: LLM Inference + Observability

> **Status:** Local dev complete; H100 numbers and screenshots pending booking slot.

## Phase 1 — Serving configuration (H100)

**Target SLO:** P95 end-to-end agent latency < 5s, ≥10 RPS over 5 minutes.

| Flag | Value | One-line justification |
|------|-------|------------------------|
| `--model` | `Qwen/Qwen3-30B-A3B-Instruct-2507` | Fixed assignment model |
| `--max-model-len` | `8192` | _TODO after H100 run_ |
| `--gpu-memory-utilization` | `0.90` | _TODO_ |
| `--enable-prefix-caching` | on | _TODO — repeated schema in agent prompts_ |
| _(add rows as you tune)_ | | |

**Local dev:** `scripts/start_vllm_cpu.sh` with `Qwen/Qwen3-0.6B` for wiring only — not for submission metrics.

---

## Phase 5 — Baseline eval

| Metric | Value |
|--------|-------|
| Overall pass rate | _TODO: `results/eval_baseline.json`_ |
| iter_0 pass rate | _TODO_ |
| iter_1 pass rate | _TODO_ |
| iter_2 pass rate | _TODO_ |
| Questions triggering revise | _TODO_ |

**Agent loop value:** _TODO — compare iter_0 vs iter_2 pass rates; cite numbers._

---

## Phase 6 — SLO tuning iteration log

| # | Saw | Hypothesis | Changed | Result |
|---|-----|------------|---------|--------|
| 1 | _TODO_ | _TODO_ | _TODO_ | _TODO_ |
| 2 | | | | |

**Final:** SLO hit / missed — _TODO_. Post-tuning eval: `results/eval_after_tuning.json`.

---

## Phase 7 — What I'd do with more time

- _TODO: be specific (e.g. continuous batching sweep, structured-output for verify JSON, etc.)_
