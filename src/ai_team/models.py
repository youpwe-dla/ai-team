"""Shared vocabulary: which business a task belongs to and how sensitive its data is."""

from enum import StrEnum

from pydantic import BaseModel, Field


class Business(StrEnum):
    """The practice a task is done for."""

    BUDGET = "budget"  # Budget coaching for individuals and families
    CONSULTING = "consulting"  # Business + AI consulting for small and mid-size businesses
    PERSONAL = "personal"  # My own day, job search and learning


class Sensitivity(StrEnum):
    """Decides which models a task may use."""

    PUBLIC = "public"  # Anything already public or made up (marketing drafts, research)
    PRIVATE = "private"  # My own notes and plans
    CLIENT = "client"  # Any client's data: bank exports, meeting notes, business numbers


class Tier(StrEnum):
    """What kind of thinking the task needs."""

    FAST = "fast"  # Short replies, routing, formatting
    DEFAULT = "default"  # Most work: drafting, summarizing, tool use
    REASONING = "reasoning"  # Planning, checking math, multi-step logic


class Task(BaseModel):
    """One unit of work handed to an agent."""

    request: str = Field(min_length=1)
    business: Business = Business.PERSONAL
    sensitivity: Sensitivity = Sensitivity.PRIVATE
    tier: Tier = Tier.DEFAULT
