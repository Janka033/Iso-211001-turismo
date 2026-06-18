-- =====================================================================
-- Custom Access Token Hook.
-- Inyecta tenant_id + user_role en cada JWT, leyéndolos de user_profiles.
-- ES LA ÚNICA FUENTE DE VERDAD del claim: no se duplica en app_metadata
-- (se desincronizaría si cambia el perfil).
--
-- IMPORTANTE: el rol de la app va en el claim `user_role`, NO en `role`.
-- PostgREST reserva el claim `role` para el rol de Postgres (authenticated);
-- sobrescribirlo rompería la conexión. Las policies de rol usan
-- `auth.jwt() ->> 'user_role'`.
-- =====================================================================

create or replace function public.custom_access_token_hook(event jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
  claims    jsonb;
  v_tenant  uuid;
  v_role    text;
begin
  select tenant_id, role
    into v_tenant, v_role
    from public.user_profiles
   where user_id = (event ->> 'user_id')::uuid;

  claims := event -> 'claims';

  if v_tenant is not null then
    claims := jsonb_set(claims, '{tenant_id}', to_jsonb(v_tenant::text));
    claims := jsonb_set(claims, '{user_role}', to_jsonb(coalesce(v_role, 'empresa')));
  end if;

  event := jsonb_set(event, '{claims}', claims);
  return event;
end;
$$;

-- El hook corre como supabase_auth_admin: necesita ejecutar la función y
-- leer user_profiles. Nadie más debe poder ejecutar el hook.
grant execute on function public.custom_access_token_hook(jsonb) to supabase_auth_admin;
revoke execute on function public.custom_access_token_hook(jsonb) from authenticated, anon, public;

grant select on table public.user_profiles to supabase_auth_admin;

-- RLS: permitir que supabase_auth_admin lea los perfiles dentro del hook.
create policy "auth_admin_read_profiles" on public.user_profiles
  for select to supabase_auth_admin
  using (true);
