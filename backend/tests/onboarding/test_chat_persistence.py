"""El chat de onboarding persiste su transcript en ``chat_messages`` para poder
REHIDRATAR la conversación al recargar (antes un F5 la perdía por completo).

Herméticos: la fixture ``wire`` mockea ``chat_messages`` con una lista en memoria
(``captured["messages"]``) y captura lo que persiste cada turno.
"""

from tests.onboarding.conftest import _auth


def test_real_turn_persists_user_and_assistant(client, make_token, wire):
    """Un turno real guarda el mensaje del cliente y la respuesta del asistente."""
    captured = wire(
        ai_output={
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
    msgs = captured["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert msgs[0]["content"] == "Operamos en Santander."
    assert msgs[1]["content"] == "¿En qué ubicaciones operan?"


def test_init_turn_seeds_first_question_once(client, make_token, wire):
    """El turno de arranque (sin mensaje, con actividades) siembra la primera
    pregunta UNA sola vez; una recarga posterior NO la duplica."""
    captured = wire(ai_output={}, stored={"activities": ["rafting"]})

    r1 = client.post(
        "/onboarding/chat",
        json={"activities": ["rafting"], "message": None},
        headers=_auth(make_token),
    )
    assert r1.status_code == 200, r1.text
    msgs = captured["messages"]
    assert [m["role"] for m in msgs] == ["assistant"]
    assert msgs[0]["content"]  # la pregunta pendiente actual, sembrada

    # Recarga: otro turno sin mensaje, ya hay historial => no se re-siembra.
    r2 = client.post(
        "/onboarding/chat",
        json={"message": None},
        headers=_auth(make_token),
    )
    assert r2.status_code == 200, r2.text
    assert captured["messages"] == msgs  # sin cambios


def test_init_turn_without_activities_seeds_nothing(client, make_token, wire):
    """Sin actividades (tenant recién llegado a la pantalla de selección) no se
    persiste nada: aún no hay conversación real que reconstruir."""
    captured = wire(ai_output={}, stored={})
    resp = client.post(
        "/onboarding/chat",
        json={"message": None},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    assert captured["messages"] == []


def test_blocked_turn_persists_user_and_safety_note(client, make_token, wire):
    """Un turno rechazado por el interceptor guarda el mensaje del cliente y la
    nota de seguridad como respuesta del asistente (el hilo se reconstruye igual)."""
    captured = wire(
        ai_output={
            "compliant": False,
            "safety_issue": "trasladar al participante la decisión sobre restricciones",
            "iso_requirement": "definir y aplicar restricciones de salud por actividad",
            "rephrase_hint": "indica qué condiciones de salud impiden participar",
            "extracted": {},
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
    msgs = captured["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert "embarazadas" in msgs[0]["content"]
    assert "NTC-ISO 21101" in msgs[1]["content"]


def test_history_endpoint_returns_persisted_transcript(client, make_token, wire):
    """GET /onboarding/chat/history devuelve el transcript en orden."""
    wire(
        ai_output={
            "extracted": {"main_region": "Meta"},
            "next_field_key": "locations",
            "next_question": "¿En qué ubicaciones operan?",
            "completed": False,
        },
        stored={"activities": ["rafting"]},
    )
    client.post(
        "/onboarding/chat",
        json={"message": "Estamos en el Meta."},
        headers=_auth(make_token),
    )
    resp = client.get("/onboarding/chat/history", headers=_auth(make_token))
    assert resp.status_code == 200, resp.text
    history = resp.json()
    assert [m["role"] for m in history] == ["user", "assistant"]
    assert history[0]["content"] == "Estamos en el Meta."
    assert history[1]["content"] == "¿En qué ubicaciones operan?"


def test_history_requires_tenant_claim(client, make_token, wire):
    wire(ai_output={})
    resp = client.get(
        "/onboarding/chat/history", headers=_auth(make_token, tenant_id=None)
    )
    assert resp.status_code == 401
