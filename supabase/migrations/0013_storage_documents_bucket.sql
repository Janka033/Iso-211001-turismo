-- =====================================================================
-- Bucket privado de documentos generados + RLS de Storage por tenant.
--
-- La ruta de cada archivo es `{tenant_id}/{document_type}/v{n}.{ext}`, así
-- que la PRIMERA carpeta del path es el tenant_id. Las policies exigen que
-- coincida con el claim tenant_id del JWT: un tenant nunca ve archivos de
-- otro, ni siquiera con una URL firmada de la ruta ajena.
--
-- Requiere el esquema `storage` de Supabase (no aplica en un Postgres pelado).
-- =====================================================================

insert into storage.buckets (id, name, public)
values ('documents', 'documents', false)
on conflict (id) do nothing;

create policy "tenant_docs_select" on storage.objects
  for select to authenticated
  using (
    bucket_id = 'documents'
    and (storage.foldername(name))[1] = public.current_tenant_id()::text
  );

create policy "tenant_docs_insert" on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'documents'
    and (storage.foldername(name))[1] = public.current_tenant_id()::text
  );

create policy "tenant_docs_update" on storage.objects
  for update to authenticated
  using (
    bucket_id = 'documents'
    and (storage.foldername(name))[1] = public.current_tenant_id()::text
  )
  with check (
    bucket_id = 'documents'
    and (storage.foldername(name))[1] = public.current_tenant_id()::text
  );

create policy "tenant_docs_delete" on storage.objects
  for delete to authenticated
  using (
    bucket_id = 'documents'
    and (storage.foldername(name))[1] = public.current_tenant_id()::text
  );
