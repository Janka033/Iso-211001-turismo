-- =====================================================================
-- 0059 · onboarding v10: la IA deja de anunciar el NÚMERO de paso.
-- Bug cosmético hallado por Jan en uso real: en el turno que cambia de
-- paso (p. ej. al cerrar la identidad y entrar al paso 1) la IA anuncia
-- "Paso 0", porque el marcador <<CURRENT_STEP>> se arma con el estado
-- PREVIO a extraer la respuesta del turno. El contador correcto ya lo
-- muestra la barra del frontend (Fase 3, a partir de current_step =
-- step_after). v10 = v9 revirtiendo la locución numérica que añadió v6:
-- la IA puede nombrar el TEMA del documento, pero nunca el contador.
-- =====================================================================

update public.prompt_versions
set is_active = false
where module = 'onboarding';

insert into public.prompt_versions (module, document_type, version, content, is_active)
select
  'onboarding',
  null,
  'v10',
  replace(
    replace(
      content,
      $old$3. REDACTAR la siguiente pregunta, en español de Colombia, tono cercano y claro.
   Si "PASO ACTUAL DE LA RUTA" indica un documento, ANÚNCIALO al preguntar de
   forma natural y breve ("Paso 4 de 15 — Política de seguridad: …"); si el
   turno completó los campos de ese paso, celébralo en una frase corta antes
   de pasar al siguiente. En el paso 0 (identidad) no menciones documentos.$old$,
      $new$3. REDACTAR la siguiente pregunta, en español de Colombia, tono cercano y claro.
   NO anuncies el NÚMERO de paso ("Paso 4 de 15", ni "Paso 0"): la interfaz ya
   le muestra al cliente en qué paso va con el número correcto, y repetirlo aquí
   sale DESFASADO justo en el turno que cambia de paso. Puedes nombrar el TEMA
   del documento en curso de forma natural cuando ayude ("Ahora, para tu política
   de seguridad, …"), pero SIN el contador de pasos. Si el turno completó los
   campos del paso actual, celébralo en una frase corta antes de la siguiente
   pregunta. En el paso 0 (identidad) no menciones documentos.$new$
    ),
    $old2$=== PASO ACTUAL DE LA RUTA (anúncialo al preguntar) ===$old2$,
    $new2$=== PASO ACTUAL DE LA RUTA (contexto interno; NO lo anuncies con número) ===$new2$
  ),
  true
from public.prompt_versions
where module = 'onboarding' and version = 'v9';

-- Guarda: v10 activo, con el marcador intacto, con la regla nueva y SIN la
-- vieja instrucción de anunciar el paso (si algún ancla no aplicó, aborta).
do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'onboarding' and version = 'v10' and is_active
      and content like '%<<CURRENT_STEP>>%'
      and content like '%NO anuncies el NÚMERO de paso%'
      and content not like '%ANÚNCIALO al preguntar%'
  ) then
    raise exception 'replace de v10 no aplicó: revisar los textos ancla de la tarea 3 / marcador';
  end if;
end $$;
