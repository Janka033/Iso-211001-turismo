"""Generador .docx del Procedimiento de comunicación, participación y consulta
(PR-07, numeral 7.4).

Generador DELGADO sobre ``FelipeDocxBuilder``. Anti-alucinación: dato faltante
= [PENDIENTE].
"""

from __future__ import annotations

from pydantic import BaseModel

from app.modules.generation.generators.base import (
    DocumentGenerator,
    ResolvedField,
    resolve_text,
)
from app.modules.generation.generators.felipe_docx import FelipeDocxBuilder
from app.modules.generation.schemas import (
    CommunicationEntry,
    CommunicationProcedureVariables,
)

# Columnas de la matriz de comunicación (4.1): (clave, encabezado).
_COMM_COLUMNS: list[tuple[str, str]] = [
    ("topic", "Qué se comunica"),
    ("method", "Cómo"),
    ("channel", "Vía / medio"),
    ("audience", "A quién"),
    ("frequency", "Frecuencia"),
]


class CommunicationProcedureGenerator(DocumentGenerator):
    template_version = "pr-comunicacion-docx-v3"
    engine = "docx"
    custom_fields = frozenset({"communication_matrix"})

    def _extra_pending(
        self, variables: BaseModel, required_fields: set[str] | None
    ) -> list[str]:
        assert isinstance(variables, CommunicationProcedureVariables)
        if not variables.communication_matrix:
            return (
                ["communication_matrix"]
                if self._is_required("communication_matrix", required_fields)
                else []
            )
        # Pendientes de CELDA (patrón de risk_matrix): visibles para el cliente
        # y el auditor aunque no muevan la completitud de la checklist.
        pending: list[str] = []
        for i, entry in enumerate(variables.communication_matrix):
            for key, _ in _COMM_COLUMNS:
                value = getattr(entry, key)
                if not (value.strip() if isinstance(value, str) else value):
                    pending.append(f"communication_matrix[{i}].{key}")
        return pending

    def _render(
        self, resolved: dict[str, ResolvedField], variables: BaseModel
    ) -> bytes:
        assert isinstance(variables, CommunicationProcedureVariables)

        def val(key: str) -> str:
            f = resolved[key]
            return f.value if isinstance(f.value, str) else "\n".join(f.value)

        # Aprobación: real si el cliente la dio; si no, [PENDIENTE]. El firmante
        # "Aprobado por" es el representante legal (consistente con PO-01/PL-01).
        approval_date = (variables.approval_date or "").strip() or (
            "[PENDIENTE: fecha de aprobación]"
        )
        legal_rep = (variables.legal_representative or "").strip()

        b = FelipeDocxBuilder(
            code="PR-07",
            title="Procedimiento de comunicación, participación y consulta",
            company=val("company_name"),
            norm_reference="NTC-ISO 21101 — numeral 7.4",
            approval_date=approval_date,
        )
        b.section("1. Objetivo", val("objective"))
        b.section("2. Alcance", val("scope"))
        b.section("3. Responsables", val("responsibles"))
        b.heading("4. Desarrollo")
        b.heading("4.1 Comunicación", level=2)
        self._comm_table(b, variables.communication_matrix)
        b.section("4.2 Participación", val("participation"), level=2)
        b.section("4.3 Consulta", val("consultation"), level=2)
        b.section("4.4 Representación en asuntos de seguridad", val("representation"), level=2)
        b.section("5. Evaluación del desempeño", val("performance_evaluation"))
        b.section("6. Registros", val("records"))
        b.signatures(approved=(legal_rep, "Representante legal" if legal_rep else ""))
        b.change_control()
        return b.render()

    @staticmethod
    def _comm_table(b: FelipeDocxBuilder, entries: list[CommunicationEntry]) -> None:
        rows = entries or [CommunicationEntry()]  # sin filas => [PENDIENTE]
        fd = {k: (v.description or k) for k, v in CommunicationEntry.model_fields.items()}
        table_rows = [
            [resolve_text(getattr(entry, key), fd[key])[0] for key, _ in _COMM_COLUMNS]
            for entry in rows
        ]
        b.table([header for _, header in _COMM_COLUMNS], table_rows)
