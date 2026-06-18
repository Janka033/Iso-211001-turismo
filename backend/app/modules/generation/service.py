"""Lógica de generación documental. Orquesta el flujo anti-alucinación:

    RAG → prompt (DB) → IA (AIProvider) → validación Pydantic → generador →
    snapshot de reproducibilidad.

Llama al repository para todo acceso a DB y a la IA SOLO vía ``AIProvider``.
La IA nunca redacta el documento: solo devuelve JSON estricto que se valida
antes de inyectarlo en una plantilla fija.
"""

from __future__ import annotations

import hashlib
import json

from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.core.ai.factory import get_ai_provider
from app.modules.generation import repository
from app.modules.generation.generators.factory import get_spec
from app.modules.generation.schemas import GeneratedDocument, GenerateRequest


async def generate(
    document_type: str,
    tenant_id: str,
    token: str,
    payload: GenerateRequest,
) -> GeneratedDocument:
    spec = get_spec(document_type)
    if spec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de documento no soportado: {document_type}",
        )

    prompt_row = repository.get_active_prompt(document_type, token)
    if prompt_row is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No hay prompt activo para {document_type} (config faltante).",
        )

    company = repository.get_company(tenant_id, token) or {}
    onboarding = repository.get_onboarding_data(tenant_id, token)
    checklist = repository.get_checklist(document_type, token)
    patterns = repository.get_generation_patterns(document_type, token)

    provider = get_ai_provider()

    # 1. RAG: recuperar el contexto normativo del numeral.
    query = (
        f"{spec.title} (numeral {spec.numeral}) NTC-ISO 21101 "
        f"para una empresa de turismo de aventura"
    )
    embedding = await provider.embed(query)
    chunks = repository.match_knowledge_chunks(embedding, spec.numeral, token)

    # 2. Ensamblar el prompt desde la versión activa (datos, no código).
    prompt = _assemble_prompt(
        template=prompt_row["content"],
        company=company,
        onboarding=onboarding,
        chunks=chunks,
        checklist=checklist,
        patterns=patterns,
        variables_model=spec.variables_model,
    )

    # 3. IA → JSON estricto.
    raw = await provider.generate_json(prompt)

    # 4. Validación Pydantic ANTES de tocar la plantilla.
    try:
        variables = spec.variables_model.model_validate(raw)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"La IA devolvió un JSON que no cumple el schema: {exc.errors()}",
        ) from exc

    # 5. Generar el documento (estructura fija; faltantes => [PENDIENTE]).
    result = spec.generator.generate(variables)

    # 6. Persistir: snapshot de reproducibilidad + estado.
    completeness = _completeness(checklist, result.pending_fields)
    version = repository.next_version(tenant_id, document_type, token)
    storage_path = repository.upload_document(
        tenant_id, document_type, version, result.content, token
    )

    settings = get_settings()
    record = {
        "tenant_id": tenant_id,
        "document_type": document_type,
        "storage_path": storage_path,
        "version": version,
        "prompt_hash": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "prompt_version": prompt_row["version"],
        "rag_chunks_ids": [c["id"] for c in chunks],
        "template_version": spec.generator.template_version,
        "model_version": settings.gemini_model,
        "variables_snapshot": variables.model_dump(),
    }
    document = repository.insert_document(record, token)

    repository.upsert_document_status(
        tenant_id, document_type, "generated", completeness, token
    )

    return GeneratedDocument(
        document_id=document["id"],
        document_type=document_type,
        version=version,
        status="generated",
        storage_path=storage_path,
        completeness=completeness,
        pending_fields=result.pending_fields,
        prompt_version=prompt_row["version"],
        template_version=spec.generator.template_version,
    )


# ---------------------------------------------------------------------------
# Helpers de ensamblado de prompt y métricas
# ---------------------------------------------------------------------------


def _assemble_prompt(
    *,
    template: str,
    company: dict,
    onboarding: dict,
    chunks: list[dict],
    checklist: list[dict],
    patterns: list[dict],
    variables_model: type[BaseModel],
) -> str:
    """Rellena los marcadores del prompt activo con el contexto dinámico.

    Usamos marcadores ``<<...>>`` (no str.format) para no chocar con las
    llaves del JSON del schema.
    """
    company_context = json.dumps(
        {"company": company, "onboarding_data": onboarding},
        ensure_ascii=False,
        indent=2,
    )

    if chunks:
        norm_context = "\n\n".join(
            f"[{c.get('source')} {c.get('numeral')}] {c.get('content')}" for c in chunks
        )
    else:
        norm_context = "(sin extractos de la norma disponibles)"

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

    json_schema = json.dumps(
        variables_model.model_json_schema(), ensure_ascii=False, indent=2
    )

    return (
        template.replace("<<COMPANY_CONTEXT>>", company_context)
        .replace("<<NORM_CONTEXT>>", norm_context)
        .replace("<<CHECKLIST>>", checklist_lines)
        .replace("<<PATTERNS>>", patterns_lines)
        .replace("<<JSON_SCHEMA>>", json_schema)
    )


def _completeness(checklist: list[dict], pending_fields: list[str]) -> float:
    """% de campos OBLIGATORIOS que quedaron con dato (0-100).

    Si no hay checklist, no podemos medir contra requisitos: devolvemos 0.0.
    """
    required = [c["field_key"] for c in checklist if c.get("required")]
    if not required:
        return 0.0
    pending = set(pending_fields)
    filled = [f for f in required if f not in pending]
    return round(len(filled) / len(required) * 100, 2)
