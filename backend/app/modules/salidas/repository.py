"""Único punto que habla con Supabase en el módulo salidas.

Dos familias de funciones:

- Staff autenticado → USER client (RLS por tenant + rol). ``tenant_id``
  siempre explícito.
- Flujo público del turista → SERVICE client (salta RLS): el turista no es
  usuario del tenant. El service DERIVA el tenant del token de la salida y
  estas funciones lo reciben ya resuelto; ninguna acepta datos del body como
  fuente del tenant.
"""

from __future__ import annotations

from app.core.supabase import get_service_client, get_user_client

_SALIDA_COLS = (
    "id, activity_profile_id, route_name, scheduled_start, capacity, status, "
    "qr_token_expires_at, started_at, finished_at, created_at"
)
_PARTICIPANTE_COLS = (
    "id, full_name, document_type, document_number, phone, status, "
    "has_medical_alert, guardian, emergency_contacts"
)
_SALUD_COLS = (
    "participante_id, eps, arl, blood_type, allergies, medical_conditions, "
    "current_medications, activity_specific"
)
_CHECK_COLS = (
    "id, item_id, phase, status, quantity, note, evidence_paths, "
    "checked_by, checked_at"
)
_INCIDENT_COLS = (
    "id, salida_id, activity_type, occurred_at, location, status, "
    "lead_guide_name, lead_guide_phone, other_staff, involved_participants, "
    "witnesses, environmental_conditions, equipment_state, circumstances, "
    "probable_causes, emergency_response, consequences, action_plan, "
    "info_source, risk_was_identified, investigators, observations, "
    "evidence_paths, reported_by, created_at, updated_at"
)


# ---------------------------------------------------------------------------
# Staff autenticado (user client => RLS)
# ---------------------------------------------------------------------------


