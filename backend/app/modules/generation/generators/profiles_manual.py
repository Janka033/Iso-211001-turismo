"""Generador .docx del Manual de perfiles y funciones de cargo (MA-02, 5.3 + 7.2).

Generador DELGADO: mapea sus Variables a secciones y delega el layout real
(Calibri, encabezado, firmas, CONTROL DE CAMBIOS) en ``FelipeDocxBuilder``.
Anti-alucinación: dato faltante = [PENDIENTE].
"""

from __future__ import annotations

from pydantic import BaseModel

from app.modules.generation.generators.base import (
    DocumentGenerator,
    ResolvedField,
    pending_marker,
    resolve_text,
)
from app.modules.generation.generators.felipe_docx import FelipeDocxBuilder
from app.modules.generation.schemas import ProfilesManualVariables, RoleProfile


class ProfilesManualGenerator(DocumentGenerator):
    template_version = "manual-perfiles-docx-v3"
    engine = "docx"
    custom_fields = frozenset({"role_profiles"})

    def _extra_pending(
        self, variables: BaseModel, required_fields: set[str] | None
    ) -> list[str]:
        assert isinstance(variables, ProfilesManualVariables)
        if not variables.role_profiles:
            return (
                ["role_profiles"]
                if self._is_required("role_profiles", required_fields)
                else []
            )
        # Pendientes de CELDA (patrón de risk_matrix): cada subcampo vacío de
        # cada perfil real. No mueven la completitud, pero el cliente y el
        # auditor deben verlos: son los [PENDIENTE: ...] del documento.
        pending: list[str] = []
        for i, profile in enumerate(variables.role_profiles):
            for key in ("role", "level", "purpose", "requirements", "reports_to"):
                value = getattr(profile, key)
                if not (value.strip() if isinstance(value, str) else value):
                    pending.append(f"role_profiles[{i}].{key}")
            if not [f for f in profile.functions if str(f).strip()]:
                pending.append(f"role_profiles[{i}].functions")
        return pending

    def _render(
        self, resolved: dict[str, ResolvedField], variables: BaseModel
    ) -> bytes:
        assert isinstance(variables, ProfilesManualVariables)

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
            code="MA-02",
            title="Manual de perfiles y funciones de cargo",
            company=val("company_name"),
            norm_reference="NTC-ISO 21101 — numerales 5.3 y 7.2",
            approval_date=approval_date,
        )
        b.section("1. Objetivo", val("objective"))
        b.section("2. Alcance", val("scope"))
        b.section("3. Estructura organizacional", val("org_structure"))
        b.heading("4. Perfiles y funciones por cargo")
        self._profiles(b, variables.role_profiles)
        b.signatures(approved=(legal_rep, "Representante legal" if legal_rep else ""))
        b.change_control()
        return b.render()

    @staticmethod
    def _profiles(b: FelipeDocxBuilder, profiles: list[RoleProfile]) -> None:
        rows = profiles or [RoleProfile()]  # sin perfiles => bloque [PENDIENTE]
        fd = {k: (v.description or k) for k, v in RoleProfile.model_fields.items()}
        for p in rows:
            role, _ = resolve_text(p.role, fd["role"])
            b.heading(role, level=2)
            level, _ = resolve_text(p.level, fd["level"])
            purpose, _ = resolve_text(p.purpose, fd["purpose"])
            reqs, _ = resolve_text(p.requirements, fd["requirements"])
            rep, _ = resolve_text(p.reports_to, fd["reports_to"])
            b.doc.add_paragraph(f"Nivel: {level}")
            b.doc.add_paragraph(f"Objetivo del cargo: {purpose}")
            b.doc.add_paragraph(f"Reporta a: {rep}")
            b.doc.add_paragraph(f"Requisitos y competencias: {reqs}")
            b.doc.add_paragraph("Funciones:")
            funcs = [str(f).strip() for f in (p.functions or []) if str(f).strip()]
            if funcs:
                for f in funcs:
                    b.doc.add_paragraph(f, style="List Bullet")
            else:
                b.doc.add_paragraph(pending_marker(fd["functions"]), style="List Bullet")
