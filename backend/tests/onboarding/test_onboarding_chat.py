"""Tests de integración del onboarding conversacional (POST /onboarding/chat).

Herméticos: se mockean los bordes (Supabase vía repository, IA vía AIProvider).
Se ejercita el flujo real del service: checklist (universal + por actividad) →
IA extrae → merge → completitud dinámica → el BACKEND decide la próxima pregunta.
"""

from app.modules.onboarding import service
from tests.onboarding.conftest import _CATS, _auth, _checklist_for


def _levantamiento_rows(act: str) -> list[dict]:
    """Simula los campos del cuestionario "Información Técnica de Actividades"
    (0025): 2 obligatorios (responden alertas de auditor) + 3 opcionales."""
    return [
        {
            "field_key": f"edades_permitidas_{act}",
            "description": "Edad mínima y máxima permitida",
            "activity": act,
            "required": True,
        },
        {
            "field_key": f"restricciones_salud_{act}",
            "description": "Restricciones de salud para participar",
            "activity": act,
            "required": True,
        },
        {
            "field_key": f"ruta_descripcion_{act}",
            "description": "Ruta: inicio, fin, tipo y dificultad",
            "activity": act,
            "required": False,
        },
        {
            "field_key": f"grupo_participantes_{act}",
            "description": "Mínimo y máximo de participantes",
            "activity": act,
            "required": False,
        },
        {
            "field_key": f"seguro_contratado_{act}",
            "description": "Seguro contratado para la actividad",
            "activity": act,
            "required": False,
        },
    ]


class FailingProvider:
    """Simula la IA caída (503 de Gemini agotando reintentos)."""

    async def embed(self, text: str) -> list[float]:
        return [0.0] * 768

    async def generate_json(self, prompt: str, **kwargs) -> dict:
        raise RuntimeError("503 UNAVAILABLE (simulado)")


def _stored_until(field_key: str) -> dict:
    """onboarding_data con todo respondido HASTA (sin incluir) field_key, para
    que ese sea el pendiente en curso del turno."""
    from app.modules.onboarding.schemas import OnboardingPayload

    blank = OnboardingPayload()
    stored: dict = {"activities": ["rafting"]}
    for key, _q in service._UNIVERSAL_QUESTIONS:
        if key == field_key:
            break
        current = getattr(blank, key)
        if isinstance(current, dict):
            stored[key] = {"gerente": "1"}
        elif isinstance(current, list):
            stored[key] = ["dato"]
        else:
            stored[key] = "dato"
    return stored


# ---------------------------------------------------------------------------
# Primer turno: sin mensaje, el backend hace la primera pregunta (universal).
# ---------------------------------------------------------------------------


