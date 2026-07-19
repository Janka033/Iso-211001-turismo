-- =====================================================================
-- 0058 · onboarding v9: manejar "no tengo / no aplica" sin bucle.
-- Bug hallado por Jan en uso real (2026-07-18): respondió "no tengo" a
-- los cargos del equipo y la IA repreguntó lo mismo una y otra vez (el
-- campo quedaba pendiente sin forma de resolverlo). v9 = v8 + regla:
-- esas respuestas van a "not_applicable_fields" (nuevo en el schema);
-- el backend marca el campo resuelto y avanza.
-- =====================================================================

update public.prompt_versions
set is_active = false
where module = 'onboarding';

insert into public.prompt_versions (module, document_type, version, content, is_active)
select
  'onboarding',
  null,
  'v9',
  replace(
    content,
    $old$inclúyelo en "extracted" con el field_key de
   ese dato (búscalo en DATOS YA CAPTURADOS) y el valor NUEVO completo.$old$,
    $new$inclúyelo en "extracted" con el field_key de
   ese dato (búscalo en DATOS YA CAPTURADOS) y el valor NUEVO completo.
2b. CAMPOS QUE EL CLIENTE NO TIENE O NO APLICAN: si el cliente responde que NO
   tiene el dato preguntado, que NO aplica, que no lo maneja, que no cuenta con
   eso, o pide QUITAR uno ya dado ("no tengo", "no aplica", "ninguno", "no
   manejo eso", "no contamos con", "quítalo", "ya no"), pon su field_key en
   "not_applicable_fields" (NUNCA lo dejes pendiente ni lo pongas vacío en
   "extracted"). "next_field_key" debe ser el SIGUIENTE campo, no ese. Si el
   cliente MÁS ADELANTE sí da ese dato, extráelo normal (deja de ser no aplica).
   OJO: "no tengo equipo/empleados" o "solo yo" => "staff_roles" en
   not_applicable_fields (NO inventes cargos).$new$
  ),
  true
from public.prompt_versions
where module = 'onboarding' and version = 'v8';

-- Guarda: v9 activo con la regla nueva y los marcadores intactos.
do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'onboarding' and version = 'v9' and is_active
      and content like '%not_applicable_fields%'
      and content like '%<<CURRENT_STEP>>%'
  ) then
    raise exception 'replace de v9 no aplicó: revisar el texto ancla de la tarea 2';
  end if;
end $$;
