-- =====================================================================
-- 0051 · Matriz de objetivos de seguridad (6.2): generador 4/8 de la
-- ruta guiada (Fase 4). Sin preguntas nuevas de onboarding: su insumo
-- (safety_objectives + management_commitment) se captura en el paso de
-- la política. El bloque de planificación del molde MinCIT es fijo de
-- la plantilla; resultado/análisis son del seguimiento.
--
-- 1) prompt de extracción v1 (module=generation, marcadores <<...>>)
-- 2) extraction_checklist del documento
-- 3) document_roadmap: el paso queda generator_ready
-- =====================================================================

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'matriz_objetivos_seguridad',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (sistema de gestión de
seguridad para turismo de aventura). Tu trabajo NO es redactar el documento
final, sino EXTRAER y ESTRUCTURAR las variables que alimentan una plantilla fija.

OBJETIVO: construir las filas de la MATRIZ DE OBJETIVOS DE SEGURIDAD (numeral
6.2) a partir EXCLUSIVAMENTE de los objetivos reales del cliente. El bloque de
planificación del molde y las columnas de seguimiento son fijos de la
plantilla: tú SOLO aportas la política marco y las filas de objetivos.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema indicado abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto de la empresa, deja
   ese campo en null (o lista vacía). El sistema lo marcará como [PENDIENTE].
3. No redactes prosa libre fuera de los campos del schema.
4. Usa un tono formal, institucional y en español de Colombia.
5. "objectives": UNA fila por cada objetivo de seguridad REAL del cliente
   (campo safety_objectives del contexto y el objetivo medible de la
   dirección si existe). PROHIBIDO crear objetivos que el cliente no declaró
   y PROHIBIDO omitir alguno de los declarados.
6. Por cada fila, DESCOMPÓN el enunciado del cliente: "indicator_name" (nombre
   corto del indicador), "formula" (cálculo del indicador si se puede derivar
   del enunciado sin inventar), "frequency" (solo si el cliente la dio o el
   plazo la implica), "goal" (meta numérica y plazo tal como los dio). Lo que
   no se pueda derivar sin inventar => null.
7. "origin": asigna a cada objetivo UNO de los orígenes del kit: 'Contexto',
   'Política de seguridad de turismo de aventura', 'Riesgos y oportunidades',
   'Gestión del riesgo de actividad de <actividad>' (usa la actividad real) o
   'Requisitos del cliente', según el contenido del objetivo.
8. "responsible": SOLO si el cliente lo dijo o es evidente del organigrama
   (p. ej. el gerente). En caso contrario => null.
9. "policy_statement": enunciado breve de la política que enmarca los
   objetivos. DERÍVALO del compromiso de la dirección real del cliente.
10. El contexto puede contener objetivos ETIQUETADOS PARA OTROS DOCUMENTOS
    (p. ej. "Manual … (MA-03) — objetivo definido por el cliente: …").
    NUNCA los uses como objetivos de seguridad de esta matriz.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 6.2 y política 5.2) ===
<<NORM_CONTEXT>>

=== CAMPOS REQUERIDOS (checklist de extracción) ===
<<CHECKLIST>>

=== PATRONES DE RECHAZO/APROBACIÓN DE AUDITORES (evítalos/aplícalos) ===
<<PATTERNS>>

=== SCHEMA JSON DE SALIDA (cúmplelo exactamente) ===
<<JSON_SCHEMA>>

Responde solo con el JSON.$prompt$,
  true
);

insert into public.extraction_checklist (document_type, numeral, field_key, description, required)
values
  ('matriz_objetivos_seguridad', '6.2', 'company_name',     'Razón social de la empresa', true),
  ('matriz_objetivos_seguridad', '6.2', 'policy_statement', 'Política de seguridad que enmarca los objetivos', true),
  ('matriz_objetivos_seguridad', '6.2', 'objectives',       'Objetivos de seguridad con indicador, meta y responsable', true);

-- El paso de la ruta ya tiene generador: se enciende como DATO.
update public.document_roadmap
set generator_ready = true
where document_type = 'matriz_objetivos_seguridad';

-- Guardas: prompt activo con marcadores + paso encendido.
do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'generation' and document_type = 'matriz_objetivos_seguridad'
      and version = 'v1' and is_active
      and content like '%<<JSON_SCHEMA>>%' and content like '%<<COMPANY_CONTEXT>>%'
  ) then
    raise exception 'prompt matriz_objetivos_seguridad v1 no quedó activo o sin marcadores';
  end if;
  if not exists (
    select 1 from public.document_roadmap
    where document_type = 'matriz_objetivos_seguridad' and generator_ready
  ) then
    raise exception 'document_roadmap: matriz_objetivos_seguridad no quedó generator_ready';
  end if;
end $$;
