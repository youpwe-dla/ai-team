"""Day 2 test agent: proves the pipe works end to end with structured output."""

from pydantic import BaseModel
from pydantic_ai import Agent

from ai_team.llm import pick_model
from ai_team.models import Task


class EchoReply(BaseModel):
    summary: str  # one sentence restating the request
    business: str  # which practice the agent thinks this belongs to
    next_step: str  # one concrete next action


INSTRUCTIONS = (
    "You are a test agent for Manny's AI team. Manny runs two businesses: "
    "budget coaching for individuals and families, and business + AI consulting for "
    "small and mid-size businesses. Restate the request in one sentence, say which "
    "business it belongs to (budget, consulting or personal), and suggest one next step."
)


def build_agent(task: Task) -> Agent[None, EchoReply]:
    return Agent(pick_model(task), output_type=EchoReply, instructions=INSTRUCTIONS, retries=2)


def run(task: Task) -> EchoReply:
    return build_agent(task).run_sync(task.request).output