def test_first_turn_sets_activities_and_asks_first_universal(client, make_token, wire):
    wire(ai_output={})  # no se usa la IA en el primer turno (sin message)
    resp = client.post(
        "/onboarding/chat",
        json={"activities": ["rafting", "parapente", "buceo"], "message": None},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Universales + 5*3 por actividad; solo `activities` con dato. El número de
    # universales se deriva del service para no romper al añadir preguntas.
    expected_total = len(service._UNIVERSAL_KEYS) + 15
    assert body["completeness"] == round(1 / expected_total * 100, 2)
    assert body["completed"] is False
    assert body["next_field"]["field_key"] == "main_region"
    assert body["data"]["activities"] == ["rafting", "parapente", "buceo"]
    assert body["extracted"] == {}


# ---------------------------------------------------------------------------
# Turno con respuesta: la IA extrae varios campos; el backend avanza.
# ---------------------------------------------------------------------------


def test_extracts_multiple_universal_fields(client, make_token, wire):
    wire(
        ai_output={
            "extracted": {
                "main_region": "Santander",
                "locations": "río Suárez",
                "company_purpose": "Rafting seguro en el río Suárez",
                "certified_guides": "8",
            },
            "next_field_key": "staff_roles",
            "next_question": "¿Qué cargos tiene tu equipo?",
            "completed": False,
        },
        stored={"activities": ["rafting"]},
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "Operamos en Santander, en el río Suárez, con 8 guías."},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["main_region"] == "Santander"
    assert body["data"]["locations"] == ["río Suárez"]  # campo de lista
    assert body["data"]["certified_guides"] == "8"
    assert body["extracted"]["main_region"] == "Santander"
    # El alcance se DERIVA de actividades + ubicaciones + región (no se pregunta).
    assert body["data"]["scope"].startswith("Prestación de servicios de turismo")
    assert "río Suárez" in body["data"]["scope"]
    # La pregunta de la IA se usa porque coincide con el campo que eligió el backend.
    assert body["next_field"]["field_key"] == "staff_roles"
    assert body["next_question"] == "¿Qué cargos tiene tu equipo?"


def test_extraction_disables_thinking(client, make_token, wire):
    """La extracción no necesita razonamiento extendido: el service debe pedir
    thinking_budget=0 (latencia y costo medidos en el ensayo E2E)."""
    captured = wire(
        ai_output={"extracted": {}, "next_field_key": "scope", "completed": False},
        stored={"activities": ["rafting"]},
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "hola"},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    assert captured["provider"].last_kwargs == {"thinking_budget": 0}


def test_activity_field_goes_into_activity_fields(client, make_token, wire):
    wire(
        ai_output={
            "extracted": {"equipo_rafting": "Balsa, remos, chalecos, cascos"},
            "next_field_key": "competencias_rafting",
            "next_question": "¿Qué certificaciones tienen sus guías de rafting?",
            "completed": False,
        },
        stored={"activities": ["rafting"], "main_region": "Santander"},
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "Tenemos balsas, remos, chalecos y cascos."},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["activity_fields"]["equipo_rafting"] == "Balsa, remos, chalecos, cascos"


def test_staff_roles_captured_as_dict(client, make_token, wire):
    # El organigrama llega por el campo dedicado staff_roles (dict), no por el
    # mapa `extracted` de strings. Alimenta MA-02.
    wire(
        ai_output={
            "extracted": {},
            "staff_roles": {"gerente": "1", "coordinador": "2", "guia": "6"},
            "next_field_key": "legal_representative",
            "next_question": "¿Quién es el representante legal?",
            "completed": False,
        },
        stored={"activities": ["rafting"], "certified_guides": "6"},
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "Somos un gerente, dos coordinadores y seis guías."},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["staff_roles"] == {"gerente": "1", "coordinador": "2", "guia": "6"}


def test_staff_roles_correction_updates_and_removes(client, make_token, wire):
    # Corrección del organigrama: el nuevo número pisa al viejo y un cargo
    # devuelto con "0" se elimina (el merge por sí solo nunca borra).
    wire(
        ai_output={
            "extracted": {},
            "staff_roles": {"guia": "8", "auxiliar": "0"},
            "next_field_key": "legal_representative",
            "next_question": "Listo, corregí el organigrama. ¿Quién es el representante legal?",
            "completed": False,
        },
        stored={
            "activities": ["rafting"],
            "staff_roles": {"gerente": "1", "guia": "6", "auxiliar": "2"},
        },
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "Son 8 guías, no 6, y ya no tenemos auxiliares."},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["staff_roles"] == {"gerente": "1", "guia": "8"}


def test_invented_keys_are_dropped(client, make_token, wire):
    wire(
        ai_output={
            "extracted": {"main_region": "Meta", "campo_inventado": "x", "equipo_kayak": "y"},
            "next_field_key": "scope",
            "next_question": "¿Alcance?",
            "completed": False,
        },
        stored={"activities": ["rafting"]},  # kayak NO fue elegida
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "Estamos en el Meta."},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["main_region"] == "Meta"
    assert "campo_inventado" not in body["extracted"]
    # equipo_kayak no aplica (kayak no elegida) => descartado.
    assert "equipo_kayak" not in (body["data"].get("activity_fields") or {})


def test_backend_overrides_ai_next_field(client, make_token, wire):
    # La IA no extrae nada y propone 'nit', pero el primer pendiente real es
    # 'main_region' => manda el backend (pregunta de fallback).
    wire(
        ai_output={
            "extracted": {},
            "next_field_key": "nit",
            "next_question": "¿Cuál es el NIT?",
            "completed": True,
        },
        stored={"activities": ["rafting"]},
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "No estoy seguro."},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["next_field"]["field_key"] == "main_region"
    assert body["next_question"] != "¿Cuál es el NIT?"
    assert body["completed"] is False  # el backend reconfirma, no confía en la IA


# ---------------------------------------------------------------------------
# Interceptor de seguridad: una respuesta que viola la norma se rechaza, no se
# guarda nada y se re-pregunta el MISMO campo con la explicación ISO.
# ---------------------------------------------------------------------------


def test_safety_interceptor_blocks_and_saves_nothing(client, make_token, wire):
    wire(
        ai_output={
            "compliant": False,
            "safety_issue": "trasladar al participante la decisión sobre restricciones de salud",
            "iso_requirement": "definir y aplicar restricciones de salud por actividad",
            "rephrase_hint": "indica qué condiciones de salud impiden participar",
            # Aunque la IA (mal) devuelva un dato, no debe guardarse.
            "extracted": {"existing_controls": "que las embarazadas monten bajo su propio riesgo"},
            "next_field_key": "existing_controls",
            "completed": False,
        },
        stored={"activities": ["rafting"]},
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "Que las embarazadas monten bajo su propio riesgo."},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Se bloqueó: nada extraído ni guardado.
    assert body["blocked"] is True
    assert body["extracted"] == {}
    assert body["data"].get("existing_controls") in (None, "")
    assert body["completed"] is False
    # La explicación ISO viaja en safety_note y como próxima "pregunta".
    assert body["safety_note"]
    assert "NTC-ISO 21101" in body["safety_note"]
    # Se re-pregunta el MISMO campo pendiente (el primero: main_region no tiene dato).
    assert body["next_field"]["field_key"] == "main_region"


def test_not_applicable_advances_instead_of_looping(client, make_token, wire):
    """'No tengo' declara el campo ausente y AVANZA (antes: bucle infinito)."""
    wire(
        ai_output={
            "extracted": {},
            "not_applicable_fields": ["staff_roles"],
            "next_field_key": "legal_representative",
            "next_question": "¿Quién es el representante legal?",
            "completed": False,
        },
        stored={
            "activities": ["rafting"],
            "main_region": "Quindío",
            "locations": ["Salento"],
            "company_purpose": "Turismo de aventura en Salento",
            "certified_guides": "7",
        },
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "no tengo"},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # staff_roles quedó declarado ausente y NO se vuelve a preguntar.
    assert "staff_roles" in body["data"]["absent_fields"]
    assert body["next_field"]["field_key"] != "staff_roles"
    assert body["next_field"]["field_key"] == "legal_representative"


def test_not_applicable_empties_a_previously_given_value(client, make_token, wire):
    """'Ya no tengo' sobre un dato ya dado lo vacía y lo marca ausente."""
    wire(
        ai_output={
            "extracted": {},
            "not_applicable_fields": ["certified_guides"],
            "next_field_key": "staff_roles",
            "next_question": "¿Qué cargos tiene tu equipo?",
            "completed": False,
        },
        stored={
            "activities": ["rafting"],
            "main_region": "Quindío",
            "certified_guides": "7",  # dato que el cliente ahora retira
        },
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "en realidad no tengo guías certificados"},
        headers=_auth(make_token),
    )
    body = resp.json()
    assert body["data"]["certified_guides"] in (None, "")
    assert "certified_guides" in body["data"]["absent_fields"]


