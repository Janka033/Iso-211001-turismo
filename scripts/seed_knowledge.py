"""Vectoriza la base de conocimiento (norma NTC-ISO 21101 + Módulo 2 ACOTUR)
hacia la tabla ``knowledge_chunks`` (pgvector).

Los dos PDFs tienen estructura distinta y se tratan por separado:

- ``norma``  -> prosa por numeral. Viene sucia (encabezados/pies repetidos,
  números de página, watermark) y trae TOC + definiciones que parecen
  numerales. Se limpia el boilerplate, se excluye el índice completo
  (bloque CONTENIDO→INTRODUCCIÓN) y se chunkea por numeral, incluidos los
  anexos (numerales A.x / B).
- ``acotur`` -> tabla (numeral y título | requisito | posibles evidencias).
  Se extrae con detección de tablas (pdfplumber), NO aplanando: las
  evidencias por numeral son lo más valioso para el RAG. Las filas de
  continuación (celda de numeral vacía) acumulan evidencias/requisito del
  numeral anterior; sale un chunk por numeral con todas sus evidencias.
- ``guias``  -> las guías MinCIT/FONTUR de ``knowledge-base/formatos/``
  (implementación, integración, indicadores). Prosa con encabezados en
  MAYÚSCULAS por numeral de la norma (4.1 … 10.2): se chunkea por numeral
  para que la generación las reciba en su RAG; las secciones sin numeral
  (introducciones, guía de indicadores) van con numeral NULL y sirven al
  RAG sin filtro (onboarding y fallback). El PST Módulo 2 de esa carpeta
  NO se procesa aquí: es el mismo PDF ya sembrado como ``acotur``.

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
# Heading de nivel superior con punto tras el numeral: "1. OBJETO Y CAMPO DE APLICACIÓN".
# Se limita a 1-2 dígitos + título en mayúscula para no confundir años u otras cifras.
TOP_HEADING_RE = re.compile(r"^(\d{1,2})\.\s+([A-ZÁÉÍÓÚÑ].*)$")
# Encabezado de anexo en línea propia: "ANEXO A" (el "(Normativo)" y el título vienen después).
ANEXO_HEADER_RE = re.compile(r"^ANEXO\s+([A-Z])\b\s*(.*)$")
# Subnumerales de anexo: "A.1 GENERALIDADES", "A.3 EVALUACIÓN DEL RIESGO".
ANEXO_NUMERAL_RE = re.compile(r"^([A-Z](?:\.\d+)+)\s+(\S.*)$")
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

    # Aplanar a líneas limpias. El índice se salta completo (CONTENIDO → primer
    # encabezado real): trae entradas partidas en dos renglones sin líder de
    # puntos que se cuelan como headings falsos. TOC_LINE_RE queda como red de
    # seguridad fuera de ese bloque.
    flat: list[str] = []
    in_toc = False
    for lines in pages_lines:
        for line in clean_lines(lines, boilerplate):
            if line == "CONTENIDO":
                in_toc = True
                continue
            if in_toc:
                is_body_start = line == "INTRODUCCIÓN" or (
                    TOP_HEADING_RE.match(line) and not TOC_LINE_RE.search(line)
                )
                if not is_body_start:
                    continue
                in_toc = False
            if TOC_LINE_RE.search(line):
                continue
            flat.append(line)

    # Agrupar por numeral (numéricos, "1. TÍTULO", anexos "A"/"A.1").
    sections: list[tuple[str, str, list[str], dict]] = []  # (numeral, titulo, lineas, meta_extra)
    current: tuple[str, str, list[str], dict] | None = None
    for line in flat:
        match = NUMERAL_RE.match(line) or TOP_HEADING_RE.match(line) or ANEXO_NUMERAL_RE.match(line)
        anexo_header = None if match else ANEXO_HEADER_RE.match(line)
        if match or anexo_header:
            if current:
                sections.append(current)
            if match:
                numeral, title = match.group(1), match.group(2)
                extra = {"section_type": "anexo"} if numeral[0].isalpha() else {}
            else:
                numeral = anexo_header.group(1)
                title = f"ANEXO {numeral}"
                extra = {"section_type": "anexo"}
            current = (numeral, title, [], extra)
        elif current:
            current[2].append(line)
    if current:
        sections.append(current)

    chunks: list[Chunk] = []
    index_por_numeral: Counter[str] = Counter()
    for numeral, title, body_lines, extra in sections:
        # Saltar preliminares/índice (0.x).
        if numeral.startswith("0"):
            continue
        is_definition = numeral.startswith("3.")
        if is_definition and skip_definitions:
            continue
        body = " ".join(body_lines).strip()
        if body:
            text = f"{numeral} {title}\n{body}".strip()
        elif is_definition and len(title) > 20:
            # Definición de una sola línea: todo el contenido vive en el heading.
            text = f"{numeral} {title}".strip()
        else:
            # Encabezado sin cuerpo (residuo de TOC u hoja suelta).
            continue
        meta = {"titulo": title, **extra}
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
# Chunking de ACOTUR (tabla: numeral y título | requisito | posibles evidencias)
# ---------------------------------------------------------------------------

# Celda de numeral: "4.1 Comprensión de la organización...", "5.2. Política",
# "6.1.1 Acciones...", "A.4. Tratamiento del riesgo", "A.3.Evaluación" (a veces
# el título viene pegado al punto, sin espacio). El punto final es opcional y
# el título puede faltar.
ACOTUR_NUMERAL_CELL_RE = re.compile(
    r"^\s*([A-Z](?:\.\d+)+|\d+(?:\.\d+)*)(?:(?:\.\s*|\s+)(.*))?$", re.S
)


def _norm_cell(cell: str | None) -> str:
    """Colapsa saltos de línea y espacios de una celda de pdfplumber."""
    return " ".join((cell or "").split())


def _is_acotur_header(cells: list[str]) -> bool:
    """Filas de encabezado (se repiten en cada página) o totalmente vacías."""
    low = " ".join(" ".join(cells).lower().split())
    if not low:
        return True
    if "numeral y titulo" in low or "ítem y titulo" in low or "item y titulo" in low:
        return True
    return low == "del requisito"


def chunk_acotur(pdf_path: Path) -> list[Chunk]:
    # Las tablas traen columnas vacías por celdas fusionadas: el numeral+título
    # vive en la PRIMERA celda, el requisito en la penúltima y las evidencias en
    # la última. Una fila sin numeral continúa el ítem anterior (más evidencias
    # o la continuación del requisito), incluso cruzando de página.
    items: list[dict] = []
    current: dict | None = None
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for row in table:
                    cells = [_norm_cell(c) for c in row]
                    if len(cells) < 3 or _is_acotur_header(cells):
                        continue
                    numeral_cell, requisito, evidencia = cells[0], cells[-2], cells[-1]
                    match = ACOTUR_NUMERAL_CELL_RE.match(numeral_cell) if numeral_cell else None
                    if match:
                        current = {
                            "numeral": match.group(1),
                            "titulo": _norm_cell(match.group(2)),
                            "requisito": [],
                            "evidencias": [],
                        }
                        items.append(current)
                    if current is None:
                        continue  # fila de datos antes del primer numeral
                    if requisito:
                        current["requisito"].append(requisito)
                    if evidencia:
                        current["evidencias"].append(evidencia)

    chunks: list[Chunk] = []
    index_por_numeral: Counter[str] = Counter()
    for item in items:
        requisito = " ".join(item["requisito"]).strip()
        evidencias = item["evidencias"]
        ev_lines = "\n".join(f"- {e}" for e in evidencias)
        content = (
            f"Numeral {item['numeral']} {item['titulo']}. Requisito: {requisito}\n"
            f"Posibles evidencias:\n{ev_lines}"
        ).strip()
        meta = {
            "titulo": item["titulo"],
            "requisito": requisito,
            "evidencias": evidencias,
        }
        for piece in _split(content):
            idx = index_por_numeral[item["numeral"]]
            index_por_numeral[item["numeral"]] += 1
            chunks.append(Chunk("acotur", item["numeral"], piece, idx, dict(meta, part=idx)))
    return chunks


# ---------------------------------------------------------------------------
# Chunking de las guías MinCIT/FONTUR (prosa con headings por numeral)
# ---------------------------------------------------------------------------

GUIAS_DIR = KNOWLEDGE_DIR / "formatos"
# Heading de sección: numeral con punto ("4.1", "10.2") + título en MAYÚSCULAS.
# Exigir el punto evita capturar listas numeradas ("1. Planificación…", en
# minúsculas) y cifras sueltas.
GUIA_HEADING_RE = re.compile(r"^(\d{1,2}(?:\.\d+)+)\s+([A-ZÁÉÍÓÚÜÑ][^a-z]{3,})$")
# Título de capítulo sin numeral, todo en mayúsculas ("OBJETIVO DE LA GUÍA").
GUIA_CAPS_RE = re.compile(r"^[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑÁ\s,\.\-:()]{6,}$")
# Entrada de índice: heading que termina en número de página.
GUIA_TOC_TAIL_RE = re.compile(r"\s\d{1,3}\s*\|?\s*$")
# Cuerpo mínimo para aceptar una sección (descarta residuos del índice).
GUIA_MIN_BODY = 200
# Secciones sin valor para el RAG (portada, índice, créditos, bibliografía).
GUIA_SKIP_TITLES = {"CONTENIDO", "ODINETNOC", "BIBLIOGRAFÍA", "MEJOR ANFITRIÓN"}


def _undouble(line: str) -> str:
    """Colapsa tokens con TODAS las letras dobladas ("CCOONNTTEENNIIDDOO" →
    "CONTENIDO", "44..11" → "4.1"): artefacto de pdfplumber con los títulos en
    fuente delineada de las guías. Los tokens normales no se tocan."""
    out = []
    for token in line.split():
        if len(token) >= 4 and len(token) % 2 == 0:
            pairs = [token[i : i + 2] for i in range(0, len(token), 2)]
            if all(p[0] == p[1] for p in pairs):
                token = "".join(p[0] for p in pairs)
        out.append(token)
    return " ".join(out)


def chunk_guia(pdf_path: Path, index_por_numeral: Counter[str]) -> list[Chunk]:
    with pdfplumber.open(pdf_path) as pdf:
        pages_lines = [(page.extract_text() or "").splitlines() for page in pdf.pages]

    boilerplate = detect_boilerplate(pages_lines)
    doc = pdf_path.stem

    sections: list[tuple[str | None, str, list[str]]] = []
    current: tuple[str | None, str, list[str]] | None = None
    for lines in pages_lines:
        for line in clean_lines(lines, boilerplate):
            line = _undouble(line)
            stripped = GUIA_TOC_TAIL_RE.sub("", line).strip()
            if stripped != line.strip() and GUIA_HEADING_RE.match(stripped):
                continue  # entrada del índice (heading + nº de página)
            heading = GUIA_HEADING_RE.match(line)
            if heading:
                if current:
                    sections.append(current)
                current = (heading.group(1), heading.group(2).strip(), [])
                continue
            if GUIA_CAPS_RE.match(line) and not any(ch.isdigit() for ch in line):
                if current and not current[2]:
                    # Título partido en dos renglones: continúa el heading en
                    # curso (no robar el cuerpo con una sección nueva).
                    current = (current[0], f"{current[1]} {line}".strip(), [])
                else:
                    if current:
                        sections.append(current)
                    # Los anexos se etiquetan con su letra: la matriz consulta
                    # el numeral "A" en su RAG (factory.extra_rag_numerales).
                    anexo = re.search(r"\bANEXO\s+([A-Z])\b", line)
                    current = (anexo.group(1) if anexo else None, line, [])
                continue
            if current is None:
                current = (None, doc, [])  # preámbulo antes del primer título
            current[2].append(line)
    if current:
        sections.append(current)

    chunks: list[Chunk] = []
    for numeral, title, body_lines in sections:
        body = " ".join(body_lines).strip()
        if len(body) < GUIA_MIN_BODY:
            continue  # residuo de índice o título huérfano
        if numeral is None and (
            title == doc or any(t in title for t in GUIA_SKIP_TITLES)
        ):
            continue  # portada/índice/créditos: ruido para el RAG
        head = f"{numeral} {title}" if numeral else title
        text = f"{head}\n{body}".strip()
        meta = {"titulo": title, "doc": doc}
        key = numeral or f"__none__/{doc}"
        for piece in _split(text):
            idx = index_por_numeral[key]
            index_por_numeral[key] += 1
            chunks.append(Chunk("guias", numeral, piece, idx, dict(meta, part=idx)))
    return chunks


def resolve_guias() -> list[Path]:
    pdfs = sorted(GUIAS_DIR.glob("*Guia*.pdf")) + sorted(GUIAS_DIR.glob("*Guía*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No hay PDFs de guías en {GUIAS_DIR}")
    return pdfs


# ---------------------------------------------------------------------------
# Persistencia
# ---------------------------------------------------------------------------

async def _embed_with_retry(provider, text: str, retries: int = 2) -> list[float]:
    """Embedding con reintento ante cuota agotada (free tier: 100 req/min)."""
    for attempt in range(retries + 1):
        try:
            return await provider.embed(text)
        except Exception as exc:  # noqa: BLE001 - cuota del upstream
            message = str(exc)
            if attempt < retries and ("429" in message or "RESOURCE_EXHAUSTED" in message):
                print("  … cuota de embeddings agotada; esperando 65 s para reintentar")
                await asyncio.sleep(65)
                continue
            raise
    raise RuntimeError("unreachable")


async def embed_and_store(chunks: list[Chunk], source: str) -> None:
    provider = get_ai_provider()
    client = get_service_client()

    rows = []
    for chunk in chunks:
        embedding = await _embed_with_retry(provider, chunk.content)
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
    targets = ["norma", "acotur", "guias"] if source == "all" else [source]
    for target in targets:
        if target == "guias":
            chunks = []
            index_por_numeral: Counter[str] = Counter()
            for pdf_path in resolve_guias():
                print(f"[guias] {pdf_path.name}")
                chunks.extend(chunk_guia(pdf_path, index_por_numeral))
        else:
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
    parser.add_argument("--source", choices=["norma", "acotur", "guias", "all"], default="all")
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
