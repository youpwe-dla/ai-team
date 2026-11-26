"""Router behaviour, without a real model."""

import json

from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from ai_team.agents.registry import SPECS, AgentName, instructions
from ai_team.agents.stubs import run_stub
from ai_team.eval_routing import evaluate, load_cases
from ai_team.router import RouteDecision, build_router, route, shortcut


def fake_router(decision: dict) -> FunctionModel:
    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[TextPart(json.dumps(decision))])

    return FunctionModel(respond)


def test_every_agent_has_a_spec_and_instructions():
    for name in AgentName:
        assert name in SPECS
        assert len(instructions(name)) > 100


def test_shortcut_skips_router():
    assert shortcut("@money is this a deal") == (AgentName.MONEY_SAVER, "is this a deal")
    assert shortcut("@video cut my clip")[0] == AgentName.VIDEO_EDITOR
    assert shortcut("@nobody hi") is None
    assert shortcut("no shortcut here") is None


def test_route_with_shortcut_needs_no_model():
    d = route("@cmo rewrite my headline")
    assert d.agent == AgentName.CMO and d.confidence == 1.0


def test_low_confidence_asks():
    m = fake_router(
        {
            "agent": "assistant",
            "business": "personal",
            "sensitivity": "private",
            "confidence": 0.4,
            "runner_up": "prioritizer",
            "question": "Schedule the day, or rank the tasks?",
        }
    )
    d = build_router(m).run_sync("plan my day").output
    assert isinstance(d, RouteDecision) and d.needs_question


def test_stub_mentions_build_day_and_approval():
    out = run_stub(AgentName.ADVERTISER, "write ads")
    assert "Day 12" in out and "approval" in out


def test_cases_file_is_well_formed():
    cases = load_cases()
    assert len(cases) == 30
    assert {c["agent"] for c in cases} == {a.value for a in AgentName}


def test_eval_scores_a_router_that_always_says_cmo():
    m = fake_router(
        {"agent": "cmo", "business": "consulting", "sensitivity": "public", "confidence": 0.9}
    )
    report = evaluate(m, load_cases()[:5] + load_cases()[16:19])
    assert report["cases"] == 8
    assert report["agent_accuracy"] == 37.5  # cases 17, 18 and 19 are cmo


def test_router_failure_raises_clean_error():
    import pytest
    from pydantic_ai.messages import TextPart

    from ai_team.router import RoutingFailed, route_with_model

    def silent(messages, info):  # a model that never gives a usable answer
        return ModelResponse(parts=[TextPart("hmm")])

    with pytest.raises(RoutingFailed):
        route_with_model("plan my day", FunctionModel(silent))


def test_eval_reports_tokens_and_calls():
    m = fake_router(
        {"agent": "cmo", "business": "consulting", "sensitivity": "public", "confidence": 0.9}
    )
    report = evaluate(m, load_cases()[:3], think_switch="think-field")
    assert report["avg_model_calls"] == 1.0
    assert "avg_output_tokens" in report and report["rows"][0]["output_tokens"] is not None


def test_think_switch_settings():
    from ai_team.router import _settings

    assert "extra_body" not in _settings("prompt")
    assert _settings("think-field")["extra_body"] == {"think": False}
    assert _settings("reasoning-effort")["extra_body"] == {"reasoning_effort": "none"}
