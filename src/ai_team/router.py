"""The router: reads a request and picks one of the 8 agents.

Not an agent itself. It is one cheap structured call. When it is unsure, it
returns a question for me instead of guessing (decision record 0001).
"""

import re

from pydantic import BaseModel, Field
from pydantic_ai import Agent, NativeOutput, PromptedOutput
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.models import Model

from ai_team.agents.registry import SPECS, AgentName
from ai_team.llm import pick_model
from ai_team.models import Business, Sensitivity, Task, Tier

ASK_BELOW = 0.6  # confidence threshold; tune it against eval/routing_cases.jsonl


class RouteDecision(BaseModel):
    agent: AgentName
    business: Business
    sensitivity: Sensitivity
    confidence: float = Field(ge=0, le=1)
    runner_up: AgentName | None = None
    question: str | None = Field(
        default=None, description="One short question for Manny, only if confidence is low"
    )

    @property
    def needs_question(self) -> bool:
        return self.confidence < ASK_BELOW


def _instructions() -> str:
    lines = [
        "You route requests for Manny's personal AI team. Pick exactly ONE agent.",
        "Business: default to 'personal'. Use 'consulting' ONLY if the request is about "
        "Manny's business + AI consulting practice (its clients, marketing, ads, website, "
        "offers). Use 'budget' ONLY if it is about his budget-coaching business. His own "
        "job search, schedule, inbox, recruiters, spending, homelab and videos are "
        "'personal', even when they mention AI.",
        "Sensitivity: 'client' if the request contains a client's data; 'public' if it "
        "is about public or made-up material (marketing, ads, websites, prices); "
        "otherwise 'private'.",
        "Give confidence from 0 to 1. If two agents fit, name the other as runner_up, "
        f"and if confidence is below {ASK_BELOW} write one short question to settle it.",
        "",
        "Agents:",
    ]
    for s in SPECS.values():
        lines.append(f"- {s.name.value}: {s.handles} Not this: {s.not_this}")
    return "\n".join(lines)


def _no_think(model: Model) -> str:
    # Qwen3 "thinks" before answering by default: slower, and on small models the
    # answer sometimes never arrives. Routing doesn't need it.
    return "\n/no_think" if "qwen3" in model.model_name else ""


# Ways to switch thinking off, compared in docs/runbooks/llm-latency.md:
#   prompt           "/no_think" in the instructions (Qwen3's soft switch)
#   think-field      Ollama's own {"think": false} sent in the request body
#   reasoning-effort the OpenAI-style {"reasoning_effort": "none"}
THINK_SWITCHES = ("prompt", "think-field", "reasoning-effort")
THINK_SWITCH = "reasoning-effort"  # the only switch that worked: see runbook


def _settings(switch: str) -> dict:
    settings: dict = {"temperature": 0}
    if switch == "think-field":
        settings["extra_body"] = {"think": False}
    elif switch == "reasoning-effort":
        settings["extra_body"] = {"reasoning_effort": "none"}
    return settings


def build_router(
    model: Model | None = None, native: bool = True, think_switch: str | None = None
) -> Agent[None, RouteDecision]:
    """native=True: Ollama constrains the reply to the JSON schema (most reliable).
    native=False: the schema goes in the prompt and the reply is parsed (fallback)."""
    model = model or pick_model(Task(request="route", tier=Tier.DEFAULT))
    switch = think_switch or THINK_SWITCH
    output = NativeOutput(RouteDecision) if native else PromptedOutput(RouteDecision)
    return Agent(
        model,
        output_type=output,
        instructions=_instructions() + (_no_think(model) if switch == "prompt" else ""),
        retries=3,
        model_settings=_settings(switch),
    )


class RoutingFailed(RuntimeError):
    """The model could not produce a valid routing decision."""


def route_detailed(
    request: str, model: Model | None = None, think_switch: str | None = None
) -> tuple[RouteDecision, dict]:
    """Route, and report what it cost: model calls and tokens in/out."""
    try:
        result = build_router(model, think_switch=think_switch).run_sync(request)
    except UnexpectedModelBehavior:
        try:
            result = build_router(model, native=False, think_switch=think_switch).run_sync(request)
        except UnexpectedModelBehavior as e:
            raise RoutingFailed(str(e)) from e
    u = result.usage
    return result.output, {
        "requests": u.requests,
        "input_tokens": u.input_tokens,
        "output_tokens": u.output_tokens,
        "reasoning_tokens": u.output_reasoning_tokens,
    }


def route_with_model(request: str, model: Model | None = None) -> RouteDecision:
    return route_detailed(request, model)[0]


_SHORTCUT = re.compile(r"^\s*@(\w+)\s+(.*)$", re.S)


def shortcut(request: str) -> tuple[AgentName, str] | None:
    """'@money is this a good deal' skips the router: free, instant, never wrong."""
    m = _SHORTCUT.match(request)
    if not m:
        return None
    word = m.group(1).lower()
    for name in AgentName:
        if name.value == word or name.value.split("_")[0] == word:
            return name, m.group(2)
    return None


def route(request: str, model: Model | None = None) -> RouteDecision:
    hit = shortcut(request)
    if hit:
        return RouteDecision(
            agent=hit[0],
            business=Business.PERSONAL,
            sensitivity=Sensitivity.PRIVATE,
            confidence=1.0,
        )
    return route_with_model(request, model)
