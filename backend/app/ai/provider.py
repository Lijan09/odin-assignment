"""Chooses the analyser and exposes it as a FastAPI dependency.

Routers depend on `get_analyser`, so a test can swap the implementation with
`app.dependency_overrides` and exercise the failure path without a network call.
"""

from functools import lru_cache

from app.ai.base import AiAnalyser
from app.ai.gemini import GeminiAnalyser
from app.ai.mock import MockAnalyser
from app.config import settings


@lru_cache(maxsize=1)
def _build_analyser() -> AiAnalyser:
    """Construct the configured analyser once and reuse it across requests."""
    if settings.ai_provider == "gemini":
        return GeminiAnalyser(
            # The only place the key is unwrapped.
            api_key=settings.gemini_api_key.get_secret_value(),
            model=settings.gemini_model,
            timeout_seconds=settings.gemini_timeout_seconds,
        )
    return MockAnalyser()


def get_analyser() -> AiAnalyser:
    return _build_analyser()
