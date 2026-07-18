-- =====================================================================
-- 0057 · onboarding v8: no repreguntar datos ya capturados.
-- Observación de Jan (2026-07-18): "la IA me pregunta qué actividades
-- presto o dónde opero, si ya lo di". La causa principal (la pregunta
-- redundante `scope`) se eliminó en código; esto REFUERZA que la IA no
-- vuelva a pedir por su cuenta datos ya presentes al entrar a un paso.
-- v8 = v7 + regla en la tarea 3.
-- =====================================================================

update public.prompt_versions
set is_active = false
where module = 'onboarding';

insert into public.prompt_versions (module, document_type, version, content, is_active)
select
  'onboarding',
  null,
  'v8',
  replace(
    content,
    $old$de pasar al siguiente. En el paso 0 (identidad) no menciones documentos.$old$,
    $new$de pasar al siguiente. En el paso 0 (identidad) no menciones documentos.
   NUNCA vuelvas a preguntar un dato que YA figura con valor en DATOS YA
   CAPTURADOS. En particular, las ACTIVIDADES, la región (main_region) y las
   UBICACIONES (locations) ya fueron dadas por el cliente: al entrar a un
   documento NO preguntes de nuevo qué actividades presta ni dónde opera;
   úsalos como contexto para redactar la pregunta del campo que SÍ falta.$new$
  ),
  true
from public.prompt_versions
where module = 'onboarding' and version = 'v7';

-- Guarda: v8 activo con la regla nueva y los marcadores intactos.
do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'onboarding' and version = 'v8' and is_active
      and content like '%NUNCA vuelvas a preguntar un dato que YA figura%'
      and content like '%<<CURRENT_STEP>>%'
  ) then
    raise exception 'replace de v8 no aplicó: revisar el texto ancla de la tarea 3';
  end if;
end $$;
