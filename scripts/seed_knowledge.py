"""Vectoriza la base de conocimiento (norma NTC-ISO 21101 + Módulo 2 ACOTUR)
hacia la tabla ``knowledge_chunks`` (pgvector).

Los dos PDFs tienen estructura distinta y se tratan por separado:

- ``norma``  -> prosa por numeral. Viene sucia (encabezados/pies repetidos,
  números de página, watermark) y trae TOC + definiciones que parecen
  numerales. Se limpia el boilerplate, se excluye el TOC y se chunkea por
  numeral.
- ``acotur`` -> tabla (numeral | requisito | posibles evidencias). Se extrae
  con detección de tablas (pdfplumber), NO aplanando: las evidencias por
  numeral son lo más valioso para el RAG. Un chunk por fila.

Toda llamada de embedding pasa por ``AIProvider`` (regla de oro 8).
El upsert usa el service client (salta RLS: operación superadmin legítima).

Uso:
    python scripts/seed_knowledge.py --source norma --dry-run
    python scripts/seed_knowledge.py --source norma --file knowledge-base/ntc-iso-21101.pdf
    python scripts/seed_knowledge.py --source all
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber

# Permitir importar el paquete `app` del backend.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.ai.factory import get_ai_provider  # noqa: E402
from app.core.supabase import get_service_client  # noqa: E402

KNOWLEDGE_DIR = ROOT / "knowledge-base"

# Heading de numeral al inicio de línea: "5.2 Política", "6.1.1 Acciones..."
NUMERAL_RE = re.compile(r"^(\d+(?:\.\d+)*)\s+(\S.*)$")
# Línea que es solo un número de página.
PAGE_NUMBER_RE = re.compile(r"^\s*\d{1,4}\s*$")
# Línea de TOC: contiene un líder de puntos largo ("Política .......... 12").
# El número de página a veces sale como carácter ilegible (fuente del PDF), así
# que basta con detectar la fila de puntos.
TOC_LINE_RE = re.compile(r"\.{4,}")

MAX_CHARS = 1500
OVERLAP = 200


@dataclass
class Chunk:
    source: str
    numeral: str | None
    content: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Resolución de archivos
# ---------------------------------------------------------------------------

def resolve_pdf(source: str, explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.is_absolute():
            path = ROOT / explicit
        if not path.exists():
            raise FileNotFoundError(f"No existe el PDF: {path}")
        return path

    hints = {"norma": ("21101", "norma", "ntc"), "acotur": ("acotur", "modulo", "módulo")}
    candidates = sorted(KNOWLEDGE_DIR.glob("*.pdf")) + sorted(KNOWLEDGE_DIR.glob("*.PDF"))
    for pdf in candidates:
        name = pdf.name.lower()
        if any(h in name for h in hints[source]):
            return pdf
    raise FileNotFoundError(
        f"No encontré un PDF para '{source}' en {KNOWLEDGE_DIR}. "
        f"Usa --file para indicarlo explícitamente."
    )


# ---------------------------------------------------------------------------
# Limpieza de boilerplate (norma)
# ---------------------------------------------------------------------------

def detect_boilerplate(pages_lines: list[list[str]]) -> set[str]:
    """Líneas cortas que se repiten en muchas páginas = encabezado/pie/watermark."""
    counter: Counter[str] = Counter()
    for lines in pages_lines:
        for line in set(lines):  # una vez por página
            stripped = line.strip()
            if stripped and len(stripped) < 80:
                counter[stripped] += 1
    threshold = max(2, int(len(pages_lines) * 0.4))
    return {line for line, n in counter.items() if n >= threshold}


def clean_lines(lines: list[str], boilerplate: set[str]) -> list[str]:
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped in boilerplate:
            continue
        if PAGE_NUMBER_RE.match(stripped):
            continue
        cleaned.append(stripped)
    return cleaned


# ---------------------------------------------------------------------------
# Chunking de la norma (por numeral)
# ---------------------------------------------------------------------------

def chunk_norma(pdf_path: Path, skip_definitions: bool) -> list[Chunk]:
    with pdfplumber.open(pdf_path) as pdf:
        pages_lines = [(page.extract_text() or "").splitlines() for page in pdf.pages]

    boilerplate = detect_boilerplate(pages_lines)

    # Aplanar a líneas limpias, descartando líneas de TOC.
    flat: list[str] = []
    for lines in pages_lines:
        for line in clean_lines(lines, boilerplate):
            if TOC_LINE_RE.search(line):
                continue  # excluir el índice
            flat.append(line)

    # Agrupar por numeral.
    sections: list[tuple[str, str, list[str]]] = []  # (numeral, titulo, lineas)
    current: tuple[str, str, list[str]] | None = None
    for line in flat:
        match = NUMERAL_RE.match(line)
        if match:
            numeral, title = match.group(1), match.group(2)
            if current:
                sections.append(current)
            current = (numeral, title, [])
        elif current:
            current[2].append(line)
    if current:
        sections.append(current)

    chunks: list[Chunk] = []
    index_por_numeral: Counter[str] = Counter()
    for numeral, title, body_lines in sections:
        # Saltar preliminares/índice (0.x) y encabezados sin cuerpo (TOC residual).
        if numeral.startswith("0"):
            continue
        is_definition = numeral.startswith("3.")
        if is_definition and skip_definitions:
            continue
        body = " ".join(body_lines).strip()
        if not body:
            continue
        text = f"{numeral} {title}\n{body}".strip()
        meta = {"titulo": title}
        if is_definition:
            meta["section_type"] = "definicion"
        for piece in _split(text):
            idx = index_por_numeral[numeral]
            index_por_numeral[numeral] += 1
            chunks.append(
                Chunk("norma", numeral, piece, idx, dict(meta, part=idx)),
            )
    return chunks


def _split(text: str) -> list[str]:
    """Sub-split de secciones largas con solapamiento, conservando el numeral."""
    if len(text) <= MAX_CHARS:
        return [text]
    pieces, start = [], 0
    while start < len(text):
        end = start + MAX_CHARS
        pieces.append(text[start:end])
        start = end - OVERLAP
    return pieces


# ---------------------------------------------------------------------------
# Chunking de ACOTUR (tabla: numeral | requisito | posibles evidencias)
# ---------------------------------------------------------------------------

def chunk_acotur(pdf_path: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    index_por_numeral: Counter[str] = Counter()
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for row in table:
                    cells = [(c or "").strip() for c in row]
                    if len(cells) < 2:
                        continue
                    numeral = cells[0]
                    # Saltar la fila de encabezado de la tabla.
                    if not re.match(r"^\d+(?:\.\d+)*$", numeral):
                        continue
                    requisito = cells[1] if len(cells) > 1 else ""
                    evidencias = cells[2] if len(cells) > 2 else ""
                    content = (
                        f"Numeral {numeral}. Requisito: {requisito}\n"
                        f"Posibles evidencias: {evidencias}"
                    ).strip()
                    idx = index_por_numeral[numeral]
                    index_por_numeral[numeral] += 1
                    chunks.append(
                        Chunk(
                            "acotur",
                            numeral,
                            content,
                            idx,
                            {"requisito": requisito, "evidencias": evidencias},
                        )
                    )
    return chunks


# ---------------------------------------------------------------------------
# Persistencia
# ---------------------------------------------------------------------------

async def embed_and_store(chunks: list[Chunk], source: str) -> None:
    provider = get_ai_provider()
    client = get_service_client()

    rows = []
    for chunk in chunks:
        embedding = await provider.embed(chunk.content)
        rows.append(
            {
                "source": chunk.source,
                "numeral": chunk.numeral,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "embedding": embedding,
                "metadata": chunk.metadata,
            }
        )

    # Idempotente: reemplaza todo el source.
    client.table("knowledge_chunks").delete().eq("source", source).execute()
    if rows:
        client.table("knowledge_chunks").insert(rows).execute()
    print(f"  -> {len(rows)} chunks insertados para source='{source}'")


def preview(chunks: list[Chunk]) -> None:
    print(f"  {len(chunks)} chunks (dry-run, sin embeddings ni DB):")
    for chunk in chunks[:8]:
        head = chunk.content.replace("\n", " ")[:90]
        print(f"    [{chunk.source} {chunk.numeral} #{chunk.chunk_index}] {head}…")
    if len(chunks) > 8:
        print(f"    … (+{len(chunks) - 8} más)")


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------

async def run(source: str, file: str | None, dry_run: bool, skip_definitions: bool) -> None:
    targets = ["norma", "acotur"] if source == "all" else [source]
    for target in targets:
        pdf_path = resolve_pdf(target, file if source == target else None)
        print(f"[{target}] {pdf_path.name}")
        if target == "norma":
            chunks = chunk_norma(pdf_path, skip_definitions)
        else:
            chunks = chunk_acotur(pdf_path)

        if dry_run:
            preview(chunks)
        else:
            await embed_and_store(chunks, target)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed de knowledge_chunks (norma + ACOTUR).")
    parser.add_argument("--source", choices=["norma", "acotur", "all"], default="all")
    parser.add_argument("--file", help="Ruta al PDF (si no, se autodetecta en knowledge-base/).")
    parser.add_argument("--dry-run", action="store_true", help="Solo imprime chunks; no toca API ni DB.")
    parser.add_argument(
        "--skip-definitions",
        action="store_true",
        help="Excluir los numerales 3.x (definiciones) de la norma.",
    )
    args = parser.parse_args()
    asyncio.run(run(args.source, args.file, args.dry_run, args.skip_definitions))


if __name__ == "__main__":
    main()
