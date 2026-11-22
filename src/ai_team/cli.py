"""Command line: `ai-team check` and `ai-team ask "..."`."""

import argparse
import json
import sys
import urllib.request

from ai_team.agents import echo
from ai_team.llm import describe, pick_model
from ai_team.models import Business, Sensitivity, Task, Tier
from ai_team.settings import get_settings


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


def ask(args: argparse.Namespace) -> int:
    task = Task(
        request=args.request,
        business=Business(args.business),
        sensitivity=Sensitivity(args.sensitivity),
        tier=Tier(args.tier),
    )
    print(f"model: {describe(pick_model(task))}")
    reply = echo.run(task)
    print(reply.model_dump_json(indent=2))
    return 0


def main() -> None:
    p = argparse.ArgumentParser(prog="ai-team")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="Is Ollama up and are the models installed?")
    a = sub.add_parser("ask", help="Send one request to the test agent")
    a.add_argument("request")
    a.add_argument("--business", default="personal", choices=[b.value for b in Business])
    a.add_argument("--sensitivity", default="private", choices=[s.value for s in Sensitivity])
    a.add_argument("--tier", default="default", choices=[t.value for t in Tier])
    args = p.parse_args()
    sys.exit(check() if args.cmd == "check" else ask(args))


if __name__ == "__main__":
    main()
