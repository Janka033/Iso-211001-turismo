"""Tests del modo guiado por pasos del chat (Fase 2 de la ruta).

Con la ruta sembrada (document_roadmap), el chat agrupa los pendientes por el
documento del paso activo: identidad primero (paso 0), luego los campos de
cada documento en el orden de la ruta. Los pasos con datos completos y sin
documento generado salen en ``ready_to_generate``.
"""

from tests.onboarding.conftest import _auth

_ROUTE = [
    {
        "step_order": 4,
        "document_type": "politica_seguridad",
        "title": "Política de seguridad",
        "numeral": "5.2",
        "generator_ready": True,
    },
    {
        "step_order": 7,
        "document_type": "matriz_riesgos",
        "title": "Matriz de riesgos y oportunidades",
        "numeral": "6.1.1",
        "generator_ready": True,
    },
    {
        "step_order": 14,
        "document_type": "plan_emergencias",
        "title": "Plan de respuesta a emergencias",
        "numeral": "8.2",
        "generator_ready": True,
    },
]

_IDENTITY_DONE = {
    "activities": ["rafting"],
    "main_region": "Santander",
    "locations": ["río Fonce"],
    "scope": "Rafting en San Gil",
    "certified_guides": "4",
    "staff_roles": {"gerente": "1", "guia": "4"},
    "legal_representative": "Ana Ruiz",
    "nit": "901.234.567-8",
    "rnt_status": "Vigente",
    "rnt_number": "12345",
}


