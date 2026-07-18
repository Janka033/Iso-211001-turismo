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
    CurrentStepInfo,
    OnboardingChatRequest,
    OnboardingChatResponse,
    OnboardingExtraction,
    OnboardingField,
    OnboardingPayload,
    OnboardingState,
    RoadmapResponse,
    RoadmapStep,
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
    ("staff_roles", "¿Qué cargos tiene su equipo y cuántas personas hay en cada uno?"),
    ("legal_representative", "¿Quién es el representante legal de la empresa?"),
    ("nit", "¿Cuál es el NIT de la empresa?"),
    ("rnt_status", "¿Su RNT está vigente, por renovar o aún no lo tienen?"),
    ("rnt_number", "¿Cuál es el número de RNT?"),
    ("emergency_contacts", "¿Qué contactos de emergencia tienen (bomberos, ambulancia, rescate)?"),
    # Bloque PL-01 (8.2). Fuente: cuestionario "Caracterización para el Plan de
    # Respuesta a Emergencias". Responden alertas reales de generation_patterns.
    (
        "brigada_emergencias",
        "¿Cuentan con brigada de emergencias? ¿Qué roles la integran y cómo se "
        "contacta a cada uno?",
    ),
    (
        "capacitaciones_personal_emergencias",
        "¿Qué capacitaciones en emergencias tiene el personal (primeros auxilios, "
        "evacuación y rescate, manejo de incendios, autorrescate u otras)?",
    ),
    (
        "equipos_emergencia",
        "¿Con qué equipos para emergencias cuentan (botiquín, camilla con "
        "inmovilizadores, sistema de comunicación —descríbanlo—, otros)?",
    ),
    (
        "organismos_apoyo",
        "¿Qué organismos de apoyo tienen identificados (Cruz Roja, Defensa Civil, "
        "bomberos) y en qué teléfonos los contactan?",
    ),
    (
        "hospital_cercano",
        "¿Cuál es el hospital o centro de salud más cercano (nombre, ubicación, "
        "distancia y tiempo de acceso)?",
    ),
    (
        "vehiculos_evacuacion",
        "¿Con qué vehículos contarían para una evacuación y quién es el encargado "
        "(tipo de vehículo y contacto)?",
    ),
    ("existing_controls", "¿Qué medidas o controles de seguridad ya aplican en su operación?"),
    ("management_commitment", "¿Cómo se compromete la dirección con la seguridad?"),
    # ------------------------------------------------------------------
    # Micro-preguntas de granularidad por documento (NTC-ISO 21101). Sin
    # ellas, la extracción no encuentra el dato y el documento sale con
    # [PENDIENTE]. Cada bloque alimenta las variables de su documento.
    # ------------------------------------------------------------------
    # Política de seguridad (5.2)
    (
        "safety_objectives",
        "Definan 3 objetivos de seguridad MEDIBLES: cada uno con indicador, meta "
        "numérica y plazo (p. ej. 'Reducir los incidentes reportados en 20% a "
        "diciembre de 2026'). Sepárenlos con punto y coma.",
    ),
    (
        "approval_date",
        "¿En qué fecha la gerencia aprobó (o aprobará) oficialmente la política "
        "de seguridad? (día/mes/año)",
    ),
    (
        "communication_channels",
        "¿Por qué canales divulgan la política y las normas de seguridad "
        "(cartelera, inducción, WhatsApp, página web, briefing pre-actividad)?",
    ),
    # Procedimiento de gestión de riesgos y oportunidades (6.1.1)
    (
        "risk_management_lead",
        "¿Qué cargo lidera la gestión de riesgos y oportunidades en su empresa "
        "(p. ej. el gerente), y con qué frecuencia le hacen seguimiento formal "
        "a los riesgos: semestral o anual?",
    ),
    # Matriz de riesgos y oportunidades (6.1.1)
    (
        "activity_step_breakdown",
        "Describan su actividad principal PASO A PASO (llegada, charla, "
        "equipamiento, desarrollo, cierre) y en cada paso indiquen el PELIGRO "
        "(la fuente: roca suelta, corriente, equipo defectuoso) y el RIESGO "
        "que genera (la consecuencia: golpe, ahogamiento, caída).",
    ),
    (
        "risk_factors",
        "¿Qué riesgos identifican por cada factor: ambientales (clima, terreno, "
        "crecientes), humanos (participantes, guías, terceros), de materiales/"
        "equipos, y organizativos (procedimientos, comunicación, supervisión)?",
    ),
    (
        "business_risks",
        "¿Qué riesgos del NEGOCIO y sus procesos identifican (cancelaciones por "
        "clima, reputación, dependencia de proveedores, temporada baja, permisos "
        "o requisitos legales)?",
    ),
    (
        "opportunities",
        "¿Qué oportunidades de mejora identifican y qué plan tienen para "
        "aprovecharlas (certificaciones, alianzas, capacitación, nuevos "
        "mercados)?",
    ),
    # Inspección y mantenimiento de equipos (8.1)
    (
        "equipment_maintenance",
        "Para CADA equipo que usan (balsas, remos, chalecos, cascos, cuerdas, "
        "arneses…): ¿con qué frecuencia lo inspeccionan, qué tipo de revisión "
        "hacen (visual o técnica) y cada cuánto le hacen mantenimiento?",
    ),
    # Comunicación, participación y consulta (7.4)
    (
        "communication_matrix",
        "¿Qué comunican sobre seguridad, A QUIÉN (guías, clientes, gerencia, "
        "organismos), por qué CANAL y con qué FRECUENCIA? Den varias filas "
        "(p. ej. 'briefing de seguridad — clientes — verbal — antes de cada "
        "salida').",
    ),
    (
        "participation_consultation",
        "¿Qué mecanismos formales tienen para que el personal participe y sea "
        "consultado en temas de seguridad (reuniones periódicas, comité, buzón "
        "de sugerencias, evaluación de simulacros)?",
    ),
    # Alcance del SGSTA (4.3) — completan el taller del kit MinCIT; los
    # servicios y ubicaciones del alcance ya se capturan en identidad.
    (
        "site_characteristics",
        "¿Qué características especiales tiene la zona donde operan (zona "
        "rural, reserva o área natural protegida, ribera de río, montaña)?",
    ),
    (
        "norm_exclusions",
        "¿Hay requisitos de la norma NTC-ISO 21101 que NO apliquen a su "
        "operación? Si es así, ¿cuáles y por qué? Si aplican todos, indíquenlo.",
    ),
    # Acta de compromiso de la alta dirección (5.1) — molde del kit MinCIT.
    (
        "management_signer",
        "Para el acta de compromiso de la dirección: ¿quién la firma (nombre y "
        "cargo), con qué teléfono y correo se le contacta, y en qué ciudad y "
        "fecha se firma (o firmará)?",
    ),
    # Matriz de partes interesadas (4.2) — taller del kit MinCIT.
    (
        "stakeholder_needs",
        "¿Quiénes son las partes interesadas de su operación y qué necesita y "
        "espera cada una de ustedes? Recorran: proveedores (incluidos los de "
        "actividades de aventura), organizaciones gubernamentales (Alcaldía, "
        "MinCIT, ARL), ONG, clientes/participantes, colaboradores, propietarios "
        "y la comunidad donde operan.",
    ),
    (
        "stakeholder_compliance",
        "¿Hoy cumplen lo que cada parte interesada les exige o espera? Si algo "
        "se cumple a medias o no se cumple, digan qué acción tienen prevista, "
        "quién es el responsable y para cuándo.",
    ),
    # Gestión de incidentes (8.3)
    (
        "incident_classification",
        "¿Cómo clasifican los eventos: qué consideran un INCIDENTE (casi ocurre, "
        "sin lesión) frente a un ACCIDENTE (con lesión o daño), y qué categorías "
        "de severidad usan (leve, grave, crítico)?",
    ),
    (
        "incident_report_fields",
        "Cuando ocurre un incidente, ¿qué datos registran en el reporte (fecha, "
        "lugar, actividad, personas involucradas, descripción, atención "
        "brindada, causa probable)?",
    ),
)

