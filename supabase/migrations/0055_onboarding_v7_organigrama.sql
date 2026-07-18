-- =====================================================================
-- 0055 · onboarding v7: correcciones al organigrama sin cargos sinónimos.
-- Bug hallado en la revisión en vivo (2026-07-18): "ya no tenemos 4
-- guias sino 5" creó un cargo NUEVO 'guias: 5' junto al existente
-- 'guias certificados: 4' (el merge conserva ambos => organigrama con 9
-- guías) y certified_guides quedó sin actualizar. v7 = v6 con la regla
-- 5 reforzada: reutilizar el nombre de cargo YA CAPTURADO y sincronizar
-- certified_guides cuando la corrección cambia el número de guías.
-- =====================================================================

update public.prompt_versions
set is_active = false
where module = 'onboarding';

insert into public.prompt_versions (module, document_type, version, content, is_active)
select
  'onboarding',
  null,
  'v7',
  replace(
    content,
    $old$5. CORRECCIONES AL ORGANIGRAMA (staff_roles): van por su campo dedicado
   "staff_roles" del schema, NUNCA por "extracted". Devuelve cada cargo
   mencionado con su número NUEVO; para ELIMINAR un cargo devuélvelo con valor
   "0". Los cargos que no menciones se conservan como están.$old$,
    $new$5. CORRECCIONES AL ORGANIGRAMA (staff_roles): van por su campo dedicado
   "staff_roles" del schema, NUNCA por "extracted". Devuelve cada cargo
   mencionado con su número NUEVO; para ELIMINAR un cargo devuélvelo con valor
   "0". Los cargos que no menciones se conservan como están.
   USA EXACTAMENTE el nombre de cargo que YA exista en DATOS YA CAPTURADOS
   cuando el cliente se refiera al mismo cargo aunque lo nombre distinto
   ('guías', 'los guías certificados' y 'guía' son EL MISMO cargo): el sistema
   fusiona por nombre y un sinónimo crearía un cargo duplicado con doble
   conteo. PROHIBIDO crear un cargo nuevo si ya existe uno equivalente.
   Si la corrección cambia el número de guías, incluye TAMBIÉN
   "certified_guides" con el número nuevo en "extracted".$new$
  ),
  true
from public.prompt_versions
where module = 'onboarding' and version = 'v6';

-- Guarda: v7 activo con la regla nueva y los marcadores intactos.
do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'onboarding' and version = 'v7' and is_active
      and content like '%PROHIBIDO crear un cargo nuevo si ya existe uno equivalente%'
      and content like '%<<CURRENT_STEP>>%'
  ) then
    raise exception 'replace de v7 no aplicó: revisar el texto ancla de la regla 5';
  end if;
end $$;
