"""Factory de clientes Supabase.

Dos clientes con propósitos distintos y NO intercambiables:

- ``get_user_client(access_token)``: lleva el JWT del usuario, por lo que
  PostgREST aplica RLS. **Es el default para TODO el flujo de la app.**
- ``get_service_client()``: usa la service_role key y **salta RLS**. Solo
  para el seed de la base de conocimiento y el provisioning en signup
  (cuando el claim tenant_id todavía no existe).
"""

from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


def get_user_client(access_token: str) -> Client:
    """Cliente scoped al JWT del usuario => RLS activo. Default de la app."""
    settings = get_settings()
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    # PostgREST usará este token => las policies ven el claim tenant_id.
    client.postgrest.auth(access_token)
    return client


@lru_cache
def get_service_client() -> Client:
    """Cliente service_role. SALTA RLS. Solo seed + provisioning."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
