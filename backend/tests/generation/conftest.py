"""Infra compartida de los tests de generación.

El gate de secuencia (``onboarding.service.check_generatable``) se saltea por
defecto: estos tests ejercitan el MOTOR de generación (RAG → IA → validación →
generador), no el orden de la ruta. Un test que quiera ejercitar el gate puede
volver a monkeypatchearlo dentro del propio test.
"""

import pytest

from app.modules.onboarding import service as onboarding_service


@pytest.fixture(autouse=True)
def _bypass_sequence_gate(monkeypatch):
    async def _ok(document_type: str, tenant_id: str, token: str) -> tuple[bool, str]:
        return True, ""

    monkeypatch.setattr(onboarding_service, "check_generatable", _ok)
