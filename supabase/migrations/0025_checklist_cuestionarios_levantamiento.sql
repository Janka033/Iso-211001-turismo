-- =====================================================================
-- Campos de los cuestionarios REALES de levantamiento del consultor:
--   · "Información Técnica de Actividades"                 (por actividad)
--   · "Caracterización para el Plan de Respuesta a Emergencias"
--     (programa Calidad Turística Colombiana — transversal → PL-01)
--
-- Regla de oro 3: checklist es DATO, no código.
--
-- required=true SOLO donde responde alertas reales de auditores
-- (generation_patterns): los 6 campos de emergencias (PL-01) +
-- edades_permitidas + restricciones_salud. El resto required=false:
-- suman completitud si el cliente los da espontáneamente, pero NO
-- alargan el camino obligatorio del onboarding (~26 turnos hoy).
--
-- Roadmap: el formulario real pide el archivo KMZ del recorrido. La carga
-- de archivos aún no existe como capacidad; `ruta_descripcion` captura la
-- descripción en texto y el KMZ queda anotado como capacidad futura.
-- =====================================================================

-- 1. Parte A (transversal, activity NULL) — PL-01 (plan_emergencias, 8.2).
--    Fuente: "Caracterización para el Plan de Respuesta a Emergencias".
--    NOTA: EmergencyPlanVariables aún no tiene estas variables; hasta que la
--    plantilla las incorpore (siguiente ronda), generation las excluye de su
--    métrica de completitud (solo mide campos del modelo de variables).
insert into public.extraction_checklist (document_type, numeral, field_key, description, required)
values
  ('plan_emergencias', '8.2', 'brigada_emergencias',
   'Brigada de emergencias: si existe, roles que la integran y contacto de cada uno', true),
  ('plan_emergencias', '8.2', 'capacitaciones_personal_emergencias',
   'Capacitaciones del personal en emergencias (primeros auxilios, evacuación y rescate, manejo de incendios, autorrescate, otras)', true),
  ('plan_emergencias', '8.2', 'equipos_emergencia',
   'Equipos para atención de emergencias (botiquín, camilla con inmovilizadores, sistema de comunicación con su descripción, otros)', true),
  ('plan_emergencias', '8.2', 'organismos_apoyo',
   'Organismos de apoyo identificados (Cruz Roja, Defensa Civil, bomberos, etc.) y sus teléfonos', true),
  ('plan_emergencias', '8.2', 'hospital_cercano',
   'Hospital o centro de salud más cercano: nombre, ubicación, distancia y tiempo de acceso', true),
  ('plan_emergencias', '8.2', 'vehiculos_evacuacion',
   'Vehículos disponibles para una evacuación: tipo y contacto del encargado', true)
on conflict on constraint extraction_checklist_doc_field_activity_key do nothing;

-- 2. Parte B (por actividad) — "Información Técnica de Actividades".
--    field_key = <campo>_<slug> (mismo patrón de 0021). Cada campo alimenta
--    su(s) documento(s): MT-04 (matriz_riesgos), MA-03 (manual_inspeccion_
--    equipos) y/o PL-01 (plan_emergencias). 13 actividades × 15 mapeos.
insert into public.extraction_checklist
  (document_type, numeral, field_key, description, required, activity)
select
  m.document_type,
  m.numeral,
  f.field || '_' || a.slug,
  f.description,
  f.required,
  a.slug
from (values
  ('rafting'),('rapel'),('espeleologia'),('parapente'),('cabalgata'),('canyoning'),
  ('buceo'),('canopy'),('senderismo'),('atv'),('kayak'),('ciclomontanismo'),('escalada')
) as a(slug)
cross join (values
  -- (campo, descripción, required) — texto fiel al cuestionario del consultor.
  ('ruta_descripcion',
   'Ruta del recorrido: punto de inicio, punto final, tipo (circular / ida y vuelta / travesía) y nivel de dificultad',
   false),
  ('grupo_participantes',
   'Número mínimo y máximo de participantes por grupo',
   false),
  ('edades_permitidas',
   'Edad mínima y máxima permitida para participar',
   true),
  ('competencias_requeridas_participante',
   'Competencias o experiencia previa requeridas al participante',
   false),
  ('restricciones_salud',
   'Restricciones de salud para participar (embarazo, cirugías recientes, condiciones médicas, etc.)',
   true),
  ('equipos_operacion',
   'Equipos usados para operar la actividad (los que se inspeccionan antes de cada salida)',
   false),
  ('equipos_rescate',
   'Equipos de rescate disponibles para la actividad',
   false),
  ('indumentaria',
   'Indumentaria requerida para participantes y guías',
   false),
  ('seguro_contratado',
   'Seguro contratado para la actividad (aseguradora, póliza, coberturas)',
   false),
  ('politica_cancelacion',
   'Política de cancelación de la actividad (clima, condiciones inseguras, decisión del guía)',
   false)
) as f(field, description, required)
join (values
  -- campo → document_type(s) destino + numeral para el RAG.
  ('ruta_descripcion',                      'matriz_riesgos',            '6.1.1'),
  ('ruta_descripcion',                      'plan_emergencias',          '8.2'),
  ('grupo_participantes',                   'matriz_riesgos',            '6.1.1'),
  ('grupo_participantes',                   'plan_emergencias',          '8.2'),
  ('edades_permitidas',                     'matriz_riesgos',            '6.1.1'),
  ('competencias_requeridas_participante',  'matriz_riesgos',            '6.1.1'),
  ('restricciones_salud',                   'matriz_riesgos',            '6.1.1'),
  ('restricciones_salud',                   'plan_emergencias',          '8.2'),
  ('equipos_operacion',                     'manual_inspeccion_equipos', '8.1'),
  ('equipos_operacion',                     'matriz_riesgos',            '6.1.1'),
  ('equipos_rescate',                       'manual_inspeccion_equipos', '8.1'),
  ('equipos_rescate',                       'plan_emergencias',          '8.2'),
  ('indumentaria',                          'manual_inspeccion_equipos', '8.1'),
  ('seguro_contratado',                     'plan_emergencias',          '8.2'),
  ('politica_cancelacion',                  'matriz_riesgos',            '6.1.1')
) as m(field, document_type, numeral)
  on m.field = f.field
