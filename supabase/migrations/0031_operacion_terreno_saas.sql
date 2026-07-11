-- =====================================================================
-- Ecosistema operativo + modelo SaaS.
--
-- 1. Suscripción B2B en tenants (trial 14 días, tiers, soft-lock past_due)
--    con límites por tier como DATOS (plan_limits), no hardcodeados.
-- 2. activity_profiles: ficha técnica por actividad (molde del formulario
--    del Drive); alimenta validaciones del formulario del turista.
-- 3. Operación de terreno: salidas (QR), salida_guias, participantes,
--    participante_salud (datos sensibles SEPARADOS), consent_templates,
--    consentimientos (INMUTABLE) y salida_eventos (log append-only,
--    offline-first: id lo genera el cliente).
--
-- Decisiones de seguridad:
-- - El turista NUNCA toca PostgREST: el endpoint público de FastAPI valida
--   el token de la salida (aquí solo vive su hash) y escribe con
--   service_role. tenant_id se deriva del token, jamás del body.
-- - participante_salud es tabla aparte: recepcionista NO la lee (solo el
--   flag has_medical_alert en participantes); guía solo la de sus salidas.
-- - Soft-lock (Regla 3): past_due / trial vencido = solo lectura para
--   roles administrativos. Las salidas EN CURSO no se interrumpen: los
--   guías siguen insertando salida_eventos y actualizando su salida.
-- - Rol legado 'empresa' se trata como 'gerente' (current_user_role());
--   la migración de datos del rol se hará cuando el backend adopte los
--   roles nuevos.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1a. Suscripción en tenants
-- ---------------------------------------------------------------------
alter table public.tenants
  add column plan text not null default 'esencial'
    check (plan in ('esencial', 'profesional', 'empresarial')),
  add column subscription_status text not null default 'trialing'
    check (subscription_status in ('trialing', 'active', 'past_due', 'canceled')),
  add column trial_ends_at timestamptz not null default (now() + interval '14 days');

-- Los tenants PREEXISTENTES (piloto Felipe, QA) no entran al trial: quedan
-- activos sin límites para no bloquear la validación en curso.
update public.tenants
   set subscription_status = 'active',
       plan = 'empresarial';

-- ---------------------------------------------------------------------
-- 1b. Límites por tier: son DATOS del producto (null = ilimitado)
-- ---------------------------------------------------------------------
create table public.plan_limits (
  plan                  text primary key
                        check (plan in ('esencial', 'profesional', 'empresarial')),
  max_active_activities int,
  max_guias             int
);

insert into public.plan_limits (plan, max_active_activities, max_guias) values
  ('esencial',     2,    3),
  ('profesional',  5,    15),
  ('empresarial',  null, null);

-- ---------------------------------------------------------------------
-- 1c. Helpers de suscripción y rol
-- ---------------------------------------------------------------------
-- Regla 1: durante el trial vigente se opera con límites de 'profesional'.
create or replace function public.tenant_effective_plan(t uuid)
returns text
language sql stable set search_path = public
as $$
  select case
           when subscription_status = 'trialing' and now() < trial_ends_at
             then 'profesional'
           else plan
         end
    from tenants
   where id = t;
$$;

-- Regla 3: escribible solo con suscripción activa o trial vigente.
create or replace function public.tenant_is_writable(t uuid)
returns boolean
language sql stable set search_path = public
as $$
  select coalesce(
    (select subscription_status = 'active'
         or (subscription_status = 'trialing' and now() < trial_ends_at)
       from tenants
      where id = t),
    false);
$$;

-- Rol de app del JWT; 'empresa' (legado) equivale a 'gerente'.
create or replace function public.current_user_role()
returns text
language sql stable set search_path = public
as $$
  select case coalesce(auth.jwt() ->> 'user_role', '')
           when 'empresa' then 'gerente'
           else coalesce(auth.jwt() ->> 'user_role', '')
         end;
$$;

-- ---------------------------------------------------------------------
-- 1d. Roles del tenant en user_profiles
-- ---------------------------------------------------------------------
-- El check existente solo permitía empresa|admin|superadmin: se reemplaza
-- por el catálogo extendido con los roles operativos del tenant.
alter table public.user_profiles
  drop constraint user_profiles_role_check;

alter table public.user_profiles
  add constraint user_profiles_role_check
  check (role in ('empresa', 'gerente', 'coordinador', 'recepcionista', 'guia',
                  'admin', 'superadmin'));

