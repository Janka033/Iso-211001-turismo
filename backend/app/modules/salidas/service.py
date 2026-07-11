"""Lógica de negocio de salidas y del registro público del turista.

Seguridad del flujo público: el turista llega con el token del QR. El service
calcula su sha256, busca la salida por hash y DERIVA tenant_id de esa fila.
Nada del body decide el tenant. El token en claro solo existe en la respuesta
de creación de la salida; en DB vive su hash.
"""

from __future__ import annotations

import functools
import hashlib
import secrets
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from typing import TypeVar

import anyio
from fastapi import HTTPException, status
from postgrest.exceptions import APIError

from app.modules.salidas import repository
from app.modules.salidas.schemas import (
    EventosSyncIn,
    EventosSyncOut,
    GuiaAssignIn,
    GuiaOut,
    ManifiestoOut,
    ParticipanteOut,
    RegistroTuristaIn,
    RegistroTuristaOut,
    SalidaCreate,
    SalidaCreatedOut,
    SalidaOut,
    SalidaStatusUpdate,
    SaludOut,
)

T = TypeVar("T")

# El registro sigue abierto un margen tras la hora programada: firmas de última
# hora en la base. Decisión de producto, ajustable.
_TOKEN_GRACE = timedelta(hours=24)

_ADULT_AGE = 18

# Valores de "sin alergias" que NO encienden la alerta médica del manifiesto.
_NO_ALLERGY = {"ninguna", "ninguno", "no", "n/a", "na", "no aplica"}

_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "programada": {"en_curso", "cancelada"},
    "en_curso": {"finalizada"},
}


async def _run(fn: Callable[..., T], *args: object) -> T:
    return await anyio.to_thread.run_sync(functools.partial(fn, *args))


def _map_db_error(exc: APIError) -> HTTPException:
    """Traduce errores de Postgres/RLS a HTTP con semántica clara."""
    msg = f"{exc.message or ''} {exc.details or ''}"
    if "SUBSCRIPTION_LOCKED" in msg:
        return HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Suscripción vencida: el tenant está en modo solo lectura.",
        )
    if "PLAN_LIMIT" in msg:
        return HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Límite del plan alcanzado. Actualiza el plan para continuar.",
        )
    if exc.code == "23505":
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="El registro ya existe."
        )
    if exc.code == "42501":
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Operación no permitida."
        )
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY, detail="Error de base de datos."
    )


def _to_salida_out(row: dict) -> SalidaOut:
    return SalidaOut(
        id=row["id"],
        activity_profile_id=row["activity_profile_id"],
        route_name=row.get("route_name"),
        scheduled_start=row["scheduled_start"],
        capacity=row["capacity"],
        status=row["status"],
        qr_token_expires_at=row["qr_token_expires_at"],
        started_at=row.get("started_at"),
        finished_at=row.get("finished_at"),
        created_at=row["created_at"],
    )


# ---------------------------------------------------------------------------
# Salidas (staff)
# ---------------------------------------------------------------------------


async def create_salida(
    payload: SalidaCreate, tenant_id: str, user_id: str, token: str
) -> SalidaCreatedOut:
    profile = await _run(
        repository.get_activity_profile, tenant_id, payload.activity_profile_id, token
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Actividad no encontrada."
        )
    if not profile["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La actividad está inactiva; actívala antes de programar salidas.",
        )

    public_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(public_token.encode()).hexdigest()
    expires_at = payload.scheduled_start + _TOKEN_GRACE

    data = {
        "activity_profile_id": payload.activity_profile_id,
        "route_name": payload.route_name,
        "scheduled_start": payload.scheduled_start.isoformat(),
        "capacity": payload.capacity,
        "qr_token_hash": token_hash,
        "qr_token_expires_at": expires_at.isoformat(),
        "created_by": user_id,
    }
    try:
        row = await _run(repository.insert_salida, tenant_id, data, token)
    except APIError as exc:
        raise _map_db_error(exc) from exc

    base = _to_salida_out(row)
    return SalidaCreatedOut(
        **base.model_dump(),
        public_token=public_token,
        public_registration_path=f"/registro/{public_token}",
    )


async def list_salidas(
    tenant_id: str, token: str, status_filter: str | None = None
) -> list[SalidaOut]:
    rows = await _run(repository.list_salidas, tenant_id, token, status_filter)
    return [_to_salida_out(r) for r in rows]


