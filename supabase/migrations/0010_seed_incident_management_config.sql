-- =====================================================================
-- Seed de configuración para el "Procedimiento de gestión de incidentes"
-- (8.3), documento #4 del MVP. Prompt y checklist son DATOS.
-- =====================================================================

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'gestion_incidentes',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (gestión de seguridad para
turismo de aventura), numeral 8.3 (gestión de incidentes). Tu trabajo NO es
redactar prosa libre, sino EXTRAER y ESTRUCTURAR las variables del procedimiento
a partir EXCLUSIVAMENTE de los datos del cliente.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema de abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto, deja el campo en
   null (o lista vacía). El sistema lo marcará como [PENDIENTE].
3. "procedure_steps" debe describir el ciclo completo de gestión: reportar,
   registrar, atender, investigar causa raíz, definir acciones correctivas,
   verificar eficacia y documentar lecciones aprendidas.
4. "incident_classification" debe distinguir casi-accidente, incidente y
   accidente.

NOTA: el documento incluye además un FORMATO de reporte en blanco con estructura
fija; no necesitas generarlo, solo las variables del procedimiento.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 8.3) ===
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
  ('gestion_incidentes', '8.3', 'company_name',               'Razón social de la empresa', true),
  ('gestion_incidentes', '8.3', 'scope',                      'Alcance del procedimiento', true),
  ('gestion_incidentes', '8.3', 'objective',                  'Objetivo del procedimiento', true),
  ('gestion_incidentes', '8.3', 'incident_classification',    'Clasificación de eventos', true),
  ('gestion_incidentes', '8.3', 'procedure_steps',            'Pasos del procedimiento', true),
  ('gestion_incidentes', '8.3', 'responsible',                'Responsable de la gestión de incidentes', true),
  ('gestion_incidentes', '8.3', 'corrective_actions_process', 'Proceso de acciones correctivas', true),
  ('gestion_incidentes', '8.3', 'record_retention',           'Conservación de registros', false),
  ('gestion_incidentes', '8.3', 'review_frequency',           'Frecuencia de revisión', false),
  ('gestion_incidentes', '8.3', 'legal_representative',       'Representante legal que aprueba', false),
  ('gestion_incidentes', '8.3', 'approval_date',              'Fecha de aprobación (YYYY-MM-DD)', false);