def test_identity_phase_is_step_zero(client, make_token, wire):
    wire(stored={"activities": ["rafting"]}, roadmap=_ROUTE)
    resp = client.post("/onboarding/chat", json={}, headers=_auth(make_token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["next_field"]["field_key"] == "main_region"
    step = body["current_step"]
    assert step["step_order"] == 0
    assert step["document_type"] is None
    assert step["total"] == 3
    assert step["fields_total"] == 9


def test_after_identity_asks_active_step_fields_only(client, make_token, wire):
    # Identidad completa => el paso activo es el primero de la ruta (política)
    # y la próxima pregunta es SU campo, no el orden lineal (que seguiría con
    # emergency_contacts, un campo del plan de emergencias).
    wire(stored=dict(_IDENTITY_DONE), roadmap=_ROUTE)
    resp = client.post("/onboarding/chat", json={}, headers=_auth(make_token))
    body = resp.json()
    assert body["next_field"]["field_key"] == "management_commitment"
    step = body["current_step"]
    assert step["step_order"] == 4
    assert step["document_type"] == "politica_seguridad"
    assert step["title"] == "Política de seguridad"
    assert step["fields_done"] == 0


def test_completed_step_reports_ready_to_generate(client, make_token, wire):
    # Política con todos sus campos => aparece en ready_to_generate (no tiene
    # documento generado) y el paso activo avanza a la matriz.
    stored = dict(
        _IDENTITY_DONE,
        management_commitment="La dirección prioriza la seguridad",
        safety_objectives=["Reducir incidentes 20% a dic 2026"],
        approval_date="15/01/2026",
        communication_channels=["Briefing", "Cartelera"],
    )
    wire(stored=stored, roadmap=_ROUTE)
    resp = client.post("/onboarding/chat", json={}, headers=_auth(make_token))
    body = resp.json()
    assert "politica_seguridad" in body["ready_to_generate"]
    step = body["current_step"]
    assert step["step_order"] == 7
    assert step["document_type"] == "matriz_riesgos"
    assert body["next_field"]["field_key"] == "existing_controls"


def test_generated_document_leaves_ready_list(client, make_token, wire):
    stored = dict(
        _IDENTITY_DONE,
        management_commitment="ok",
        safety_objectives=["obj"],
        approval_date="15/01/2026",
        communication_channels=["Briefing"],
    )
    wire(
        stored=stored,
        roadmap=_ROUTE,
        statuses=[{"document_type": "politica_seguridad", "status": "generated"}],
    )
    resp = client.post("/onboarding/chat", json={}, headers=_auth(make_token))
    body = resp.json()
    assert body["ready_to_generate"] == []


def test_activity_fields_belong_to_their_step(client, make_token, wire):
    # Con identidad y política completas, los campos por actividad de la
    # matriz (riesgos_rafting) van en el paso de la matriz, no antes.
    stored = dict(
        _IDENTITY_DONE,
        management_commitment="ok",
        safety_objectives=["obj"],
        approval_date="15/01/2026",
        communication_channels=["Briefing"],
        existing_controls="Chequeo de equipo",
        activity_step_breakdown="Embarque: corriente / caída",
        risk_factors="Ambiental: crecientes",
        business_risks=["Clima"],
        opportunities=["Certificación"],
    )
    wire(stored=stored, roadmap=_ROUTE)
    resp = client.post("/onboarding/chat", json={}, headers=_auth(make_token))
    body = resp.json()
    # Matriz: quedan sus campos de actividad (riesgos/edades/restricciones no
    # están en el checklist simulado, que solo trae las 5 categorías base).
    step = body["current_step"]
    assert step["document_type"] == "matriz_riesgos"
    assert body["next_field"]["field_key"] == "riesgos_rafting"


def test_alcance_step_asks_its_fields_first(client, make_token, wire):
    # Fase 4: el alcance (4.3) es el paso 1 de la ruta real. Con identidad
    # completa, sus dos preguntas del taller MinCIT van ANTES que la política.
    route = [
        {
            "step_order": 1,
            "document_type": "alcance_sgsta",
            "title": "Alcance del SGSTA",
            "numeral": "4.3",
            "generator_ready": True,
        },
        *_ROUTE,
    ]
    wire(stored=dict(_IDENTITY_DONE), roadmap=route)
    resp = client.post("/onboarding/chat", json={}, headers=_auth(make_token))
    body = resp.json()
    assert body["next_field"]["field_key"] == "site_characteristics"
    step = body["current_step"]
    assert step["step_order"] == 1
    assert step["document_type"] == "alcance_sgsta"
    assert step["fields_total"] == 2

    # Con el taller respondido, el alcance queda listo para generar y el paso
    # activo avanza a la política.
    stored = dict(
        _IDENTITY_DONE,
        site_characteristics="Zona rural, ribera del río Fonce",
        norm_exclusions="Aplican todos los requisitos",
    )
    wire(stored=stored, roadmap=route)
    resp = client.post("/onboarding/chat", json={}, headers=_auth(make_token))
    body = resp.json()
    assert body["ready_to_generate"] == ["alcance_sgsta"]
    assert body["current_step"]["document_type"] == "politica_seguridad"


def test_step_without_own_fields_waits_for_its_inputs(client, make_token, wire):
    # La matriz de objetivos no tiene preguntas propias: su insumo
    # (safety_objectives) se captura en el paso de la política. NO debe salir
    # "lista para generar" apenas termina la identidad (generaría un documento
    # lleno de [PENDIENTE]).
    route = [
        *_ROUTE,
        {
            "step_order": 9,
            "document_type": "matriz_objetivos_seguridad",
            "title": "Matriz de objetivos de seguridad",
            "numeral": "6.2",
            "generator_ready": True,
        },
    ]
    wire(stored=dict(_IDENTITY_DONE), roadmap=route)
    resp = client.post("/onboarding/chat", json={}, headers=_auth(make_token))
    assert "matriz_objetivos_seguridad" not in resp.json()["ready_to_generate"]

    # Con los datos de la política capturados, SÍ está lista.
    stored = dict(
        _IDENTITY_DONE,
        management_commitment="La dirección prioriza la seguridad",
        safety_objectives=["Reducir incidentes 20% a dic 2026"],
        approval_date="15/01/2026",
        communication_channels=["Briefing"],
    )
    wire(stored=stored, roadmap=route)
    resp = client.post("/onboarding/chat", json={}, headers=_auth(make_token))
    assert "matriz_objetivos_seguridad" in resp.json()["ready_to_generate"]


def test_nothing_ready_before_identity_completes(client, make_token, wire):
    # Con la identidad a medias, ningún documento se ofrece para generar
    # aunque sus campos propios estén respondidos.
    stored = {
        "activities": ["rafting"],
        "main_region": "Santander",
        "management_commitment": "ok",
        "safety_objectives": ["obj"],
        "approval_date": "15/01/2026",
        "communication_channels": ["Briefing"],
    }
    wire(stored=stored, roadmap=_ROUTE)
    resp = client.post("/onboarding/chat", json={}, headers=_auth(make_token))
    assert resp.json()["ready_to_generate"] == []


def test_without_route_flow_stays_linear(client, make_token, wire):
    wire(stored=dict(_IDENTITY_DONE))  # sin roadmap => lineal
    resp = client.post("/onboarding/chat", json={}, headers=_auth(make_token))
    body = resp.json()
    # Orden lineal de siempre: tras identidad sigue emergency_contacts.
    assert body["next_field"]["field_key"] == "emergency_contacts"
    assert body["current_step"] is None
    assert body["ready_to_generate"] == []
