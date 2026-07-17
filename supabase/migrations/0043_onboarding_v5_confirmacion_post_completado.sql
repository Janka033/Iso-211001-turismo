-- =====================================================================
-- 0043 · onboarding v5: confirmación de correcciones con el onboarding
-- ya completo. La regla 7 de v4 obligaba a la IA a devolver
-- next_question=null cuando no quedaban pendientes, lo que se tragaba
-- las confirmaciones de correcciones tardías y de valores sospechosos
-- (detectado en prueba en vivo 2026-07-17: el cliente corregía y la
-- respuesta salía vacía). Ahora, sin pendientes, next_question lleva
-- SOLO la confirmación (si la hubo); el backend además pone un acuse
-- determinista si la IA no dio texto (onboarding/service.py).
-- v5 = v4 con la regla 7 reescrita (replace quirúrgico, mismo prompt).
-- =====================================================================

-- El índice parcial idx_prompt_versions_one_active exige desactivar ANTES
-- de insertar el nuevo activo.
update public.prompt_versions
set is_active = false
where module = 'onboarding';

insert into public.prompt_versions (module, document_type, version, content, is_active)
select
  'onboarding',
  null,
  'v5',
  replace(
    content,
    $old$queda ninguno, "next_field_key": null, "next_question": null,
   "completed": true.$old$,
    $new$queda ninguno: "next_field_key": null y "completed": true; en ese caso
   "next_question" NO es una pregunta nueva: si hubo corrección (regla 8) o
   valor sospechoso (regla 9), lleva SOLO esa confirmación; si no, null.$new$
  ),
  true
from public.prompt_versions
where module = 'onboarding' and version = 'v4';

-- Guarda: el replace debe haber cambiado el texto (si no, la migración
-- habría clonado v4 silenciosamente).
do $$
begin
  if exists (
    select 1 from public.prompt_versions
    where module = 'onboarding' and version = 'v5'
      and content like '%"next_question": null,%"completed": true.%'
  ) then
    raise exception 'replace de la regla 7 no aplicó: revisar el texto ancla';
  end if;
end $$;
