import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    database_url: str
    llm_provider: str
    openai_model: str
    max_agent_steps: int
    memory_window: int


@lru_cache
def get_settings() -> Settings:
    return Settings(
        database_url=os.environ.get("DATABASE_URL", "sqlite:///./local.db"),
        llm_provider=os.environ.get("LLM_PROVIDER", "fake").lower(),
        openai_model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        max_agent_steps=int(os.environ.get("MAX_AGENT_STEPS", "5")),
        memory_window=int(os.environ.get("MEMORY_WINDOW", "10")),
    )
