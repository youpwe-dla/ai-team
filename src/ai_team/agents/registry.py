"""The 8 specialists: name, what they handle, and their instructions file."""

from dataclasses import dataclass
from enum import StrEnum
from importlib.resources import files


class AgentName(StrEnum):
    ASSISTANT = "assistant"
    PRIORITIZER = "prioritizer"
    MONEY_SAVER = "money_saver"
    STRATEGIST = "strategist"
    CMO = "cmo"
    ADVERTISER = "advertiser"
    WEB_BUILDER = "web_builder"
    VIDEO_EDITOR = "video_editor"


@dataclass(frozen=True)
class Spec:
    name: AgentName
    handles: str  # what the router reads to decide
    not_this: str  # the nearest neighbour, to cut confusion between overlapping agents
    approval: bool  # does anything it produces wait in the approval queue?
    built_on_day: int


SPECS: dict[AgentName, Spec] = {
    s.name: s
    for s in [
        Spec(
            AgentName.ASSISTANT,
            "Today and my inbox: what needs a reply, drafting replies or messages, "
            "time-blocking a specific day, dropped follow-ups, the morning brief.",
            "Ranking or cutting a list of tasks is the Prioritizer.",
            True,
            6,
        ),
        Spec(
            AgentName.PRIORITIZER,
            "Ranking open work: what to do first, what to drop or defer, what is blocked.",
            "Scheduling a specific day is the Assistant; a multi-week plan is the Strategist.",
            False,
            5,
        ),
        Spec(
            AgentName.MONEY_SAVER,
            "My own spending: is a price a good deal, subscriptions to cancel, "
            "cheaper or free alternatives, price watches. Never buys.",
            "Ad budgets are the Advertiser; hosting choices for a site are the Web Builder.",
            False,
            7,
        ),
        Spec(
            AgentName.STRATEGIST,
            "Goals into plans: job-search strategy, weekly or 90-day plans, business "
            "strategy, who the customer is, testing whether people will pay.",
            "Marketing messages and content are the CMO; ranking today's tasks is the Prioritizer.",
            False,
            10,
        ),
        Spec(
            AgentName.CMO,
            "Marketing: positioning, messaging, LinkedIn profile copy, content plans, "
            "which channels to use for a business.",
            "Paid ads and ad budgets are the Advertiser; whether the business should exist "
            "is the Strategist.",
            False,
            11,
        ),
        Spec(
            AgentName.ADVERTISER,
            "Paid ads: ad copy and headlines, ad budget and platform choice, ad tests "
            "and when to stop an ad.",
            "Unpaid content and positioning are the CMO.",
            True,
            12,
        ),
        Spec(
            AgentName.WEB_BUILDER,
            "Websites: designing or building a site or landing page, pages it needs, "
            "hosting and forms.",
            "The words on the site's positioning are the CMO.",
            True,
            13,
        ),
        Spec(
            AgentName.VIDEO_EDITOR,
            "Video: scripts, hooks, shot lists, cutting recordings into clips, captions.",
            "A post or plan with no video is the CMO.",
            True,
            14,
        ),
    ]
}


def instructions(name: AgentName) -> str:
    return files("ai_team.prompts").joinpath(f"{name.value}.md").read_text(encoding="utf-8")
