"""Infraestructura compartida de los tests del chat de onboarding.

Herméticos: se mockean los bordes (Supabase vía repository, IA vía AIProvider).
La fixture ``wire`` cablea ambos y devuelve la captura del estado guardado.
"""

import pytest

from app.modules.onboarding import repository, service

TENANT_A = "11111111-1111-1111-1111-111111111111"

_CATS = ("equipo", "competencias", "emergencias", "riesgos", "seguimiento")


def _checklist_for(activities: list[str]) -> list[dict]:
    """Simula la Parte B: 5 categorías por actividad elegida."""
    rows: list[dict] = []
    for act in activities:
        for cat in _CATS:
            rows.append(
                {"field_key": f"{cat}_{act}", "description": f"{cat} de {act}", "activity": act}
            )
    return rows


class FakeProvider:
    def __init__(self, output: dict):
        self._output = output

    async def embed(self, text: str) -> list[float]:
        return [0.0] * 768

    async def generate_json(self, prompt: str, **kwargs) -> dict:
        self.last_prompt = prompt
        self.last_kwargs = kwargs
        return self._output


@pytest.fixture
def wire(monkeypatch):
    """Cablea repository + provider con dobles. Devuelve captura + estado guardado."""

    captured: dict = {}

    def setup(
        ai_output: dict | None = None,
        stored: dict | None = None,
        roadmap: list[dict] | None = None,
        statuses: list[dict] | None = None,
    ):
        state = {"data": dict(stored or {})}
        captured["state"] = state

        if ai_output is not None:
            provider = FakeProvider(ai_output)
            captured["provider"] = provider
            monkeypatch.setattr(service, "get_ai_provider", lambda: provider)

        monkeypatch.setattr(
            repository, "get_onboarding", lambda tid, token: dict(state["data"])
        )
        # Ruta guiada: sin filas => modo lineal (el comportamiento de siempre).
        monkeypatch.setattr(repository, "get_roadmap", lambda token: list(roadmap or []))
        monkeypatch.setattr(
            repository, "get_document_statuses", lambda tid, token: list(statuses or [])
        )
        monkeypatch.setattr(
            repository,
            "get_activity_checklist",
            lambda activities, token: _checklist_for(activities),
        )
        monkeypatch.setattr(
            repository,
            "get_active_onboarding_prompt",
            lambda token: {
                "version": "v2",
                "content": "PENDIENTES: <<PENDING_FIELDS>>\nOPCIONALES: <<OPTIONAL_FIELDS>>",
            },
        )
        monkeypatch.setattr(
            repository, "match_knowledge_chunks", lambda emb, numeral, token: []
        )

        def fake_save(tid, data, token):
            state["data"] = data
            return data

        monkeypatch.setattr(repository, "save_onboarding", fake_save)
        return captured

    return setup


def _auth(make_token, tenant_id: str | None = TENANT_A):
    token = make_token(tenant_id=tenant_id)
    return {"Authorization": f"Bearer {token}"}