-- ---------------------------------------------------------------------
-- 2. Ficha técnica por actividad (molde: formulario técnico del Drive)
-- ---------------------------------------------------------------------
create table public.activity_profiles (
  id                      uuid primary key default gen_random_uuid(),
  tenant_id               uuid not null references public.tenants(id),
  name                    text not null,
  activity_type           text not null,
  is_active               boolean not null default true,
  min_participants        int,
  max_participants        int,
  min_age                 int,
  max_age                 int,
  difficulty              text,
  duration_minutes        int,
  location                text,
  route_kmz_path          text,
  required_competencies   text,
  health_restrictions     text,
  -- Campos condicionales que el formulario del turista debe pedir para
  -- esta actividad (p. ej. [{"key":"sabe_nadar","type":"bool"}]).
  participant_form_fields jsonb not null default '[]'::jsonb,
  cancellation_policy     text,
  insurance_info          text,
  created_at              timestamptz not null default now(),
  updated_at              timestamptz not null default now(),
  unique (tenant_id, name)
);

create index activity_profiles_tenant_idx on public.activity_profiles (tenant_id);

-- ---------------------------------------------------------------------
-- 3. Operación de terreno
-- ---------------------------------------------------------------------
create table public.salidas (
  id                  uuid primary key default gen_random_uuid(),
  tenant_id           uuid not null references public.tenants(id),
  activity_profile_id uuid not null references public.activity_profiles(id),
  route_name          text,
  scheduled_start     timestamptz not null,
  capacity            int not null check (capacity > 0),
  status              text not null default 'programada'
                      check (status in ('programada', 'en_curso', 'finalizada', 'cancelada')),
  -- sha256 del token del link/QR; el token en claro SOLO viaja en el QR.
  qr_token_hash       text not null unique,
  qr_token_expires_at timestamptz not null,
  created_by          uuid not null references public.user_profiles(user_id),
  started_at          timestamptz,
  finished_at         timestamptz,
  created_at          timestamptz not null default now()
);

create index salidas_tenant_sched_idx on public.salidas (tenant_id, scheduled_start);

create table public.salida_guias (
  salida_id    uuid not null references public.salidas(id) on delete cascade,
  guia_user_id uuid not null references public.user_profiles(user_id),
  tenant_id    uuid not null references public.tenants(id),
  is_lead      boolean not null default false,
  primary key (salida_id, guia_user_id)
);

create index salida_guias_guia_idx on public.salida_guias (guia_user_id);

create table public.participantes (
  id                 uuid primary key default gen_random_uuid(),
  tenant_id          uuid not null references public.tenants(id),
  salida_id          uuid not null references public.salidas(id),
  document_type      text not null check (document_type in ('CC', 'TI', 'CE', 'PA')),
  document_number    text not null,
  full_name          text not null,
  birth_date         date not null,
  nationality        text,
  phone              text not null,
  email              text not null,
  -- Si es menor: {nombre, documento, parentesco, telefono} del acudiente.
  guardian           jsonb,
  -- [{nombre, parentesco, telefono}] (1..2 contactos).
  emergency_contacts jsonb not null,
  -- La ALERTA ROJA del manifiesto. El detalle vive en participante_salud;
  -- este flag es lo único de salud que ve recepcionista/monitor.
  has_medical_alert  boolean not null default false,
  status             text not null default 'registrado'
                     check (status in ('registrado', 'firmado', 'embarcado',
                                       'finalizado', 'no_show')),
  created_at         timestamptz not null default now(),
  unique (salida_id, document_type, document_number)
);

create index participantes_salida_idx on public.participantes (salida_id);
create index participantes_tenant_idx on public.participantes (tenant_id);

-- Datos SENSIBLES (Ley 1581/2012): tabla aparte para minimizar acceso.
create table public.participante_salud (
  participante_id      uuid primary key
                       references public.participantes(id) on delete cascade,
  tenant_id            uuid not null references public.tenants(id),
  eps                  text not null,
  blood_type           text not null
                       check (blood_type in ('A+','A-','B+','B-','AB+','AB-','O+','O-')),
  allergies            text not null,
  medical_conditions   jsonb not null,
  current_medications  text,
  -- Respuestas a los campos condicionales de la ficha técnica.
  activity_specific    jsonb,
  declared_truthful_at timestamptz not null
);

