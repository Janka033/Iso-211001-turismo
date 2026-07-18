-- =====================================================================
-- 0054 · Planificación y control operacional (8.1): generador 7/8 de
-- la ruta guiada (Fase 4). Molde del kit MinCIT: una fila por actividad
-- con normas aplicables (nacional/internacional), aspectos a controlar
-- y cómo se controlan. Regla dura: las normas citadas deben venir del
-- contexto (cliente o extractos RAG), NUNCA de memoria del modelo.
--
-- 1) prompt de extracción v1 (module=generation, marcadores <<...>>)
-- 2) extraction_checklist del documento
-- 3) document_roadmap: el paso queda generator_ready
-- =====================================================================

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'control_operacional',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (sistema de gestión de
seguridad para turismo de aventura). Tu trabajo NO es redactar el documento
final, sino EXTRAER y ESTRUCTURAR las variables que alimentan una plantilla fija.

OBJETIVO: construir las filas de la PLANIFICACIÓN Y CONTROL OPERACIONAL
(numeral 8.1): una fila por actividad de aventura del cliente con las normas
aplicables, los aspectos a controlar y cómo se controlan.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema indicado abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto de la empresa, deja
   ese campo en null (o lista vacía). El sistema lo marcará como [PENDIENTE].
3. No redactes prosa libre fuera de los campos del schema.
4. Usa un tono formal, institucional y en español de Colombia.
5. "controls": UNA fila por CADA actividad de aventura declarada por el
   cliente (onboarding_data.activities). PROHIBIDO omitir actividades y
   PROHIBIDO crear filas de actividades que el cliente no ofrece.
6. "national_standards" e "international_standards": SOLO normas o estándares
   que aparezcan TEXTUALMENTE en el contexto del cliente (campo
   operational_standards u otros) o en los extractos normativos de abajo.
   NUNCA cites de memoria un número de norma (NTC, ISO u otra) que no esté
   en el contexto: una norma mal citada invalida la auditoría. Si el cliente
   declaró no tener normas identificadas, escribe su declaración. Sin dato
   => null.
7. "aspects": los aspectos a controlar de ESA actividad. DERÍVALOS de los
   datos reales del cliente (equipos, competencias de guías, protocolos,
   edades y restricciones, condiciones del sitio).
8. "controls" (de la fila): cómo se controlan esos aspectos. DERÍVALO de los
   controles, inspecciones, briefings y registros que el cliente ya
   describió; NUNCA inventes prácticas o recursos que no tenga.
9. El contexto puede contener textos ETIQUETADOS PARA OTROS DOCUMENTOS.
   NUNCA los uses en los campos de esta planificación.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 8.1 y Anexo A) ===
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
  ('control_operacional', '8.1', 'company_name', 'Razón social de la empresa', true),
  ('control_operacional', '8.1', 'controls',     'Controles operacionales por actividad (normas, aspectos, controles)', true);

-- El paso de la ruta ya tiene generador: se enciende como DATO.
update public.document_roadmap
set generator_ready = true
where document_type = 'control_operacional';

-- Guardas: prompt activo con marcadores + paso encendido.
do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'generation' and document_type = 'control_operacional'
      and version = 'v1' and is_active
      and content like '%<<JSON_SCHEMA>>%' and content like '%<<COMPANY_CONTEXT>>%'
  ) then
    raise exception 'prompt control_operacional v1 no quedó activo o sin marcadores';
  end if;
  if not exists (
    select 1 from public.document_roadmap
    where document_type = 'control_operacional' and generator_ready
  ) then
    raise exception 'document_roadmap: control_operacional no quedó generator_ready';
  end if;
end $$;
