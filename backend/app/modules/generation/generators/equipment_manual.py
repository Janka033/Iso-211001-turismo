"""Generador .docx del Manual de inspección y mantenimiento de equipos
(MA-03, numeral 8.1 + Anexo A).

Generador DELGADO sobre ``FelipeDocxBuilder``. El control de equipos se DERIVA
del equipo real del cliente (``activity_fields`` del onboarding), no de texto
genérico. Anti-alucinación: dato faltante = [PENDIENTE].
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
    EquipmentInspectionItem,
    EquipmentManualVariables,
)

# Columnas del control de equipos: (clave, encabezado).
_EQUIP_COLUMNS: list[tuple[str, str]] = [
    ("activity", "Actividad"),
    ("equipment", "Equipo"),
    ("state", "Estado"),
    ("inspection_type", "Tipo de revisión"),
    ("frequency", "Frecuencia"),
]


class EquipmentManualGenerator(DocumentGenerator):
    template_version = "manual-equipos-docx-v3"
    engine = "docx"
    custom_fields = frozenset({"equipment_items"})

    def _extra_pending(
        self, variables: BaseModel, required_fields: set[str] | None
    ) -> list[str]:
        assert isinstance(variables, EquipmentManualVariables)
        if not variables.equipment_items:
            return (
                ["equipment_items"]
                if self._is_required("equipment_items", required_fields)
                else []
            )
        # Pendientes de CELDA (patrón de risk_matrix): visibles para el cliente
        # y el auditor aunque no muevan la completitud de la checklist.
        pending: list[str] = []
        for i, entry in enumerate(variables.equipment_items):
            for key, _ in _EQUIP_COLUMNS:
                value = getattr(entry, key)
                if not (value.strip() if isinstance(value, str) else value):
                    pending.append(f"equipment_items[{i}].{key}")
        return pending

    def _render(
        self, resolved: dict[str, ResolvedField], variables: BaseModel
    ) -> bytes:
        assert isinstance(variables, EquipmentManualVariables)

        def val(key: str) -> str:
            f = resolved[key]
            return f.value if isinstance(f.value, str) else "\n".join(f.value)

        def items(key: str) -> list[str]:
            f = resolved[key]
            return f.value if isinstance(f.value, list) else [f.value]

        # Aprobación: real si el cliente la dio; si no, [PENDIENTE]. El firmante
        # "Aprobado por" es el representante legal (consistente con PO-01/PL-01).
        approval_date = (variables.approval_date or "").strip() or (
            "[PENDIENTE: fecha de aprobación]"
        )
        legal_rep = (variables.legal_representative or "").strip()

        b = FelipeDocxBuilder(
            code="MA-03",
            title="Manual de inspección y mantenimiento de equipos",
            company=val("company_name"),
            norm_reference="NTC-ISO 21101 — numeral 8.1 y Anexo A",
            approval_date=approval_date,
        )
        b.section("1. Objetivo", val("objective"))
        b.section("2. Alcance", val("scope"))
        b.section("3. Obligaciones por rol", val("role_obligations"))
        b.heading("4. Control de equipos")
        self._equipment_table(b, variables.equipment_items)
        b.bullet_list("5. Tipos de mantenimiento", items("maintenance_types"))
        b.signatures(approved=(legal_rep, "Representante legal" if legal_rep else ""))
        b.change_control()
        return b.render()

    @staticmethod
    def _equipment_table(
        b: FelipeDocxBuilder, entries: list[EquipmentInspectionItem]
    ) -> None:
        rows = entries or [EquipmentInspectionItem()]  # sin equipo => [PENDIENTE]
        fd = {
            k: (v.description or k)
            for k, v in EquipmentInspectionItem.model_fields.items()
        }
        table_rows = [
            [resolve_text(getattr(entry, key), fd[key])[0] for key, _ in _EQUIP_COLUMNS]
            for entry in rows
        ]
        b.table([header for _, header in _EQUIP_COLUMNS], table_rows)
