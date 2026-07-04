"""Lógica de negocio del onboarding.

Persiste los datos crudos del cliente en ``onboarding_data`` (separados de
``ai_outputs``) y calcula el avance. La generación los consume como contexto.

El onboarding conversacional (``chat``) replica el patrón anti-alucinación de
generation/quality: checklist (universal + por actividad) + RAG → prompt (DB) →
IA (AIProvider) → validación Pydantic → merge en ``onboarding_data``. La IA solo
EXTRAE lo que el cliente dijo y REDACTA la siguiente pregunta; **el backend
decide de forma determinística cuál es el próximo campo** (regla mental central:
el sistema controla el flujo, la IA solo el contenido inteligente).

El repository (supabase-py es síncrono) se ejecuta en un hilo para no bloquear
el event loop.
"""

from __future__ import annotations

import functools
import json
import logging
from collections.abc import Callable
from typing import TypeVar

import anyio
from fastapi import HTTPException, status

from app.core.ai.factory import get_ai_provider
from app.modules.onboarding import repository
from app.modules.onboarding.schemas import (
    OnboardingChatRequest,
    OnboardingChatResponse,
    OnboardingExtraction,
    OnboardingField,
    OnboardingPayload,
    OnboardingState,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Campos universales que se le PREGUNTAN al cliente, en orden de prioridad.
# `activities` NO está aquí (se captura por selección de chips), pero sí cuenta
# para la completitud (ver _UNIVERSAL_KEYS).
_UNIVERSAL_QUESTIONS: tuple[tuple[str, str], ...] = (
    ("main_region", "¿En qué departamento o zona operan principalmente?"),
    ("locations", "¿En qué ubicaciones específicas operan (ríos, cañones, sedes)?"),
    ("scope", "¿Cuál es el alcance de su operación: qué actividades y dónde las prestan?"),
    ("certified_guides", "¿Cuántos guías certificados tiene su operación?"),
    ("legal_representative", "¿Quién es el representante legal de la empresa?"),
    ("nit", "¿Cuál es el NIT de la empresa?"),
    ("rnt_status", "¿Su RNT está vigente, por renovar o aún no lo tienen?"),
    ("rnt_number", "¿Cuál es el número de RNT?"),
    ("emergency_contacts", "¿Qué contactos de emergencia tienen (bomberos, ambulancia, rescate)?"),
    ("existing_controls", "¿Qué medidas o controles de seguridad ya aplican en su operación?"),
    ("management_commitment", "¿Cómo se compromete la dirección con la seguridad?"),
)

# Todos los campos universales que cuentan para la completitud (12).
_UNIVERSAL_KEYS: tuple[str, ...] = ("activities",) + tuple(k for k, _ in _UNIVERSAL_QUESTIONS)

# Campos universales de tipo lista (para coercionar el valor extraído por la IA).
_LIST_FIELDS: frozenset[str] = frozenset({"activities", "locations", "emergency_contacts"})

# Orden de las categorías por actividad (Parte B) al preguntar.
_ACTIVITY_CATEGORY_ORDER: tuple[str, ...] = (
    "equipo",
    "competencias",
    "emergencias",
    "riesgos",
    "seguimiento",
)

# Plantillas de pregunta por categoría (fallback cuando la IA no redacta, y como
# guía que se le pasa a la IA). {act} = actividad, {desc} = descripción del checklist.
_ACTIVITY_QUESTION_TEMPLATES: dict[str, str] = {
    "equipo": "Para {act}, ¿con qué equipo de seguridad cuentan? (ref.: {desc})",
    "competencias": "Para {act}, ¿qué certificaciones tienen sus guías? (ref.: {desc})",
    "emergencias": "Para {act}, ¿qué protocolos de emergencia tienen definidos? (ref.: {desc})",
    "riesgos": "Para {act}, ¿qué riesgos identifican y cómo los controlan? (ref.: {desc})",
    "seguimiento": "Para {act}, ¿qué seguimiento o registros llevan? (ref.: {desc})",
}


# Campos clave del avance LEGACY (GET/PUT). El onboarding conversacional
# (/chat) usa completitud dinámica; los endpoints simples conservan su contrato.
_KEY_FIELDS: tuple[str, ...] = (
    "activities",
    "main_region",
    "certified_guides",
    "legal_representative",
    "rnt_status",
)


async def _run(fn: Callable[..., T], *args: object) -> T:
    """Ejecuta una llamada bloqueante (repository) en un hilo."""
    return await anyio.to_thread.run_sync(functools.partial(fn, *args))


def _has_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, dict, str)):
        return len(value) > 0
    return True


