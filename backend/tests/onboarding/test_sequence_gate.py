"""Gate de SECUENCIA de la generación (``onboarding.service.check_generatable``).

No se puede generar un documento fuera de orden ni con datos insuficientes.
Un documento ya generado sí puede regenerarse; uno fuera de la ruta no se gatea.
Herméticos: la fixture ``wire`` mockea el repository.
"""

from app.modules.onboarding import service
from tests.onboarding.conftest import TENANT_A
from tests.onboarding.test_chat_steps import _IDENTITY_DONE

_TOKEN = "tok"

_ROUTE = [
    {
        "step_order": 1,
        "document_type": "alcance_sgsta",
        "title": "Alcance del SGSTA",
        "numeral": "4.3",
        "generator_ready": True,
    },
    {
        "step_order": 4,
        "document_type": "politica_seguridad",
        "title": "Política de seguridad",
        "numeral": "5.2",
        "generator_ready": True,
    },
]

# Alcance con sus dos campos del taller respondidos => datos suficientes.
_ALCANCE_READY = dict(
    _IDENTITY_DONE,
    site_characteristics="Zona rural, ribera del río Fonce",
    norm_exclusions="Aplican todos los requisitos",
)


async def test_gate_allows_active_step_with_sufficient_data(wire):
    wire(stored=_ALCANCE_READY, roadmap=_ROUTE)
    ok, reason = await service.check_generatable("alcance_sgsta", TENANT_A, _TOKEN)
    assert ok is True
    assert reason == ""


async def test_gate_blocks_future_step_out_of_order(wire):
    # El alcance (paso 1) aún no está generado: no se puede generar la política
    # (paso 4) todavía.
    wire(stored=_ALCANCE_READY, roadmap=_ROUTE)
    ok, reason = await service.check_generatable("politica_seguridad", TENANT_A, _TOKEN)
    assert ok is False
    assert "pasos anteriores" in reason


async def test_gate_blocks_active_step_with_insufficient_data(wire):
    # El alcance es el paso activo pero le faltan sus campos (site/norm).
    wire(stored=dict(_IDENTITY_DONE), roadmap=_ROUTE)
    ok, reason = await service.check_generatable("alcance_sgsta", TENANT_A, _TOKEN)
    assert ok is False
    assert "faltan datos" in reason.lower()


async def test_gate_blocks_before_identity_completes(wire):
    wire(stored={"activities": ["rafting"]}, roadmap=_ROUTE)
    ok, reason = await service.check_generatable("alcance_sgsta", TENANT_A, _TOKEN)
    assert ok is False
    assert "datos generales" in reason


async def test_gate_allows_already_generated_for_regeneration(wire):
    # Un doc ya generado puede regenerarse/subsanarse aunque cambie el orden.
    wire(
        stored=dict(_IDENTITY_DONE),
        roadmap=_ROUTE,
        statuses=[{"document_type": "alcance_sgsta", "status": "generated"}],
    )
    ok, reason = await service.check_generatable("alcance_sgsta", TENANT_A, _TOKEN)
    assert ok is True


async def test_gate_ignores_documents_outside_roadmap(wire):
    wire(stored=dict(_IDENTITY_DONE), roadmap=_ROUTE)
    ok, reason = await service.check_generatable("gestion_incidentes", TENANT_A, _TOKEN)
    assert ok is True  # sin paso en la ruta: no se le aplica secuencia
