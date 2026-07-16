"""Lógica de generación documental. Orquesta el flujo anti-alucinación:

    RAG → prompt (DB) → IA (AIProvider) → validación Pydantic → generador →
    snapshot de reproducibilidad.

Llama al repository para todo acceso a DB y a la IA SOLO vía ``AIProvider``.
La IA nunca redacta el documento: solo devuelve JSON estricto que se valida
antes de inyectarlo en una plantilla fija.

Las llamadas al repository (supabase-py es síncrono) se ejecutan en un hilo
(``anyio.to_thread``) para no bloquear el event loop.
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
from collections.abc import Callable
from typing import TypeVar

import anyio
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.core.ai.factory import get_ai_provider
from app.modules.generation import repository
from app.modules.generation.generators.factory import get_spec
from app.modules.generation.schemas import (
    DownloadResponse,
    GeneratedDocument,
    GenerateRequest,
)
from app.modules.inventory import service as inventory_service

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def _run(fn: Callable[..., T], *args: object, **kwargs: object) -> T:
    """Ejecuta una llamada bloqueante (repository) en un hilo."""
    return await anyio.to_thread.run_sync(functools.partial(fn, *args, **kwargs))


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

    prompt_row = await _run(repository.get_active_prompt, document_type, token)
    if prompt_row is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No hay prompt activo para {document_type} (config faltante).",
        )

    company = (await _run(repository.get_company, tenant_id, token)) or {}
    onboarding = await _run(repository.get_onboarding_data, tenant_id, token)
    checklist = await _run(repository.get_checklist, document_type, token)
    patterns = await _run(repository.get_generation_patterns, document_type, token)

    # Inventario operativo del tenant (trazabilidad → listas dinámicas).
    # Regla: un módulo no importa el repository de otro; se llama vía service.
    items = await inventory_service.list_items(tenant_id, token)
    inventory = _group_inventory(items)

    if not checklist:
        logger.warning(
            "Sin extraction_checklist para %s: no se puede medir completitud.",
            document_type,
        )

    provider = get_ai_provider()

    # 1. RAG: contexto normativo de TODOS los numerales del spec (p. ej. la
    #    matriz consulta 6.1.1 y el Anexo A) y de todos los sources (norma +
    #    evidencias de ACOTUR). Un solo embedding; una consulta por numeral.
    query = (
        f"{spec.title} (numeral {spec.numeral}) NTC-ISO 21101 "
        f"para una empresa de turismo de aventura"
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
        logger.exception("Fallo en el paso RAG para %s", document_type)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo recuperar el contexto normativo (RAG/IA no disponible).",
        ) from exc

    # 2. Ensamblar el prompt desde la versión activa (datos, no código).
    prompt = _assemble_prompt(
        template=prompt_row["content"],
        company=company,
        onboarding=onboarding,
        chunks=chunks,
        checklist=checklist,
        patterns=patterns,
        inventory=inventory,
        variables_model=spec.variables_model,
    )

    # 3. IA → JSON estricto.
    try:
        raw = await provider.generate_json(prompt)
    except Exception as exc:  # noqa: BLE001 - upstream IA
        logger.exception("Fallo al invocar la IA para %s", document_type)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="La IA no devolvió una respuesta válida.",
        ) from exc

    # 4. Validación Pydantic ANTES de tocar la plantilla.
    try:
        variables = spec.variables_model.model_validate(raw)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"La IA devolvió un JSON que no cumple el schema: {exc.errors()}",
        ) from exc

    # 5. Generar el documento (estructura fija; obligatorios faltantes => [PENDIENTE]).
    #    Qué es obligatorio lo dice la checklist (datos). Sin checklist => conservador.
    #    El código del documento (PO-01, MA-02, …) es DATO por tenant
    #    (onboarding_data.document_codes): sin código confirmado, el generador
    #    emite [PENDIENTE: código por confirmar] — nunca se adivina.
    required_fields = (
        {c["field_key"] for c in checklist if c.get("required")} if checklist else None
    )
    document_codes = (onboarding or {}).get("document_codes") or {}
    result = spec.generator.generate(
        variables, required_fields, document_code=document_codes.get(document_type)
    )

    # 6. Persistir: snapshot de reproducibilidad + estado.
    completeness = _completeness(
        checklist, result.pending_fields, set(spec.variables_model.model_fields)
    )
    version = await _run(repository.next_version, tenant_id, document_type, token)
    storage_path = await _run(
        repository.upload_document,
        tenant_id,
        document_type,
        version,
        result.content,
        token,
        engine=spec.generator.engine,
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
    document = await _run(repository.insert_document, record, token)

    await _run(
        repository.upsert_document_status,
        tenant_id,
        document_type,
        "generated",
        completeness,
        token,
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


async def rerender_from_snapshot(
    document_type: str, tenant_id: str, token: str
) -> GeneratedDocument:
    """Re-render DETERMINÍSTICO del último documento desde su variables_snapshot.

    Aplica la plantilla/builder ACTUAL a las variables ya extraídas y sube una
    VERSIÓN NUEVA sin llamar al provider de IA: separa la extracción (LLM, no
    determinística) del render (determinístico desde el snapshot). Los arreglos
    de formato, encabezado o código de documento se re-aplican por aquí — nunca
    regenerando, que re-tira los dados de la extracción.

    Snapshot de reproducibilidad: conserva la PROCEDENCIA de las variables
    (prompt_hash, prompt_version, rag_chunks_ids, model_version del registro
    origen); lo único que cambia es template_version (el render).
    """
    spec = get_spec(document_type)
    if spec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de documento no soportado: {document_type}",
        )

    source = await _run(
        repository.get_latest_document, tenant_id, document_type, token
    )
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay documento previo del cual re-renderizar.",
        )

    # Validación Pydantic del snapshot contra el modelo ACTUAL (los campos
    # nuevos opcionales toman su default; un snapshot incompatible es un error
    # explícito, nunca un documento silenciosamente distinto).
    try:
        variables = spec.variables_model.model_validate(
            source.get("variables_snapshot") or {}
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "El variables_snapshot no cumple el modelo actual: "
                f"{exc.errors()}"
            ),
        ) from exc

    onboarding = await _run(repository.get_onboarding_data, tenant_id, token)
    checklist = await _run(repository.get_checklist, document_type, token)
    required_fields = (
        {c["field_key"] for c in checklist if c.get("required")} if checklist else None
    )
    document_codes = (onboarding or {}).get("document_codes") or {}
    result = spec.generator.generate(
        variables, required_fields, document_code=document_codes.get(document_type)
    )

    completeness = _completeness(
        checklist, result.pending_fields, set(spec.variables_model.model_fields)
    )
    version = await _run(repository.next_version, tenant_id, document_type, token)
    storage_path = await _run(
        repository.upload_document,
        tenant_id,
        document_type,
        version,
        result.content,
        token,
        engine=spec.generator.engine,
    )

    record = {
        "tenant_id": tenant_id,
        "document_type": document_type,
        "storage_path": storage_path,
        "version": version,
        "prompt_hash": source.get("prompt_hash"),
        "prompt_version": source.get("prompt_version"),
        "rag_chunks_ids": source.get("rag_chunks_ids") or [],
        "template_version": spec.generator.template_version,
        "model_version": source.get("model_version"),
        "variables_snapshot": variables.model_dump(),
    }
    document = await _run(repository.insert_document, record, token)

    await _run(
        repository.upsert_document_status,
        tenant_id,
        document_type,
        "generated",
        completeness,
        token,
    )

    return GeneratedDocument(
        document_id=document["id"],
        document_type=document_type,
        version=version,
        status="generated",
        storage_path=storage_path,
        completeness=completeness,
        pending_fields=result.pending_fields,
        prompt_version=source.get("prompt_version") or "",
        template_version=spec.generator.template_version,
    )


async def download_url(
    document_type: str, version: int, tenant_id: str
) -> DownloadResponse:
    """URL firmada y temporal para descargar un documento del tenant.

    ``tenant_id`` sale del JWT, así que solo se firman documentos propios.
    """
    spec = get_spec(document_type)
    if spec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de documento no soportado: {document_type}",
        )
    url = await _run(
        repository.create_signed_url,
        tenant_id,
        document_type,
        version,
        spec.generator.engine,
    )
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El documento no está disponible para descargar.",
        )
    return DownloadResponse(url=url)


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
    inventory: dict[str, list[dict]],
    variables_model: type[BaseModel],
) -> str:
    """Rellena los marcadores del prompt activo con el contexto dinámico.

    Usamos marcadores ``<<...>>`` (no str.format) para no chocar con las
    llaves del JSON del schema.

    El ``inventario`` (operación real del tenant) se presenta como una sección
    PROMINENTE y legible al frente del contexto —no como JSON enterrado— y la
    precedencia sobre ``onboarding_data`` se aplica EN CÓDIGO: cuando hay ítems
    de inventario, esa es la fuente y el ``onboarding_data`` pasa a secundario.
    Así la IA no tiene que "decidir" la fuente (no lo hace de forma fiable);
    el sistema controla la estructura y la IA solo estructura el contenido.
    """
    inventory_block = _render_inventory(inventory)
    onboarding_for_prompt, onboarding_note = _apply_inventory_precedence(
        onboarding, inventory
    )
    remediation_block = _render_remediation(onboarding_for_prompt)

    company_json = json.dumps(
        {"company": company, "onboarding_data": onboarding_for_prompt},
        ensure_ascii=False,
        indent=2,
    )
    company_context = (
        f"{remediation_block}{inventory_block}\n\n{onboarding_note}{company_json}"
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


_CAT_LABELS = {
    "salida_emergencia": "Salidas / rutas de evacuación",
    "vehiculo": "Vehículos",
    "equipo": "Equipos",
    "actividad": "Actividades",
    "riesgo": "Riesgos identificados por el cliente",
    "contacto_emergencia": "Contactos de emergencia",
    "guia": "Guías",
    "otro": "Otros",
}


def _render_inventory(inventory: dict[str, list[dict]]) -> str:
    """Inventario como bloque legible y prominente (no JSON enterrado).

    La IA ignora datos sepultados en un JSON anidado; presentado como lista
    encabezada y obligatoria, sí los usa. Cada ítem muestra nombre + atributos.
    """
    if not inventory:
        return (
            "=== INVENTARIO OPERATIVO REAL ===\n"
            "(El cliente aún no ha registrado inventario operativo.)"
        )
    lines = [
        "=== INVENTARIO OPERATIVO REAL DEL CLIENTE "
        "(FUENTE PRINCIPAL Y OBLIGATORIA) ===",
        "Genera el documento a partir de ESTOS ítems reales. Inclúyelos TODOS, "
        "uno por uno. NO inventes ítems que no estén aquí.",
        "",
    ]
    for cat, items in inventory.items():
        lines.append(f"## {_CAT_LABELS.get(cat, cat)} ({len(items)}):")
        for it in items:
            attrs = it.get("attributes") or {}
            attr_str = "; ".join(
                f"{k}: {v}" for k, v in attrs.items() if v not in (None, "", [])
            )
            line = f"  - {it['name']}"
            if attr_str:
                line += f" ({attr_str})"
            lines.append(line)
        lines.append("")
    return "\n".join(lines).rstrip()


def _render_remediation(onboarding: dict) -> str:
    """Subsanaciones del cliente como bloque prominente al frente del contexto.

    ``onboarding_data.remediation_fields`` son respuestas del cliente a
    correcciones de calidad, indexadas por field_key de la checklist. Igual que
    el inventario: enterradas en el JSON la IA las ignora; como bloque
    encabezado y obligatorio, las usa. Devuelve "" si no hay subsanaciones.
    """
    remediation = onboarding.get("remediation_fields") or {}
    if not remediation:
        return ""
    lines = [
        "=== DATOS SUBSANADOS POR EL CLIENTE (MÁXIMA PRIORIDAD) ===",
        "El cliente aportó estos datos para corregir versiones anteriores del "
        "documento. ÚSALOS para los campos indicados; tienen precedencia sobre "
        "cualquier otro dato del contexto.",
        "",
    ]
    for key, value in remediation.items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    return "\n".join(lines) + "\n"


def _apply_inventory_precedence(
    onboarding: dict, inventory: dict[str, list[dict]]
) -> tuple[dict, str]:
    """Precedencia en CÓDIGO: si el inventario tiene actividades, se quitan las
    actividades del onboarding del contexto para que la IA no ancle en ellas.

    Devuelve (onboarding_para_prompt, nota_aclaratoria).
    """
    if not inventory.get("actividad"):
        return onboarding, ""
    filtered = {
        k: v
        for k, v in (onboarding or {}).items()
        if k not in ("activities", "actividades")
    }
    note = (
        "NOTA: el inventario operativo de arriba ya contiene las actividades "
        "reales del cliente; úsalo como fuente. Los datos de onboarding de abajo "
        "son SECUNDARIOS (contexto general de la empresa), no una lista de "
        "actividades para generar el documento.\n\n"
    )
    return filtered, note


def _group_inventory(items: list) -> dict[str, list[dict]]:
    """Agrupa los ítems del inventario por categoría → ``{cat: [{name, attributes}]}``.

    Solo se exponen ``name`` y ``attributes`` (lo operativo); IDs y metadatos no
    aportan a la generación. Las categorías vacías no aparecen.
    """
    grouped: dict[str, list[dict]] = {}
    for item in items:
        grouped.setdefault(item.category, []).append(
            {"name": item.name, "attributes": item.attributes}
        )
    return grouped


def _completeness(
    checklist: list[dict], pending_fields: list[str], model_fields: set[str]
) -> float:
    """% de campos OBLIGATORIOS que quedaron con dato (0-100).

    Solo cuentan los field_key que el generador puede resolver (campos del
    modelo de variables): la checklist puede ir por delante del modelo (p. ej.
    los campos de levantamiento de PL-01 aún sin variable/plantilla) y esos ni
    inflan el % como "llenos" ni castigan como pendientes.

    Si no hay checklist, no podemos medir contra requisitos: devolvemos 0.0.
    """
    required = [
        c["field_key"]
        for c in checklist
        if c.get("required") and c["field_key"] in model_fields
    ]
    if not required:
        return 0.0
    pending = set(pending_fields)
    filled = [f for f in required if f not in pending]
    return round(len(filled) / len(required) * 100, 2)
