-- =====================================================================
-- Evita versiones duplicadas de un mismo documento por tenant. Si dos
-- generaciones concurrentes calculan el mismo next_version, la segunda
-- inserción falla en vez de crear un duplicado silencioso.
-- =====================================================================

alter table public.documents
  add constraint documents_tenant_type_version_unique
  unique (tenant_id, document_type, version);