# Todos los campos universales que cuentan para la completitud (19: las 18
# preguntas + `activities`).
_UNIVERSAL_KEYS: tuple[str, ...] = ("activities",) + tuple(k for k, _ in _UNIVERSAL_QUESTIONS)

# Campos universales de tipo lista (para coercionar el valor extraído por la IA).
_LIST_FIELDS: frozenset[str] = frozenset(
    {
        "activities",
        "locations",
        "emergency_contacts",
        "capacitaciones_personal_emergencias",
        "equipos_emergencia",
        "organismos_apoyo",
        "safety_objectives",
        "communication_channels",
        "business_risks",
        "opportunities",
        "incident_classification",
        "incident_report_fields",
    }
)

# Orden de las categorías por actividad (Parte B) al preguntar. `edades` y
# `restricciones` son los dos campos del cuestionario "Información Técnica de
# Actividades" con required=true (responden alertas de auditor); el resto de
# esos campos es opcional y nunca entra al flujo de preguntas.
_ACTIVITY_CATEGORY_ORDER: tuple[str, ...] = (
    "equipo",
    "competencias",
    "emergencias",
    "riesgos",
    "seguimiento",
    "edades",
    "restricciones",
)

# Plantillas de pregunta por categoría (fallback cuando la IA no redacta, y como
# guía que se le pasa a la IA). {act} = actividad, {desc} = descripción del checklist.
_ACTIVITY_QUESTION_TEMPLATES: dict[str, str] = {
    "equipo": "Para {act}, ¿con qué equipo de seguridad cuentan? (ref.: {desc})",
    "competencias": "Para {act}, ¿qué certificaciones tienen sus guías? (ref.: {desc})",
    "emergencias": "Para {act}, ¿qué protocolos de emergencia tienen definidos? (ref.: {desc})",
    "riesgos": "Para {act}, ¿qué riesgos identifican y cómo los controlan? (ref.: {desc})",
    "seguimiento": "Para {act}, ¿qué seguimiento o registros llevan? (ref.: {desc})",
    "edades": "Para {act}, ¿cuál es la edad mínima y la máxima permitida para participar?",
    "restricciones": (
        "Para {act}, ¿qué restricciones de salud impiden participar "
        "(embarazo, cirugías recientes, etc.)?"
    ),
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

# ---------------------------------------------------------------------------
# Ruta guiada (Fase 2): agrupar las preguntas por el documento del paso activo.
# La RUTA (orden de pasos) es dato (document_roadmap, 0045); el mapeo pregunta→
# documento vive aquí junto a _UNIVERSAL_QUESTIONS, que también es código —
# varias preguntas del onboarding no existen en extraction_checklist y meterlas
# allí contaminaría los prompts de generación.
# ---------------------------------------------------------------------------

# Paso 0 — identidad de la empresa: se pregunta antes de cualquier documento.
_IDENTITY_KEYS: tuple[str, ...] = (
    "main_region",
    "locations",
    "scope",
    "certified_guides",
    "staff_roles",
    "legal_representative",
    "nit",
    "rnt_status",
    "rnt_number",
)
_IDENTITY_TITLE = "Conozcamos tu empresa"

# Preguntas universales que alimentan cada documento de la ruta.
_DOC_UNIVERSAL_KEYS: dict[str, tuple[str, ...]] = {
    "alcance_sgsta": ("site_characteristics", "norm_exclusions"),
    "matriz_partes_interesadas": ("stakeholder_needs", "stakeholder_compliance"),
    "acta_compromiso": ("management_signer",),
    "procedimiento_riesgos_oportunidades": ("risk_management_lead",),
    "politica_seguridad": (
        "management_commitment",
        "safety_objectives",
        "approval_date",
        "communication_channels",
    ),
    "matriz_riesgos": (
        "existing_controls",
        "activity_step_breakdown",
        "risk_factors",
        "business_risks",
        "opportunities",
    ),
    "plan_emergencias": (
        "emergency_contacts",
        "brigada_emergencias",
        "capacitaciones_personal_emergencias",
        "equipos_emergencia",
        "organismos_apoyo",
        "hospital_cercano",
        "vehiculos_evacuacion",
    ),
    "manual_inspeccion_equipos": ("equipment_maintenance",),
    "comunicacion_participacion_consulta": (
        "communication_matrix",
        "participation_consultation",
    ),
    "gestion_incidentes": ("incident_classification", "incident_report_fields"),
    "manual_perfiles_cargos": (),  # su insumo (staff_roles) es de identidad
    # Su insumo (safety_objectives + management_commitment) se captura en el
    # paso de la política: el paso de la matriz no pregunta nada propio.
    "matriz_objetivos_seguridad": (),
}

# Categoría de la Parte B → documento de la ruta que la consume.
_ACTIVITY_CAT_DOC: dict[str, str] = {
    "equipo": "manual_inspeccion_equipos",
    "competencias": "manual_perfiles_cargos",
    "emergencias": "plan_emergencias",
    "riesgos": "matriz_riesgos",
    "edades": "matriz_riesgos",
    "restricciones": "matriz_riesgos",
    "seguimiento": "gestion_incidentes",
}


def _doc_of_field(field: dict) -> str | None:
    """Documento de la ruta al que pertenece un pendiente (None = sin mapa)."""
    if field.get("activity"):
        return _ACTIVITY_CAT_DOC.get(_category_of(field["field_key"]))
    for doc, keys in _DOC_UNIVERSAL_KEYS.items():
        if field["field_key"] in keys:
            return doc
    return None


def _doc_field_universe(doc: str, data: dict, checklist: list[dict]) -> tuple[int, int]:
    """(respondidos, total) de los campos obligatorios que alimentan un doc."""
    activity_fields = data.get("activity_fields") or {}
    total = done = 0
    for key in _DOC_UNIVERSAL_KEYS.get(doc, ()):
        total += 1
        done += 1 if _has_value(data.get(key)) else 0
    for row in checklist:
        if not row.get("required", True):
            continue
        if _ACTIVITY_CAT_DOC.get(_category_of(row["field_key"])) == doc:
            total += 1
            done += 1 if activity_fields.get(row["field_key"]) else 0
    return done, total


def _route_view(
    pending: list[dict],
    route_steps: list[dict],
    statuses: dict[str, dict],
    data: dict,
    checklist: list[dict],
) -> tuple[list[dict], dict | None, list[str]]:
    """Reordena los pendientes por la ruta y calcula el paso activo.

    Devuelve (pendientes ordenados, info del paso activo o None, documentos
    listos para generar). Sin ruta configurada (lista vacía) el orden queda
    intacto: modo lineal de siempre.
    """
    if not route_steps:
        return pending, None, []

    identity = [f for f in pending if f["field_key"] in _IDENTITY_KEYS]
    by_doc: dict[str, list[dict]] = {}
    rest: list[dict] = []
    for field in pending:
        if field["field_key"] in _IDENTITY_KEYS:
            continue
        doc = _doc_of_field(field)
        if doc is None:
            rest.append(field)
        else:
            by_doc.setdefault(doc, []).append(field)

    ordered = list(identity)
    ready: list[str] = []
    for step in route_steps:
        doc = step["document_type"]
        doc_pending = by_doc.pop(doc, [])
        ordered.extend(doc_pending)
        if not doc_pending and statuses.get(doc) is None:
            ready.append(doc)
    for leftover in by_doc.values():  # docs fuera de la ruta habilitada
        ordered.extend(leftover)
    ordered.extend(rest)

    total_steps = len(route_steps)
    if not ordered:
        return ordered, None, ready

    first = ordered[0]
    if first["field_key"] in _IDENTITY_KEYS:
        done = sum(1 for k in _IDENTITY_KEYS if _has_value(data.get(k)))
        step_info = {
            "step_order": 0,
            "total": total_steps,
            "document_type": None,
            "title": _IDENTITY_TITLE,
            "numeral": None,
            "fields_done": done,
            "fields_total": len(_IDENTITY_KEYS),
        }
    else:
        doc = _doc_of_field(first)
        step_row = next((s for s in route_steps if s["document_type"] == doc), None)
        if step_row is None:
            return ordered, None, ready
        done, total = _doc_field_universe(doc, data, checklist)
        step_info = {
            "step_order": step_row["step_order"],
            "total": total_steps,
            "document_type": doc,
            "title": step_row["title"],
            "numeral": step_row.get("numeral"),
            "fields_done": done,
            "fields_total": total,
        }
    return ordered, step_info, ready


def _current_step_text(step_info: dict | None) -> str:
    """Texto del marcador <<CURRENT_STEP>> del prompt (v6)."""
    if step_info is None:
        return "(ruta guiada no configurada; flujo lineal)"
    if step_info["document_type"] is None:
        return (
            f"Paso 0 de {step_info['total']} — {step_info['title']}: datos "
            "generales de la empresa antes de entrar a los documentos "
            f"({step_info['fields_done']}/{step_info['fields_total']} respondidos)."
        )
    return (
        f"Paso {step_info['step_order']} de {step_info['total']} — "
        f"{step_info['title']} (numeral {step_info['numeral']}). Los campos "
        "pendientes de abajo alimentan ESTE documento "
        f"({step_info['fields_done']}/{step_info['fields_total']} respondidos)."
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


def _dedupe_checklist(checklist: list[dict]) -> list[dict]:
    """Una fila por ``field_key``. La tabla asocia el mismo campo a varios
    ``document_type``; para preguntar y medir avance el campo es uno solo.
    Si CUALQUIERA de las filas duplicadas es ``required``, el campo queda
    ``required``: un campo obligatorio para un documento no se vuelve opcional
    por el orden en que llegan las filas."""
    by_key: dict[str, dict] = {}
    unique: list[dict] = []
    for row in checklist:
        prev = by_key.get(row["field_key"])
        if prev is None:
            row = dict(row)
            by_key[row["field_key"]] = row
            unique.append(row)
        elif row.get("required", True) and not prev.get("required", True):
            prev["required"] = True
    return unique


def _pending_fields(data: dict, checklist: list[dict]) -> list[dict]:
    """Lista ORDENADA de campos OBLIGATORIOS aún sin dato: universales primero,
    luego por actividad (por orden de categoría). Los campos opcionales
    (required=false) NUNCA entran aquí: no alargan el camino obligatorio (ver
    ``_optional_unanswered``). Cada item: field_key, activity, prompt."""
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
        if not row.get("required", True):
            continue
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


def _optional_unanswered(data: dict, checklist: list[dict]) -> list[dict]:
    """Campos OPCIONALES (required=false) de la Parte B aún sin dato. No se
    preguntan nunca; se listan en el prompt para que la IA los extraiga si el
    cliente los menciona espontáneamente (y sumen completitud al darse)."""
    activity_fields = data.get("activity_fields") or {}
    return [
        {
            "field_key": row["field_key"],
            "activity": row.get("activity"),
            "description": row.get("description", ""),
        }
        for row in checklist
        if not row.get("required", True) and not activity_fields.get(row["field_key"])
    ]


def _measure(data: dict) -> tuple[float, bool]:
    """Avance LEGACY sobre los 5 campos clave fijos (contrato de GET/PUT)."""
    filled = [f for f in _KEY_FIELDS if _has_value(data.get(f))]
    pct = round(len(filled) / len(_KEY_FIELDS) * 100, 2)
    return pct, len(filled) == len(_KEY_FIELDS)


def _measure_dynamic(data: dict, checklist: list[dict]) -> tuple[float, bool]:
    """% de campos esperados con dato: 19 universales + los Parte B de las
    actividades elegidas. Es la completitud del onboarding conversacional.

    Los campos OPCIONALES (required=false) solo entran al cálculo si el
    cliente los dio: suman completitud al responderse, pero su ausencia no
    baja el % ni bloquea ``completed``."""
    total = len(_UNIVERSAL_KEYS)
    filled = sum(1 for k in _UNIVERSAL_KEYS if _has_value(data.get(k)))
    activity_fields = data.get("activity_fields") or {}
    for row in checklist:
        has_value = bool(activity_fields.get(row["field_key"]))
        if not row.get("required", True) and not has_value:
            continue
        total += 1
        if has_value:
            filled += 1
    pct = round(filled / total * 100, 2) if total else 0.0
    return pct, filled == total


def _sanitize_extracted(raw: dict[str, str], activity_keys: set[str]) -> dict[str, str]:
    """Deja solo lo que la IA puede tocar por texto: campos universales escalares
    o field_keys de las actividades elegidas. ``staff_roles`` NO va aquí: es un
    dict y se captura por su campo dedicado en OnboardingExtraction. Descarta
    claves inventadas/vacías."""
    allowed = (set(_UNIVERSAL_KEYS) - {"staff_roles"}) | activity_keys
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


def _clamp_for_field(key: str, value: str) -> str:
    """Recorta el texto crudo a los límites del schema del campo destino.

    Solo lo usa el fallback determinista (IA caída): el mensaje del chat admite
    hasta 8000 caracteres pero los campos escalares tienen su propio
    ``max_length``; capturar recortado es mejor que perder el turno con un 500.
    Para campos lista el límite del schema es de ÍTEMS y lo aplica ``_to_list``
    aguas abajo vía este mismo recorte de texto (no hace falta contar ítems:
    Pydantic valida longitud de lista tras el split, así que se recorta la
    lista aquí también).
    """
    field = OnboardingPayload.model_fields.get(key)
    if field is None:
        return value  # Parte B (activity_fields): dict[str, str] sin límite propio
    max_len = next(
        (m.max_length for m in field.metadata if getattr(m, "max_length", None)),
        None,
    )
    if max_len is None:
        return value
    if key in _LIST_FIELDS:
        # max_length en listas = nº máximo de ítems tras el split.
        items = _to_list(value)[:max_len]
        return "; ".join(items)
    return value[:max_len]


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
# Ruta guiada (GET /onboarding/roadmap) — Fase 1 del plan de la ruta
# ---------------------------------------------------------------------------


async def get_roadmap(tenant_id: str, token: str) -> RoadmapResponse:
    """La ruta de pasos (config en ``document_roadmap``) + estado del tenant.

    El estado se DERIVA en cada lectura de ``document_status`` (generación) y
    ``quality_reviews`` (score más reciente): la ruta nunca cachea progreso —
    la gamificación decora, la fuente de verdad sigue siendo el motor.
    """
    steps_rows = await _run(repository.get_roadmap, token)
    statuses = {
        row["document_type"]: row
        for row in await _run(repository.get_document_statuses, tenant_id, token)
    }
    scores: dict[str, float] = {}
    for row in await _run(repository.get_latest_review_scores, tenant_id, token):
        doc_type = (row.get("documents") or {}).get("document_type")
        if doc_type and doc_type not in scores and row.get("score") is not None:
            scores[doc_type] = float(row["score"])

    steps: list[RoadmapStep] = []
    current_step: int | None = None
    for row in steps_rows:
        doc_type = row["document_type"]
        status_row = statuses.get(doc_type)
        steps.append(
            RoadmapStep(
                step_order=row["step_order"],
                document_type=doc_type,
                title=row["title"],
                numeral=row["numeral"],
                generator_ready=row.get("generator_ready", False),
                status=(status_row or {}).get("status") or "pendiente",
                completeness=(status_row or {}).get("completeness"),
                last_score=scores.get(doc_type),
            )
        )
        if current_step is None and status_row is None:
            current_step = row["step_order"]
    return RoadmapResponse(steps=steps, current_step=current_step, total=len(steps))


# ---------------------------------------------------------------------------
# Subsanación (lo llama quality.service; datos crudos del cliente)
# ---------------------------------------------------------------------------


async def apply_remediation(
    answers: dict[str, str], tenant_id: str, token: str
) -> list[str]:
    """Merge de respuestas de subsanación en ``onboarding_data``.

    Mismas reglas de destino que el chat (``_apply_extracted``): campos
    universales arriba (con coerción a lista), field_key de actividad en
    ``activity_fields``, y el resto (field_key de variables de documento,
    p.ej. ``safety_objectives``) en ``remediation_fields``. Todo es dato CRUDO
    del cliente: la IA lo consumirá al regenerar, nunca se escribe en
    ``ai_outputs``. Devuelve los field_key efectivamente guardados.
    """
    clean = {
        k: v.strip()
        for k, v in answers.items()
        if isinstance(v, str) and v.strip()
    }
    if not clean:
        return []

    data = dict(await _run(repository.get_onboarding, tenant_id, token) or {})

    activities = [a for a in (data.get("activities") or []) if isinstance(a, str)]
    activity_rows = (
        await _run(repository.get_activity_checklist, activities, token)
        if activities
        else []
    )
    activity_keys = {row["field_key"] for row in activity_rows}

    for key, value in clean.items():
        if key in _LIST_FIELDS:
            data[key] = _to_list(value)
        elif key in _UNIVERSAL_KEYS and key != "staff_roles":
            # staff_roles es un dict (cargo -> nº); un texto libre no lo pisa.
            data[key] = value
        elif key in activity_keys:
            data.setdefault("activity_fields", {})[key] = value
        else:
            data.setdefault("remediation_fields", {})[key] = value

    payload = OnboardingPayload.model_validate(data)
    await _run(repository.save_onboarding, tenant_id, payload.model_dump(), token)
    return sorted(clean)


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
    # La Parte B repite field_key entre document_types (un mismo campo alimenta
    # varios documentos). Para el FLUJO y la completitud cuenta el campo ÚNICO:
    # sin dedupe el denominador se infla (21 filas vs 15 con 3 actividades) y
    # el prompt lista pendientes duplicados.
    checklist = _dedupe_checklist(checklist)
    activity_keys = {row["field_key"] for row in checklist}

    # Ruta guiada (0045): pasos con generador listo + estado de documentos del
    # tenant. Sin ruta sembrada, el chat se comporta lineal (como siempre).
    roadmap_rows = await _run(repository.get_roadmap, token)
    route_steps = [r for r in roadmap_rows if r.get("generator_ready")]
    statuses: dict[str, dict] = {}
    if route_steps:
        statuses = {
            row["document_type"]: row
            for row in await _run(repository.get_document_statuses, tenant_id, token)
        }

    extracted: dict[str, str] = {}
    ai_out: OnboardingExtraction | None = None
    rejected = False  # el interceptor de seguridad rechazó la respuesta
    ai_degraded = False  # la IA falló y el turno se capturó en modo determinista
    roles_changed = False  # el turno corrigió el organigrama (staff_roles)

    # Solo llamamos a la IA si hay una respuesta del cliente que interpretar.
    if payload.message and payload.message.strip():
        prompt_row = await _run(repository.get_active_onboarding_prompt, token)
        if prompt_row is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No hay prompt activo para el módulo onboarding (config faltante).",
            )

        provider = get_ai_provider()
        pending_before, step_before, _ = _route_view(
            _pending_fields(data, checklist), route_steps, statuses, data, checklist
        )
        optional_before = _optional_unanswered(data, checklist)
        chunks = await _rag(provider, activities, token)

        prompt = _assemble_prompt(
            template=prompt_row["content"],
            activities=activities,
            captured=data,
            last_answer=payload.message.strip(),
            pending=pending_before,
            optional=optional_before,
            chunks=chunks,
            current_step=_current_step_text(step_before),
        )

        try:
            # Extracción de campos: el thinking extendido solo agrega latencia
            # y costo (medido en el ensayo E2E); se desactiva.
            raw_ai = await provider.generate_json(prompt, thinking_budget=0)
            ai_out = OnboardingExtraction.model_validate(raw_ai)
        except Exception:  # noqa: BLE001 - upstream IA caída o JSON fuera de schema
            # RED DE SEGURIDAD determinista: la respuesta del cliente es dato
            # crudo y su casa es onboarding_data CON o SIN IA. Si el provider
            # falla (503 de Gemini, JSON roto), el turno NO se pierde: el texto
            # se asigna tal cual al campo en curso (las listas se parten por
            # coma/';'/salto de línea) y la siguiente pregunta sale de la
            # plantilla. Antes esto era un 502 y el cliente perdía lo escrito.
            logger.exception(
                "IA no disponible en onboarding chat; fallback determinista"
            )
            current = pending_before[0] if pending_before else None
            # staff_roles es un dict estructurado (cargo -> nº): texto libre lo
            # corrompería, así que ese campo se re-pregunta en vez de asignarse.
            if current is not None and current["field_key"] != "staff_roles":
                extracted = {
                    current["field_key"]: _clamp_for_field(
                        current["field_key"], payload.message.strip()
                    )
                }
                _apply_extracted(data, extracted, activity_keys)
                ai_degraded = True

        # INTERCEPTOR de seguridad: si la respuesta describe una práctica que
        # incumple un requisito obligatorio de la norma, este turno NO extrae ni
        # guarda nada del cliente (solo se conserva el estado ya persistido). El
        # turno se marca como rechazado y más abajo se re-pregunta el MISMO campo
        # con la explicación del requisito ISO.
        if ai_out is not None:
            rejected = not ai_out.compliant
            if not rejected:
                extracted = _sanitize_extracted(ai_out.extracted, activity_keys)
                _apply_extracted(data, extracted, activity_keys)

                # Organigrama: la IA lo devuelve estructurado (cargo -> nº) en su
                # propio campo; se fusiona con lo ya capturado. Alimenta MA-02.
                clean_roles = {
                    str(k).strip(): str(v).strip()
                    for k, v in ai_out.staff_roles.items()
                    if str(k).strip() and str(v).strip()
                }
                if clean_roles:
                    merged_roles = dict(data.get("staff_roles") or {})
                    merged_roles.update(clean_roles)
                    # Corrección de organigrama: un cargo devuelto con "0"
                    # significa "quítalo" (el merge por sí solo nunca borra).
                    data["staff_roles"] = {
                        k: v for k, v in merged_roles.items() if v != "0"
                    }
                    roles_changed = True

    # Persistir el estado ya fusionado.
    saved_payload = OnboardingPayload.model_validate(data)
    saved = await _run(
        repository.save_onboarding, tenant_id, saved_payload.model_dump(), token
    )
    saved_payload = OnboardingPayload.model_validate(saved or saved_payload.model_dump())
    data = saved_payload.model_dump()

    # Backend AUTORIDAD: recalcula pendientes y completitud sobre lo persistido.
    pending_after, step_after, ready_docs = _route_view(
        _pending_fields(data, checklist), route_steps, statuses, data, checklist
    )
    pct, completed = _measure_dynamic(data, checklist)
    current_step = CurrentStepInfo(**step_after) if step_after else None

    next_field_row = pending_after[0] if pending_after else None
    next_field = (
        OnboardingField(
            field_key=next_field_row["field_key"], activity=next_field_row["activity"]
        )
        if next_field_row
        else None
    )

    # Turno rechazado por el interceptor: se re-pregunta el MISMO campo (nada se
    # aplicó, así que ``next_field_row`` sigue siendo el pendiente en curso) y la
    # "pregunta" pasa a ser la explicación del requisito ISO + cómo replantear.
    if rejected and ai_out is not None:
        safety_note = _safety_message(ai_out)
        return OnboardingChatResponse(
            next_question=safety_note,
            next_field=next_field,
            extracted={},
            data=saved_payload,
            completeness=pct,
            completed=False,
            blocked=True,
            safety_note=safety_note,
            current_step=current_step,
            ready_to_generate=ready_docs,
        )

    next_question = _resolve_question(next_field_row, ai_out)
    # Onboarding ya completo pero el turno SÍ cambió datos (corrección tardía o
    # valor sospechoso): sin este acuse la respuesta salía vacía y el cliente no
    # sabía si su corrección se aplicó. Se usa la confirmación de la IA si la
    # dio; si no, un acuse determinista con los campos tocados.
    if next_question is None and (extracted or roles_changed):
        touched = sorted(extracted)
        if roles_changed:
            touched.append("staff_roles")
        next_question = (
            "Listo, quedó actualizado: " + ", ".join(touched) + ". "
            "Tu onboarding sigue completo; si necesitas corregir otro dato, "
            "escríbelo y lo ajusto."
        )
    # Turno capturado en modo determinista: se le dice al cliente con claridad
    # profesional que su respuesta quedó registrada tal cual (nada se perdió).
    if ai_degraded and extracted:
        ack = (
            "Registré tu respuesta tal como la escribiste (tuve un problema "
            "momentáneo para interpretarla con detalle; podrás revisarla al "
            "final)."
        )
        next_question = f"{ack} {next_question}" if next_question else ack
    return OnboardingChatResponse(
        next_question=next_question,
        next_field=next_field,
        extracted=extracted,
        data=saved_payload,
        completeness=pct,
        completed=completed,
        current_step=current_step,
        ready_to_generate=ready_docs,
    )


def _safety_message(ai_out: OnboardingExtraction) -> str:
    """Rechazo cortés y accionable: qué incumple + requisito ISO + cómo replantear.

    Todo sale del veredicto de la IA (que se apoya en la norma del RAG); si algún
    tramo falta, se omite sin romper el mensaje."""
    issue = (ai_out.safety_issue or "").strip()
    requirement = (ai_out.iso_requirement or "").strip()
    hint = (ai_out.rephrase_hint or "").strip()

    parts: list[str] = []
    if issue:
        parts.append(f"Esa respuesta no puedo registrarla tal cual: {issue}")
    else:
        parts.append(
            "Esa respuesta describe una práctica que no cumple la norma, así que "
            "no puedo registrarla tal cual."
        )
    if requirement:
        parts.append(f"La NTC-ISO 21101 exige: {requirement}")
    if hint:
        parts.append(f"¿Podrías replantearla así? {hint}")
    else:
        parts.append("¿Podrías replantear tu respuesta para que cumpla ese requisito?")
    return " ".join(parts)


def _resolve_question(
    next_field: dict | None, ai_out: OnboardingExtraction | None
) -> str | None:
    """Redacción de la próxima pregunta. Se usa la de la IA SOLO si coincide con
    el campo que el backend eligió; si no, el fallback determinístico. Sin campo
    pendiente, el texto de la IA (si lo dio) es la CONFIRMACIÓN de una
    corrección o de un valor sospechoso — no una pregunta— y sí se muestra."""
    if next_field is None:
        return ai_out.next_question if ai_out is not None else None
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
    optional: list[dict],
    chunks: list[dict],
    current_step: str = "(ruta guiada no configurada; flujo lineal)",
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

    if optional:
        optional_lines = "\n".join(
            f"- {o['field_key']}"
            + (f" (actividad: {o['activity']})" if o["activity"] else "")
            + f": {o['description']}"
            for o in optional
        )
    else:
        optional_lines = "(sin campos opcionales pendientes)"

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
        .replace("<<OPTIONAL_FIELDS>>", optional_lines)
        .replace("<<NORM_CONTEXT>>", norm_context)
        .replace("<<JSON_SCHEMA>>", json_schema)
        .replace("<<CURRENT_STEP>>", current_step)
    )
