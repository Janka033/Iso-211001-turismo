"""Lógica de negocio del onboarding.

Persiste los datos crudos del cliente en ``onboarding_data`` (separados de
``ai_outputs``) y calcula el avance. La generación los consume como contexto.
El repository (supabase-py es síncrono) se ejecuta en un hilo para no bloquear
el event loop.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import TypeVar

import anyio

from app.modules.onboarding import repository
from app.modules.onboarding.schemas import OnboardingPayload, OnboardingState

T = TypeVar("T")

# Campos clave para medir el avance del onboarding (los que más necesita el motor).
_KEY_FIELDS = (
    "activities",
    "main_region",
    "certified_guides",
    "legal_representative",
    "rnt_status",
)


async def _run(fn: Callable[..., T], *args: object) -> T:
    """Ejecuta una llamada bloqueante (repository) en un hilo."""
    return await anyio.to_thread.run_sync(functools.partial(fn, *args))


def _has_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, str)):
        return len(value) > 0
    return True


def _measure(data: OnboardingPayload) -> tuple[float, bool]:
    dump = data.model_dump()
    filled = [f for f in _KEY_FIELDS if _has_value(dump.get(f))]
    pct = round(len(filled) / len(_KEY_FIELDS) * 100, 2)
    return pct, len(filled) == len(_KEY_FIELDS)


async def get_state(tenant_id: str, token: str) -> OnboardingState:
    raw = await _run(repository.get_onboarding, tenant_id, token)
    data = OnboardingPayload.model_validate(raw or {})
    pct, completed = _measure(data)
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

    pct, completed = _measure(data)
    return OnboardingState(data=data, completeness=pct, completed=completed)