-- Texto del consentimiento VERSIONADO (plantillas son datos, no código).
create table public.consent_templates (
  id             uuid primary key default gen_random_uuid(),
  tenant_id      uuid not null references public.tenants(id),
  version        int not null,
  body_md        text not null,
  content_hash   text not null,
  effective_from timestamptz not null default now(),
  unique (tenant_id, version)
);

-- Firma digital: evidencia legal (Ley 527/1999). INMUTABLE.
create table public.consentimientos (
  id                   uuid primary key default gen_random_uuid(),
  tenant_id            uuid not null references public.tenants(id),
  participante_id      uuid not null unique references public.participantes(id),
  consent_template_id  uuid not null references public.consent_templates(id),
  signed_document_hash text not null,
  -- Trazo de la firma en bucket PRIVADO de Storage.
  signature_path       text not null,
  signer_name          text not null,
  signer_document      text not null,
  signed_by_guardian   boolean not null default false,
  accepted_privacy     boolean not null,
  accepted_risk_info   boolean not null,
  signed_at            timestamptz not null default now(),
  ip_address           inet,
  user_agent           text
);

-- Log de terreno append-only. El id lo genera el DISPOSITIVO del guía:
-- el sync offline es un INSERT idempotente (ON CONFLICT DO NOTHING).
create table public.salida_eventos (
  id              uuid primary key,
  tenant_id       uuid not null references public.tenants(id),
  salida_id       uuid not null references public.salidas(id),
  participante_id uuid references public.participantes(id),
  event_type      text not null
                  check (event_type in ('check_in', 'inicio_recorrido',
                                        'punto_control', 'novedad', 'fin_recorrido')),
  note            text,
  occurred_at     timestamptz not null,
  recorded_by     uuid not null references public.user_profiles(user_id),
  synced_at       timestamptz not null default now()
);

create index salida_eventos_salida_idx on public.salida_eventos (salida_id, occurred_at);

-- ---------------------------------------------------------------------
-- 4. Helpers de acceso (SECURITY DEFINER: evitan recursión de RLS
--     dentro de las policies; search_path fijado — lección de 0020)
-- ---------------------------------------------------------------------
create or replace function public.guia_in_salida(s uuid)
returns boolean
language sql stable security definer set search_path = public
as $$
  select exists (
    select 1 from salida_guias
     where salida_id = s and guia_user_id = auth.uid());
$$;

create or replace function public.salida_of_participante(p uuid)
returns uuid
language sql stable security definer set search_path = public
as $$
  select salida_id from participantes where id = p;
$$;

-- ---------------------------------------------------------------------
-- 5. Triggers: soft-lock, límites por tier e inmutabilidad
-- ---------------------------------------------------------------------
-- Soft-lock (Regla 3): bloquea CREAR salidas / actividades / asignaciones
-- cuando la suscripción no está activa. Corre también bajo service_role.
create or replace function public.enforce_tenant_writable()
returns trigger
language plpgsql set search_path = public
as $$
begin
  if not public.tenant_is_writable(new.tenant_id) then
    raise exception 'SUBSCRIPTION_LOCKED: suscripción vencida — tenant en solo lectura'
      using errcode = 'P0001';
  end if;
  return new;
end;
$$;

-- Nombre con prefijo 00: los triggers disparan en orden alfabético y el
-- soft-lock debe evaluarse ANTES que los límites de plan (el error correcto
-- para un tenant vencido es SUBSCRIPTION_LOCKED, no PLAN_LIMIT).
create trigger trg_00_writable
  before insert on public.salidas
  for each row execute function public.enforce_tenant_writable();

create trigger trg_00_writable
  before insert on public.activity_profiles
  for each row execute function public.enforce_tenant_writable();

create trigger trg_00_writable
  before insert on public.salida_guias
  for each row execute function public.enforce_tenant_writable();

-- Regla 2: máximo de actividades ACTIVAS según el plan efectivo.
create or replace function public.enforce_activity_limit()
returns trigger
language plpgsql set search_path = public
as $$
declare
  v_plan  text;
  v_limit int;
  v_count int;