def _to_list(value: str) -> list[str]:
    """Parte un texto en lista por saltos de línea, ';' o ','. Sin inventar."""
    parts: list[str] = []
    for chunk in value.replace("\n", ";").replace(",", ";").split(";"):
        item = chunk.strip()
        if item:
            parts.append(item)
    return parts


# ---------------------------------------------------------------------------
# Completitud y flujo (autoridad del backend)
# ---------------------------------------------------------------------------


def _category_of(field_key: str) -> str:
    return field_key.split("_", 1)[0]


def _pending_fields(data: dict, checklist: list[dict]) -> list[dict]:
    """Lista ORDENADA de campos aún sin dato: universales primero, luego por
    actividad (por orden de categoría). Cada item: field_key, activity, prompt."""
    pending: list[dict] = []
    for key, question in _UNIVERSAL_QUESTIONS:
        if not _has_value(data.get(key)):
            pending.append({"field_key": key, "activity": None, "prompt": question})

    activity_fields = data.get("activity_fields") or {}

    def rank(row: dict) -> tuple[int, str]:
        cat = _category_of(row["field_key"])
        idx = _ACTIVITY_CATEGORY_ORDER.index(cat) if cat in _ACTIVITY_CATEGORY_ORDER else 99
        return idx, row["field_key"]

    for row in sorted(checklist, key=rank):
        if not activity_fields.get(row["field_key"]):
            cat = _category_of(row["field_key"])
            template = _ACTIVITY_QUESTION_TEMPLATES.get(cat, "Para {act}: {desc}")
            prompt = template.format(
                act=row.get("activity", ""), desc=row.get("description", "")
            )
            pending.append(
                {"field_key": row["field_key"], "activity": row.get("activity"), "prompt": prompt}
            )
    return pending


def _measure(data: dict) -> tuple[float, bool]:
    """Avance LEGACY sobre los 5 campos clave fijos (contrato de GET/PUT)."""
    filled = [f for f in _KEY_FIELDS if _has_value(data.get(f))]
    pct = round(len(filled) / len(_KEY_FIELDS) * 100, 2)
    return pct, len(filled) == len(_KEY_FIELDS)


def _measure_dynamic(data: dict, checklist: list[dict]) -> tuple[float, bool]:
    """% de campos esperados con dato: 12 universales + los Parte B de las
    actividades elegidas. Es la completitud del onboarding conversacional."""
    total = len(_UNIVERSAL_KEYS)
    filled = sum(1 for k in _UNIVERSAL_KEYS if _has_value(data.get(k)))
    activity_fields = data.get("activity_fields") or {}
    for row in checklist:
        total += 1
        if activity_fields.get(row["field_key"]):
            filled += 1
    pct = round(filled / total * 100, 2) if total else 0.0
    return pct, filled == total


def _sanitize_extracted(raw: dict[str, str], activity_keys: set[str]) -> dict[str, str]:
    """Deja solo lo que la IA puede tocar: campos universales conocidos o
    field_keys de las actividades elegidas. Descarta claves inventadas/vacías."""
    allowed = set(_UNIVERSAL_KEYS) | activity_keys
    return {
        k: v.strip()
        for k, v in raw.items()
        if k in allowed and isinstance(v, str) and v.strip()
    }


