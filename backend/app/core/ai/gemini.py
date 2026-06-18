"""Implementación de AIProvider con Gemini (proveedor primario)."""

import json

from google import genai
from google.genai import types

from app.config import get_settings
from app.core.ai.provider import AIProvider

EMBEDDING_DIM = 768


class GeminiProvider(AIProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model
        self._embedding_model = settings.gemini_embedding_model

    async def generate_json(self, prompt: str) -> dict:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        return json.loads(response.text)

    async def embed(self, text: str) -> list[float]:
        response = self._client.models.embed_content(
            model=self._embedding_model,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
        )
        return list(response.embeddings[0].values)
