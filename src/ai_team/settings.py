"""All configuration comes from environment variables or a local .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_base_url: str = "http://192.168.1.240:11434/v1"
    default_model: str = "qwen3:8b"
    fast_model: str = "llama3.2:3b"
    reasoning_model: str = "deepseek-r1:8b"

    enable_claude: bool = False
    anthropic_api_key: str = ""
    claude_model: str = "claude-haiku-4-5"


@lru_cache
def get_settings() -> Settings:
    return Settings()
