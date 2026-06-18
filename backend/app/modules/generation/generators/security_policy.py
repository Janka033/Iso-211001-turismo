"""Generador .docx de la Política de seguridad (numeral 5.2).

La ESTRUCTURA del documento es fija (este código). La IA solo aporta los
valores de las variables, ya validados por Pydantic y resueltos a texto o
``[PENDIENTE: ...]`` por la clase base.
"""

from __future__ import annotations

import io

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from pydantic import BaseModel

from app.modules.generation.generators.base import DocumentGenerator, ResolvedField


class SecurityPolicyGenerator(DocumentGenerator):
    template_version = "politica-seguridad-docx-v1"
    engine = "docx"

    def _render(
        self, resolved: dict[str, ResolvedField], variables: BaseModel
    ) -> bytes:
        def val(key: str) -> str:
            field = resolved[key]
            return field.value if isinstance(field.value, str) else "\n".join(field.value)

        def items(key: str) -> list[str]:
            field = resolved[key]
            return field.value if isinstance(field.value, list) else [field.value]

        doc = Document()

        # --- Encabezado / identidad -------------------------------------
        title = doc.add_heading("POLÍTICA DE SEGURIDAD", level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        subtitle = doc.add_paragraph()
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = subtitle.add_run(val("company_name"))
        run.bold = True
        run.font.size = Pt(13)

        nit_p = doc.add_paragraph()
        nit_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        nit_p.add_run(f"NIT: {val('nit')}")

        meta = doc.add_paragraph()
        meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
        meta.add_run("Conforme a la NTC-ISO 21101 — numeral 5.2").italic = True

        # --- Cuerpo -----------------------------------------------------
        self._section(doc, "1. Alcance", val("scope"))

        doc.add_heading("2. Actividades de turismo de aventura", level=1)
        for activity in items("activities"):
            doc.add_paragraph(activity, style="List Bullet")

        self._section(
            doc,
            "3. Compromiso de la alta dirección",
            val("management_commitment"),
        )

        doc.add_heading("4. Objetivos de seguridad", level=1)
        for objective in items("safety_objectives"):
            doc.add_paragraph(objective, style="List Bullet")

        self._section(
            doc,
            "5. Compromiso de cumplimiento legal y reglamentario",
            val("legal_commitment"),
        )
        self._section(
            doc,
            "6. Compromiso de mejora continua",
            val("continuous_improvement"),
        )
        self._section(
            doc,
            "7. Comunicación y disponibilidad",
            val("communication"),
        )

        # --- Aprobación -------------------------------------------------
        doc.add_heading("8. Aprobación", level=1)
        doc.add_paragraph(
            "Esta política es aprobada por la alta dirección y comunicada a todas "
            "las partes interesadas."
        )
        doc.add_paragraph(f"Representante legal: {val('legal_representative')}")
        doc.add_paragraph(f"Fecha de aprobación: {val('approval_date')}")

        buffer = io.BytesIO()
        doc.save(buffer)
        return buffer.getvalue()

    @staticmethod
    def _section(doc: Document, heading: str, body: str) -> None:
        doc.add_heading(heading, level=1)
        doc.add_paragraph(body)