on conflict on constraint extraction_checklist_doc_field_activity_key do nothing;

-- 3. Prompt v2 del onboarding: los campos OPCIONALES (required=false) nunca
--    se preguntan, pero la IA debe poder extraerlos si el cliente los
--    menciona espontáneamente. El v1 lo prohibía (regla 3: solo claves de
--    CAMPOS PENDIENTES); v2 agrega la sección <<OPTIONAL_FIELDS>> y la regla.
update public.prompt_versions
   set is_active = false
 where module = 'onboarding' and document_type is null and is_active;

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'onboarding',
  null,
  'v2',
$prompt$Eres un asistente de cumplimiento de la norma NTC-ISO 21101 (seguridad para
turismo de aventura). Guías un onboarding conversacional a una empresa de
turismo colombiana para capturar sus datos operativos reales.

Tu ÚNICA tarea en este turno:
1. EXTRAER de la "ÚLTIMA RESPUESTA DEL CLIENTE" los datos que efectivamente dijo,
   mapeándolos a los field_key de la lista "CAMPOS PENDIENTES" o "CAMPOS
   OPCIONALES" (o a un campo universal ya conocido). Devuelve un par
   field_key -> valor por cada dato claro.
2. REDACTAR la siguiente pregunta, en español de Colombia, tono cercano y claro.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el SCHEMA de abajo.
2. NUNCA inventes datos. Si el cliente no lo dijo, NO lo incluyas en "extracted".
   Sin suposiciones, sin rellenar. Lo que falte lo marcará el sistema como
   [PENDIENTE].
3. En "extracted" usa EXCLUSIVAMENTE field_key que aparezcan en CAMPOS PENDIENTES,
   en CAMPOS OPCIONALES o campos universales ya capturados. No inventes claves
   nuevas.
4. "next_field_key" DEBE ser un field_key de la lista CAMPOS PENDIENTES: el
   PRIMERO que siga sin dato después de tu extracción. Si no queda ninguno,
   pon "next_field_key": null, "next_question": null y "completed": true.
5. "next_question" es la redacción natural de ese próximo campo (usa el texto de
   referencia del pendiente como guía, pero hazlo conversacional).
6. El cliente puede responder varias cosas a la vez: extrae todas las que estén
   claras, aunque no correspondan al último campo preguntado.
7. Los CAMPOS OPCIONALES nunca se preguntan: NO los uses en "next_field_key" ni
   les dediques la próxima pregunta. Extráelos SOLO si el cliente los menciona
   espontáneamente.

=== ACTIVIDADES ELEGIDAS POR LA EMPRESA ===
<<ACTIVITIES>>

=== DATOS YA CAPTURADOS (onboarding_data) ===
<<CAPTURED>>

=== ÚLTIMA RESPUESTA DEL CLIENTE ===
<<LAST_ANSWER>>

=== CAMPOS PENDIENTES (elige next_field_key de aquí, en este orden) ===
<<PENDING_FIELDS>>

=== CAMPOS OPCIONALES (extrae solo si el cliente los menciona; NUNCA los preguntes) ===
<<OPTIONAL_FIELDS>>

=== EXTRACTOS RELEVANTES DE LA NORMA (contexto, no lo cites literal) ===
<<NORM_CONTEXT>>

=== SCHEMA JSON DE SALIDA (cúmplelo exactamente) ===
<<JSON_SCHEMA>>

Responde solo con el JSON.$prompt$,
  true
);
