from functools import lru_cache

from app.agents.llm import get_llm
from app.domain.orchestrator import Orchestrator


@lru_cache
def get_orchestrator() -> Orchestrator:
    return Orchestrator(get_llm())
