"""Eval runner using execution accuracy."""
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EVAL_FILE = ROOT / "evals" / "eval_set.jsonl"
DEFAULT_OUT_FILE = ROOT / "results" / "eval_baseline.json"
DB_DIR = ROOT / "data" / "bird"
AGENT_URL_DEFAULT = "http://localhost:8001/answer"
MAX_TRACKED_ITERATIONS = 5


def run_sql(db_id: str, sql: str, timeout: float = 5.0) -> tuple[bool, list[tuple] | None, str | None]:
    path = DB_DIR / f"{db_id}.sqlite"
    try:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=timeout) as conn:
            cur = conn.execute(sql)
            rows = cur.fetchall()
            return True, rows, None
    except Exception as e:  # noqa: BLE001
        return False, None, f"{type(e).__name__}: {e}"


def canonicalize(rows: list[tuple] | None) -> list[tuple] | None:
    if rows is None:
        return None
    return sorted(tuple("" if c is None else str(c) for c in row) for row in rows)


def matches(gold_rows: list[tuple] | None, pred_rows: list[tuple] | None) -> bool:
    if gold_rows is None or pred_rows is None:
        return False
    return canonicalize(gold_rows) == canonicalize(pred_rows)


def _sql_attempts_from_history(history: list[dict]) -> list[str]:
    """Ordered SQL strings after each generate_sql / revise node."""
    return [
        entry["sql"]
        for entry in history
        if entry.get("node") in ("generate_sql", "revise") and entry.get("sql")
    ]


def eval_one(question: dict, agent_url: str, *, run: str) -> dict:
    db_id = question["db_id"]
    gold_sql = question["gold_sql"]

    ok_gold, gold_rows, gold_err = run_sql(db_id, gold_sql)
    if not ok_gold:
        return {
            "question": question["question"],
            "db_id": db_id,
            "gold_sql": gold_sql,
            "error": f"gold_sql failed: {gold_err}",
            "agent_ok": False,
            "final_correct": False,
            "per_iteration_correct": [],
            "iterations": 0,
            "history": [],
        }

    payload = {
        "question": question["question"],
        "db": db_id,
        "tags": {
            "eval_id": str(question.get("id", "")),
            "phase": "eval",
            "run": run,
        },
    }
    with httpx.Client(timeout=300.0) as client:
        resp = client.post(agent_url, json=payload)
        resp.raise_for_status()
        agent = resp.json()

    history = agent.get("history", [])
    sql_attempts = _sql_attempts_from_history(history)
    per_iteration_correct: list[bool] = []

    for sql in sql_attempts:
        ok_pred, pred_rows, _ = run_sql(db_id, sql)
        per_iteration_correct.append(
            ok_pred and matches(gold_rows, pred_rows)
        )

    # Carry-forward: after termination, later iteration slots mirror the last attempt.
    if per_iteration_correct:
        last = per_iteration_correct[-1]
        while len(per_iteration_correct) < MAX_TRACKED_ITERATIONS:
            per_iteration_correct.append(last)

    final_correct = per_iteration_correct[-1] if per_iteration_correct else False

    return {
        "question": question["question"],
        "db_id": db_id,
        "gold_sql": gold_sql,
        "pred_sql": agent.get("sql", ""),
        "agent_ok": agent.get("ok", False),
        "agent_error": agent.get("error"),
        "final_correct": final_correct,
        "per_iteration_correct": per_iteration_correct,
        "iterations": agent.get("iterations", 0),
        "history": history,
    }


def summarize(results: list[dict]) -> dict:
    valid = [r for r in results if "error" not in r]
    n = len(valid)
    if n == 0:
        return {"n": 0, "overall_pass_rate": 0.0, "per_iteration_pass_rate": {}}

    overall = sum(1 for r in valid if r.get("final_correct")) / n

    per_iter_rates: dict[str, float] = {}
    for i in range(MAX_TRACKED_ITERATIONS):
        key = f"iter_{i}"
        scored = [
            r["per_iteration_correct"][i]
            for r in valid
            if len(r.get("per_iteration_correct", [])) > i
        ]
        if scored:
            per_iter_rates[key] = sum(scored) / len(scored)

    revise_triggered = sum(
        1 for r in valid
        if any(h.get("node") == "revise" for h in r.get("history", []))
    )

    return {
        "n": n,
        "overall_pass_rate": round(overall, 4),
        "per_iteration_pass_rate": {k: round(v, 4) for k, v in per_iter_rates.items()},
        "questions_with_revise": revise_triggered,
        "errors": sum(1 for r in results if r.get("error") or r.get("agent_error")),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-set", type=Path, default=DEFAULT_EVAL_FILE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_FILE)
    parser.add_argument("--agent-url", default=AGENT_URL_DEFAULT)
    parser.add_argument("--limit", type=int, default=0, help="Run first N questions only (0=all)")
    parser.add_argument(
        "--run",
        choices=("baseline", "after_tuning"),
        default="baseline",
        help="Langfuse tag for this eval run (baseline vs post-tuning)",
    )
    args = parser.parse_args()

    questions = [
        json.loads(line)
        for line in args.eval_set.read_text().splitlines()
        if line.strip()
    ]
    if args.limit > 0:
        questions = questions[: args.limit]

    print(f"Loaded {len(questions)} eval questions from {args.eval_set}")

    results: list[dict] = []
    t0 = time.monotonic()
    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {q['db_id']}: {q['question'][:60]}...", flush=True)
        try:
            results.append(eval_one(q, args.agent_url, run=args.run))
        except Exception as e:  # noqa: BLE001
            results.append({
                "question": q.get("question", ""),
                "db_id": q.get("db_id", ""),
                "error": f"{type(e).__name__}: {e}",
                "final_correct": False,
                "per_iteration_correct": [],
            })
    elapsed = time.monotonic() - t0

    summary = summarize(results)
    out = {
        "summary": summary,
        "wall_clock_seconds": round(elapsed, 2),
        "results": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(f"Wrote {args.out}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
