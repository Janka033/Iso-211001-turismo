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
    resolve_code,
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


# Secciones normativas FIJAS de la plantilla (numeral 8.1 + patrones de
# auditoría reales, sesión 17): texto prescriptivo estándar del manual, no
# datos del cliente ni salida de la IA. La estructura la controla el sistema.
_INSPECTION_TYPES_TEXT = (
    "Previa a uso: verificación visual y funcional rápida de cada equipo antes "
    "de cada uso, realizada por el guía o líder de la actividad y registrada "
    "en el control de entrada y salida de equipos. "
    "Periódica: revisión técnica programada (mensual, trimestral o semestral "
    "según el equipo y su criticidad), con registro en la hoja de vida del "
    "equipo. "
    "Especial: revisión obligatoria tras un golpe, sobrecarga, exposición a un "
    "evento crítico o cualquier sospecha de daño; mientras se realiza, el "
    "equipo pasa al estado EN CUARENTENA."
)
_STATES_TEXT = (
    "Todo equipo se gestiona con cuatro estados normalizados: OK (nuevo o en "
    "condición óptima, apto para uso), A REVISAR (uso normal con desgaste, "
    "bajo vigilancia en las revisiones periódicas), EN CUARENTENA (no puede "
    "usarse hasta contar con concepto favorable de un experto o del "
    "fabricante) y DE BAJA (retiro definitivo: el equipo se marca y se "
    "inutiliza para impedir su uso accidental). El guía o líder de actividad "
    "tiene la facultad de pasar a cuarentena cualquier equipo con duda "
    "razonable, sin necesidad de autorización previa."
)
_LIFESPAN_TEXT = (
    "Cada tipo de equipo tiene una vida útil máxima conforme a las "
    "recomendaciones de su fabricante, registrada en su hoja de vida. Son "
    "criterios de baja o decomiso automático: el vencimiento de la vida útil, "
    "el daño estructural y la exposición a un evento crítico (carga de "
    "rescate real, impacto severo, contacto con sustancias que degraden el "
    "material). Un equipo en cuarentena solo regresa al servicio con concepto "
    "favorable del experto o del fabricante."
)
_LIFECYCLE_TEXT = (
    "Cada equipo cuenta con una identificación única (dos letras por tipo más "
    "consecutivo, p. ej. CA-01, aplicada sin contravenir el marcado permitido "
    "por el fabricante) y con una hoja de vida individual que registra: "
    "marca y referencia, fecha de compra y asignación, historial cronológico "
    "de revisiones con su resultado, cambios de estado y conceptos técnicos. "
    "La hoja de vida es el soporte que el auditor solicita por unidad, no por "
    "lote."
)


class EquipmentManualGenerator(DocumentGenerator):
    template_version = "manual-equipos-docx-v4"
    engine = "docx"
    custom_fields = frozenset({"equipment_items"})
    static_sections = (
        "Procedimiento por tipo de revisión (previa a uso por el guía con "
        "registro en control de entrada/salida; periódica programada con "
        "registro en hoja de vida; especial tras golpe o evento crítico con "
        "paso a cuarentena)",
        "Estados normalizados del equipo (Ok / A revisar / En cuarentena / De "
        "baja, con criterios y facultad del guía de aislar sin autorización)",
        "Vida útil máxima según fabricante y criterios de baja/decomiso "
        "automático",
        "Hoja de vida individual e identificación única por equipo (ID de dos "
        "letras + consecutivo, historial cronológico de revisiones)",
    )

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
        self,
        resolved: dict[str, ResolvedField],
        variables: BaseModel,
        document_code: str | None,
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
            code=resolve_code(document_code),
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
        b.section("6. Procedimiento por tipo de revisión", _INSPECTION_TYPES_TEXT)
        b.section("7. Estados normalizados del equipo", _STATES_TEXT)
        b.section("8. Vida útil y criterios de baja", _LIFESPAN_TEXT)
        b.section("9. Hoja de vida e identificación de equipos", _LIFECYCLE_TEXT)
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
