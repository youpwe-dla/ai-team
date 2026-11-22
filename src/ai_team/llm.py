"""Picks the model for a task. The privacy rule lives here, in one place.

Rule: client data only ever goes to the local Ollama models. A cloud model is used
only when it is switched on AND the task is not client data AND the task needs reasoning.
"""

from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from ai_team.models import Business, Sensitivity, Task, Tier
from ai_team.settings import Settings, get_settings


class PrivacyError(RuntimeError):
    """Raised if anything tries to send client data to a cloud model."""


def local_model_name(tier: Tier, settings: Settings) -> str:
    return {
        Tier.FAST: settings.fast_model,
        Tier.DEFAULT: settings.default_model,
        Tier.REASONING: settings.reasoning_model,
    }[tier]


def is_client_data(task: Task) -> bool:
    # Budget-coaching work is treated as client data even if the caller forgot to mark it.
    return task.sensitivity == Sensitivity.CLIENT or task.business == Business.BUDGET


def uses_cloud(task: Task, settings: Settings) -> bool:
    return (
        settings.enable_claude
        and bool(settings.anthropic_api_key)
        and not is_client_data(task)
        and task.tier == Tier.REASONING
    )


def pick_model(task: Task, settings: Settings | None = None) -> Model:
    settings = settings or get_settings()
    if uses_cloud(task, settings):
        if is_client_data(task):  # belt and braces
            raise PrivacyError("Client data must stay on local models.")
        from pydantic_ai.models.anthropic import AnthropicModel
        from pydantic_ai.providers.anthropic import AnthropicProvider

        return AnthropicModel(
            settings.claude_model,
            provider=AnthropicProvider(api_key=settings.anthropic_api_key),
        )
    return OpenAIChatModel(
        local_model_name(task.tier, settings),
        provider=OllamaProvider(base_url=settings.ollama_base_url),
    )


def describe(model: Model) -> str:
    return f"{model.system}:{model.model_name}"
