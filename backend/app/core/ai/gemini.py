"""Implementación de AIProvider con Gemini (proveedor primario).

El SDK de Gemini es síncrono; sus llamadas se ejecutan en un hilo
(``anyio.to_thread``) para no bloquear el event loop. El cliente lleva un
timeout para que un upstream colgado no cuelgue la request.

Resiliencia y costo (medidos en el ensayo E2E del 2026-07-06):

- ``_call_with_retries``: reintenta errores TRANSITORIOS (429/5xx/timeout) con
  backoff corto. Antes, un 429 puntual = 502 directo al cliente.
- ``embed`` cachea por texto (LRU): el RAG usa queries CONSTANTES (por
  actividad/documento), re-embebirlas en cada turno multiplicaba por 4 las
  llamadas y agotaba la cuota.
- ``generate_json(thinking_budget=0)`` para EXTRACCIÓN: el thinking por defecto
  de gemini-2.5 gastaba ~650 tokens y segundos extra sin mejorar la extracción.
  La generación de documentos mantiene el thinking por defecto.
"""

import functools
import json
import logging
import time

import anyio
import httpx
from google import genai
from google.genai import errors, types

from app.config import get_settings
from app.core.ai.provider import AIProvider

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 768

# Códigos upstream que vale la pena reintentar (transitorios).
_RETRYABLE_CODES = frozenset({429, 500, 502, 503, 504})
# Pausas entre intentos (attempts = len + 1). Cortas a propósito: esto corre
# dentro de una request HTTP; los agotamientos de cuota diaria no se arreglan
# esperando y deben fallar rápido.
_RETRY_SLEEPS = (2.0, 6.0)


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, errors.APIError):
        return exc.code in _RETRYABLE_CODES
    return False


def _call_with_retries(fn, *, what: str):
    """Ejecuta ``fn()`` reintentando errores transitorios. Síncrono: vive en el
    worker thread de ``anyio.to_thread``, así que ``time.sleep`` no bloquea el
    event loop."""
    for i, pause in enumerate((*_RETRY_SLEEPS, None)):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - se re-lanza si no es transitorio
            if pause is None or not _is_retryable(exc):
                raise
            logger.warning(
                "Gemini %s transitorio (intento %d): %s — reintento en %.0fs",
                what, i + 1, str(exc)[:120], pause,
            )
            time.sleep(pause)
    raise RuntimeError("unreachable")  # pragma: no cover


class GeminiProvider(AIProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(timeout=settings.gemini_timeout_ms),
        )
        self._model = settings.gemini_model
        self._embedding_model = settings.gemini_embedding_model

    async def generate_json(
        self, prompt: str, *, thinking_budget: int | None = None
    ) -> dict:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            thinking_config=(
                types.ThinkingConfig(thinking_budget=thinking_budget)
                if thinking_budget is not None
                else None
            ),
        )
        response = await anyio.to_thread.run_sync(
            functools.partial(
                _call_with_retries,
                functools.partial(
                    self._client.models.generate_content,
                    model=self._model,
                    contents=prompt,
                    config=config,
                ),
                what="generate_content",
            )
        )
        return json.loads(response.text)

    async def embed(self, text: str) -> list[float]:
        vector = await anyio.to_thread.run_sync(
            functools.partial(self._embed_cached, text)
        )
        return list(vector)

    @functools.lru_cache(maxsize=512)  # noqa: B019 - provider es singleton (factory)
    def _embed_cached(self, text: str) -> tuple[float, ...]:
        """Embedding con caché LRU por texto. Las queries del RAG son constantes
        (por actividad/numeral): la caché elimina ~75% de las llamadas en el
        onboarding. Devuelve tupla (inmutable) para que la caché sea segura."""
        response = _call_with_retries(
            functools.partial(
                self._client.models.embed_content,
                model=self._embedding_model,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
            ),
            what="embed_content",
        )
        return tuple(response.embeddings[0].values)