def test_giving_value_reactivates_absent_field(client, make_token, wire):
    """Si el cliente da un dato que antes declaró ausente, deja de ser 'no aplica'."""
    wire(
        ai_output={
            "extracted": {"certified_guides": "3"},
            "next_field_key": "staff_roles",
            "next_question": "¿Qué cargos tiene tu equipo?",
            "completed": False,
        },
        stored={
            "activities": ["rafting"],
            "main_region": "Quindío",
            "absent_fields": ["certified_guides"],
        },
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "ah, sí tengo 3 guías certificados"},
        headers=_auth(make_token),
    )
    body = resp.json()
    assert body["data"]["certified_guides"] == "3"
    assert "certified_guides" not in body["data"].get("absent_fields", [])


def test_data_warning_on_malformed_nit(client, make_token, wire):
    """Un NIT con muy pocos dígitos genera un aviso (no bloquea)."""
    wire(
        ai_output={
            "extracted": {"nit": "123"},
            "next_field_key": "rnt_status",
            "next_question": "¿Su RNT está vigente?",
            "completed": False,
        },
        stored={"activities": ["rafting"], "main_region": "Quindío"},
    )
    resp = client.post(
        "/onboarding/chat", json={"message": "el nit es 123"}, headers=_auth(make_token)
    )
    body = resp.json()
    assert body["data"]["nit"] == "123"  # se guarda igual (no bloquea)
    assert any("NIT" in w for w in body["data_warnings"])


