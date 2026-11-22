"""The privacy rule is the one thing that must never break."""

import pytest
from pydantic_ai.models.test import TestModel

from ai_team.agents import echo
from ai_team.llm import pick_model, uses_cloud
from ai_team.models import Business, Sensitivity, Task, Tier
from ai_team.settings import Settings

CLAUDE_ON = Settings(enable_claude=True, anthropic_api_key="sk-test", _env_file=None)
CLAUDE_OFF = Settings(enable_claude=False, _env_file=None)


def test_default_is_local_qwen():
    m = pick_model(Task(request="hi"), CLAUDE_OFF)
    assert m.model_name == "qwen3:8b"


@pytest.mark.parametrize(
    "tier,name",
    [
        (Tier.FAST, "llama3.2:3b"),
        (Tier.DEFAULT, "qwen3:8b"),
        (Tier.REASONING, "deepseek-r1:8b"),
    ],
)
def test_tiers_map_to_local_models(tier, name):
    assert pick_model(Task(request="x", tier=tier), CLAUDE_OFF).model_name == name


def test_client_data_never_uses_cloud():
    t = Task(request="x", sensitivity=Sensitivity.CLIENT, tier=Tier.REASONING)
    assert not uses_cloud(t, CLAUDE_ON)


def test_budget_business_is_always_local():
    t = Task(
        request="x", business=Business.BUDGET, sensitivity=Sensitivity.PUBLIC, tier=Tier.REASONING
    )
    assert not uses_cloud(t, CLAUDE_ON)


def test_cloud_only_when_switched_on():
    t = Task(request="x", sensitivity=Sensitivity.PUBLIC, tier=Tier.REASONING)
    assert not uses_cloud(t, CLAUDE_OFF)
    assert uses_cloud(t, CLAUDE_ON)


def test_echo_agent_returns_structured_reply():
    agent = echo.build_agent(Task(request="Draft a LinkedIn post"))
    with agent.override(model=TestModel()):
        out = agent.run_sync("Draft a LinkedIn post").output
    assert isinstance(out, echo.EchoReply)
