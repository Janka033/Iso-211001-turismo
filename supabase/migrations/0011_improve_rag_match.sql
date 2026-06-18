-- =====================================================================
-- Mejora del RAG: el filtro por numeral ya no es un AND duro que puede
-- devolver vacío.
--
--   * Coincide con el numeral exacto, sus DESCENDIENTES (6.1.1.x) y sus
--     ANCESTROS (6.1, 6) — la cláusula de la norma suele estar en el padre.
--   * Si aun así no hay filas, cae a búsqueda por similitud SIN filtro de
--     numeral (mejor traer algo relevante que nada).
--
-- Pasa a plpgsql para poder hacer el fallback en una sola función.
-- =====================================================================

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
language plpgsql
stable
as $$
begin
  return query
  select
    kc.id, kc.source, kc.numeral, kc.content, kc.metadata,
    1 - (kc.embedding <=> query_embedding) as similarity
  from public.knowledge_chunks kc
  where kc.embedding is not null
    and (filter_source is null or kc.source = filter_source)
    and (
      filter_numeral is null
      or kc.numeral = filter_numeral
      or kc.numeral like filter_numeral || '.%'   -- descendientes del numeral
      or filter_numeral like kc.numeral || '.%'   -- ancestros del numeral
    )
  order by kc.embedding <=> query_embedding
  limit greatest(match_count, 1);

  -- Fallback: si el filtro de numeral no devolvió nada, similitud sin numeral.
  if not found then
    return query
    select
      kc.id, kc.source, kc.numeral, kc.content, kc.metadata,
      1 - (kc.embedding <=> query_embedding) as similarity
    from public.knowledge_chunks kc
    where kc.embedding is not null
      and (filter_source is null or kc.source = filter_source)
    order by kc.embedding <=> query_embedding
    limit greatest(match_count, 1);
  end if;
end;
$$;

grant execute on function public.match_knowledge_chunks(
  extensions.vector, int, text, text
) to authenticated, service_role;
