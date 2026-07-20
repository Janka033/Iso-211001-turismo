-- =====================================================================
-- 0066 · Cierre del árbol GEN: dos procedimientos de metodología fija que
-- faltaban del kit MinCIT, con el mismo patrón que 6.1.1/7.5.1/9.2 (todo el
-- contenido vive fijo en el generador; la IA solo aporta identidad, el cargo
-- responsable —derivado del organigrama— y la aprobación):
--
--   · procedimiento_requisitos_legales (6.1.3): complementa la Matriz de
--     requisitos legales (MT-03) describiendo cómo se identifica, elabora,
--     actualiza, comunica y evalúa el cumplimiento legal.
--   · procedimiento_seleccion_personal (5.3): complementa el Manual de perfiles
--     y cargos (MA-02) describiendo cómo se identifican perfiles, se selecciona,
--     se forma y se toma conciencia del personal.
--
-- 1) prompts de extracción v1 (module=generation, marcadores <<...>>)
-- 2) extraction_checklist de cada documento
-- 3) document_roadmap: se insertan los 2 pasos y se RENUMERA la ruta completa a
--    21 pasos en orden de capítulo (config global sin tenant_id; el progreso por
--    tenant se deriva de document_status por document_type, no de step_order, así
--    que renumerar NO afecta ningún dato de tenant). Ambos quedan generator_ready.
-- =====================================================================

-- 1) prompts -----------------------------------------------------------
insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'procedimiento_requisitos_legales',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (sistema de gestión de
seguridad para turismo de aventura). Tu trabajo NO es redactar el documento
final, sino EXTRAER y ESTRUCTURAR las variables que alimentan una plantilla fija.

OBJETIVO: extraer las variables del PROCEDIMIENTO DE REQUISITOS LEGALES (numeral
6.1.3). Toda la metodología (objetivo, alcance, las 4 definiciones —decreto,
decreto ley, ley, resolución— y las 7 actividades: generalidades, consulta e
identificación de la legislación, elaboración de la matriz, actualización,
comunicación, evaluación del cumplimiento y plan de intervención) es contenido
fijo de la plantilla: tú SOLO aportas identidad, el cargo responsable del
sistema de gestión y los datos de aprobación.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema indicado abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto de la empresa, deja
   ese campo en null. El sistema lo marcará como [PENDIENTE].
3. No redactes prosa libre fuera de los campos del schema.
4. "responsible_role": el cargo responsable del sistema de gestión que
   identifica y evalúa los requisitos legales. DERÍVALO del organigrama del
   cliente (p. ej. Gerente). Escríbelo con inicial mayúscula.
5. "approval_date": SOLO si el cliente indicó la fecha de aprobación de ESTE
   documento. NUNCA la derives de otras fechas del contexto. Sin fecha => null.
6. El contexto puede contener textos ETIQUETADOS PARA OTROS DOCUMENTOS. NUNCA
   los uses en los campos de este procedimiento.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 6.1.3) ===
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

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'procedimiento_seleccion_personal',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (sistema de gestión de
seguridad para turismo de aventura). Tu trabajo NO es redactar el documento
final, sino EXTRAER y ESTRUCTURAR las variables que alimentan una plantilla fija.

OBJETIVO: extraer las variables del PROCEDIMIENTO DE IDENTIFICACIÓN Y SELECCIÓN
DE PERSONAL (numeral 5.3). Toda la metodología (objetivo, alcance, las 11
definiciones, las aclaraciones y las 7 actividades: identificar perfiles/roles,
seleccionar y contratar, entregar EPP, inducción/reinducción, programa de
formación, toma de conciencia y desvinculación) es contenido fijo de la
plantilla: tú SOLO aportas identidad, el cargo responsable del proceso y los
datos de aprobación.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema indicado abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto de la empresa, deja
   ese campo en null. El sistema lo marcará como [PENDIENTE].
3. No redactes prosa libre fuera de los campos del schema.
4. "responsible_role": el cargo responsable de identificar perfiles, seleccionar
   y formar al personal (p. ej. Gerente, Coordinador de talento humano).
   DERÍVALO del organigrama del cliente. Escríbelo con inicial mayúscula.
5. "approval_date": SOLO si el cliente indicó la fecha de aprobación de ESTE
   documento. NUNCA la derives de otras fechas del contexto. Sin fecha => null.
6. El contexto puede contener textos ETIQUETADOS PARA OTROS DOCUMENTOS. NUNCA
   los uses en los campos de este procedimiento.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 5.3 y 7.2) ===
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

