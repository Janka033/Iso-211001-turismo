"""Lógica del módulo de calidad. Orquesta la evaluación anti-alucinación:

    documento (variables_snapshot) + checklist + patrones + RAG →
    prompt (DB) → IA (AIProvider) → validación Pydantic →
    quality_reviews (con snapshot de reproducibilidad).

La IA NO decide si un documento se aprueba: produce una evaluación
estructurada (completitud, coherencia con el numeral, alertas según los
patrones de auditoría reales) y la decisión queda en el revisor humano.

Se evalúa ``variables_snapshot`` —el contenido inteligente que se inyectó en
la plantilla—, no el .docx de Storage: la parte fija de la plantilla es
idéntica por diseño y re-parsearla solo agrega ruido y puntos de fallo.

Las llamadas al repository (supabase-py es síncrono) se ejecutan en un hilo
(``anyio.to_thread``) para no bloquear el event loop.
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TypeVar

import anyio
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.config import get_settings
from app.core.ai.factory import get_ai_provider
from app.core.security import CurrentUser

# El registry de documentos vive en generation (es configuración de dominio,
# no su repository): dice qué tipos existen, su título y su(s) numeral(es).
from app.modules.generation import service as generation_service
from app.modules.generation.generators.factory import get_spec
from app.modules.generation.schemas import GenerateRequest

# Un módulo nunca importa el repository de otro: la subsanación escribe los
# datos del cliente vía el SERVICE de onboarding y regenera vía el de generation.
from app.modules.onboarding import service as onboarding_service
from app.modules.quality import repository
from app.modules.quality.schemas import (
    QualityEvaluation,
    QualityReviewOut,
    RemediationOut,
    RemediationRequest,
    ReviewDecisionOut,
    ReviewDecisionRequest,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

# La decisión del revisor se refleja en document_status (estados de 0018).
_DECISION_TO_DOC_STATUS = {
    "approved": "approved",
    "rejected": "rejected",
    "needs_correction": "needs_correction",
}


async def _run(fn: Callable[..., T], *args: object, **kwargs: object) -> T:
    """Ejecuta una llamada bloqueante (repository) en un hilo."""
    return await anyio.to_thread.run_sync(functools.partial(fn, *args, **kwargs))


async def evaluate(document_id: str, tenant_id: str, token: str) -> QualityReviewOut:
    """Evalúa con la IA un documento generado y persiste el resultado."""
    document = await _run(repository.get_document, document_id, tenant_id, token)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado para este tenant.",
        )

    spec = get_spec(document["document_type"])
    if spec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de documento no soportado: {document['document_type']}",
        )

    prompt_row = await _run(repository.get_active_quality_prompt, token)
    if prompt_row is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No hay prompt activo para el módulo de calidad (config faltante).",
        )

    checklist = await _run(repository.get_checklist, document["document_type"], token)
    patterns = await _run(
        repository.get_generation_patterns, document["document_type"], token
    )

    provider = get_ai_provider()

    # RAG: contexto normativo de los numerales del documento, para juzgar la
    # coherencia contra la norma real (no contra lo que el modelo "recuerde").
    query = (
        f"Requisitos del numeral {spec.numeral} de la NTC-ISO 21101 para "
        f"{spec.title} de una empresa de turismo de aventura"
    )
    try:
        embedding = await provider.embed(query)
        chunks = []
        seen_ids: set[str] = set()
        for numeral in spec.rag_numerales:
            for chunk in await _run(
                repository.match_knowledge_chunks, embedding, numeral, token
            ):
                if chunk["id"] not in seen_ids:
                    seen_ids.add(chunk["id"])
                    chunks.append(chunk)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 - upstream IA/RAG
        logger.exception("Fallo en el paso RAG al evaluar %s", document_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo recuperar el contexto normativo (RAG/IA no disponible).",
        ) from exc

    prompt = _assemble_prompt(
        template=prompt_row["content"],
        spec_title=spec.title,
        numeral=spec.numeral,
        document_type=document["document_type"],
        document_version=document["version"],
        variables=document.get("variables_snapshot") or {},
        checklist=checklist,
        patterns=patterns,
        chunks=chunks,
    )

    # IA → JSON estricto. Timeout y reintentos viven en el provider/cliente;
    # aquí cualquier fallo upstream (timeout, rate limit, JSON roto) es 502.
    try:
        raw = await provider.generate_json(prompt)
    except Exception as exc:  # noqa: BLE001 - upstream IA
        logger.exception("Fallo al invocar la IA para evaluar %s", document_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="La IA no devolvió una respuesta válida.",
        ) from exc

    # Validación Pydantic ANTES de persistir.
    try:
        evaluation = QualityEvaluation.model_validate(raw)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"La IA devolvió un JSON que no cumple el schema: {exc.errors()}",
        ) from exc

    # Persistir con snapshot de reproducibilidad (regla de oro 6).
    settings = get_settings()
    record = {
        "tenant_id": tenant_id,
        "document_id": document_id,
        "score": evaluation.score,
        "evaluation": evaluation.model_dump(),
        "prompt_hash": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "prompt_version": prompt_row["version"],
        "model_version": settings.gemini_model,
    }
    review = await _run(repository.insert_review, record, token)

    return QualityReviewOut(
        review_id=review["id"],
        document_id=document_id,
        document_type=document["document_type"],
        document_version=document["version"],
        score=evaluation.score,
        evaluation=evaluation,
        review_status=review.get("review_status", "pending_review"),
        prompt_version=prompt_row["version"],
        model_version=settings.gemini_model,
        created_at=review.get("created_at"),
    )


async def decide(
    review_id: str,
    payload: ReviewDecisionRequest,
    tenant_id: str,
    user: CurrentUser,
) -> ReviewDecisionOut:
    """Aplica la decisión del revisor y la refleja en document_status."""
    review = await _run(repository.get_review, review_id, tenant_id, user.token)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluación no encontrada para este tenant.",
        )

    fields = {
        "review_status": payload.decision,
        "reviewed_by": user.user_id,
        "review_notes": payload.notes,
        "reviewed_at": datetime.now(UTC).isoformat(),
    }
    updated = await _run(
        repository.update_review_decision, review_id, tenant_id, fields, user.token
    )
    if updated is None:
        # El endpoint ya exige admin/superadmin; si aun así RLS filtró la fila
        # (policy de UPDATE con rol revisor), no hay nada que decidir.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para decidir sobre esta evaluación.",
        )

    document_status = _DECISION_TO_DOC_STATUS[payload.decision]
    embedded = review.get("documents") or {}
    document_type = embedded.get("document_type", "")
    if document_type:
        await _run(
            repository.set_document_status,
            tenant_id,
            document_type,
            document_status,
            user.token,
        )

    return ReviewDecisionOut(
        review_id=review_id,
        review_status=payload.decision,
        document_id=review["document_id"],
        document_type=document_type,
        document_status=document_status,
    )


# Estados de revisión sobre los que tiene sentido subsanar: el revisor pidió
# corrección o rechazó. (pending_review aún no tiene veredicto; approved no
# necesita subsanación.)
_REMEDIABLE_STATUSES = frozenset({"needs_correction", "rejected"})


async def remediate(
    review_id: str,
    payload: RemediationRequest,
    tenant_id: str,
    user: CurrentUser,
) -> RemediationOut:
    """Subsanación de la empresa: guarda los datos que respondan a la
    corrección (en ``onboarding_data``, vía onboarding.service) y regenera el
    documento (versión nueva con su snapshot, vía generation.service).

    La evaluación y la decisión originales NO se tocan: son rastro de auditoría
    de la versión anterior. La versión nueva nace sin evaluar.
    """
    review = await _run(repository.get_review, review_id, tenant_id, user.token)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluación no encontrada para este tenant.",
        )

    review_status = review.get("review_status")
    if review_status not in _REMEDIABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Solo se puede subsanar una evaluación con corrección solicitada "
                f"o rechazada (estado actual: {review_status})."
            ),
        )

    embedded = review.get("documents") or {}
    document_type = embedded.get("document_type", "")
    if not document_type or get_spec(document_type) is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La evaluación no está ligada a un tipo de documento válido.",
        )

    # Universo de claves admitidas: lo que marcó la evaluación + la checklist
    # del documento. Nada fuera de eso entra a onboarding_data.
    evaluation = review.get("evaluation") or {}
    completeness = evaluation.get("completeness") or {}
    allowed: set[str] = {
        *(completeness.get("missing_required_fields") or []),
        *(completeness.get("missing_optional_fields") or []),
        *(
            c.get("field")
            for c in (evaluation.get("suggested_corrections") or [])
            if c.get("field")
        ),
    }
    checklist = await _run(repository.get_checklist, document_type, user.token)
    allowed.update(c["field_key"] for c in checklist)

    unknown = sorted(set(payload.answers) - allowed)
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "field_key fuera de la corrección y de la checklist del "
                f"documento: {', '.join(unknown)}"
            ),
        )

    try:
        saved_fields = await onboarding_service.apply_remediation(
            payload.answers, tenant_id, user.token
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Datos de subsanación inválidos: {exc.errors()}",
        ) from exc
    if not saved_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ninguna respuesta traía dato (todas vacías).",
        )

    document = None
    if payload.regenerate:
        document = await generation_service.generate(
            document_type,
            tenant_id,
            user.token,
            GenerateRequest(regenerate=True),
        )

    return RemediationOut(
        review_id=review_id,
        document_type=document_type,
        saved_fields=saved_fields,
        regenerated=document is not None,
        document=document,
    )


# ---------------------------------------------------------------------------
# Helper de ensamblado de prompt
# ---------------------------------------------------------------------------


def _assemble_prompt(
    *,
    template: str,
    spec_title: str,
    numeral: str,
    document_type: str,
    document_version: int,
    variables: dict,
    checklist: list[dict],
    patterns: list[dict],
    chunks: list[dict],
) -> str:
    """Rellena los marcadores ``<<...>>`` del prompt activo con el contexto real.

    Mismo mecanismo que generation: marcadores (no str.format) para no chocar
    con las llaves del JSON del schema y del contenido.
    """
    variables_json = json.dumps(variables, ensure_ascii=False, indent=2)

    if checklist:
        checklist_lines = "\n".join(
            f"- {c['field_key']}: {c.get('description', '')} "
            f"({'obligatorio' if c.get('required') else 'opcional'})"
            for c in checklist
        )
    else:
        checklist_lines = "(sin checklist)"

    if patterns:
        patterns_lines = "\n".join(
            f"- ({p['pattern_type']}) {p['description']}" for p in patterns
        )
    else:
        patterns_lines = "(sin patrones registrados)"

    if chunks:
        norm_context = "\n\n".join(
            f"[{c.get('source')} {c.get('numeral')}] {c.get('content')}" for c in chunks
        )
    else:
        norm_context = "(sin extractos de la norma disponibles)"

    json_schema = json.dumps(
        QualityEvaluation.model_json_schema(), ensure_ascii=False, indent=2
    )

    return (
        template.replace("<<DOCUMENT_TITLE>>", spec_title)
        .replace("<<NUMERAL>>", numeral)
        .replace("<<DOCUMENT_TYPE>>", document_type)
        .replace("<<DOCUMENT_VERSION>>", str(document_version))
        .replace("<<DOCUMENT_VARIABLES>>", variables_json)
        .replace("<<CHECKLIST>>", checklist_lines)
        .replace("<<PATTERNS>>", patterns_lines)
        .replace("<<NORM_CONTEXT>>", norm_context)
        .replace("<<JSON_SCHEMA>>", json_schema)
    )
