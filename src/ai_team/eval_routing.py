"""Score the router against eval/routing_cases.jsonl.

Reports agent accuracy (top-1), how many misses a question would have rescued,
business and sensitivity accuracy, latency, and which agents get confused.
"""

import json
import time
from collections import Counter
from pathlib import Path

from pydantic_ai.models import Model

from ai_team.router import route_detailed

CASES = Path(__file__).resolve().parents[2] / "eval" / "routing_cases.jsonl"


def load_cases(path: Path = CASES) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def evaluate(
    model: Model | None = None, cases: list[dict] | None = None, think_switch: str | None = None
) -> dict:
    cases = cases or load_cases()
    rows, confusions = [], Counter()
    for c in cases:
        t0 = time.perf_counter()
        try:
            d, usage = route_detailed(c["request"], model, think_switch)
            err = None
        except Exception as e:  # a failed call counts as a miss, not a crash
            d, usage, err = None, {}, f"{type(e).__name__}: {e}"
        secs = time.perf_counter() - t0
        agent_ok = bool(d) and d.agent.value == c["agent"]
        rescued = (
            bool(d)
            and not agent_ok
            and d.needs_question
            and d.runner_up is not None
            and d.runner_up.value == c["agent"]
        )
        if d and not agent_ok:
            confusions[(c["agent"], d.agent.value)] += 1
        rows.append(
            {
                "id": c["id"],
                "hard": c["hard"],
                "expected": c["agent"],
                "got": d.agent.value if d else None,
                "confidence": d.confidence if d else None,
                "agent_ok": agent_ok,
                "rescued": rescued,
                "business_ok": bool(d) and d.business.value == c["business"],
                "sensitivity_ok": bool(d) and d.sensitivity.value == c["sensitivity"],
                "secs": round(secs, 2),
                "requests": usage.get("requests"),
                "output_tokens": usage.get("output_tokens"),
                "reasoning_tokens": usage.get("reasoning_tokens"),
                "error": err,
            }
        )
    n = len(rows)

    def pct(key: str, subset=rows) -> float:
        return round(100 * sum(r[key] for r in subset) / max(len(subset), 1), 1)

    hard = [r for r in rows if r["hard"]]
    return {
        "cases": n,
        "agent_accuracy": pct("agent_ok"),
        "agent_accuracy_hard": pct("agent_ok", hard),
        "rescued_by_question": sum(r["rescued"] for r in rows),
        "business_accuracy": pct("business_ok"),
        "sensitivity_accuracy": pct("sensitivity_ok"),
        "avg_secs": round(sum(r["secs"] for r in rows) / max(n, 1), 2),
        "median_secs": sorted(r["secs"] for r in rows)[n // 2] if n else 0,
        "avg_output_tokens": round(sum(r["output_tokens"] or 0 for r in rows) / max(n, 1), 1),
        "avg_reasoning_tokens": round(sum(r["reasoning_tokens"] or 0 for r in rows) / max(n, 1), 1),
        "avg_model_calls": round(sum(r["requests"] or 0 for r in rows) / max(n, 1), 2),
        "errors": sum(1 for r in rows if r["error"]),
        "confusions": [f"{a} -> {b}: {k}" for (a, b), k in confusions.most_common()],
        "rows": rows,
    }