-- 2) checklist ---------------------------------------------------------
insert into public.extraction_checklist (document_type, numeral, field_key, description, required)
values
  ('procedimiento_requisitos_legales', '6.1.3', 'company_name',         'Razón social de la empresa', true),
  ('procedimiento_requisitos_legales', '6.1.3', 'responsible_role',     'Cargo responsable del sistema de gestión que identifica y evalúa los requisitos legales', true),
  ('procedimiento_requisitos_legales', '6.1.3', 'legal_representative', 'Representante legal que aprueba', false),
  ('procedimiento_requisitos_legales', '6.1.3', 'approval_date',        'Fecha de aprobación del documento', false),
  ('procedimiento_seleccion_personal', '5.3',   'company_name',         'Razón social de la empresa', true),
  ('procedimiento_seleccion_personal', '5.3',   'responsible_role',     'Cargo responsable de la identificación, selección y formación del personal', true),
  ('procedimiento_seleccion_personal', '5.3',   'legal_representative', 'Representante legal que aprueba', false),
  ('procedimiento_seleccion_personal', '5.3',   'approval_date',        'Fecha de aprobación del documento', false);

-- 3) roadmap: insertar los 2 pasos y renumerar la ruta a 21 en orden de
--    capítulo. Se desplazan los existentes +100 para liberar el rango 1..21 y
--    evitar cualquier choque de unicidad durante la renumeración.
update public.document_roadmap set step_order = step_order + 100;

insert into public.document_roadmap (step_order, document_type, title, numeral, generator_ready) values
  (200, 'procedimiento_seleccion_personal', 'Procedimiento de identificación y selección de personal', '5.3',   true),
  (201, 'procedimiento_requisitos_legales', 'Procedimiento de requisitos legales',                     '6.1.3', true)
on conflict (document_type) do nothing;

update public.document_roadmap set step_order = case document_type
  when 'alcance_sgsta'                        then 1
  when 'matriz_partes_interesadas'           then 2
  when 'acta_compromiso'                     then 3
  when 'politica_seguridad'                  then 4
  when 'manual_perfiles_cargos'              then 5
  when 'procedimiento_seleccion_personal'    then 6
  when 'procedimiento_riesgos_oportunidades' then 7
  when 'matriz_riesgos'                      then 8
  when 'procedimiento_requisitos_legales'    then 9
  when 'matriz_requisitos_legales'           then 10
  when 'matriz_objetivos_seguridad'          then 11
  when 'comunicacion_participacion_consulta' then 12
  when 'control_informacion_documentada'     then 13
  when 'control_operacional'                 then 14
  when 'manual_inspeccion_equipos'           then 15
  when 'plan_emergencias'                    then 16
  when 'gestion_incidentes'                  then 17
  when 'matriz_indicadores'                  then 18
  when 'auditoria_interna'                   then 19
  when 'revision_direccion'                  then 20
  when 'acciones_correctivas_mejora'         then 21
  else step_order
end;

-- Guardas: prompts activos con marcadores + los 2 pasos generator_ready + la
-- ruta con 21 pasos y step_order contiguo 1..21 (sin duplicados ni huecos).
do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'generation' and document_type = 'procedimiento_requisitos_legales'
      and version = 'v1' and is_active
      and content like '%<<JSON_SCHEMA>>%' and content like '%<<COMPANY_CONTEXT>>%'
  ) then
    raise exception 'prompt procedimiento_requisitos_legales v1 no quedó activo o sin marcadores';
  end if;
  if not exists (
    select 1 from public.prompt_versions
    where module = 'generation' and document_type = 'procedimiento_seleccion_personal'
      and version = 'v1' and is_active
      and content like '%<<JSON_SCHEMA>>%' and content like '%<<COMPANY_CONTEXT>>%'
  ) then
    raise exception 'prompt procedimiento_seleccion_personal v1 no quedó activo o sin marcadores';
  end if;
  if (select count(*) from public.document_roadmap
      where document_type in ('procedimiento_requisitos_legales','procedimiento_seleccion_personal')
        and generator_ready) <> 2 then
    raise exception 'document_roadmap: los 2 procedimientos no quedaron generator_ready';
  end if;
  if (select count(*) from public.document_roadmap) <> 21 then
    raise exception 'document_roadmap: la ruta no quedó con 21 pasos';
  end if;
  if (select count(distinct step_order) from public.document_roadmap) <> 21
     or (select min(step_order) from public.document_roadmap) <> 1
     or (select max(step_order) from public.document_roadmap) <> 21 then
    raise exception 'document_roadmap: step_order no quedó contiguo 1..21';
  end if;
end $$;
