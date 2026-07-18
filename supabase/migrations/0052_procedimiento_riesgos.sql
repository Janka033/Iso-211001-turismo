-- =====================================================================
-- 0052 · Procedimiento de gestión de riesgos y oportunidades (6.1.1):
-- generador 5/8 de la ruta guiada (Fase 4). Toda la metodología del
-- molde MinCIT (objetivo, alcance, definiciones, aclaraciones y los 7
-- pasos) es contenido FIJO de la plantilla; la IA solo aporta
-- identidad, cargo líder, frecuencia de seguimiento y aprobación.
--
-- 1) prompt de extracción v1 (module=generation, marcadores <<...>>)
-- 2) extraction_checklist del documento
-- 3) document_roadmap: el paso queda generator_ready
-- =====================================================================

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'procedimiento_riesgos_oportunidades',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (sistema de gestión de
seguridad para turismo de aventura). Tu trabajo NO es redactar el documento
final, sino EXTRAER y ESTRUCTURAR las variables que alimentan una plantilla fija.

OBJETIVO: extraer las variables del PROCEDIMIENTO DE GESTIÓN DE RIESGOS Y
OPORTUNIDADES (numeral 6.1.1). La metodología completa (objetivo, alcance,
definiciones, aclaraciones y la tabla de actividades) es contenido fijo de la
plantilla: tú SOLO aportas identidad, el cargo que lidera la gestión, la
frecuencia de seguimiento y los datos de aprobación.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema indicado abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto de la empresa, deja
   ese campo en null. El sistema lo marcará como [PENDIENTE].
3. No redactes prosa libre fuera de los campos del schema.
4. "responsible_role": el cargo que lidera la gestión de riesgos. El campo
   risk_management_lead del contexto responde EXACTAMENTE esto: si ahí
   aparece un cargo, ese ES el cargo líder. En su defecto, DERÍVALO del
   organigrama (p. ej. Gerente). Escríbelo con inicial mayúscula.
5. "follow_up_frequency": 'Semestral' o 'Anual'. Si risk_management_lead trae
   la frecuencia, esa ES la frecuencia. Sin declaración => null.
6. "approval_date": SOLO si el cliente indicó la fecha de aprobación de ESTE
   documento. NUNCA la derives de otras fechas del contexto. Sin fecha => null.
7. El contexto puede contener textos ETIQUETADOS PARA OTROS DOCUMENTOS.
   NUNCA los uses en los campos de este procedimiento.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 6.1.1 y Anexo A) ===
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
  ('procedimiento_riesgos_oportunidades', '6.1.1', 'company_name',         'Razón social de la empresa', true),
  ('procedimiento_riesgos_oportunidades', '6.1.1', 'responsible_role',     'Cargo que lidera la gestión de riesgos', true),
  ('procedimiento_riesgos_oportunidades', '6.1.1', 'follow_up_frequency',  'Frecuencia del seguimiento (semestral o anual)', true),
  ('procedimiento_riesgos_oportunidades', '6.1.1', 'legal_representative', 'Representante legal que aprueba', false),
  ('procedimiento_riesgos_oportunidades', '6.1.1', 'approval_date',        'Fecha de aprobación del documento', false);

-- El paso de la ruta ya tiene generador: se enciende como DATO.
update public.document_roadmap
set generator_ready = true
where document_type = 'procedimiento_riesgos_oportunidades';

-- Guardas: prompt activo con marcadores + paso encendido.
do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'generation' and document_type = 'procedimiento_riesgos_oportunidades'
      and version = 'v1' and is_active
      and content like '%<<JSON_SCHEMA>>%' and content like '%<<COMPANY_CONTEXT>>%'
  ) then
    raise exception 'prompt procedimiento_riesgos_oportunidades v1 no quedó activo o sin marcadores';
  end if;
  if not exists (
    select 1 from public.document_roadmap
    where document_type = 'procedimiento_riesgos_oportunidades' and generator_ready
  ) then
    raise exception 'document_roadmap: procedimiento_riesgos_oportunidades no quedó generator_ready';
  end if;
end $$;
