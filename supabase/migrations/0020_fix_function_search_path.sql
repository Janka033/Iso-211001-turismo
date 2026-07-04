-- =====================================================================
-- Advisors WARN: search_path mutable. Se fija para impedir hijacking por
-- objetos homónimos en schemas del atacante. 'extensions' solo donde se
-- usa el tipo/operadores de pgvector.
--
-- NOTA de reconciliación: esta migración ya estaba aplicada en el remoto
-- (version 20260703002043, sin archivo en el repo). Se versiona aquí para
-- que un setup local desde cero quede idéntico. No re-aplicar en remoto.
-- =====================================================================

alter function public.current_tenant_id() set search_path = public;
alter function public.custom_access_token_hook(jsonb) set search_path = public;
alter function public.match_knowledge_chunks(vector, integer, text, text)
  set search_path = public, extensions;
