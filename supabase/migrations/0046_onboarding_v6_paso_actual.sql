-- =====================================================================
-- 0046 · onboarding v6: el prompt recibe el PASO ACTUAL de la ruta
-- guiada (<<CURRENT_STEP>>, Fase 2) y la IA lo anuncia al preguntar
-- ("Paso 4 de 15 — Política de seguridad: …"), estilo ruta Duolingo.
-- v6 = v5 con dos replaces quirúrgicos: la tarea 3 gana la instrucción
-- de anunciar el paso y se inserta la sección del marcador antes de
-- ACTIVIDADES. Sin ruta configurada el marcador dice "(ruta guiada no
-- configurada; flujo lineal)" y la instrucción no aplica.
-- =====================================================================

update public.prompt_versions
set is_active = false
where module = 'onboarding';

insert into public.prompt_versions (module, document_type, version, content, is_active)
select
  'onboarding',
  null,
  'v6',
  replace(
    replace(
      content,
      $old$3. REDACTAR la siguiente pregunta, en español de Colombia, tono cercano y claro.$old$,
      $new$3. REDACTAR la siguiente pregunta, en español de Colombia, tono cercano y claro.
   Si "PASO ACTUAL DE LA RUTA" indica un documento, ANÚNCIALO al preguntar de
   forma natural y breve ("Paso 4 de 15 — Política de seguridad: …"); si el
   turno completó los campos de ese paso, celébralo en una frase corta antes
   de pasar al siguiente. En el paso 0 (identidad) no menciones documentos.$new$
    ),
    $old2$=== ACTIVIDADES ELEGIDAS POR LA EMPRESA ===$old2$,
    $new2$=== PASO ACTUAL DE LA RUTA (anúncialo al preguntar) ===
<<CURRENT_STEP>>

=== ACTIVIDADES ELEGIDAS POR LA EMPRESA ===$new2$
  ),
  true
from public.prompt_versions
where module = 'onboarding' and version = 'v5';

-- Guarda: v6 debe contener el marcador nuevo (si no, el replace no aplicó).
do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'onboarding' and version = 'v6'
      and content like '%<<CURRENT_STEP>>%'
      and content like '%ANÚNCIALO al preguntar%'
  ) then
    raise exception 'replace de v6 no aplicó: revisar los textos ancla';
  end if;
end $$;
