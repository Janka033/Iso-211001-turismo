-- =====================================================================
-- Configuración (DATOS, no código) de los 3 documentos nuevos del sistema
-- documental real de Felipe (TOURS AND ADVENTURES):
--   MA-02  manual_perfiles_cargos               (5.3 + 7.2)
--   PR-07  comunicacion_participacion_consulta  (7.4)
--   MA-03  manual_inspeccion_equipos            (8.1 + Anexo A)
--
-- Mismo patrón que 0007–0010: un prompt activo por (module, document_type) y
-- la checklist de extracción (field_key = nombre del campo del modelo Pydantic).
-- Los field_key son Parte A (universal): activity = NULL.
-- =====================================================================

-- ---------------------------------------------------------------------
-- MA-02 · Manual de perfiles y funciones de cargo
-- ---------------------------------------------------------------------
insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'manual_perfiles_cargos',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (turismo de aventura),
numerales 5.3 (roles, responsabilidades y autoridades) y 7.2 (competencia). Tu
trabajo NO es redactar prosa libre, sino EXTRAER y ESTRUCTURAR las variables del
Manual de perfiles y funciones de cargo a partir EXCLUSIVAMENTE de los datos del
cliente.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema de abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto, deja el campo en
   null (o lista vacía). El sistema lo marcará como [PENDIENTE].
3. "role_profiles" debe tener un perfil por cada cargo que exista en el cliente
   (usa "staff_roles" del contexto: cargo -> nº de personas). Para cada cargo,
   deriva funciones coherentes con la norma y con la operación real; clasifica el
   "level" como Directivo u Operativo. NO inventes cargos que el cliente no tenga.
4. Tono formal, institucional, español de Colombia.

=== CONTEXTO DE LA EMPRESA (onboarding_data, incluye staff_roles y activities) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numerales 5.3 y 7.2) ===
<<NORM_CONTEXT>>

=== CAMPOS REQUERIDOS (checklist de extracción) ===
<<CHECKLIST>>

=== PATRONES DE RECHAZO/APROBACIÓN DE AUDITORES ===
<<PATTERNS>>

=== SCHEMA JSON DE SALIDA (cúmplelo exactamente) ===
<<JSON_SCHEMA>>

Responde solo con el JSON.$prompt$,
  true
);

insert into public.extraction_checklist (document_type, numeral, field_key, description, required)
values
  ('manual_perfiles_cargos', '5.3', 'company_name',  'Razón social de la empresa', true),
  ('manual_perfiles_cargos', '5.3', 'objective',     'Objetivo del manual de perfiles y funciones', true),
  ('manual_perfiles_cargos', '5.3', 'scope',         'Alcance del manual', true),
  ('manual_perfiles_cargos', '5.3', 'org_structure', 'Estructura organizacional (niveles y cargos)', true),
  ('manual_perfiles_cargos', '7.2', 'role_profiles', 'Perfil y funciones por cada cargo', true);

-- ---------------------------------------------------------------------
-- PR-07 · Procedimiento de comunicación, participación y consulta
-- ---------------------------------------------------------------------
insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'comunicacion_participacion_consulta',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (turismo de aventura),
numeral 7.4 (comunicación). Tu trabajo NO es redactar prosa libre, sino EXTRAER y
ESTRUCTURAR las variables del Procedimiento de comunicación, participación y
consulta a partir EXCLUSIVAMENTE de los datos del cliente.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema de abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto, deja el campo en
   null (o lista vacía). El sistema lo marcará como [PENDIENTE].
3. "communication_matrix" debe tener una fila por cada comunicación relevante
   del SGS (qué / cómo / vía / a quién / frecuencia), coherente con el tamaño de
   equipo y los cargos reales del cliente.
4. Participación, consulta y representación deben reflejar mecanismos concretos
   para el personal (guías incluidos), no genéricos.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 7.4) ===
<<NORM_CONTEXT>>

=== CAMPOS REQUERIDOS (checklist de extracción) ===
<<CHECKLIST>>

=== PATRONES DE RECHAZO/APROBACIÓN DE AUDITORES ===
<<PATTERNS>>