def _apply_extracted(data: dict, extracted: dict[str, str], activity_keys: set[str]) -> None:
    """Aplica lo extraído sobre el dict de onboarding_data (in place)."""
    for key, value in extracted.items():
        if key in _LIST_FIELDS:
            data[key] = _to_list(value)
        elif key in _UNIVERSAL_KEYS:
            data[key] = value
        elif key in activity_keys:
            data.setdefault("activity_fields", {})[key] = value


# ---------------------------------------------------------------------------
# Lectura / escritura simple (GET, PUT) — compatibilidad (medida legacy)
# ---------------------------------------------------------------------------


async def get_state(tenant_id: str, token: str) -> OnboardingState:
    raw = await _run(repository.get_onboarding, tenant_id, token)
    data = OnboardingPayload.model_validate(raw or {})
    pct, completed = _measure(data.model_dump())
    return OnboardingState(data=data, completeness=pct, completed=completed)


async def save(
    payload: OnboardingPayload, tenant_id: str, token: str
) -> OnboardingState:
    # Merge incremental: solo los campos enviados sobreescriben lo ya guardado,
    # para no perder respuestas previas del onboarding.
    current = await _run(repository.get_onboarding, tenant_id, token)
    incoming = payload.model_dump(exclude_unset=True)
    merged = {**(current or {}), **incoming}
    data = OnboardingPayload.model_validate(merged)

    saved = await _run(repository.save_onboarding, tenant_id, data.model_dump(), token)
    data = OnboardingPayload.model_validate(saved or data.model_dump())

    pct, completed = _measure(data.model_dump())
    return OnboardingState(data=data, completeness=pct, completed=completed)


# ---------------------------------------------------------------------------
# Onboarding conversacional (POST /onboarding/chat)
# ---------------------------------------------------------------------------


async def chat(
    payload: OnboardingChatRequest, tenant_id: str, token: str
) -> OnboardingChatResponse:
    """Un turno del onboarding conversacional. La IA extrae + redacta; el
    backend manda en el flujo y en la completitud."""
    raw = await _run(repository.get_onboarding, tenant_id, token)
    data = dict(raw or {})

    # Las actividades elegidas (chips) fijan el set por actividad.
    if payload.activities is not None:
        data["activities"] = payload.activities
    activities = data.get("activities") or []

    checklist = (
        await _run(repository.get_activity_checklist, activities, token)
        if activities
        else []
    )
    activity_keys = {row["field_key"] for row in checklist}

    extracted: dict[str, str] = {}
    ai_out: OnboardingExtraction | None = None

    # Solo llamamos a la IA si hay una respuesta del cliente que interpretar.
    if payload.message and payload.message.strip():
        prompt_row = await _run(repository.get_active_onboarding_prompt, token)
        if prompt_row is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No hay prompt activo para el módulo onboarding (config faltante).",
            )

        provider = get_ai_provider()
        pending_before = _pending_fields(data, checklist)
        chunks = await _rag(provider, activities, token)

        prompt = _assemble_prompt(
            template=prompt_row["content"],
            activities=activities,
            captured=data,
            last_answer=payload.message.strip(),
            pending=pending_before,
            chunks=chunks,
        )

        try:
            raw_ai = await provider.generate_json(prompt)
        except Exception as exc:  # noqa: BLE001 - upstream IA
            logger.exception("Fallo al invocar la IA en onboarding chat")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="La IA no devolvió una respuesta válida.",
            ) from exc

        try:
            ai_out = OnboardingExtraction.model_validate(raw_ai)
        except Exception as exc:  # noqa: BLE001 - Pydantic ValidationError
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"La IA devolvió un JSON que no cumple el schema: {exc}",
            ) from exc

        extracted = _sanitize_extracted(ai_out.extracted, activity_keys)
        _apply_extracted(data, extracted, activity_keys)

    # Persistir el estado ya fusionado.
    saved_payload = OnboardingPayload.model_validate(data)
    saved = await _run(
        repository.save_onboarding, tenant_id, saved_payload.model_dump(), token
    )
    saved_payload = OnboardingPayload.model_validate(saved or saved_payload.model_dump())
    data = saved_payload.model_dump()

    # Backend AUTORIDAD: recalcula pendientes y completitud sobre lo persistido.
    pending_after = _pending_fields(data, checklist)
    pct, completed = _measure_dynamic(data, checklist)

    next_field_row = pending_after[0] if pending_after else None
    next_question = _resolve_question(next_field_row, ai_out)
    next_field = (
        OnboardingField(
            field_key=next_field_row["field_key"], activity=next_field_row["activity"]
        )
        if next_field_row
        else None
    )

    return OnboardingChatResponse(
        next_question=next_question,
        next_field=next_field,
        extracted=extracted,
        data=saved_payload,
        completeness=pct,
        completed=completed,
    )


