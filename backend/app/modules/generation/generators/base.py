"""Generador base (patrón Template Method).

El flujo fijo vive aquí; cada documento concreto implementa ``_render``. Lo
crítico para auditoría sucede en la resolución:

- Campo OBLIGATORIO sin dato  → placeholder VISIBLE ``[PENDIENTE: ...]`` (cuenta
  como pendiente y baja la completitud). Es la señal anti-alucinación: nunca se
  inventa.
- Campo OPCIONAL sin dato      → texto neutro ``No especificado`` (no es un
  pendiente ni ensucia el documento ante el auditor).

Qué campos son obligatorios lo decide la ``extraction_checklist`` (datos en DB),
no el generador: el service pasa ``required_fields``. Si no se pasa (tests/uso
suelto), se tratan TODOS como obligatorios (comportamiento conservador).

Campos planos (str / list[str]) los resuelve la base. Los campos estructurados
(p.ej. una lista de filas) los declara el generador en ``custom_fields`` y los
resuelve él mismo, reportando sus pendientes vía ``_extra_pending``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from pydantic import BaseModel

NOT_SPECIFIED = "No especificado"


def pending_marker(description: str) -> str:
    """Placeholder visible para un campo OBLIGATORIO sin dato del cliente."""
    return f"[PENDIENTE: {description}]"


def resolve_text(value: object, description: str) -> tuple[str, bool]:
    """Resuelve un valor escalar OBLIGATORIO a texto; devuelve (texto, is_pending).

    Se usa para celdas de tablas estructuradas, donde todo dato faltante es un
    pendiente. Para campos planos opcionales, ver ``_resolve_flat``.
    """
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

    def generate(
        self, variables: BaseModel, required_fields: set[str] | None = None
    ) -> GenerationResult:
        resolved, pending = self._resolve_flat(variables, required_fields)
        pending = pending + self._extra_pending(variables, required_fields)
        content = self._render(resolved, variables)
        return GenerationResult(content=content, pending_fields=pending)

    # -- Template Method: pasos comunes ----------------------------------

    def _is_required(self, name: str, required_fields: set[str] | None) -> bool:
        # Sin checklist => conservador: todo obligatorio.
        return required_fields is None or name in required_fields

    def _resolve_flat(
        self, variables: BaseModel, required_fields: set[str] | None
    ) -> tuple[dict[str, ResolvedField], list[str]]:
        """Resuelve los campos PLANOS (str / list[str]). Omite ``custom_fields``.

        Vacío + obligatorio → ``[PENDIENTE: descripción]`` (cuenta como pendiente).
        Vacío + opcional    → ``No especificado`` (no cuenta). La descripción
        sale de ``Field(description=...)``: una sola fuente de verdad.
        """
        resolved: dict[str, ResolvedField] = {}
        pending: list[str] = []
        for name, info in type(variables).model_fields.items():
            if name in self.custom_fields:
                continue
            raw = getattr(variables, name)
            description = info.description or name
            required = self._is_required(name, required_fields)

            if isinstance(raw, list):
                items = [str(x).strip() for x in raw if str(x).strip()]
                if items:
                    resolved[name] = ResolvedField(value=items, is_pending=False)
                elif required:
                    resolved[name] = ResolvedField(
                        value=[pending_marker(description)], is_pending=True
                    )
                    pending.append(name)
                else:
                    resolved[name] = ResolvedField(value=[NOT_SPECIFIED], is_pending=False)
            else:
                text = raw.strip() if isinstance(raw, str) else raw
                if text:
                    resolved[name] = ResolvedField(value=str(text), is_pending=False)
                elif required:
                    resolved[name] = ResolvedField(
                        value=pending_marker(description), is_pending=True
                    )
                    pending.append(name)
                else:
                    resolved[name] = ResolvedField(value=NOT_SPECIFIED, is_pending=False)
        return resolved, pending

    def _extra_pending(
        self, variables: BaseModel, required_fields: set[str] | None
    ) -> list[str]:
        """Pendientes de los ``custom_fields`` (lo resuelve cada generador)."""
        return []

    # -- Template Method: paso variable ----------------------------------

    @abstractmethod
    def _render(self, resolved: dict[str, ResolvedField], variables: BaseModel) -> bytes:
        """Inyecta en la plantilla fija y devuelve los bytes del documento."""
        ...