def test_no_warning_when_nit_is_well_formed():
    from app.modules.onboarding import service

    assert service._data_warnings({"nit": "901.234.567-8"}, {"nit"}) == []


def test_data_warning_on_guides_vs_org_mismatch():
    from app.modules.onboarding import service

    data = {"certified_guides": "7", "staff_roles": {"guia": "4", "gerente": "1"}}
    warns = service._data_warnings(data, {"certified_guides"})
    assert len(warns) == 1
    assert "7" in warns[0] and "4" in warns[0]


def test_no_guides_warning_when_congruent():
    from app.modules.onboarding import service

    data = {"certified_guides": "4", "staff_roles": {"guías": "4"}}
    assert service._data_warnings(data, {"staff_roles"}) == []


def test_warnings_only_for_touched_fields():
    """Un NIT raro ya guardado no re-avisa si no se tocó este turno."""
    from app.modules.onboarding import service

    assert service._data_warnings({"nit": "123"}, set()) == []


def test_compliant_answer_is_not_blocked(client, make_token, wire):
    # compliant por defecto (o true) => flujo normal, sin bloqueo.
    wire(
        ai_output={
            "compliant": True,
            "extracted": {"main_region": "Santander"},
            "next_field_key": "locations",
            "next_question": "¿En qué ubicaciones operan?",
            "completed": False,
        },
        stored={"activities": ["rafting"]},
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "Operamos en Santander."},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["blocked"] is False
    assert body["safety_note"] is None
    assert body["data"]["main_region"] == "Santander"


