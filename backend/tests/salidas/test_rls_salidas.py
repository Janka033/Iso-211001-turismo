"""Aislamiento RLS de la operación de terreno (NO negociable).

Con el JWT del tenant B no se leen salidas ni datos de salud del tenant A, y
un rol sin permiso no crea salidas. Requiere Supabase local con las
migraciones (incluida 0031) y el hook de claims activo.

    supabase start
    RUN_DB_TESTS=1 pytest tests/salidas/test_rls_salidas.py
"""

from __future__ import annotations

import hashlib
import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="Integración con DB: define RUN_DB_TESTS=1 y un Supabase local con las migraciones.",
)


def _signin_token(email: str, password: str) -> str:
    from supabase import create_client

    from app.config import get_settings

    settings = get_settings()
    anon = create_client(settings.supabase_url, settings.supabase_anon_key)
    session = anon.auth.sign_in_with_password({"email": email, "password": password})
    return session.session.access_token


async def test_salidas_y_salud_aisladas_por_tenant():
    from postgrest.exceptions import APIError

    from app.core.supabase import get_service_client, get_user_client
    from app.modules.auth.repository import provision
    from app.modules.auth.schemas import SignupRequest

    suffix = uuid.uuid4().hex[:8]
    pwd = "passw0rd-test"

    a = await provision(
        SignupRequest(
            email=f"sa-{suffix}@test.co", password=pwd, company_name=f"Salidas A {suffix}"
        )
    )
    await provision(
        SignupRequest(
            email=f"sb-{suffix}@test.co", password=pwd, company_name=f"Salidas B {suffix}"
        )
    )

    client_a = get_user_client(_signin_token(f"sa-{suffix}@test.co", pwd))
    client_b = get_user_client(_signin_token(f"sb-{suffix}@test.co", pwd))
    service = get_service_client()

    user_a = service.table("user_profiles").select("user_id").eq(
        "tenant_id", a.tenant_id
    ).execute().data[0]["user_id"]

    # A (rol legado 'empresa' => gerente vía current_user_role) crea actividad
    # y salida. De paso prueba que el tenant nuevo en trial es escribible.
    activity = (
        client_a.table("activity_profiles")
        .insert(
            {"tenant_id": a.tenant_id, "name": f"ATV {suffix}", "activity_type": "atv"}
        )
        .execute()
        .data[0]
    )
    start = datetime.now(UTC) + timedelta(days=1)
    salida = (
        client_a.table("salidas")
        .insert(
            {
                "tenant_id": a.tenant_id,
                "activity_profile_id": activity["id"],
                "scheduled_start": start.isoformat(),
                "capacity": 5,
                "qr_token_hash": hashlib.sha256(uuid.uuid4().bytes).hexdigest(),
                "qr_token_expires_at": (start + timedelta(hours=24)).isoformat(),
                "created_by": user_a,
            }
        )
        .execute()
        .data[0]
    )

    # B no ve nada de A, ni siquiera pidiendo el id explícito.
    assert client_b.table("salidas").select("id").execute().data == []
    leak = client_b.table("salidas").select("id").eq("id", salida["id"]).execute()
    assert leak.data == [], "RLS roto: B pudo leer una salida de A"

    # Turista de A (vía service, como hace el endpoint público).
    participante = (
        service.table("participantes")
        .insert(
            {
                "tenant_id": a.tenant_id,
                "salida_id": salida["id"],
                "document_type": "CC",
                "document_number": f"10{suffix}",
                "full_name": "Turista RLS",
                "birth_date": "1990-01-01",
                "phone": "3000000000",
                "email": "t@rls.co",
                "emergency_contacts": [
                    {"nombre": "C", "parentesco": "Madre", "telefono": "3000000001"}
                ],
                "has_medical_alert": True,
            }
        )
        .execute()
        .data[0]
    )
    service.table("participante_salud").insert(
        {
            "participante_id": participante["id"],
            "tenant_id": a.tenant_id,
            "eps": "Sura",
            "blood_type": "O+",
            "allergies": "Abejas",
            "medical_conditions": {"respiratoria": True},
            "declared_truthful_at": datetime.now(UTC).isoformat(),
        }
    ).execute()

    # A (gerente) lee la salud de su participante; B no lee NADA.
    salud_a = client_a.table("participante_salud").select("blood_type").eq(
        "participante_id", participante["id"]
    ).execute()
    assert salud_a.data and salud_a.data[0]["blood_type"] == "O+"
    salud_b = client_b.table("participante_salud").select("blood_type").eq(
        "participante_id", participante["id"]
    ).execute()
    assert salud_b.data == [], "RLS roto: B pudo leer salud de un turista de A"

    # B tampoco puede ESCRIBIR una salida en el tenant de A.
    with pytest.raises(APIError):
        client_b.table("salidas").insert(
            {
                "tenant_id": a.tenant_id,
                "activity_profile_id": activity["id"],
                "scheduled_start": start.isoformat(),
                "capacity": 5,
                "qr_token_hash": hashlib.sha256(uuid.uuid4().bytes).hexdigest(),
                "qr_token_expires_at": (start + timedelta(hours=24)).isoformat(),
                "created_by": user_a,
            }
        ).execute()
