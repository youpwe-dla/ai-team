"""Day 3: every agent exists and answers, but only says when it will be built."""

from ai_team.agents.registry import SPECS, AgentName


def run_stub(name: AgentName, request: str) -> str:
    s = SPECS[name]
    gate = " Its output will wait in the approval queue." if s.approval else ""
    return f"[{name.value}] not built yet (Day {s.built_on_day}). Got: {request!r}.{gate}"