def _resolve_question(
    next_field: dict | None, ai_out: OnboardingExtraction | None
) -> str | None:
    """Redacción de la próxima pregunta. Se usa la de la IA SOLO si coincide con
    el campo que el backend eligió; si no, el fallback determinístico."""
    if next_field is None:
        return None
    if (
        ai_out is not None
        and ai_out.next_question
        and ai_out.next_field_key == next_field["field_key"]
    ):
        return ai_out.next_question
    return next_field["prompt"]


async def _rag(provider: object, activities: list[str], token: str) -> list[dict]:
    """RAG por actividad (best-effort). Si falla, seguimos SIN contexto —el
    onboarding no debe caerse por el RAG—, a diferencia de generation."""
    chunks: list[dict] = []
    seen: set[str] = set()
    try:
        for act in activities[:5]:
            query = (
                f"Requisitos de seguridad para {act} en turismo de aventura "
                f"según la NTC-ISO 21101"
            )
            embedding = await provider.embed(query)  # type: ignore[attr-defined]
            for chunk in await _run(repository.match_knowledge_chunks, embedding, None, token):
                if chunk["id"] not in seen:
                    seen.add(chunk["id"])
                    chunks.append(chunk)
    except Exception:  # noqa: BLE001 - RAG best-effort
        logger.warning("RAG onboarding no disponible; sigo sin contexto normativo", exc_info=True)
    return chunks


def _assemble_prompt(
    *,
    template: str,
    activities: list[str],
    captured: dict,
    last_answer: str,
    pending: list[dict],
    chunks: list[dict],
) -> str:
    """Rellena los marcadores ``<<...>>`` del prompt activo (mismo mecanismo que
    generation/quality: reemplazo de marcadores, no str.format)."""
    activities_str = ", ".join(activities) if activities else "(ninguna elegida)"
    captured_json = json.dumps(captured, ensure_ascii=False, indent=2)

    if pending:
        pending_lines = "\n".join(
            f"- {p['field_key']}"
            + (f" (actividad: {p['activity']})" if p["activity"] else " (universal)")
            + f": {p['prompt']}"
            for p in pending
        )
    else:
        pending_lines = "(no quedan campos pendientes)"

    if chunks:
        norm_context = "\n\n".join(
            f"[{c.get('source')} {c.get('numeral')}] {c.get('content')}" for c in chunks
        )
    else:
        norm_context = "(sin extractos de la norma disponibles)"

    json_schema = json.dumps(
        OnboardingExtraction.model_json_schema(), ensure_ascii=False, indent=2
    )

    return (
        template.replace("<<ACTIVITIES>>", activities_str)
        .replace("<<CAPTURED>>", captured_json)
        .replace("<<LAST_ANSWER>>", last_answer)
        .replace("<<PENDING_FIELDS>>", pending_lines)
        .replace("<<NORM_CONTEXT>>", norm_context)
        .replace("<<JSON_SCHEMA>>", json_schema)
    )