def get_activity_profile(tenant_id: str, activity_profile_id: str, token: str) -> dict | None:
    client = get_user_client(token)
    res = (
        client.table("activity_profiles")
        .select("id, name, is_active, min_age, max_age")
        .eq("tenant_id", tenant_id)
        .eq("id", activity_profile_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def insert_salida(tenant_id: str, data: dict, token: str) -> dict:
    client = get_user_client(token)
    return (
        client.table("salidas")
        .insert({"tenant_id": tenant_id, **data})
        .execute()
        .data[0]
    )


def list_salidas(tenant_id: str, token: str, status: str | None = None) -> list[dict]:
    client = get_user_client(token)
    query = client.table("salidas").select(_SALIDA_COLS).eq("tenant_id", tenant_id)
    if status:
        query = query.eq("status", status)
    return query.order("scheduled_start", desc=True).execute().data or []


def get_salida(tenant_id: str, salida_id: str, token: str) -> dict | None:
    client = get_user_client(token)
    res = (
        client.table("salidas")
        .select(_SALIDA_COLS)
        .eq("tenant_id", tenant_id)
        .eq("id", salida_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def update_salida(tenant_id: str, salida_id: str, changes: dict, token: str) -> dict | None:
    client = get_user_client(token)
    res = (
        client.table("salidas")
        .update(changes)
        .eq("tenant_id", tenant_id)
        .eq("id", salida_id)
        .execute()
    )
    return res.data[0] if res.data else None


def insert_guia(
    tenant_id: str, salida_id: str, guia_user_id: str, is_lead: bool, token: str
) -> dict:
    client = get_user_client(token)
    return (
        client.table("salida_guias")
        .insert(
            {
                "tenant_id": tenant_id,
                "salida_id": salida_id,
                "guia_user_id": guia_user_id,
                "is_lead": is_lead,
            }
        )
        .execute()
        .data[0]
    )


def delete_guia(tenant_id: str, salida_id: str, guia_user_id: str, token: str) -> bool:
    client = get_user_client(token)
    res = (
        client.table("salida_guias")
        .delete()
        .eq("tenant_id", tenant_id)
        .eq("salida_id", salida_id)
        .eq("guia_user_id", guia_user_id)
        .execute()
    )
    return bool(res.data)


def list_guias(tenant_id: str, salida_id: str, token: str) -> list[dict]:
    client = get_user_client(token)
    return (
        client.table("salida_guias")
        .select("guia_user_id, is_lead")
        .eq("tenant_id", tenant_id)
        .eq("salida_id", salida_id)
        .execute()
        .data
        or []
    )


def list_participantes(tenant_id: str, salida_id: str, token: str) -> list[dict]:
    client = get_user_client(token)
    return (
        client.table("participantes")
        .select(_PARTICIPANTE_COLS)
        .eq("tenant_id", tenant_id)
        .eq("salida_id", salida_id)
        .order("full_name")
        .execute()
        .data
        or []
    )


def list_salud(tenant_id: str, participante_ids: list[str], token: str) -> list[dict]:
    """Detalle de salud de los participantes. RLS decide cuánto vuelve:
    gerente/coordinador todo, guía solo sus salidas, recepcionista nada."""
    if not participante_ids:
        return []
    client = get_user_client(token)
    return (
        client.table("participante_salud")
        .select(_SALUD_COLS)
        .eq("tenant_id", tenant_id)
        .in_("participante_id", participante_ids)
        .execute()
        .data
        or []
    )


def insert_equipment_checks(rows: list[dict], token: str) -> int:
    """Sync append-only de revisiones de equipos: upsert que IGNORA
    duplicados (id del dispositivo => reintentos idempotentes). Devuelve
    cuántas revisiones eran nuevas."""
    client = get_user_client(token)
    res = (
        client.table("equipment_checks")
        .upsert(rows, on_conflict="id", ignore_duplicates=True)
        .execute()
    )
    return len(res.data or [])


def list_equipment_checks(
    tenant_id: str, salida_id: str, token: str, phase: str | None = None
) -> list[dict]:
    client = get_user_client(token)
    query = (
        client.table("equipment_checks")
        .select(_CHECK_COLS)
        .eq("tenant_id", tenant_id)
        .eq("salida_id", salida_id)
    )
    if phase:
        query = query.eq("phase", phase)
    return query.order("checked_at").execute().data or []


def list_general_equipment_checks(
    tenant_id: str, token: str, desde: str | None = None, hasta: str | None = None
) -> list[dict]:
    """Revisiones matinales generales (sin salida), acotables por rango."""
    client = get_user_client(token)
    query = (
        client.table("equipment_checks")
        .select(_CHECK_COLS)
        .eq("tenant_id", tenant_id)
        .is_("salida_id", "null")
    )
    if desde:
        query = query.gte("checked_at", desde)
    if hasta:
        query = query.lte("checked_at", hasta)
    return query.order("checked_at").execute().data or []


def insert_incident(tenant_id: str, data: dict, token: str) -> dict:
    client = get_user_client(token)
    return (
        client.table("incident_reports")
        .insert({"tenant_id": tenant_id, **data})
        .execute()
        .data[0]
    )


def get_incident(tenant_id: str, incident_id: str, token: str) -> dict | None:
    client = get_user_client(token)
    res = (
        client.table("incident_reports")
        .select(_INCIDENT_COLS)
        .eq("tenant_id", tenant_id)
        .eq("id", incident_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def list_incidents(
    tenant_id: str, token: str, status: str | None = None
) -> list[dict]:
    client = get_user_client(token)
    query = (
        client.table("incident_reports").select(_INCIDENT_COLS).eq("tenant_id", tenant_id)
    )
    if status:
        query = query.eq("status", status)
    return query.order("occurred_at", desc=True).execute().data or []


def update_incident(
    tenant_id: str, incident_id: str, changes: dict, token: str
) -> dict | None:
    client = get_user_client(token)
    res = (
        client.table("incident_reports")
        .update(changes)
        .eq("tenant_id", tenant_id)
        .eq("id", incident_id)
        .execute()
    )
    return res.data[0] if res.data else None


def insert_eventos(rows: list[dict], token: str) -> int:
    """Sync append-only de la app de guías: upsert que IGNORA duplicados
    (el id lo genera el dispositivo => reintentos idempotentes). Devuelve
    cuántos eventos eran nuevos."""
    client = get_user_client(token)
    res = (
        client.table("salida_eventos")
        .upsert(rows, on_conflict="id", ignore_duplicates=True)
        .execute()
    )
    return len(res.data or [])


# ---------------------------------------------------------------------------
# Perfil del guía a asignar: user_profiles solo expone la fila propia vía RLS
# (policy own_profile), así que la verificación de rol usa el service client
# como lectura puntual, SIEMPRE filtrada por el tenant del JWT.
# ---------------------------------------------------------------------------


def get_profile_for_tenant(tenant_id: str, user_id: str) -> dict | None:
    client = get_service_client()
    res = (
        client.table("user_profiles")
        .select("user_id, role")
        .eq("tenant_id", tenant_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


# ---------------------------------------------------------------------------
# Flujo público del turista (service client; el tenant sale del token del QR)
# ---------------------------------------------------------------------------


def get_salida_by_token_hash(token_hash: str) -> dict | None:
    client = get_service_client()
    res = (
        client.table("salidas")
        .select(
            "id, tenant_id, activity_profile_id, scheduled_start, capacity, "
            "status, qr_token_expires_at"
        )
        .eq("qr_token_hash", token_hash)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def get_activity_profile_public(activity_profile_id: str) -> dict | None:
    client = get_service_client()
    res = (
        client.table("activity_profiles")
        .select("id, name, min_age, max_age, participant_form_fields")
        .eq("id", activity_profile_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def count_participantes_public(salida_id: str) -> int:
    client = get_service_client()
    res = (
        client.table("participantes")
        .select("id", count="exact")
        .eq("salida_id", salida_id)
        .execute()
    )
    return res.count or 0


def insert_participante_public(data: dict) -> dict:
    client = get_service_client()
    return client.table("participantes").insert(data).execute().data[0]


def insert_salud_public(data: dict) -> dict:
    client = get_service_client()
    return client.table("participante_salud").insert(data).execute().data[0]


def delete_participante_public(participante_id: str) -> None:
    """Compensación: si la fila de salud falla, el registro queda incompleto y
    se revierte (PostgREST no da transacciones entre las dos escrituras)."""
    client = get_service_client()
    client.table("participantes").delete().eq("id", participante_id).execute()