def test_invalid_ai_json_falls_back_to_raw_capture(client, make_token, wire):
    """Un JSON de la IA fuera de schema ya NO es 502: activa la misma red de
    seguridad que la IA caída — el texto se captura tal cual en el campo en
    curso y el flujo continúa."""
    wire(ai_output={"extracted": "no-soy-un-dict"}, stored={"activities": ["rafting"]})
    resp = client.post(
        "/onboarding/chat",
        json={"message": "Operamos en Santander"},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # El primer pendiente universal (main_region) recibió el texto crudo.
    assert body["data"]["main_region"] == "Operamos en Santander"
    assert "Registré tu respuesta" in body["next_question"]


def test_requires_tenant_claim(client, make_token, wire):
    wire(ai_output={})
    resp = client.post(
        "/onboarding/chat",
        json={"activities": ["rafting"], "message": None},
        headers=_auth(make_token, tenant_id=None),
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# FASE 4 — escenario "empresa con 3 actividades distintas" (determinista,
# sin IA): el flujo debe generar preguntas específicas de CADA actividad y el
# universo de campos esperados debe superar los 5.
# ---------------------------------------------------------------------------

_ALL_UNIVERSAL = {
    "activities": ["rafting", "parapente", "buceo"],
    "main_region": "Santander",
    "locations": ["río Suárez"],
    "scope": "Rafting y parapente en Santander",
    "company_purpose": "Ofrecer turismo de aventura seguro en Santander",
    "certified_guides": "8",
    "staff_roles": {"gerente": "1", "guia": "5"},
    "legal_representative": "María Gómez",
    "nit": "900123456-7",
    "rnt_status": "Vigente",
    "rnt_number": "12345",
    "emergency_contacts": ["Bomberos 119"],
    "brigada_emergencias": "Sí: la lidera el coordinador (300 111 2233)",
    "capacitaciones_personal_emergencias": ["Primeros auxilios", "Rescate en agua"],
    "equipos_emergencia": ["Botiquín", "Camilla con inmovilizadores", "Radio VHF"],
    "organismos_apoyo": ["Cruz Roja 132", "Bomberos San Gil 119"],
    "hospital_cercano": "Hospital de San Gil, a 20 minutos",
    "vehiculos_evacuacion": "Camioneta 4x4 — Juan (310 000 0000)",
    "existing_controls": "Chequeo de equipo",
    "management_commitment": "La dirección prioriza la seguridad",
    # Micro-preguntas de granularidad por documento (NTC-ISO 21101).
    "safety_objectives": ["Reducir incidentes reportados 20% a diciembre 2026"],
    "approval_date": "15/01/2026",
    "communication_channels": ["Briefing pre-actividad", "Cartelera"],
    "activity_step_breakdown": "Embarque: peligro corriente, riesgo caída al agua",
    "risk_factors": "Ambiental: crecientes; humano: pánico; material: desgaste",
    "business_risks": ["Cancelaciones por clima"],
    "opportunities": ["Certificación NTC-ISO 21101"],
    "site_characteristics": "Zona rural, ribera del río Suárez",
    "norm_exclusions": "Aplican todos los requisitos de la norma",
    "management_signer": "Ana Ruiz, gerente; tel 300 111 2233; ana@x.co; San Gil, 15/01/2026",
    "risk_management_lead": "El gerente; seguimiento semestral",
    "document_control_info": "El gerente; electrónicos en la nube, físicos en la oficina",
    "operational_standards": "Seguimos la NTC-ISO 21101; no tenemos otras identificadas",
    "stakeholder_needs": "Clientes: seguridad; Alcaldía: RNT vigente; comunidad: empleo local",
    "stakeholder_compliance": "Cumplimos; la señalización está a medias (gerente, dic 2026)",
    "equipment_maintenance": "Balsas: inspección visual diaria y técnica mensual",
    "communication_matrix": "Briefing — clientes — verbal — antes de cada salida",
    "participation_consultation": "Reunión semanal de seguridad con los guías",
    "communication_representation": "Vocero de los guías; el gerente es el responsable",
    "incident_classification": ["Incidente: sin lesión", "Accidente: con lesión"],
    "incident_report_fields": ["Fecha", "Lugar", "Descripción", "Atención brindada"],
    "incident_followup": "Acciones correctivas en comité; registros 5 años; revisión anual",
}


def test_three_activities_produce_activity_specific_pending():
    activities = ["rafting", "parapente", "buceo"]
    checklist = _checklist_for(activities)
    # Todos los universales ya respondidos => los pendientes son SOLO por actividad.
    pending = service._pending_fields(_ALL_UNIVERSAL, checklist)

    assert len(pending) == 15  # 5 categorías × 3 actividades
    assert all(p["activity"] in activities for p in pending)
    # Cubre las 3 actividades y arranca por una pregunta específica de actividad.
    assert {p["activity"] for p in pending} == set(activities)
    assert pending[0]["activity"] is not None


def test_three_activities_expected_fields_exceed_five():
    activities = ["rafting", "parapente", "buceo"]
    checklist = _checklist_for(activities)
    pct, completed = service._measure_dynamic(_ALL_UNIVERSAL, checklist)

    # Universales + 15 por actividad (mucho más que 5). Con los universales
    # respondidos, faltan solo los 15 de actividad.
    n_universal = len(service._UNIVERSAL_KEYS)
    assert pct == round(n_universal / (n_universal + 15) * 100, 2)
    assert completed is False


def test_full_capture_completes():
    activities = ["rafting"]
    checklist = _checklist_for(activities)
    data = dict(_ALL_UNIVERSAL)
    data["activities"] = activities
    data["activity_fields"] = {row["field_key"]: "ok" for row in checklist}

    pending = service._pending_fields(data, checklist)
    pct, completed = service._measure_dynamic(data, checklist)
    assert pending == []
    assert pct == 100.0
    assert completed is True


def _completed_stored() -> dict:
    """Estado completo (universales + Parte B de rafting): no queda pendiente."""
    data = dict(_ALL_UNIVERSAL)
    data["activities"] = ["rafting"]
    data["activity_fields"] = {
        row["field_key"]: "ok" for row in _checklist_for(["rafting"])
    }
    return data


def test_late_correction_shows_ai_confirmation_when_completed(client, make_token, wire):
    """Onboarding completo + corrección tardía: la confirmación de la IA se
    muestra (antes se descartaba y la respuesta salía vacía)."""
    wire(
        ai_output={
            "extracted": {"nit": "901"},
            "next_field_key": None,
            "next_question": "Anoté el NIT 901; ¿está completo? Suele tener 9 dígitos.",
            "completed": True,
        },
        stored=_completed_stored(),
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "Corrige el NIT, el bueno es 901."},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["completed"] is True
    assert body["data"]["nit"] == "901"
    assert "901" in body["next_question"]  # la confirmación llegó al cliente


def test_late_correction_gets_deterministic_ack_when_ai_says_nothing(
    client, make_token, wire
):
    """Onboarding completo + corrección de organigrama sin texto de la IA: el
    backend arma un acuse determinista con los campos tocados."""
    wire(
        ai_output={
            "extracted": {},
            "staff_roles": {"guia": "6"},
            "next_field_key": None,
            "next_question": None,
            "completed": True,
        },
        stored=_completed_stored(),
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "Ya son 6 guías."},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["completed"] is True
    assert body["data"]["staff_roles"]["guia"] == "6"
    assert "staff_roles" in body["next_question"]
    assert "sigue completo" in body["next_question"]


# ---------------------------------------------------------------------------
# Dedupe de la Parte B: la tabla asocia el MISMO field_key a varios
# document_type; para el flujo y el % cuenta el campo único.
# ---------------------------------------------------------------------------


def _duplicated_checklist(activities: list[str]) -> list[dict]:
    """Como la tabla real: equipo_* y competencias_* aparecen 2 veces (asociados
    a document_types distintos)."""
    rows = _checklist_for(activities)
    dupes = [
        dict(row) for row in rows
        if row["field_key"].startswith(("equipo_", "competencias_"))
    ]
    return rows + dupes


def test_dedupe_checklist_keeps_one_row_per_field_key():
    checklist = _duplicated_checklist(["rafting"])
    assert len(checklist) == 7  # 5 + 2 duplicadas
    unique = service._dedupe_checklist(checklist)
    assert len(unique) == 5
    assert [r["field_key"] for r in unique] == [
        f"{cat}_rafting" for cat in _CATS
    ]


def test_duplicated_rows_do_not_inflate_completeness(client, make_token, wire):
    """Con 3 actividades la tabla real trae 21 filas (15 únicas): el % debe
    calcularse sobre las únicas y los pendientes no deben repetirse."""
    captured = wire(ai_output={})
    monkeypatch_checklist = captured  # legibilidad

    # Recablea la checklist para que devuelva filas duplicadas.
    import app.modules.onboarding.repository as repo

    original = repo.get_activity_checklist
    try:
        repo.get_activity_checklist = (
            lambda activities, token: _duplicated_checklist(activities)
        )
        resp = client.post(
            "/onboarding/chat",
            json={"activities": ["rafting", "parapente", "buceo"], "message": None},
            headers=_auth(make_token),
        )
    finally:
        repo.get_activity_checklist = original

    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Universales + 15 únicos por actividad (los duplicados no inflan).
    expected_total = len(service._UNIVERSAL_KEYS) + 15
    assert body["completeness"] == round(1 / expected_total * 100, 2)
    assert monkeypatch_checklist is captured


# ---------------------------------------------------------------------------
# Campos del levantamiento (0025): los required=false NUNCA se preguntan ni
# castigan la completitud, pero suman si el cliente los da espontáneamente.
# ---------------------------------------------------------------------------


def test_optional_fields_are_never_asked():
    checklist = _checklist_for(["rafting"]) + _levantamiento_rows("rafting")
    data = dict(_ALL_UNIVERSAL, activities=["rafting"])
    pending = service._pending_fields(data, checklist)

    keys = [p["field_key"] for p in pending]
    # Los obligatorios nuevos SÍ se preguntan, tras las 5 categorías de 0021;
    # los opcionales (ruta, grupo, seguro) no aparecen jamás.
    assert keys == [f"{cat}_rafting" for cat in _CATS] + [
        "edades_permitidas_rafting",
        "restricciones_salud_rafting",
    ]


def test_optional_absence_does_not_lower_completeness_nor_block_completion():
    checklist = _checklist_for(["rafting"]) + _levantamiento_rows("rafting")
    data = dict(_ALL_UNIVERSAL)
    data["activities"] = ["rafting"]
    data["activity_fields"] = {f"{cat}_rafting": "ok" for cat in _CATS}
    data["activity_fields"]["edades_permitidas_rafting"] = "12 a 60 años"
    data["activity_fields"]["restricciones_salud_rafting"] = "Embarazo, cirugías recientes"

    pending = service._pending_fields(data, checklist)
    pct, completed = service._measure_dynamic(data, checklist)
    assert pending == []
    assert pct == 100.0
    assert completed is True


def test_optional_fields_add_to_completeness_when_given():
    checklist = _checklist_for(["rafting"]) + _levantamiento_rows("rafting")
    data = dict(_ALL_UNIVERSAL, activities=["rafting"])

    # Universales llenos; 7 obligatorios por actividad vacíos.
    n_universal = len(service._UNIVERSAL_KEYS)
    pct_before, _ = service._measure_dynamic(data, checklist)
    assert pct_before == round(n_universal / (n_universal + 7) * 100, 2)

    # Un opcional dado espontáneamente entra al numerador Y al denominador.
    data["activity_fields"] = {"seguro_contratado_rafting": "Póliza Sura 123"}
    pct_after, completed = service._measure_dynamic(data, checklist)
    assert pct_after == round((n_universal + 1) / (n_universal + 8) * 100, 2)
    assert pct_after > pct_before
    assert completed is False


def test_correction_overwrites_already_captured_field(client, make_token, wire):
    """El cliente puede corregir un dato ya registrado ("me equivoqué en el
    NIT…"): la IA lo re-extrae (prompt v3) y el backend SOBREESCRIBE el valor,
    sin perder el pendiente en curso."""
    stored = _stored_until("emergency_contacts")
    assert stored["nit"] == "dato"  # valor "mal digitado" previo
    captured = wire(
        ai_output={
            "extracted": {"nit": "901.234.567-8"},
            "next_field_key": "emergency_contacts",
            "next_question": (
                "Listo, corregí el NIT a 901.234.567-8. ¿Qué contactos de "
                "emergencia tienen?"
            ),
            "completed": False,
        },
        stored=stored,
    )

    resp = client.post(
        "/onboarding/chat",
        json={"message": "me equivoqué en el NIT, el correcto es 901.234.567-8"},
        headers=_auth(make_token),
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["nit"] == "901.234.567-8"
    # El pendiente en curso no cambió y la pregunta confirma la corrección.
    assert body["next_field"]["field_key"] == "emergency_contacts"
    assert "corregí el NIT" in body["next_question"]
    assert captured["state"]["data"]["nit"] == "901.234.567-8"  # persistido


# ---------------------------------------------------------------------------
# Red de seguridad determinista: la IA caída NO pierde la respuesta del cliente.
# ---------------------------------------------------------------------------


def test_ai_failure_captures_raw_answer_deterministically(
    client, make_token, wire, monkeypatch
):
    """Si el provider falla (503 de Gemini), el turno se captura igual: el
    texto crudo va al campo en curso (lista partida por saltos, ';' y comas),
    el flujo avanza y la respuesta lo dice con claridad. Antes: 502 y el
    cliente perdía lo escrito."""
    wire(stored=_stored_until("emergency_contacts"))
    monkeypatch.setattr(service, "get_ai_provider", lambda: FailingProvider())

    message = (
        "Bomberos San Gil: (607) 724-2222 / 119\n"
        "Hospital Regional de San Gil: (607) 724-9000\n"
        "Policía Nacional: 123\n"
        "Defensa Civil / Cruz Roja: 144"
    )
    resp = client.post(
        "/onboarding/chat", json={"message": message}, headers=_auth(make_token)
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["emergency_contacts"] == [
        "Bomberos San Gil: (607) 724-2222 / 119",
        "Hospital Regional de San Gil: (607) 724-9000",
        "Policía Nacional: 123",
        "Defensa Civil / Cruz Roja: 144",
    ]
    # El flujo avanza al siguiente pendiente y se avisa la captura literal.
    assert body["next_field"]["field_key"] != "emergency_contacts"
    assert "Registré tu respuesta" in body["next_question"]


def test_ai_failure_on_staff_roles_reasks_without_corrupting(
    client, make_token, wire, monkeypatch
):
    """staff_roles es un dict estructurado: el fallback NO le asigna texto
    libre; el turno no guarda nada y se re-pregunta el mismo campo."""
    wire(stored=_stored_until("staff_roles"))
    monkeypatch.setattr(service, "get_ai_provider", lambda: FailingProvider())

    resp = client.post(
        "/onboarding/chat",
        json={"message": "somos 6 guías, 1 gerente y 2 auxiliares"},
        headers=_auth(make_token),
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["staff_roles"] == {}
    assert body["next_field"]["field_key"] == "staff_roles"


def test_dedupe_checklist_keeps_required_when_duplicated_row_is_optional():
    # El mismo field_key puede alimentar 2 documentos con exigencia distinta;
    # el dedupe no debe degradar un campo obligatorio según el orden de filas.
    rows = [
        {
            "field_key": "restricciones_salud_rafting",
            "description": "Restricciones de salud",
            "activity": "rafting",
            "required": False,
        },
        {
            "field_key": "restricciones_salud_rafting",
            "description": "Restricciones de salud",
            "activity": "rafting",
            "required": True,
        },
    ]
    unique = service._dedupe_checklist(rows)
    assert len(unique) == 1
    assert unique[0]["required"] is True


def test_chat_extracts_optional_field_spontaneously(client, make_token, wire):
    """La IA puede extraer un opcional mencionado de pasada: se persiste en
    activity_fields y el prompt lo lista como OPCIONAL, no como pendiente."""
    captured = wire(
        ai_output={
            "extracted": {
                "equipo_rafting": "Balsa y cascos",
                "seguro_contratado_rafting": "Póliza de accidentes Sura",
            },
            "next_field_key": "competencias_rafting",
            "next_question": "¿Qué certificaciones tienen sus guías de rafting?",
            "completed": False,
        },
        stored={**_ALL_UNIVERSAL, "activities": ["rafting"]},
    )

    import app.modules.onboarding.repository as repo

    original = repo.get_activity_checklist
    try:
        repo.get_activity_checklist = lambda activities, token: (
            _checklist_for(activities) + _levantamiento_rows("rafting")
        )
        resp = client.post(
            "/onboarding/chat",
            json={"message": "Balsa y cascos; además tenemos póliza con Sura."},
            headers=_auth(make_token),
        )
    finally:
        repo.get_activity_checklist = original

    assert resp.status_code == 200, resp.text
    body = resp.json()
    fields = body["data"]["activity_fields"]
    assert fields["seguro_contratado_rafting"] == "Póliza de accidentes Sura"
    assert body["next_field"]["field_key"] == "competencias_rafting"

    # El prompt separa PENDIENTES (obligatorios) de OPCIONALES.
    prompt = captured["provider"].last_prompt
    pendientes, opcionales = prompt.split("OPCIONALES:")
    assert "seguro_contratado_rafting" in opcionales
    assert "seguro_contratado_rafting" not in pendientes
    assert "edades_permitidas_rafting" in pendientes


def test_new_emergency_universals_enter_flow_and_coerce_lists(client, make_token, wire):
    """El bloque PL-01 (brigada, organismos, etc.) entra al camino obligatorio
    tras emergency_contacts; los campos de lista se coercionan."""
    stored = {
        k: v
        for k, v in _ALL_UNIVERSAL.items()
        if k
        not in (
            "brigada_emergencias",
            "capacitaciones_personal_emergencias",
            "equipos_emergencia",
            "organismos_apoyo",
            "hospital_cercano",
            "vehiculos_evacuacion",
        )
    }
    wire(
        ai_output={
            "extracted": {
                "brigada_emergencias": "Sí, la lidera el coordinador de operaciones",
                "organismos_apoyo": "Cruz Roja 132; Bomberos 119",
            },
            "next_field_key": "capacitaciones_personal_emergencias",
            "next_question": "¿Qué capacitaciones en emergencias tiene el personal?",
            "completed": False,
        },
        stored=stored,
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "Sí hay brigada; nos apoyan Cruz Roja y bomberos."},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["brigada_emergencias"] == "Sí, la lidera el coordinador de operaciones"
    assert body["data"]["organismos_apoyo"] == ["Cruz Roja 132", "Bomberos 119"]
    # El backend elige el primer universal aún pendiente del bloque PL-01.
    assert body["next_field"]["field_key"] == "capacitaciones_personal_emergencias"