=== SCHEMA JSON DE SALIDA (cúmplelo exactamente) ===
<<JSON_SCHEMA>>

Responde solo con el JSON.$prompt$,
  true
);

insert into public.extraction_checklist (document_type, numeral, field_key, description, required)
values
  ('comunicacion_participacion_consulta', '7.4', 'company_name',           'Razón social de la empresa', true),
  ('comunicacion_participacion_consulta', '7.4', 'objective',              'Objetivo del procedimiento', true),
  ('comunicacion_participacion_consulta', '7.4', 'scope',                  'Alcance del procedimiento', true),
  ('comunicacion_participacion_consulta', '7.4', 'responsibles',           'Responsables del proceso de comunicación', true),
  ('comunicacion_participacion_consulta', '7.4', 'communication_matrix',   'Matriz de comunicación (qué/cómo/vía/a quién/frecuencia)', true),
  ('comunicacion_participacion_consulta', '7.4', 'participation',          'Mecanismos de participación del personal', true),
  ('comunicacion_participacion_consulta', '7.4', 'consultation',           'Mecanismos de consulta al personal', true),
  ('comunicacion_participacion_consulta', '7.4', 'representation',         'Representación del personal en asuntos de seguridad', false),
  ('comunicacion_participacion_consulta', '7.4', 'performance_evaluation', 'Evaluación del desempeño del proceso', false),
  ('comunicacion_participacion_consulta', '7.4', 'records',                'Registros del procedimiento', false);

-- ---------------------------------------------------------------------
-- MA-03 · Manual de inspección y mantenimiento de equipos
-- ---------------------------------------------------------------------
insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'manual_inspeccion_equipos',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (turismo de aventura),
numeral 8.1 (control operacional) y Anexo A. Tu trabajo NO es redactar prosa
libre, sino EXTRAER y ESTRUCTURAR las variables del Manual de inspección y
mantenimiento de equipos a partir EXCLUSIVAMENTE de los datos del cliente.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema de abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto, deja el campo en
   null (o lista vacía). El sistema lo marcará como [PENDIENTE].
3. "equipment_items" DEBE derivarse del EQUIPO REAL del cliente: usa
   "activity_fields" del contexto (claves equipo_<actividad>, p.ej. equipo_rafting,
   equipo_buceo). Genera una fila por cada equipo/elemento mencionado, asociado a
   su actividad. NO inventes equipos que el cliente no listó; si una actividad no
   tiene equipo declarado, no inventes filas para ella.
4. "state" usa el conjunto {Ok, A revisar, En cuarentena, De baja}; por defecto
   "Ok" solo si el cliente no indica otro estado. "inspection_type" usa {previa a
   uso, especial, periódica trimestral}.

=== CONTEXTO DE LA EMPRESA (onboarding_data, incluye activity_fields con el equipo real) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 8.1 y Anexo A) ===
<<NORM_CONTEXT>>

=== CAMPOS REQUERIDOS (checklist de extracción) ===
<<CHECKLIST>>

=== PATRONES DE RECHAZO/APROBACIÓN DE AUDITORES ===
<<PATTERNS>>

=== SCHEMA JSON DE SALIDA (cúmplelo exactamente) ===
<<JSON_SCHEMA>>

Responde solo con el JSON.$prompt$,
  true
);

insert into public.extraction_checklist (document_type, numeral, field_key, description, required)
values
  ('manual_inspeccion_equipos', '8.1', 'company_name',      'Razón social de la empresa', true),
  ('manual_inspeccion_equipos', '8.1', 'objective',         'Objetivo del manual de inspección y mantenimiento', true),
  ('manual_inspeccion_equipos', '8.1', 'scope',             'Alcance del manual', true),
  ('manual_inspeccion_equipos', '8.1', 'role_obligations',  'Obligaciones por rol (Gerencia, Coordinador, Guía)', true),
  ('manual_inspeccion_equipos', '8.1', 'equipment_items',   'Control de equipos por actividad (derivado del equipo real)', true),
  ('manual_inspeccion_equipos', '8.1', 'maintenance_types', 'Tipos de mantenimiento (previa a uso, especial, periódica)', true);
