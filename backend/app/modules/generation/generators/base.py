"""Generador base (patrón Template Method).

El flujo fijo vive aquí; cada documento concreto solo implementa ``_render``.
Lo crítico para auditoría sucede en ``_resolve``: la IA llena variables, y todo
campo sin dato se sustituye por un placeholder VISIBLE ``[PENDIENTE: ...]``.
NUNCA se inventa un valor.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from pydantic import BaseModel


def pending_marker(description: str) -> str:
    """Placeholder visible para un campo sin dato del cliente."""
    return f"[PENDIENTE: {description}]"


@dataclass
class GenerationResult:
    content: bytes
    pending_fields: list[str] = field(default_factory=list)


@dataclass
class ResolvedField:
    """Un campo listo para inyectar: su valor de render y si quedó pendiente."""

    value: str | list[str]
    is_pending: bool


class DocumentGenerator(ABC):
    """Plantilla de generación. La estructura del documento es FIJA (no la
    escribe la IA); solo se inyectan las variables validadas."""

    #: Versión lógica de la plantilla; va al snapshot de reproducibilidad.
    template_version: str = "v1"
    #: Motor: 'docx' o 'xlsx'. Lo usa DocumentFactory / la trazabilidad.
    engine: str = "docx"

    def generate(self, variables: BaseModel) -> GenerationResult:
        resolved, pending = self._resolve(variables)
        content = self._render(resolved)
        return GenerationResult(content=content, pending_fields=pending)

    # -- Template Method: paso común -------------------------------------

    def _resolve(self, variables: BaseModel) -> tuple[dict[str, ResolvedField], list[str]]:
        """Convierte el modelo en campos listos para render.

        Un campo se considera PENDIENTE si es ``None``, cadena en blanco o
        lista vacía. La descripción del placeholder sale de
        ``Field(description=...)`` del propio schema: una sola fuente de verdad.
        """
        resolved: dict[str, ResolvedField] = {}
        pending: list[str] = []
        for name, info in type(variables).model_fields.items():
            raw = getattr(variables, name)
            description = info.description or name
            is_list = isinstance(raw, list)

            if is_list:
                items = [str(x).strip() for x in raw if str(x).strip()]
                if items:
                    resolved[name] = ResolvedField(value=items, is_pending=False)
                else:
                    resolved[name] = ResolvedField(
                        value=[pending_marker(description)], is_pending=True
                    )
                    pending.append(name)
            else:
                text = (raw or "").strip() if isinstance(raw, str) else raw
                if text:
                    resolved[name] = ResolvedField(value=str(text), is_pending=False)
                else:
                    resolved[name] = ResolvedField(
                        value=pending_marker(description), is_pending=True
                    )
                    pending.append(name)
        return resolved, pending

    # -- Template Method: paso variable ----------------------------------

    @abstractmethod
    def _render(self, resolved: dict[str, ResolvedField]) -> bytes:
        """Inyecta los campos resueltos en la plantilla fija y devuelve bytes."""
        ...
