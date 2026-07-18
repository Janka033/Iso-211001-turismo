-- =====================================================================
-- 0050 · acta_compromiso prompt v2: la fecha del acta SÍ se extrae de
-- management_signer. En el smoke del 0049 el cliente dio "en San Gil el
-- 20 de julio de 2026" dentro de management_signer y el modelo dejó
-- acta_date en null por leer la regla anti-derivación como prohibición
-- total. v2 aclara: management_signer responde EXACTAMENTE quién firma
-- y en qué ciudad y fecha, así que esa ciudad y fecha SON las del acta;
-- lo prohibido sigue siendo derivarla de OTRAS fechas del contexto.
-- =====================================================================

update public.prompt_versions
set is_active = false
where module = 'generation' and document_type = 'acta_compromiso';

insert into public.prompt_versions (module, document_type, version, content, is_active)
select
  'generation',
  'acta_compromiso',
  'v2',
  replace(
    replace(
      content,
      $old$6. "city": ciudad de firma. DERÍVALA del municipio sede de la operación
   (ubicaciones del cliente) si no la dijo explícitamente.
7. "acta_date": SOLO si el cliente indicó la fecha de firma de ESTA acta.
   NUNCA la derives de otras fechas del contexto. Sin fecha => null.$old$,
      $new$6. "city": ciudad de firma. El campo management_signer del contexto responde
   EXACTAMENTE quién firma esta acta y en qué ciudad y fecha: si ahí aparece
   una ciudad, esa ES la ciudad del acta. En su defecto, DERÍVALA del
   municipio sede de la operación (ubicaciones del cliente).
7. "acta_date": la fecha de firma dada por el cliente. Si management_signer
   trae una fecha, esa ES la fecha de esta acta (escríbela como la dio el
   cliente). Lo PROHIBIDO es derivarla de OTRAS fechas del contexto (p. ej.
   la aprobación de la política). Sin fecha en el contexto => null.$new$
    ),
    $old2$4. "signer_name" y "signer_role": quien firma por la alta dirección. DERÍVALOS
   del campo management_signer del cliente o, en su defecto, del representante
   legal / gerente del organigrama.$old2$,
    $new2$4. "signer_name" y "signer_role": quien firma por la alta dirección. DERÍVALOS
   del campo management_signer del cliente o, en su defecto, del representante
   legal / gerente del organigrama. Escribe el cargo con inicial mayúscula
   (p. ej. "Gerente").$new2$
  ),
  true
from public.prompt_versions
where module = 'generation' and document_type = 'acta_compromiso' and version = 'v1';

-- Guarda: v2 activo y con el texto nuevo.
do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'generation' and document_type = 'acta_compromiso'
      and version = 'v2' and is_active
      and content like '%esa ES la fecha de esta acta%'
      and content like '%<<JSON_SCHEMA>>%'
  ) then
    raise exception 'replace de acta v2 no aplicó: revisar los textos ancla';
  end if;
end $$;
