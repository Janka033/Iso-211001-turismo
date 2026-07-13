-- =====================================================================
-- Sprint terreno 1: la historia end-to-end del kit MinCIT se vuelve
-- demostrable (docs/ARBOL-DOCUMENTAL.md §4 y §5).
--
-- 1. equipment_checks: revisión PRE y POST operacional de equipos
--    (molde 8.1 MinCIT: estado B/C/MC + evidencia + responsable + hora).
--    Offline-first como salida_eventos: el id lo genera el dispositivo.
-- 2. incident_reports: registro e investigación de incidentes (molde 8.3).
--    El servidor pre-llena lo que ya sabe (salida, actividad, guías); el
--    guía narra; el coordinador completa la investigación.
-- 3. Inducción de riesgos y PON de emergencias: NO son tablas nuevas —
--    son tipos nuevos de salida_eventos (induccion, emergencia_activada,
--    pon_paso, emergencia_cerrada). El "SÍ se le realizó inducción" del
--    Anexo A se deriva del evento con participante_id.
-- 4. participante_salud.arl: campo del Anexo A que faltaba (gap §5.4).
--
-- Decisiones de seguridad:
-- - La operación en terreno NUNCA se bloquea por suscripción vencida
--   (mismo criterio que salida_eventos en 0031): un check de seguridad o
--   un incidente no pueden esperar a que pase el past_due.
-- - equipment_checks es append-only (evidencia de auditoría): sin UPDATE
--   ni DELETE para authenticated.
-- - incident_reports: el guía que reporta solo edita mientras el reporte
--   está en borrador; la investigación la cierran gerente/coordinador.
-- - El rol que revisa equipos sin estar asignado a la salida (mecánico /
--   logística) opera hoy con rol coordinador; si se crea un rol propio,
--   solo se amplía el check de las policies.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Revisión pre/post operacional de equipos (molde 8.1)
-- ---------------------------------------------------------------------
create table public.equipment_checks (
  id             uuid primary key,  -- lo genera el DISPOSITIVO: sync idempotente
  tenant_id      uuid not null references public.tenants(id),
  -- Nullable: la revisión general de la mañana puede no estar atada a
  -- una salida; la de despacho/retorno sí.
  salida_id      uuid references public.salidas(id),
  item_id        uuid not null references public.operational_items(id),
  phase          text not null check (phase in ('pre', 'post')),
  -- Clasificación del molde MinCIT: B = buen estado, C = cambio de
  -- equipo, MC = mantenimiento correctivo.
  status         text not null check (status in ('B', 'C', 'MC')),
  quantity       int check (quantity > 0),
  note           text,
  -- Rutas de fotos/videos en el bucket privado 'evidence'
  -- ({tenant_id}/checks/...); el backend firma las URLs.
  evidence_paths jsonb not null default '[]'::jsonb,
  checked_by     uuid not null references public.user_profiles(user_id),
  checked_at     timestamptz not null,  -- hora real en terreno
  synced_at      timestamptz not null default now()
);

create index equipment_checks_tenant_salida_idx
  on public.equipment_checks (tenant_id, salida_id);
create index equipment_checks_item_idx
  on public.equipment_checks (item_id, checked_at desc);

-- ---------------------------------------------------------------------
-- 2. Registro e investigación de incidentes (molde 8.3)
-- ---------------------------------------------------------------------
create table public.incident_reports (
  id                       uuid primary key default gen_random_uuid(),
  tenant_id                uuid not null references public.tenants(id),
  salida_id                uuid references public.salidas(id),
  -- Tipo de actividad del molde (montañismo, rafting, cabalgata…): dato
  -- libre porque el molde admite "Otra, ¿cuál?".
  activity_type            text not null,
  occurred_at              timestamptz not null,
  location                 text not null,
  status                   text not null default 'borrador'
                           check (status in ('borrador', 'en_investigacion', 'cerrado')),
  -- Involucrados: IDs cuando existen en el sistema + texto para externos.
  lead_guide_name          text,
  lead_guide_phone         text,
  other_staff              jsonb not null default '[]'::jsonb,  -- [{nombre, telefono}]
  involved_participants    jsonb not null default '[]'::jsonb,  -- [{participante_id?, nombre, telefono}]
  witnesses                jsonb not null default '[]'::jsonb,  -- [{nombre, telefono, version}]
  -- Descripciones del molde MinCIT (8.3), una a una:
  environmental_conditions text,
  equipment_state          text,
  circumstances            text,
  probable_causes          text,
  emergency_response       text,
  consequences             text,
  action_plan              text,
  info_source              text,
  -- ¿El peligro/riesgo ya estaba identificado? Conecta con la matriz de
  -- riesgos (MT-04): si es false, dispara su actualización.
  risk_was_identified      boolean,
  investigators            jsonb not null default '[]'::jsonb,  -- [{nombre, cargo}]
  observations             text,
  evidence_paths           jsonb not null default '[]'::jsonb,
  reported_by              uuid not null references public.user_profiles(user_id),
  created_at               timestamptz not null default now(),
  updated_at               timestamptz not null default now()
);

