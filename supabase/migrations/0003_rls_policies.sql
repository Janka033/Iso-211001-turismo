-- =====================================================================
-- Row Level Security. Aislamiento de tenants a nivel de DB (día 1).
--
-- El tenant_id viaja como claim en el JWT (inyectado por el
-- custom_access_token_hook, ver 0004). El backend pega a PostgREST con el
-- JWT DEL USUARIO, nunca con service_role: service_role salta RLS.
-- =====================================================================

-- Helper: tenant_id del JWT actual (null si no hay claim).
create or replace function public.current_tenant_id()
returns uuid
language sql
stable
as $$
  select nullif(auth.jwt() ->> 'tenant_id', '')::uuid;
$$;

-- ---------------------------------------------------------------------
-- Habilitar RLS en TODAS las tablas
-- ---------------------------------------------------------------------
alter table public.tenants              enable row level security;
alter table public.user_profiles        enable row level security;
alter table public.companies            enable row level security;
alter table public.onboarding_data      enable row level security;
alter table public.ai_outputs           enable row level security;
alter table public.document_status      enable row level security;
alter table public.documents            enable row level security;
alter table public.chat_messages        enable row level security;
alter table public.knowledge_chunks     enable row level security;
alter table public.extraction_checklist enable row level security;
alter table public.templates            enable row level security;
alter table public.prompt_versions      enable row level security;

-- ---------------------------------------------------------------------
-- tenants: el usuario solo ve su propio tenant
-- ---------------------------------------------------------------------
create policy "tenant_self_read" on public.tenants
  for select to authenticated
  using (id = public.current_tenant_id());

-- ---------------------------------------------------------------------
-- user_profiles: el usuario solo ve/edita su propia fila
-- ---------------------------------------------------------------------
create policy "own_profile" on public.user_profiles
  for all to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- ---------------------------------------------------------------------
-- Tablas tenant-scoped: aislamiento por claim del JWT
-- ---------------------------------------------------------------------
do $$
declare
  tbl text;
begin
  foreach tbl in array array[
    'companies', 'onboarding_data', 'ai_outputs',
    'document_status', 'documents', 'chat_messages'
  ]
  loop
    execute format($f$
      create policy "tenant_isolation" on public.%I
        for all to authenticated
        using (tenant_id = public.current_tenant_id())
        with check (tenant_id = public.current_tenant_id());
    $f$, tbl);
  end loop;
end$$;

-- ---------------------------------------------------------------------
-- Datos de producto (globales): lectura para cualquier autenticado.
-- La generación corre con el JWT del usuario y necesita leer la norma,
-- la plantilla y el prompt activos. Escritura: solo service_role/superadmin
-- (que salta RLS vía el seed / la administración de plantillas).
-- ---------------------------------------------------------------------
create policy "read_for_authenticated" on public.knowledge_chunks
  for select to authenticated using (true);

create policy "read_for_authenticated" on public.extraction_checklist
  for select to authenticated using (true);

create policy "read_for_authenticated" on public.templates
  for select to authenticated using (true);

create policy "read_for_authenticated" on public.prompt_versions
  for select to authenticated using (true);
