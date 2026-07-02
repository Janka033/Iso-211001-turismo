"""Vectoriza los videos de capacitaciones/auditorías hacia ``knowledge_chunks``
(source='capacitaciones').

Flujo por archivo en ``knowledge-base/capacitaciones/``:

1. Si existe una transcripción con el mismo nombre (.srt/.vtt/.txt), se usa.
   Si solo hay medio (.mp4/.mp3/...), se transcribe con faster-whisper y la
   transcripción se guarda como .srt junto al video (las corridas siguientes
   ya no transcriben).
2. La transcripción se fragmenta en ventanas de ~1200 caracteres con
   solapamiento, conservando los tiempos (start/end) en metadata para poder
   citar el momento exacto del video.
3. A cada chunk se le detectan menciones de numerales de la norma
   ("numeral 6.1.1", "el 8.2", "anexo A"); el más mencionado queda en la
   columna ``numeral`` para que el RAG de generación lo recupere por numeral.
   Sin mención clara, queda NULL (recuperable por similitud semántica).
4. Embeddings vía ``AIProvider`` (regla de oro 8) y upsert idempotente por
   source (reutiliza ``embed_and_store`` de seed_knowledge, que ya maneja la
   cuota free tier con reintentos).

Uso:
    python scripts/seed_trainings.py --dry-run
    python scripts/seed_trainings.py
    python scripts/seed_trainings.py --file "knowledge-base/capacitaciones/aud1.mp4" --model small
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

from seed_knowledge import Chunk, embed_and_store, preview  # noqa: E402

TRAININGS_DIR = ROOT / "knowledge-base" / "capacitaciones"

MEDIA_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4a", ".mp3", ".wav", ".ogg"}
TRANSCRIPT_EXTS = (".srt", ".vtt", ".txt")

MAX_CHARS = 1200
OVERLAP = 200

# Menciones de numerales de la norma dentro del habla: "numeral 6.1.1",
# "el punto 8.2", "capítulo 5", "anexo A". Se limita a capítulos 4-10 (los
# normativos) para no confundir cifras sueltas con numerales.
NUMERAL_MENTION_RE = re.compile(r"(?<![\d.])([4-9]|10)(\.\d{1,2}){1,2}(?![\d.])")
ANEXO_MENTION_RE = re.compile(r"\banexo\s+([a-dA-D])\b", re.IGNORECASE)


@dataclass
class Cue:
    start: float  # segundos
    end: float
    text: str


# ---------------------------------------------------------------------------
# Transcripción (faster-whisper) — solo si no hay transcripción previa
# ---------------------------------------------------------------------------

def transcribe(media: Path, model_size: str, language: str) -> Path:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit(
            "falta faster-whisper para transcribir video/audio: pip install faster-whisper"
        )

    print(f"  transcribiendo con whisper ({model_size}, {language}) — puede tardar…")
    model = WhisperModel(model_size, device="auto", compute_type="int8")
    segments, info = model.transcribe(str(media), language=language, vad_filter=True)

    srt_path = media.with_suffix(".srt")
    with srt_path.open("w", encoding="utf-8") as fh:
        for i, seg in enumerate(segments, start=1):
            fh.write(f"{i}\n{_fmt_ts(seg.start)} --> {_fmt_ts(seg.end)}\n{seg.text.strip()}\n\n")
    print(f"  transcripción guardada: {srt_path.name} (duración {info.duration:.0f}s)")
    return srt_path


def _fmt_ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# ---------------------------------------------------------------------------
# Parseo de transcripciones
# ---------------------------------------------------------------------------

_TS_RE = re.compile(
    r"(\d{1,2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[.,](\d{3})"
)


def _ts_to_seconds(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_cues(path: Path) -> list[Cue]:
    """Parsea .srt/.vtt a cues con tiempos; .txt a un solo cue sin tiempos."""
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    if path.suffix.lower() == ".txt":
        return [Cue(0.0, 0.0, text)]

    cues: list[Cue] = []
    current: Cue | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = _TS_RE.search(line)
        if match:
            if current and current.text.strip():
                cues.append(current)
            g = match.groups()
            current = Cue(_ts_to_seconds(*g[:4]), _ts_to_seconds(*g[4:]), "")
            continue
        if current is None:
            continue  # cabecera WEBVTT / índices antes del primer timestamp
        if not line or line.isdigit():
            continue
        current.text += (" " if current.text else "") + line
    if current and current.text.strip():
        cues.append(current)
    return cues


# ---------------------------------------------------------------------------
# Chunking por ventanas con solapamiento (conserva tiempos)
# ---------------------------------------------------------------------------

def detect_numeral(text: str) -> str | None:
    """Numeral más mencionado en el texto, o None si no hay mención clara."""
    mentions = [m.group(0) for m in NUMERAL_MENTION_RE.finditer(text)]
    mentions += [m.group(1).upper() for m in ANEXO_MENTION_RE.finditer(text)]
    if not mentions:
        return None
    return Counter(mentions).most_common(1)[0][0]


def chunk_transcript(video_name: str, cues: list[Cue]) -> list[dict]:
    """Ventanas de ~MAX_CHARS con solapamiento de cues completos."""
    chunks: list[dict] = []
    window: list[Cue] = []
    size = 0

    def flush() -> None:
        nonlocal window, size
        if not window:
            return
        content = " ".join(c.text.strip() for c in window).strip()
        if content:
            chunks.append(
                {
                    "content": content,
                    "start": window[0].start,
                    "end": window[-1].end,
                    "video": video_name,
                }
            )
        # Solapamiento: arrastra los últimos cues hasta ~OVERLAP chars.
        kept: list[Cue] = []
        acc = 0
        for cue in reversed(window):
            acc += len(cue.text)
            kept.insert(0, cue)
            if acc >= OVERLAP:
                break
        window = kept if len(kept) < len(window) else []
        size = sum(len(c.text) for c in window)

    for cue in cues:
        # Un .txt llega como un único cue gigante: partirlo por tamaño.
        if len(cue.text) > MAX_CHARS:
            for piece_start in range(0, len(cue.text), MAX_CHARS - OVERLAP):
                piece = cue.text[piece_start : piece_start + MAX_CHARS]
                window.append(Cue(cue.start, cue.end, piece))
                size += len(piece)
                if size >= MAX_CHARS:
                    flush()
            continue
        window.append(cue)
        size += len(cue.text)
        if size >= MAX_CHARS:
            flush()
    flush()
    return chunks


def build_chunks(files: list[tuple[str, Path]]) -> list[Chunk]:
    """(video, transcripción) → Chunks listos para embed_and_store."""
    out: list[Chunk] = []
    index_por_numeral: Counter[str | None] = Counter()
    for video_name, transcript in files:
        cues = parse_cues(transcript)
        for piece in chunk_transcript(video_name, cues):
            numeral = detect_numeral(piece["content"])
            idx = index_por_numeral[numeral]
            index_por_numeral[numeral] += 1
            meta = {
                "video": piece["video"],
                "start_seconds": round(piece["start"], 1),
                "end_seconds": round(piece["end"], 1),
            }
            out.append(Chunk("capacitaciones", numeral, piece["content"], idx, meta))
    return out


# ---------------------------------------------------------------------------
# Descubrimiento de archivos
# ---------------------------------------------------------------------------

def discover(directory: Path, explicit: str | None, model: str, language: str) -> list[tuple[str, Path]]:
    """Devuelve pares (nombre_video, ruta_transcripción), transcribiendo si falta."""
    if explicit:
        candidates = [Path(explicit) if Path(explicit).is_absolute() else ROOT / explicit]
    else:
        if not directory.exists():
            sys.exit(f"No existe {directory}. Crea la carpeta y pon ahí los videos/transcripciones.")
        candidates = sorted(
            p for p in directory.iterdir()
            if p.suffix.lower() in MEDIA_EXTS or p.suffix.lower() in TRANSCRIPT_EXTS
        )

    seen_stems: set[str] = set()
    pairs: list[tuple[str, Path]] = []
    for path in candidates:
        stem = path.stem
        if stem in seen_stems:
            continue
        seen_stems.add(stem)
        if path.suffix.lower() in TRANSCRIPT_EXTS:
            pairs.append((stem, path))
            continue
        # Es un medio: ¿ya existe su transcripción?
        transcript = next(
            (path.with_suffix(ext) for ext in TRANSCRIPT_EXTS if path.with_suffix(ext).exists()),
            None,
        )
        if transcript is None:
            transcript = transcribe(path, model, language)
        pairs.append((path.name, transcript))
    return pairs


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------

async def run(args: argparse.Namespace) -> None:
    pairs = discover(TRAININGS_DIR, args.file, args.model, args.language)
    if not pairs:
        sys.exit(
            f"No hay videos ni transcripciones en {TRAININGS_DIR}. "
            "Formatos: video/audio (mp4, mp3, …) o transcripción (.srt/.vtt/.txt)."
        )
    print(f"{len(pairs)} archivo(s) de capacitación:")
    for name, transcript in pairs:
        print(f"  - {name}  (transcripción: {transcript.name})")

    chunks = build_chunks(pairs)
    con_numeral = sum(1 for c in chunks if c.numeral)
    print(f"\n{len(chunks)} chunks ({con_numeral} con numeral detectado)")

    if args.dry_run:
        preview(chunks)
        return
    await embed_and_store(chunks, "capacitaciones")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed de knowledge_chunks con transcripciones de capacitaciones."
    )
    parser.add_argument("--file", help="Un solo archivo (video o transcripción).")
    parser.add_argument("--dry-run", action="store_true", help="Solo imprime chunks; no toca API ni DB.")
    parser.add_argument("--model", default="small", help="Modelo whisper (tiny/base/small/medium).")
    parser.add_argument("--language", default="es", help="Idioma del audio (default: es).")
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
