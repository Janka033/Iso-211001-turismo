"""Interfaz Strategy para los modelos de IA.

TODA llamada a un modelo pasa por aquí. Ningún service ni script usa el SDK
de Gemini directamente. Esto nos permite cambiar de proveedor (Claude/OpenAI
como fallback) sin tocar la lógica de negocio.
"""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    async def generate_json(self, prompt: str) -> dict:
        """Devuelve JSON estructurado (response_mime_type=application/json).

        La salida se valida con Pydantic en el caller antes de tocar plantillas.
        """
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Embedding de 768 dimensiones (compatible con knowledge_chunks)."""
        ...
