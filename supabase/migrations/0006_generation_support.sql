-- =====================================================================
-- Soporte para el módulo de generación documental.
--
--   1. match_knowledge_chunks(): búsqueda semántica (pgvector) sobre la
--      base de conocimiento. Es el paso RAG del flujo de generación.
--   2. generation_patterns: patrones reales de rechazo/aprobación de
--      auditores. Datos de PRODUCTO (globales, sin tenant_id): alimentan
--      el contexto de la IA para evitar errores ya conocidos.
-- =====================================================================

-- ---------------------------------------------------------------------
-- RAG: top-K chunks por similitud de coseno, opcionalmente filtrando
-- por numeral y/o fuente. SECURITY INVOKER (default): corre con el rol
-- del llamante, así que la policy read_for_authenticated de
-- knowledge_chunks sigue aplicando. No expone datos de ningún tenant
-- (la base de conocimiento es global).
-- ---------------------------------------------------------------------
create or replace function public.match_knowledge_chunks(
  query_embedding extensions.vector(768),
  match_count     int     default 5,
  filter_source   text    default null,
  filter_numeral  text    default null
)
returns table (
  id          uuid,
  source      text,
  numeral     text,
  content     text,
  metadata    jsonb,
  similarity  float
)
language sql
stable
as $$
  select
    kc.id,
    kc.source,
    kc.numeral,
    kc.content,
    kc.metadata,
    1 - (kc.embedding <=> query_embedding) as similarity
  from public.knowledge_chunks kc
  where kc.embedding is not null
    and (filter_source  is null or kc.source  = filter_source)
    and (filter_numeral is null or kc.numeral = filter_numeral
         or kc.numeral like filter_numeral || '.%')
  order by kc.embedding <=> query_embedding
  limit greatest(match_count, 1);
$$;

-- authenticated puede ejecutar el RPC (la generación corre con su JWT).
grant execute on function public.match_knowledge_chunks(
  extensions.vector, int, text, text
) to authenticated, service_role;

-- ---------------------------------------------------------------------
-- generation_patterns (global): aprendizaje de auditoría compartido.
-- ---------------------------------------------------------------------
create table public.generation_patterns (
  id            uuid primary key default gen_random_uuid(),
  document_type text not null,
  numeral       text,
  pattern_type  text not null default 'rechazo'
                check (pattern_type in ('rechazo', 'aprobacion')),
  description   text not null,
  created_at    timestamptz not null default now()
);
create index idx_generation_patterns_doc on public.generation_patterns (document_type);

alter table public.generation_patterns enable row level security;

-- Lectura para cualquier autenticado (la generación los inyecta al prompt).
-- Escritura: solo service_role (administración/aprendizaje supervisado).
create policy "read_for_authenticated" on public.generation_patterns
  for select to authenticated using (true);