async def get_salida(salida_id: str, tenant_id: str, token: str) -> SalidaOut:
    row = await _run(repository.get_salida, tenant_id, salida_id, token)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Salida no encontrada."
        )
    return _to_salida_out(row)


async def update_status(
    salida_id: str, payload: SalidaStatusUpdate, tenant_id: str, token: str
) -> SalidaOut:
    row = await _run(repository.get_salida, tenant_id, salida_id, token)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Salida no encontrada."
        )
    allowed = _STATUS_TRANSITIONS.get(row["status"], set())
    if payload.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Transición inválida: {row['status']} → {payload.status}.",
        )
    changes: dict = {"status": payload.status}
    now = datetime.now(UTC).isoformat()
    if payload.status == "en_curso":
        changes["started_at"] = now
    elif payload.status == "finalizada":
        changes["finished_at"] = now

    try:
        updated = await _run(repository.update_salida, tenant_id, salida_id, changes, token)
    except APIError as exc:
        raise _map_db_error(exc) from exc
    if updated is None:
        # RLS filtró el UPDATE (rol sin permiso o suscripción vencida sin ser
        # el guía asignado): para el caller es un 403, no un 404.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Operación no permitida."
        )
    return _to_salida_out(updated)


# ---------------------------------------------------------------------------
# Guías de la salida
# ---------------------------------------------------------------------------


async def assign_guia(
    salida_id: str, payload: GuiaAssignIn, tenant_id: str, token: str
) -> GuiaOut:
    salida = await _run(repository.get_salida, tenant_id, salida_id, token)
    if salida is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Salida no encontrada."
        )
    profile = await _run(repository.get_profile_for_tenant, tenant_id, payload.guia_user_id)
    if profile is None or profile["role"] != "guia":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El usuario no existe en el tenant o no tiene rol de guía.",
        )
    try:
        row = await _run(
            repository.insert_guia,
            tenant_id,
            salida_id,
            payload.guia_user_id,
            payload.is_lead,
            token,
        )
    except APIError as exc:
        raise _map_db_error(exc) from exc
    return GuiaOut(guia_user_id=row["guia_user_id"], is_lead=row["is_lead"])


async def remove_guia(salida_id: str, guia_user_id: str, tenant_id: str, token: str) -> None:
    deleted = await _run(repository.delete_guia, tenant_id, salida_id, guia_user_id, token)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada."
        )


# ---------------------------------------------------------------------------
# Manifiesto de ruta
# ---------------------------------------------------------------------------


async def manifiesto(salida_id: str, tenant_id: str, token: str) -> ManifiestoOut:
    salida = await _run(repository.get_salida, tenant_id, salida_id, token)
    if salida is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Salida no encontrada."
        )
    parts = await _run(repository.list_participantes, tenant_id, salida_id, token)
    salud_rows = await _run(
        repository.list_salud, tenant_id, [p["id"] for p in parts], token
    )
    salud_by_id = {s["participante_id"]: s for s in salud_rows}

    participantes = []
    for p in parts:
        salud = salud_by_id.get(p["id"])
        participantes.append(
            ParticipanteOut(
                id=p["id"],
                full_name=p["full_name"],
                document_type=p["document_type"],
                document_number=p["document_number"],
                phone=p["phone"],
                status=p["status"],
                has_medical_alert=p["has_medical_alert"],
                guardian=p.get("guardian"),
                emergency_contacts=p["emergency_contacts"],
                salud=SaludOut(
                    eps=salud["eps"],
                    blood_type=salud["blood_type"],
                    allergies=salud["allergies"],
                    medical_conditions=salud["medical_conditions"],
                    current_medications=salud.get("current_medications"),
                    activity_specific=salud.get("activity_specific") or {},
                )
                if salud
                else None,
            )
        )
    return ManifiestoOut(salida=_to_salida_out(salida), participantes=participantes)


# ---------------------------------------------------------------------------
# Sync de eventos (app de guías, offline-first)
# ---------------------------------------------------------------------------


