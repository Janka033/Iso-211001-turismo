"""Generador .docx del Plan de respuesta a emergencias (PL-01, numeral 8.2).

Estructura fija. La IA aporta los escenarios y los campos planos; las celdas
sin dato quedan ``[PENDIENTE: ...]``, nunca inventadas.

Tipo PL de la taxonomía: portada + contenido + firmas + CONTROL DE CAMBIOS,
vía ``FelipeDocxBuilder``. Código provisional PL-01: confirmar con Felipe.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.modules.generation.generators.base import (
    DocumentGenerator,
    ResolvedField,
    resolve_code,
    resolve_text,
)
from app.modules.generation.generators.felipe_docx import FelipeDocxBuilder
from app.modules.generation.schemas import EmergencyPlanVariables, EmergencyScenario

# Columnas de la tabla de escenarios: (clave, encabezado).
_SCENARIO_COLUMNS: list[tuple[str, str]] = [
    ("scenario", "Escenario de emergencia"),
    ("activity", "Actividad"),
    ("response_steps", "Pasos de respuesta"),
    ("responsible", "Responsable"),
    ("resources", "Recursos"),
]


class EmergencyPlanGenerator(DocumentGenerator):
    template_version = "plan-emergencias-docx-v2"
    engine = "docx"
    custom_fields = frozenset({"emergency_scenarios"})

    def _extra_pending(
        self, variables: BaseModel, required_fields: set[str] | None
    ) -> list[str]:
        assert isinstance(variables, EmergencyPlanVariables)
        if variables.emergency_scenarios or not self._is_required(
            "emergency_scenarios", required_fields
        ):
            return []
        return ["emergency_scenarios"]

    def _render(
        self,
        resolved: dict[str, ResolvedField],
        variables: BaseModel,
        document_code: str | None,
    ) -> bytes:
        assert isinstance(variables, EmergencyPlanVariables)

        def val(key: str) -> str:
            f = resolved[key]
            return f.value if isinstance(f.value, str) else "\n".join(f.value)

        def items(key: str) -> list[str]:
            f = resolved[key]
            return f.value if isinstance(f.value, list) else [f.value]

        approval_date = (variables.approval_date or "").strip() or (
            "[PENDIENTE: fecha de aprobación]"
        )
        legal_rep = (variables.legal_representative or "").strip()

        b = FelipeDocxBuilder(
            code=resolve_code(document_code),
            title="Plan de respuesta a emergencias",
            company=val("company_name"),
            norm_reference="NTC-ISO 21101 — numeral 8.2",
            approval_date=approval_date,
        )
        b.section("1. Objetivo", val("general_objective"))
        b.section("2. Alcance", val("scope"))

        b.heading("3. Escenarios de emergencia y respuesta")
        self._scenario_table(b, variables.emergency_scenarios)

        b.section("4. Protocolo de comunicación", val("communication_protocol"))
        b.bullet_list("5. Contactos de emergencia", items("emergency_contacts"))
        b.section("6. Rutas y recursos de evacuación", val("evacuation_resources"))
        b.section("7. Coordinación con servicios externos", val("external_coordination"))
        b.section("8. Capacitación y simulacros", val("training_drills"))
        b.section("9. Revisión y actualización", val("review_frequency"))

        b.signatures(approved=(legal_rep, "Representante legal" if legal_rep else ""))
        b.change_control()
        return b.render()

    @staticmethod
    def _scenario_table(
        b: FelipeDocxBuilder, scenarios: list[EmergencyScenario]
    ) -> None:
        rows = scenarios or [EmergencyScenario()]  # fila vacía => [PENDIENTE]
        field_desc = {
            k: v.description or k for k, v in EmergencyScenario.model_fields.items()
        }
        table_rows = [
            [resolve_text(getattr(entry, key), field_desc[key])[0] for key, _ in _SCENARIO_COLUMNS]
            for entry in rows
        ]
        b.table([header for _, header in _SCENARIO_COLUMNS], table_rows)
