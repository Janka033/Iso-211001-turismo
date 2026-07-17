-- 0044 · knowledge_chunks acepta la fuente 'guias' (guías MinCIT/FONTUR:
-- implementación, integración, indicadores — seed_knowledge.py --source guias).
alter table public.knowledge_chunks
  drop constraint knowledge_chunks_source_check;
alter table public.knowledge_chunks
  add constraint knowledge_chunks_source_check
  check (source = any (array['norma'::text, 'acotur'::text, 'capacitaciones'::text, 'guias'::text]));
