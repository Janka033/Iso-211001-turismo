-- =====================================================================
-- Amplía los sources de la base de conocimiento con 'capacitaciones':
-- transcripciones de los videos de capacitación/auditoría, fragmentadas
-- por tema y sembradas por scripts/seed_trainings.py.
--
-- knowledge_chunks NO es dato de tenant: es la base compartida que
-- gestiona superadmin. Sus políticas RLS existentes no cambian; solo se
-- permite el nuevo valor de source.
-- =====================================================================

alter table public.knowledge_chunks
  drop constraint knowledge_chunks_source_check;

alter table public.knowledge_chunks
  add constraint knowledge_chunks_source_check
  check (source in ('norma', 'acotur', 'capacitaciones'));

comment on column public.knowledge_chunks.source is
  'Origen del chunk: norma (NTC-ISO 21101), acotur (Módulo 2, evidencias '
  'por numeral) o capacitaciones (transcripciones de videos).';