create index incident_reports_tenant_idx
  on public.incident_reports (tenant_id, occurred_at desc);
create index incident_reports_salida_idx
  on public.incident_reports (salida_id);

create trigger trg_incident_reports_updated_at
  before update on public.incident_reports
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------
-- 3. Nuevos tipos de evento de terreno: inducción y PON de emergencia
-- ---------------------------------------------------------------------
alter table public.salida_eventos
  drop constraint salida_eventos_event_type_check;

alter table public.salida_eventos
  add constraint salida_eventos_event_type_check
  check (event_type in ('check_in', 'inicio_recorrido', 'punto_control', 'novedad',
                        'induccion', 'emergencia_activada', 'pon_paso',
                        'emergencia_cerrada', 'fin_recorrido'));

-- ---------------------------------------------------------------------
-- 4. Campo ARL del Anexo A (los turistas pueden no tener: nullable)
-- ---------------------------------------------------------------------
alter table public.participante_salud
  add column arl text;

-- ---------------------------------------------------------------------
-- 5. RLS
-- ---------------------------------------------------------------------
alter table public.equipment_checks enable row level security;
alter table public.incident_reports enable row level security;

-- equipment_checks: administración lee todo; el guía lo de SUS salidas.
create policy "staff_read" on public.equipment_checks
  for select to authenticated
  using (tenant_id = public.current_tenant_id()
         and (public.current_user_role() in ('gerente', 'coordinador', 'recepcionista')
              or public.guia_in_salida(salida_id)));

-- Escribe quien revisa (checked_by = auth.uid()): gerente/coordinador
-- siempre; el guía solo sobre sus salidas. Sin gate de suscripción:
-- terreno nunca se bloquea. Append-only: sin UPDATE/DELETE.
create policy "field_insert" on public.equipment_checks
  for insert to authenticated
  with check (tenant_id = public.current_tenant_id()
              and checked_by = auth.uid()
              and (public.current_user_role() in ('gerente', 'coordinador')
                   or (salida_id is not null and public.guia_in_salida(salida_id))));

-- incident_reports: lectura restringida (contenido sensible) — gestión,
-- el guía de la salida y quien reportó. Recepcionista NO.
create policy "restricted_read" on public.incident_reports
  for select to authenticated
  using (tenant_id = public.current_tenant_id()
         and (public.current_user_role() in ('gerente', 'coordinador')
              or public.guia_in_salida(salida_id)
              or reported_by = auth.uid()));

create policy "field_insert" on public.incident_reports
  for insert to authenticated
  with check (tenant_id = public.current_tenant_id()
              and reported_by = auth.uid()
              and (public.current_user_role() in ('gerente', 'coordinador')
                   or (salida_id is not null and public.guia_in_salida(salida_id))));

-- La investigación la gestiona gerente/coordinador en cualquier estado.
create policy "gc_update" on public.incident_reports
  for update to authenticated
  using (tenant_id = public.current_tenant_id()
         and public.current_user_role() in ('gerente', 'coordinador'))
  with check (tenant_id = public.current_tenant_id());

-- Quien reportó corrige su relato SOLO mientras sigue en borrador.
create policy "reporter_update_borrador" on public.incident_reports
  for update to authenticated
  using (tenant_id = public.current_tenant_id()
         and reported_by = auth.uid()
         and status = 'borrador')
  with check (tenant_id = public.current_tenant_id()
              and reported_by = auth.uid());
-- DELETE: sin policy — un incidente no se borra (evidencia de auditoría).
