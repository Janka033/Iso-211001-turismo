-- =====================================================================
-- 0053 · Control de la información documentada (7.5.1): generador 6/8
-- de la ruta guiada (Fase 4). Metodología, definiciones, 9 actividades
-- y tiempos de retención (2 años SGSTA / 20 años SST) FIJOS del molde
-- MinCIT; la IA solo aporta identidad, cargo responsable,
-- almacenamiento real y aprobación.
--
-- 1) prompt de extracción v1 (module=generation, marcadores <<...>>)
-- 2) extraction_checklist del documento
-- 3) document_roadmap: el paso queda generator_ready
-- =====================================================================

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'control_informacion_documentada',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (sistema de gestión de
seguridad para turismo de aventura). Tu trabajo NO es redactar el documento
final, sino EXTRAER y ESTRUCTURAR las variables que alimentan una plantilla fija.

OBJETIVO: extraer las variables del PROCEDIMIENTO DE CONTROL DE LA INFORMACIÓN
DOCUMENTADA (numeral 7.5.1). La metodología completa (objetivo, alcance,
definiciones, aclaraciones, las 9 actividades y los tiempos de retención) es
contenido fijo de la plantilla: tú SOLO aportas identidad, el cargo
responsable, el almacenamiento real y los datos de aprobación.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema indicado abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto de la empresa, deja
   ese campo en null. El sistema lo marcará como [PENDIENTE].
3. No redactes prosa libre fuera de los campos del schema.
4. "responsible_role": el cargo responsable del control de documentos. El
   campo document_control_info del contexto responde EXACTAMENTE esto: si ahí
   aparece un cargo, ese ES el responsable. En su defecto, DERÍVALO del
   organigrama (p. ej. Gerente). Escríbelo con inicial mayúscula.
5. "storage_description": dónde almacena la empresa sus documentos
   (plataforma o nube para electrónicos, lugar físico para impresos). Si
   document_control_info lo trae, eso ES el almacenamiento. Redáctalo en
   tono formal. Sin declaración => null.
6. "approval_date": SOLO si el cliente indicó la fecha de aprobación de ESTE
   documento. NUNCA la derives de otras fechas del contexto. Sin fecha => null.
7. El contexto puede contener textos ETIQUETADOS PARA OTROS DOCUMENTOS.
   NUNCA los uses en los campos de este procedimiento.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 7.5.1 y 7.5.2/7.5.3) ===
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
  ('control_informacion_documentada', '7.5.1', 'company_name',         'Razón social de la empresa', true),
  ('control_informacion_documentada', '7.5.1', 'responsible_role',     'Cargo responsable del control de documentos', true),
  ('control_informacion_documentada', '7.5.1', 'storage_description',  'Almacenamiento de documentos electrónicos y físicos', true),
  ('control_informacion_documentada', '7.5.1', 'legal_representative', 'Representante legal que aprueba', false),
  ('control_informacion_documentada', '7.5.1', 'approval_date',        'Fecha de aprobación del documento', false);

-- El paso de la ruta ya tiene generador: se enciende como DATO.
update public.document_roadmap
set generator_ready = true
where document_type = 'control_informacion_documentada';

-- Guardas: prompt activo con marcadores + paso encendido.
do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'generation' and document_type = 'control_informacion_documentada'
      and version = 'v1' and is_active
      and content like '%<<JSON_SCHEMA>>%' and content like '%<<COMPANY_CONTEXT>>%'
  ) then
    raise exception 'prompt control_informacion_documentada v1 no quedó activo o sin marcadores';
  end if;
  if not exists (
    select 1 from public.document_roadmap
    where document_type = 'control_informacion_documentada' and generator_ready
  ) then
    raise exception 'document_roadmap: control_informacion_documentada no quedó generator_ready';
  end if;
end $$;