begin
  if tg_op = 'UPDATE' and (old.is_active or not new.is_active) then
    return new;  -- solo valida activaciones nuevas
  end if;
  -- Serializa por tenant: evita pasar el límite con inserts concurrentes.
  perform pg_advisory_xact_lock(hashtext('activity_limit:' || new.tenant_id::text));
  v_plan := public.tenant_effective_plan(new.tenant_id);
  select max_active_activities into v_limit from plan_limits where plan = v_plan;
  if v_limit is null then
    return new;  -- empresarial: ilimitado
  end if;
  select count(*) into v_count
    from activity_profiles
   where tenant_id = new.tenant_id
     and is_active
     and id is distinct from new.id;
  if v_count >= v_limit then
    raise exception 'PLAN_LIMIT: máximo % actividades activas en el plan %', v_limit, v_plan
      using errcode = 'P0001';
  end if;
  return new;
end;
$$;

create trigger trg_activity_limit
  before insert or update of is_active on public.activity_profiles
  for each row when (new.is_active) execute function public.enforce_activity_limit();

-- Regla 2: máximo de cuentas con rol guía según el plan efectivo.
-- (También aplica el soft-lock: con suscripción vencida no se agregan guías.)
create or replace function public.enforce_guia_limit()
returns trigger
language plpgsql set search_path = public
as $$
declare
  v_plan  text;
  v_limit int;
  v_count int;
begin
  if new.role <> 'guia' then
    return new;
  end if;
  if tg_op = 'UPDATE' and old.role = 'guia' then
    return new;  -- ya contaba como guía
  end if;
  if not public.tenant_is_writable(new.tenant_id) then
    raise exception 'SUBSCRIPTION_LOCKED: suscripción vencida — no se pueden agregar guías'
      using errcode = 'P0001';
  end if;
  perform pg_advisory_xact_lock(hashtext('guia_limit:' || new.tenant_id::text));
  v_plan := public.tenant_effective_plan(new.tenant_id);
  select max_guias into v_limit from plan_limits where plan = v_plan;
  if v_limit is null then
    return new;
  end if;
  select count(*) into v_count
    from user_profiles
   where tenant_id = new.tenant_id
     and role = 'guia'
     and user_id is distinct from new.user_id;
  if v_count >= v_limit then
    raise exception 'PLAN_LIMIT: máximo % cuentas de guía en el plan %', v_limit, v_plan
      using errcode = 'P0001';
  end if;
  return new;
end;
$$;

create trigger trg_guia_limit
  before insert or update of role on public.user_profiles
  for each row execute function public.enforce_guia_limit();

-- consentimientos: inmutable para TODOS, incluido service_role.
create or replace function public.block_mutation()
returns trigger
language plpgsql set search_path = public
as $$
begin
  raise exception 'INMUTABLE: % no admite % (evidencia legal)', tg_table_name, tg_op
    using errcode = 'P0001';
end;
$$;

create trigger trg_consentimientos_immutable
  before update or delete on public.consentimientos
  for each row execute function public.block_mutation();

-- updated_at de activity_profiles.
create or replace function public.set_updated_at()
returns trigger
language plpgsql set search_path = public
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create trigger trg_activity_profiles_updated_at
  before update on public.activity_profiles
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------
-- 6. RLS. Matriz: gerente/coordinador gestionan; recepcionista lee sin
--    datos de salud; guía solo SUS salidas. El turista no tiene rol: entra
--    por el endpoint público (service_role tras validar el token del QR).
-- ---------------------------------------------------------------------
alter table public.plan_limits        enable row level security;
alter table public.activity_profiles  enable row level security;
alter table public.salidas            enable row level security;
alter table public.salida_guias       enable row level security;
alter table public.participantes      enable row level security;
alter table public.participante_salud enable row level security;
alter table public.consent_templates  enable row level security;
alter table public.consentimientos    enable row level security;
alter table public.salida_eventos     enable row level security;

-- plan_limits: catálogo global de solo lectura (escritura: service_role).
create policy "read_for_authenticated" on public.plan_limits
  for select to authenticated using (true);

-- activity_profiles
create policy "tenant_read" on public.activity_profiles
  for select to authenticated
  using (tenant_id = public.current_tenant_id());

create policy "gc_insert" on public.activity_profiles
  for insert to authenticated
  with check (tenant_id = public.current_tenant_id()
              and public.current_user_role() in ('gerente', 'coordinador')
              and public.tenant_is_writable(tenant_id));

create policy "gc_update" on public.activity_profiles
  for update to authenticated
  using (tenant_id = public.current_tenant_id()
         and public.current_user_role() in ('gerente', 'coordinador')
         and public.tenant_is_writable(tenant_id))
  with check (tenant_id = public.current_tenant_id());

