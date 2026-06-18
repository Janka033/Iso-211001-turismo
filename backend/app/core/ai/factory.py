"""Selección del AIProvider activo (Strategy).

Hoy: Gemini. El seam queda listo para añadir Claude/OpenAI como fallback
sin tocar los callers.
"""

from functools import lru_cache

from app.core.ai.gemini import GeminiProvider
from app.core.ai.provider import AIProvider


@lru_cache
def get_ai_provider() -> AIProvider:
    return GeminiProvider()
