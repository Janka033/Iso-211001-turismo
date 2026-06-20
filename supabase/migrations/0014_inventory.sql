-- =====================================================================
-- Inventario operativo + evidencia fotográfica = TRAZABILIDAD.
--
-- La empresa registra su operación REAL (equipos, vehículos, las N salidas
-- de emergencia, guías, riesgos...) con fotos de evidencia. La IA genera los
-- documentos a partir de estos ítems (4 salidas => el plan lista las 4; una
-- cuatrimoto nueva => aparece en la matriz de riesgos) y el consultor ve cada
-- numeral respaldado con su evidencia.
--
-- Tenant-scoped con RLS (current_tenant_id() del JWT). Hereda los grants de
-- 0005 (alter default privileges), así que no se otorgan aquí.
-- =====================================================================

create table public.operational_items (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   uuid not null references public.tenants (id) on delete cascade,
  category    text not null check (category in (
                'equipo', 'vehiculo', 'salida_emergencia', 'guia',
                'actividad', 'riesgo', 'contacto_emergencia', 'otro')),
  name        text not null,
  attributes  jsonb not null default '{}'::jsonb,   -- atributos flexibles por categoría
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index idx_operational_items_tenant
  on public.operational_items (tenant_id, category);

create table public.item_evidence (
  id            uuid primary key default gen_random_uuid(),
  tenant_id     uuid not null references public.tenants (id) on delete cascade,
  item_id       uuid not null references public.operational_items (id) on delete cascade,
  storage_path  text not null,
  caption       text,
  uploaded_at   timestamptz not null default now()
);
create index idx_item_evidence_item on public.item_evidence (item_id);

-- ---------------------------------------------------------------------
-- RLS: aislamiento por tenant (claim del JWT). Igual que el resto.
-- ---------------------------------------------------------------------
alter table public.operational_items enable row level security;
alter table public.item_evidence     enable row level security;

create policy "tenant_isolation" on public.operational_items
  for all to authenticated
  using (tenant_id = public.current_tenant_id())
  with check (tenant_id = public.current_tenant_id());

create policy "tenant_isolation" on public.item_evidence
  for all to authenticated
  using (tenant_id = public.current_tenant_id())
  with check (tenant_id = public.current_tenant_id());

-- ---------------------------------------------------------------------
-- Bucket privado de evidencias (fotos). Ruta {tenant_id}/{item_id}/...;
-- el backend sube/firma con service client (acotado a la carpeta del JWT).
-- Las policies quedan como defensa en profundidad a nivel DB.
-- ---------------------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('evidence', 'evidence', false)
on conflict (id) do nothing;

create policy "tenant_evidence_all" on storage.objects
  for all to authenticated
  using (
    bucket_id = 'evidence'
    and (storage.foldername(name))[1] = public.current_tenant_id()::text
  )
  with check (
    bucket_id = 'evidence'
    and (storage.foldername(name))[1] = public.current_tenant_id()::text
  );