-- salidas: administrativos ven todas; el guía solo las suyas.
create policy "staff_read" on public.salidas
  for select to authenticated
  using (tenant_id = public.current_tenant_id()
         and (public.current_user_role() in ('gerente', 'coordinador', 'recepcionista')
              or public.guia_in_salida(id)));

create policy "gc_insert" on public.salidas
  for insert to authenticated
  with check (tenant_id = public.current_tenant_id()
              and public.current_user_role() in ('gerente', 'coordinador')
              and public.tenant_is_writable(tenant_id));

-- Regla 3: la gestión administrativa exige suscripción activa, pero el
-- guía asignado SIEMPRE puede actualizar su salida (iniciar/finalizar):
-- las salidas en curso no se interrumpen por un vencimiento.
create policy "gc_update" on public.salidas
  for update to authenticated
  using (tenant_id = public.current_tenant_id()
         and public.current_user_role() in ('gerente', 'coordinador')
         and public.tenant_is_writable(tenant_id))
  with check (tenant_id = public.current_tenant_id());

create policy "guia_update" on public.salidas
  for update to authenticated
  using (tenant_id = public.current_tenant_id() and public.guia_in_salida(id))
  with check (tenant_id = public.current_tenant_id());

-- salida_guias
create policy "tenant_read" on public.salida_guias
  for select to authenticated
  using (tenant_id = public.current_tenant_id());

create policy "gc_insert" on public.salida_guias
  for insert to authenticated
  with check (tenant_id = public.current_tenant_id()
              and public.current_user_role() in ('gerente', 'coordinador')
              and public.tenant_is_writable(tenant_id));

create policy "gc_delete" on public.salida_guias
  for delete to authenticated
  using (tenant_id = public.current_tenant_id()
         and public.current_user_role() in ('gerente', 'coordinador'));

-- participantes: identidad + flag de alerta (sin detalle de salud).
create policy "staff_read" on public.participantes
  for select to authenticated
  using (tenant_id = public.current_tenant_id()
         and (public.current_user_role() in ('gerente', 'coordinador', 'recepcionista')
              or public.guia_in_salida(salida_id)));

create policy "gc_update" on public.participantes
  for update to authenticated
  using (tenant_id = public.current_tenant_id()
         and public.current_user_role() in ('gerente', 'coordinador'))
  with check (tenant_id = public.current_tenant_id());
-- INSERT: sin policy — solo el endpoint público vía service_role.

-- participante_salud: gerente/coordinador, y el guía SOLO de sus salidas.
-- Recepcionista NO (minimización, Ley 1581/2012).
create policy "restricted_read" on public.participante_salud
  for select to authenticated
  using (tenant_id = public.current_tenant_id()
         and (public.current_user_role() in ('gerente', 'coordinador')
              or public.guia_in_salida(public.salida_of_participante(participante_id))));
-- INSERT/UPDATE: sin policy — solo service_role (flujo del turista).

-- consent_templates: versiones inmutables; nueva versión = nueva fila.
create policy "tenant_read" on public.consent_templates
  for select to authenticated
  using (tenant_id = public.current_tenant_id());

create policy "gerente_insert" on public.consent_templates
  for insert to authenticated
  with check (tenant_id = public.current_tenant_id()
              and public.current_user_role() = 'gerente'
              and public.tenant_is_writable(tenant_id));

-- consentimientos: evidencia. Lectura de gestión + guía de la salida.
create policy "restricted_read" on public.consentimientos
  for select to authenticated
  using (tenant_id = public.current_tenant_id()
         and (public.current_user_role() in ('gerente', 'coordinador')
              or public.guia_in_salida(public.salida_of_participante(participante_id))));
-- INSERT: solo service_role. UPDATE/DELETE: bloqueados por trigger.

-- salida_eventos: escribe el guía asignado (SIN exigir suscripción activa:
-- la operación en terreno nunca se bloquea) y también gerente/coordinador.
create policy "staff_read" on public.salida_eventos
  for select to authenticated
  using (tenant_id = public.current_tenant_id()
         and (public.current_user_role() in ('gerente', 'coordinador', 'recepcionista')
              or public.guia_in_salida(salida_id)));

create policy "field_insert" on public.salida_eventos
  for insert to authenticated
  with check (tenant_id = public.current_tenant_id()
              and recorded_by = auth.uid()
              and (public.guia_in_salida(salida_id)
                   or public.current_user_role() in ('gerente', 'coordinador')));
-- UPDATE/DELETE: sin policies — el log es append-only para authenticated.
