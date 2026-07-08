"""Interfaz Strategy para los modelos de IA.

TODA llamada a un modelo pasa por aquí. Ningún service ni script usa el SDK
de Gemini directamente. Esto nos permite cambiar de proveedor (Claude/OpenAI
como fallback) sin tocar la lógica de negocio.
"""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    async def generate_json(
        self, prompt: str, *, thinking_budget: int | None = None
    ) -> dict:
        """Devuelve JSON estructurado (response_mime_type=application/json).

        La salida se valida con Pydantic en el caller antes de tocar plantillas.
        ``thinking_budget=0`` desactiva el razonamiento extendido: úsalo en
        EXTRACCIÓN (onboarding), donde solo agrega latencia y costo. ``None``
        deja el default del modelo (generación de documentos).
        """
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Embedding de 768 dimensiones (compatible con knowledge_chunks)."""
        ...
