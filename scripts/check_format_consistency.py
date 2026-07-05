"""Verificación lado a lado del formato de los 7 documentos de ``samples/``.

Chequea que todos pertenezcan al MISMO sistema documental (formato Felipe):
fuente Calibri 11, encabezado con Código/Revisión/paginación, bloque de firmas
Elaborado/Revisado/Aprobado y tabla CONTROL DE CAMBIOS (docx); encabezado con
código en la hoja (xlsx, tipo MT: sin firmas por diseño).

Uso:  python scripts/check_format_consistency.py
Sale con código 1 si algún documento rompe la consistencia.
"""

from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"

# document_type -> (código esperado, portada esperada per taxonomía)
DOCX_EXPECTED: dict[str, tuple[str, bool]] = {
    "politica_seguridad": ("PO-01", False),  # PO: solo encabezado, sin portada
    "plan_emergencias": ("PL-01", True),
    "gestion_incidentes": ("PR-02", True),
    "manual_perfiles_cargos": ("MA-02", True),
    "comunicacion_participacion_consulta": ("PR-07", True),
    "manual_inspeccion_equipos": ("MA-03", True),
}


def _header_text(doc: Document) -> str:
    parts = []
    for section in doc.sections:
        for p in section.header.paragraphs:
            parts.append(p.text)
        for t in section.header.tables:
            for row in t.rows:
                parts.extend(c.text for c in row.cells)
    return "\n".join(parts)


def _body_text(doc: Document) -> str:
    parts = [p.text for p in doc.paragraphs]
    for t in doc.tables:
        for row in t.rows:
            parts.extend(c.text for c in row.cells)
    return "\n".join(parts)


def check_docx(name: str, code: str, cover: bool) -> list[str]:
    doc = Document(str(SAMPLES / f"{name}.docx"))
    problems: list[str] = []

    font = doc.styles["Normal"].font
    if font.name != "Calibri":
        problems.append(f"fuente Normal = {font.name!r}, se esperaba Calibri")
    if font.size is None or font.size.pt != 11:
        problems.append(f"tamaño Normal = {font.size}, se esperaba 11pt")

    header = _header_text(doc)
    if f"Código: {code}" not in header:
        problems.append(f"encabezado sin 'Código: {code}'")
    if "Revisión: 01" not in header:
        problems.append("encabezado sin 'Revisión: 01'")
    if "Página" not in header:
        problems.append("encabezado sin paginación 'Página N de M'")

    body = _body_text(doc)
    for required in ("Firmas", "Elaborado por", "Revisado por", "Aprobado por"):
        if required not in body:
            problems.append(f"sin bloque de firmas ('{required}')")
            break
    if "CONTROL DE CAMBIOS" not in body:
        problems.append("sin tabla CONTROL DE CAMBIOS")

    # La portada imprime el código centrado en el cuerpo; sin portada, no.
    has_cover_code = f"Código: {code}" in "\n".join(p.text for p in doc.paragraphs)
    if cover and not has_cover_code:
        problems.append("se esperaba portada (código centrado) y no está")
    if not cover and has_cover_code:
        problems.append("tiene portada y el tipo PO va sin portada")

    return problems


def check_xlsx(name: str, code: str) -> list[str]:
    wb = load_workbook(str(SAMPLES / f"{name}.xlsx"))
    ws = wb["Matriz de Riesgos"]
    problems: list[str] = []
    header_cells = [
        str(ws.cell(row=r, column=1).value or "") for r in range(1, 7)
    ]
    if not any(f"Código: {code}" in c for c in header_cells):
        problems.append(f"hoja sin 'Código: {code}' en el bloque de identidad")
    if not any("Revisión: 01" in c for c in header_cells):
        problems.append("hoja sin 'Revisión: 01'")
    return problems


def main() -> int:
    failures = 0
    for name, (code, cover) in DOCX_EXPECTED.items():
        problems = check_docx(name, code, cover)
        status = "OK" if not problems else "FALLA"
        print(f"  [{status}] {name} ({code})")
        for p in problems:
            print(f"         - {p}")
        failures += bool(problems)

    problems = check_xlsx("matriz_riesgos", "MT-01")
    status = "OK" if not problems else "FALLA"
    print(f"  [{status}] matriz_riesgos (MT-01, xlsx)")
    for p in problems:
        print(f"         - {p}")
    failures += bool(problems)

    print()
    if failures:
        print(f"{failures} documento(s) rompen la consistencia del sistema documental.")
        return 1
    print("Los 7 documentos comparten el formato del sistema documental.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
