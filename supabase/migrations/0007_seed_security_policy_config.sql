-- =====================================================================
-- Seed de configuración para el documento "Política de seguridad" (5.2),
-- documento #1 del MVP.
--
-- Regla de oro 3: prompts y checklist son DATOS, no código. Viven aquí,
-- en la DB, nunca hardcodeados en el service.
--
-- El service ensambla el prompt final reemplazando los marcadores
-- <<COMPANY_CONTEXT>>, <<NORM_CONTEXT>>, <<CHECKLIST>>, <<PATTERNS>> y
-- <<JSON_SCHEMA>> con el contexto dinámico de cada tenant. Usamos
-- marcadores (no str.format) para no chocar con las llaves del JSON.
-- =====================================================================

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'politica_seguridad',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (sistema de gestión de
seguridad para turismo de aventura). Tu trabajo NO es redactar el documento
final, sino EXTRAER y ESTRUCTURAR las variables que alimentan una plantilla fija.

OBJETIVO: extraer las variables de la Política de seguridad (numeral 5.2) de la
empresa, a partir EXCLUSIVAMENTE de los datos que el cliente proporcionó.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema indicado abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto de la empresa, deja
   ese campo en null (o lista vacía). El sistema lo marcará como [PENDIENTE].
3. No redactes prosa libre fuera de los campos del schema.
4. Usa un tono formal, institucional y en español de Colombia.
5. Los compromisos deben reflejar lo que la norma 5.2 exige (mejora continua,
   cumplimiento legal, prevención de riesgos en actividades de aventura), pero
   contextualizados con las actividades y datos reales de la empresa.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 5.2) ===
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

-- Checklist de extracción de la política (campos y si son obligatorios).
insert into public.extraction_checklist (document_type, numeral, field_key, description, required)
values
  ('politica_seguridad', '5.2', 'company_name',          'Razón social de la empresa', true),
  ('politica_seguridad', '5.2', 'nit',                   'NIT de la empresa', false),
  ('politica_seguridad', '5.2', 'scope',                 'Alcance de la política: actividades de aventura y ubicaciones de operación', true),
  ('politica_seguridad', '5.2', 'activities',            'Lista de actividades de turismo de aventura que ofrece', true),
  ('politica_seguridad', '5.2', 'management_commitment', 'Declaración de compromiso de la alta dirección con la seguridad', true),
  ('politica_seguridad', '5.2', 'safety_objectives',     'Objetivos de seguridad de la organización', true),
  ('politica_seguridad', '5.2', 'legal_commitment',      'Compromiso de cumplimiento de requisitos legales y reglamentarios aplicables', true),
  ('politica_seguridad', '5.2', 'continuous_improvement','Compromiso de mejora continua del sistema de gestión de seguridad', true),
  ('politica_seguridad', '5.2', 'communication',         'Forma en que la política se comunica y está disponible para las partes interesadas', false),
  ('politica_seguridad', '5.2', 'legal_representative',  'Nombre del representante legal que aprueba la política', false),
  ('politica_seguridad', '5.2', 'approval_date',         'Fecha de aprobación de la política (YYYY-MM-DD)', false);
