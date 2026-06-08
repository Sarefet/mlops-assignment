# MLOps Assignment: LLM Inference + Observability

## Phase 1 — Serving configuration (H100)

**Target SLO:** P95 end-to-end agent latency < 5s, ≥10 RPS over 5 minutes.

| Flag | Value | One-line justification |
|------|-------|------------------------|
| `--model` | `Qwen/Qwen3-30B-A3B-Instruct-2507` | Fixed assignment model (MoE 30B instruct) |
| `--max-model-len` | `8192` | Fits long schema + multi-turn agent prompts; 1.5–3K typical |
| `--gpu-memory-utilization` | `0.90` | Use most of H100 80GB for weights + KV without OOM |
| `--enable-prefix-caching` | on | Agent repeats similar schema/system context across calls |

---

## Phase 5 — Baseline eval

- Overall pass rate: **0.30** (9/30)
- iter_0: **0.267** → iter_1+: **0.30**
- Revise triggered on **7** questions
- **Agent loop value:** Slightly — +3.3 pp from iter_0 to final; modest gain on 30B

---

## Phase 6 — SLO load test

**Config:** `start_vllm_h100.sh` — Qwen3-30B-A3B, max-model-len 8192, gpu-memory-utilization 0.90, prefix-caching on.

**Baseline load** (`load_test/driver.py --rps 10 --duration 300`):
- achieved_rps: **8.33** (target ≥10) — **miss**
- agent latency p95: **~110s** (target <5s) — **miss**
- 413 http_errors, 8 timeouts

**Diagnosis:** Grafana vLLM E2E p95 **~2–3s** during load → serving fast. Agent `POST /answer` errors/timeouts → bottleneck is **agent capacity** under 10 RPS (multi-step LangGraph), not raw vLLM generation.

| # | Saw | Hypothesis | Changed | Result |
|---|-----|------------|---------|--------|
| 1 | 10 RPS → 413 errors, p95 110s, achieved 8.3 RPS; Grafana vLLM p95 ~3s | Serving OK; agent saturated | No vLLM change (slot time) | SLO missed; root cause documented |

**Final:** SLO **missed**. Post-tuning eval (`eval_after_tuning.json`): overall_pass_rate **0.30** — no quality regression.

---

## Phase 7 — What I'd do with more time

1. Raise `--max-num-seqs` and re-run 10 RPS; compare vLLM queue vs agent http_errors in Grafana.
2. Add agent worker pool / limit load-test concurrency to avoid 120s HTTP timeouts stacking.
3. Langfuse breakdown: generate_sql vs verify vs revise latency under load.
4. I wanted to also invest in a retune, but I had no time. Things took extra time even I arrived as ready as I could. I fly tonight to California to the Databricks AI convention + proffesional exam from my workokace so I can implement the new premium feature in our departments. Due to that I couldnt even finish the time on my slot and i have to leave now (I wish slots were open earlier, I did my prep work a week ago). Hope this is good enough for now and I will revisit this when I have more time again. Thanks
