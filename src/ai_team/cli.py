"""Command line.

ai-team check                 is Ollama up and are the models installed?
ai-team ask "..."             route a request to an agent (stubs until each is built)
ai-team ask "@money ..."      skip the router and name the agent yourself
ai-team route "..."           show only the routing decision
ai-team eval [--model NAME]   score the router on eval/routing_cases.jsonl
"""

import argparse
import json
import os
import sys
import urllib.request
from datetime import date
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from ai_team.agents.stubs import run_stub  # noqa: E402
from ai_team.llm import local_model  # noqa: E402
from ai_team.router import RoutingFailed, route, shortcut  # noqa: E402
from ai_team.settings import get_settings  # noqa: E402


def check() -> int:
    s = get_settings()
    root = s.ollama_base_url.removesuffix("/v1")
    try:
        with urllib.request.urlopen(f"{root}/api/tags", timeout=5) as r:
            installed = {m["name"] for m in json.load(r)["models"]}
    except OSError as e:
        print(f"FAIL  can't reach Ollama at {root}: {e}")
        return 1
    print(f"OK    Ollama reachable at {root} ({len(installed)} models)")
    ok = True
    for name in (s.fast_model, s.default_model, s.reasoning_model):
        found = name in installed or f"{name}:latest" in installed
        ok &= found
        print(f"{'OK  ' if found else 'MISS'}  {name}")
    print(f"INFO  Claude {'on' if s.enable_claude and s.anthropic_api_key else 'off'}")
    return 0 if ok else 1


def show_route(request: str) -> int:
    d = route(request)
    print(d.model_dump_json(indent=2))
    return 0


def ask(request: str) -> int:
    try:
        d = route(request)
    except RoutingFailed:
        print("!  The router couldn't decide. Name the agent yourself, e.g. @prioritizer ...")
        return 1
    hit = shortcut(request)
    text = hit[1] if hit else request
    print(
        f"-> {d.agent.value}  (business={d.business.value}, "
        f"sensitivity={d.sensitivity.value}, confidence={d.confidence:.2f})"
    )
    if d.needs_question:
        print(f"?  Not sure (maybe {d.runner_up.value if d.runner_up else 'another agent'}).")
        print(f"   {d.question or 'Which agent did you mean?'}")
        print("   Re-ask with @agent to choose, e.g. @prioritizer ...")
        return 0
    print(run_stub(d.agent, text))
    return 0


def run_eval(model_name: str | None, limit: int | None, think_switch: str) -> int:
    from ai_team.eval_routing import evaluate, load_cases

    name = model_name or get_settings().default_model
    cases = load_cases()[:limit] if limit else load_cases()
    print(f"Scoring router with {name} on {len(cases)} cases, think switch: {think_switch}...")
    report = evaluate(local_model(name), cases, think_switch)
    report["model"], report["think_switch"] = name, think_switch
    out = Path("eval/results")
    out.mkdir(parents=True, exist_ok=True)
    tag = f"{name.replace(':', '_')}-{think_switch}" + (f"-n{limit}" if limit else "")
    path = out / f"{date.today()}-{tag}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    for k in (
        "agent_accuracy",
        "agent_accuracy_hard",
        "rescued_by_question",
        "business_accuracy",
        "sensitivity_accuracy",
        "avg_secs",
        "median_secs",
        "avg_output_tokens",
        "avg_reasoning_tokens",
        "avg_model_calls",
        "errors",
    ):
        print(f"{k:22} {report[k]}")
    print("misses:")
    for r in report["rows"]:
        if not r["agent_ok"]:
            print(f"  #{r['id']:>2} expected {r['expected']:12} got {r['got']} ({r['confidence']})")
    print(f"saved {path}")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(prog="ai-team")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="Is Ollama up and are the models installed?")
    a = sub.add_parser("ask", help="Route a request to an agent")
    a.add_argument("request")
    r = sub.add_parser("route", help="Show only the routing decision")
    r.add_argument("request")
    e = sub.add_parser("eval", help="Score the router on the test set")
    e.add_argument("--model", default=None, help="e.g. qwen3:8b or llama3.2:3b")
    e.add_argument("--limit", type=int, default=None, help="only the first N cases (quick test)")
    e.add_argument(
        "--think-switch",
        default="reasoning-effort",
        choices=["prompt", "think-field", "reasoning-effort"],
        help="how to switch the model's thinking off (see the latency runbook)",
    )
    args = p.parse_args()
    if args.cmd == "check":
        sys.exit(check())
    if args.cmd == "ask":
        sys.exit(ask(args.request))
    if args.cmd == "route":
        sys.exit(show_route(args.request))
    sys.exit(run_eval(args.model, args.limit, args.think_switch))


if __name__ == "__main__":
    main()
