-- =====================================================================
-- Schema núcleo del MVP (Semana 1).
-- 11 tablas de CLAUDE.md + user_profiles (mapeo usuario→tenant).
--
-- Clasificación:
--   * tenant-scoped  -> llevan tenant_id; RLS por claim del JWT.
--   * globales       -> datos de producto (norma, plantillas, prompts,
--                       checklist); sin tenant_id, RLS de solo lectura.
-- =====================================================================

-- ---------------------------------------------------------------------
-- Identidad / tenancy
-- ---------------------------------------------------------------------

create table public.tenants (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  created_at  timestamptz not null default now()
);

-- Mapeo usuario -> tenant + rol. Lo lee el custom_access_token_hook para
-- inyectar los claims tenant_id / user_role. Única fuente de verdad.
create table public.user_profiles (
  user_id     uuid primary key references auth.users (id) on delete cascade,
  tenant_id   uuid not null references public.tenants (id) on delete cascade,
  role        text not null default 'empresa'
              check (role in ('empresa', 'admin', 'superadmin')),
  created_at  timestamptz not null default now()
);
create index idx_user_profiles_tenant on public.user_profiles (tenant_id);

-- ---------------------------------------------------------------------
-- Datos del cliente (tenant-scoped)
-- ---------------------------------------------------------------------

create table public.companies (
  id                   uuid primary key default gen_random_uuid(),
  tenant_id            uuid not null references public.tenants (id) on delete cascade,
  name                 text not null,
  nit                  text,
  rnt                  text,                 -- Registro Nacional de Turismo
  legal_representative text,
  contact_email        text,
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now()
);
create index idx_companies_tenant on public.companies (tenant_id);

-- Datos crudos del cliente (lo que dijo). NUNCA se mezcla con ai_outputs.
create table public.onboarding_data (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   uuid not null references public.tenants (id) on delete cascade,
  data        jsonb not null default '{}'::jsonb,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index idx_onboarding_tenant on public.onboarding_data (tenant_id);

-- Derivados de la IA (lo que interpretó). Separado de onboarding_data
-- para poder regenerar sin perder datos del cliente.
create table public.ai_outputs (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   uuid not null references public.tenants (id) on delete cascade,
  data        jsonb not null default '{}'::jsonb,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index idx_ai_outputs_tenant on public.ai_outputs (tenant_id);

create table public.document_status (
  id            uuid primary key default gen_random_uuid(),
  tenant_id     uuid not null references public.tenants (id) on delete cascade,
  document_type text not null,
  status        text not null default 'pending'
                check (status in ('pending', 'generating', 'generated', 'approved', 'rejected')),
  completeness  numeric(5, 2),       -- % de campos disponibles
  updated_at    timestamptz not null default now(),
  unique (tenant_id, document_type)
);
create index idx_document_status_tenant on public.document_status (tenant_id);

-- Documento generado + snapshot completo de reproducibilidad.
create table public.documents (
  id                 uuid primary key default gen_random_uuid(),
  tenant_id          uuid not null references public.tenants (id) on delete cascade,
  document_type      text not null,
  storage_path       text,                       -- ruta en Supabase Storage
  version            int not null default 1,
  -- snapshot de reproducibilidad
  prompt_hash        text,
  prompt_version     text,
  rag_chunks_ids     uuid[] not null default '{}',
  template_version   text,
  model_version      text,
  variables_snapshot jsonb not null default '{}'::jsonb,
  created_at         timestamptz not null default now()
);
create index idx_documents_tenant on public.documents (tenant_id);

create table public.chat_messages (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   uuid not null references public.tenants (id) on delete cascade,
  role        text not null check (role in ('user', 'assistant', 'system')),
  content     text not null,
  created_at  timestamptz not null default now()
);
create index idx_chat_messages_tenant on public.chat_messages (tenant_id, created_at);

-- ---------------------------------------------------------------------
-- Datos de producto (globales, sin tenant_id)
-- ---------------------------------------------------------------------

-- Base de conocimiento vectorizada (norma + ACOTUR). pgvector.
create table public.knowledge_chunks (
  id           uuid primary key default gen_random_uuid(),
  source       text not null check (source in ('norma', 'acotur')),
  numeral      text,
  content      text not null,
  chunk_index  int not null default 0,
  embedding    extensions.vector(768),     -- Gemini text-embedding-004
  metadata     jsonb not null default '{}'::jsonb,  -- p.ej. requisito/evidencias (acotur)
  created_at   timestamptz not null default now(),
  unique (source, numeral, chunk_index)    -- upsert idempotente del seed
);
-- Índice vectorial (cosine). Con poco dato no se nota, pero la migración
-- queda correcta desde ya.
create index idx_knowledge_chunks_embedding
  on public.knowledge_chunks
  using hnsw (embedding extensions.vector_cosine_ops);
create index idx_knowledge_chunks_numeral on public.knowledge_chunks (source, numeral);

-- Checklist de extracción: qué campos requiere cada documento/numeral.
-- Datos, no código (regla de oro 3).
create table public.extraction_checklist (
  id            uuid primary key default gen_random_uuid(),
  document_type text not null,
  numeral       text,
  field_key     text not null,
  description   text,
  required      boolean not null default true,
  created_at    timestamptz not null default now(),
  unique (document_type, field_key)
);

-- Plantillas .docx/.xlsx (solo una activa por tipo de documento).
create table public.templates (
  id            uuid primary key default gen_random_uuid(),
  document_type text not null,
  version       text not null,
  storage_path  text not null,
  engine        text not null check (engine in ('docx', 'xlsx')),
  is_active     boolean not null default false,
  created_at    timestamptz not null default now()
);
create unique index idx_templates_one_active
  on public.templates (document_type) where is_active;

-- Prompts versionados (solo uno activo por módulo+tipo). Datos, no código.
create table public.prompt_versions (
  id            uuid primary key default gen_random_uuid(),
  module        text not null,
  document_type text,
  version       text not null,
  content       text not null,
  is_active     boolean not null default false,
  created_at    timestamptz not null default now()
);
create unique index idx_prompt_versions_one_active
  on public.prompt_versions (module, coalesce(document_type, '')) where is_active;
