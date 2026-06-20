"""Implementación de AIProvider con Gemini (proveedor primario).

El SDK de Gemini es síncrono; sus llamadas se ejecutan en un hilo
(``anyio.to_thread``) para no bloquear el event loop. El cliente lleva un
timeout para que un upstream colgado no cuelgue la request.
"""

import functools
import json

import anyio
from google import genai
from google.genai import types

from app.config import get_settings
from app.core.ai.provider import AIProvider

EMBEDDING_DIM = 768


class GeminiProvider(AIProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(timeout=settings.gemini_timeout_ms),
        )
        self._model = settings.gemini_model
        self._embedding_model = settings.gemini_embedding_model

    async def generate_json(self, prompt: str) -> dict:
        response = await anyio.to_thread.run_sync(
            functools.partial(
                self._client.models.generate_content,
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
        )
        return json.loads(response.text)

    async def embed(self, text: str) -> list[float]:
        response = await anyio.to_thread.run_sync(
            functools.partial(
                self._client.models.embed_content,
                model=self._embedding_model,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
            )
        )
        return list(response.embeddings[0].values)
