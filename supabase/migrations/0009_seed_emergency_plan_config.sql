-- =====================================================================
-- Seed de configuración para el "Plan de respuesta a emergencias" (8.2),
-- documento #3 del MVP. Prompt y checklist son DATOS (regla de oro 3).
-- =====================================================================

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'plan_emergencias',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (gestión de seguridad para
turismo de aventura), numeral 8.2 (preparación y respuesta ante emergencias).
Tu trabajo NO es redactar prosa libre, sino EXTRAER y ESTRUCTURAR las variables
del plan de emergencias a partir EXCLUSIVAMENTE de los datos del cliente.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema de abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto, deja el campo en
   null (o lista vacía). El sistema lo marcará como [PENDIENTE].
3. Genera un escenario ("emergency_scenarios") por cada emergencia plausible de
   las actividades del cliente (accidentes, clima, fauna, extravío, fallo de
   equipo, emergencia médica). Si no hay actividades, devuelve la lista vacía.
4. Los pasos de respuesta deben ser concretos y accionables, derivados del
   contexto; no genéricos ni inventados.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 8.2) ===
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
  ('plan_emergencias', '8.2', 'company_name',           'Razón social de la empresa', true),
  ('plan_emergencias', '8.2', 'scope',                  'Alcance del plan (actividades y ubicaciones)', true),
  ('plan_emergencias', '8.2', 'general_objective',      'Objetivo general del plan', true),
  ('plan_emergencias', '8.2', 'emergency_scenarios',    'Escenarios de emergencia y su respuesta', true),
  ('plan_emergencias', '8.2', 'communication_protocol', 'Protocolo de comunicación y notificación', true),
  ('plan_emergencias', '8.2', 'emergency_contacts',     'Contactos de emergencia', true),
  ('plan_emergencias', '8.2', 'evacuation_resources',   'Rutas de evacuación y recursos', true),
  ('plan_emergencias', '8.2', 'external_coordination',  'Coordinación con servicios externos', false),
  ('plan_emergencias', '8.2', 'training_drills',        'Capacitación y simulacros', false),
  ('plan_emergencias', '8.2', 'review_frequency',       'Frecuencia de revisión del plan', false),
  ('plan_emergencias', '8.2', 'legal_representative',   'Representante legal que aprueba', false),
  ('plan_emergencias', '8.2', 'approval_date',          'Fecha de aprobación (YYYY-MM-DD)', false);
