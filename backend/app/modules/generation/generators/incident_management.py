"""Generador .docx del Procedimiento de gestión de incidentes (numeral 8.3).

Dos partes:
  - Procedimiento: contenido inteligente (variables de la IA, validadas).
  - Formato de reporte de incidentes: estructura FIJA en blanco, para
    diligenciar a mano. Sus etiquetas no las pone la IA.
"""

from __future__ import annotations

import io

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from pydantic import BaseModel

from app.modules.generation.generators.base import DocumentGenerator, ResolvedField
from app.modules.generation.generators.felipe_docx import apply_base_style

# Campos del FORMATO (fijos, en blanco para diligenciar).
_FORM_FIELDS: list[str] = [
    "N.° de reporte",
    "Fecha",
    "Hora",
    "Lugar",
    "Actividad",
    "Tipo de evento (casi-accidente / incidente / accidente)",
    "Personas involucradas",
    "Descripción del evento",
    "Lesiones o daños",
    "Acciones inmediatas tomadas",
    "Causa probable",
    "Acciones correctivas propuestas",
    "Reportado por",
    "Firma / cargo",
]


class IncidentManagementGenerator(DocumentGenerator):
    template_version = "gestion-incidentes-docx-v1"
    engine = "docx"

    def _render(
        self, resolved: dict[str, ResolvedField], variables: BaseModel
    ) -> bytes:
        def val(key: str) -> str:
            f = resolved[key]
            return f.value if isinstance(f.value, str) else "\n".join(f.value)

        def items(key: str) -> list[str]:
            f = resolved[key]
            return f.value if isinstance(f.value, list) else [f.value]

        doc = Document()
        apply_base_style(doc)  # Calibri 11 (consistencia del sistema documental)
        title = doc.add_heading("PROCEDIMIENTO DE GESTIÓN DE INCIDENTES", level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        sub = doc.add_paragraph()
        sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = sub.add_run(val("company_name"))
        run.bold = True
        run.font.size = Pt(13)

        meta = doc.add_paragraph()
        meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
        meta.add_run("Conforme a la NTC-ISO 21101 — numeral 8.3").italic = True

        self._section(doc, "1. Objetivo", val("objective"))
        self._section(doc, "2. Alcance", val("scope"))

        doc.add_heading("3. Clasificación de eventos", level=1)
        for cls in items("incident_classification"):
            doc.add_paragraph(cls, style="List Bullet")

        doc.add_heading("4. Procedimiento", level=1)
        for i, step in enumerate(items("procedure_steps"), start=1):
            doc.add_paragraph(f"{i}. {step}")

        self._section(doc, "5. Responsable", val("responsible"))
        self._section(doc, "6. Acciones correctivas", val("corrective_actions_process"))
        self._section(doc, "7. Conservación de registros", val("record_retention"))
        self._section(doc, "8. Revisión del procedimiento", val("review_frequency"))

        doc.add_heading("9. Aprobación", level=1)
        doc.add_paragraph(f"Representante legal: {val('legal_representative')}")
        doc.add_paragraph(f"Fecha de aprobación: {val('approval_date')}")

        # --- FORMATO DE REPORTE (estructura fija, en blanco) -----------
        doc.add_page_break()
        form_title = doc.add_heading("FORMATO DE REPORTE DE INCIDENTES", level=1)
        form_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        table = doc.add_table(rows=0, cols=2)
        table.style = "Light Grid Accent 1"
        for label in _FORM_FIELDS:
            cells = table.add_row().cells
            cells[0].paragraphs[0].add_run(label).bold = True
            cells[1].text = ""  # en blanco, para diligenciar

        buffer = io.BytesIO()
        doc.save(buffer)
        return buffer.getvalue()

    @staticmethod
    def _section(doc: Document, heading: str, body: str) -> None:
        doc.add_heading(heading, level=1)
        doc.add_paragraph(body)