async def sync_eventos(
    salida_id: str, payload: EventosSyncIn, tenant_id: str, user_id: str, token: str
) -> EventosSyncOut:
    salida = await _run(repository.get_salida, tenant_id, salida_id, token)
    if salida is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Salida no encontrada."
        )
    # tenant, salida y autor los pone el SERVIDOR; del dispositivo solo llegan
    # el id idempotente, el tipo, la nota y la hora real en terreno.
    rows = [
        {
            "id": e.id,
            "tenant_id": tenant_id,
            "salida_id": salida_id,
            "participante_id": e.participante_id,
            "event_type": e.event_type,
            "note": e.note,
            "occurred_at": e.occurred_at.isoformat(),
            "recorded_by": user_id,
        }
        for e in payload.eventos
    ]
    try:
        inserted = await _run(repository.insert_eventos, rows, token)
    except APIError as exc:
        raise _map_db_error(exc) from exc
    return EventosSyncOut(received=len(rows), inserted=inserted)


# ---------------------------------------------------------------------------
# Registro público del turista
# ---------------------------------------------------------------------------


def _age_at(birth: date, when: date) -> int:
    return when.year - birth.year - ((when.month, when.day) < (birth.month, birth.day))


def _has_medical_alert(payload: RegistroTuristaIn) -> bool:
    allergy = payload.allergies.strip().lower()
    return bool(
        payload.medical_conditions.any_condition()
        or (allergy and allergy not in _NO_ALLERGY)
        or (payload.current_medications or "").strip()
    )


async def registro_publico(
    public_token: str, payload: RegistroTuristaIn
) -> RegistroTuristaOut:
    token_hash = hashlib.sha256(public_token.encode()).hexdigest()
    salida = await _run(repository.get_salida_by_token_hash, token_hash)
    if salida is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Enlace de registro inválido."
        )

    # El tenant se deriva de la salida encontrada por hash. Nunca del body.
    tenant_id = salida["tenant_id"]

    expires_at = datetime.fromisoformat(salida["qr_token_expires_at"])
    if salida["status"] != "programada" or datetime.now(UTC) >= expires_at:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="El registro para esta salida ya no está disponible.",
        )

    count = await _run(repository.count_participantes_public, salida["id"])
    if count >= salida["capacity"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La salida ya alcanzó su capacidad máxima.",
        )

    # Validaciones de la ficha técnica de la actividad (edad, condicionales).
    profile = await _run(
        repository.get_activity_profile_public, salida["activity_profile_id"]
    )
    scheduled = datetime.fromisoformat(salida["scheduled_start"]).date()
    age = _age_at(payload.birth_date, scheduled)
    if profile:
        min_age, max_age = profile.get("min_age"), profile.get("max_age")
        if (min_age is not None and age < min_age) or (
            max_age is not None and age > max_age
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"La actividad admite edades entre {min_age or 0} y "
                f"{max_age or 'sin límite'} años.",
            )
    if age < _ADULT_AGE and payload.guardian is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Los menores de edad requieren los datos del acudiente, "
            "quien firmará el consentimiento.",
        )

    participante = {
        "tenant_id": tenant_id,
        "salida_id": salida["id"],
        "document_type": payload.document_type,
        "document_number": payload.document_number,
        "full_name": payload.full_name,
        "birth_date": payload.birth_date.isoformat(),
        "nationality": payload.nationality,
        "phone": payload.phone,
        "email": payload.email,
        "guardian": payload.guardian.model_dump() if payload.guardian else None,
        "emergency_contacts": [c.model_dump() for c in payload.emergency_contacts],
        "has_medical_alert": _has_medical_alert(payload),
    }
    try:
        row = await _run(repository.insert_participante_public, participante)
    except APIError as exc:
        if exc.code == "23505":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este documento ya está registrado en la salida.",
            ) from exc
        raise _map_db_error(exc) from exc

    salud = {
        "participante_id": row["id"],
        "tenant_id": tenant_id,
        "eps": payload.eps,
        "blood_type": payload.blood_type,
        "allergies": payload.allergies,
        "medical_conditions": payload.medical_conditions.model_dump(),
        "current_medications": payload.current_medications,
        "activity_specific": payload.activity_specific,
        "declared_truthful_at": datetime.now(UTC).isoformat(),
    }
    try:
        await _run(repository.insert_salud_public, salud)
    except APIError as exc:
        # Sin transacción entre las dos escrituras: se compensa borrando la
        # identidad para no dejar un registro sin datos de salud.
        await _run(repository.delete_participante_public, row["id"])
        raise _map_db_error(exc) from exc

    return RegistroTuristaOut(
        participante_id=row["id"], salida_id=salida["id"], status=row["status"]
    )
