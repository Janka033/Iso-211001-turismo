"""Generador base (patrón Template Method).

El flujo fijo vive aquí; cada documento concreto implementa ``_render``. Lo
crítico para auditoría sucede en la resolución: la IA llena variables, y todo
campo sin dato se sustituye por un placeholder VISIBLE ``[PENDIENTE: ...]``.
NUNCA se inventa un valor.

Campos planos (str / list[str]) los resuelve la base. Los campos estructurados
(p.ej. una lista de filas en una matriz) los declara el generador en
``custom_fields`` y los resuelve él mismo, reportando sus pendientes vía
``_extra_pending``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from pydantic import BaseModel


def pending_marker(description: str) -> str:
    """Placeholder visible para un campo sin dato del cliente."""
    return f"[PENDIENTE: {description}]"


def resolve_text(value: object, description: str) -> tuple[str, bool]:
    """Resuelve un valor escalar a texto; devuelve (texto, is_pending)."""
    text = value.strip() if isinstance(value, str) else value
    if text:
        return str(text), False
    return pending_marker(description), True


@dataclass
class GenerationResult:
    content: bytes
    pending_fields: list[str] = field(default_factory=list)


@dataclass
class ResolvedField:
    """Un campo plano listo para inyectar: valor de render y si quedó pendiente."""

    value: str | list[str]
    is_pending: bool


class DocumentGenerator(ABC):
    """Plantilla de generación. La estructura del documento es FIJA (no la
    escribe la IA); solo se inyectan las variables validadas."""

    #: Versión lógica de la plantilla; va al snapshot de reproducibilidad.
    template_version: str = "v1"
    #: Motor: 'docx' o 'xlsx'. Lo usa DocumentFactory / la trazabilidad.
    engine: str = "docx"
    #: Campos que el generador resuelve por su cuenta (no el resolutor plano).
    custom_fields: frozenset[str] = frozenset()

    def generate(self, variables: BaseModel) -> GenerationResult:
        resolved, pending = self._resolve_flat(variables)
        pending = pending + self._extra_pending(variables)
        content = self._render(resolved, variables)
        return GenerationResult(content=content, pending_fields=pending)

    # -- Template Method: pasos comunes ----------------------------------

    def _resolve_flat(
        self, variables: BaseModel
    ) -> tuple[dict[str, ResolvedField], list[str]]:
        """Resuelve los campos PLANOS (str / list[str]). Omite ``custom_fields``.

        Un campo se considera PENDIENTE si es ``None``, cadena en blanco o lista
        vacía. La descripción del placeholder sale de ``Field(description=...)``
        del propio schema: una sola fuente de verdad.
        """
        resolved: dict[str, ResolvedField] = {}
        pending: list[str] = []
        for name, info in type(variables).model_fields.items():
            if name in self.custom_fields:
                continue
            raw = getattr(variables, name)
            description = info.description or name

            if isinstance(raw, list):
                items = [str(x).strip() for x in raw if str(x).strip()]
                if items:
                    resolved[name] = ResolvedField(value=items, is_pending=False)
                else:
                    resolved[name] = ResolvedField(
                        value=[pending_marker(description)], is_pending=True
                    )
                    pending.append(name)
            else:
                text, is_pending = resolve_text(raw, description)
                resolved[name] = ResolvedField(value=text, is_pending=is_pending)
                if is_pending:
                    pending.append(name)
        return resolved, pending

    def _extra_pending(self, variables: BaseModel) -> list[str]:
        """Pendientes de los ``custom_fields`` (lo resuelve cada generador)."""
        return []

    # -- Template Method: paso variable ----------------------------------

    @abstractmethod
    def _render(self, resolved: dict[str, ResolvedField], variables: BaseModel) -> bytes:
        """Inyecta en la plantilla fija y devuelve los bytes del documento."""
        ...
