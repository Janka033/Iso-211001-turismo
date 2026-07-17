-- =====================================================================
-- 0040 · matriz v5 (dos planos + oportunidades estructuradas) y
--        equipos v3 (régimen de inspección como prescripción técnica).
--
-- Decisión de Jan (2026-07-17): el contenido técnico estándar del
-- documento lo termina la IA — los equipos de cada actividad van SIEMPRE
-- con su régimen de inspección (del texto del cliente o del estándar de
-- la industria para ese tipo de equipo), igual que la valoración de la
-- matriz (0038). Lo que sigue sin inventarse jamás: los datos operativos
-- propios del cliente (equipos que no listó, fechas, teléfonos, estados).
--
-- matriz v5 = v4 + reglas 7-10: riesgos de negocio/procesos (dos planos,
-- se perdían en v4), escenarios del contexto colombiano, contexto del
-- análisis dentro de scope, y oportunidades estructuradas (nueva tabla
-- impacto/acciones/responsable/cronograma/indicador del schema).
-- =====================================================================

update public.prompt_versions
set is_active = false
where module = 'generation' and document_type = 'matriz_riesgos';

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'matriz_riesgos',
  'v5',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (gestión de seguridad para
turismo de aventura), numeral 6.1.1 (acciones para abordar riesgos y
oportunidades) y su Anexo A. Tu trabajo tiene DOS partes distintas:
identificar filas a partir EXCLUSIVAMENTE de los datos del cliente, y VALORAR
cada fila aplicando la metodología (eso es trabajo técnico tuyo, obligatorio).

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema de abajo.
2. DATOS DEL CLIENTE (activity, hazard, risk_description, affected,
   existing_controls, responsible): salen SOLO del contexto. NUNCA los
   inventes; sin dato => null. "existing_controls" se llena con los controles
   que el cliente YA declaró y que apliquen a esa fila; "responsible" con el
   rol del organigrama del cliente que plausiblemente lo asume (p. ej. el
   coordinador de operaciones); si no hay base, null.
3. VALORACIÓN METODOLÓGICA (probability, severity, risk_level, residual_risk):
   es TU obligación técnica y NO es un dato del cliente. Asígnala en el 100%
   de las filas aplicando la metodología declarada; PROHIBIDO dejarla en null:
   - probability: {Baja / Media / Alta} según la naturaleza del peligro, la
     exposición descrita y la casuística del contexto.
   - severity: {Leve / Moderada / Grave} según la peor consecuencia razonable
     descrita en "risk_description".
   - risk_level: {Bajo / Medio / Alto} = cruce probabilidad × severidad
     (Alta×Grave=Alto; Baja×Leve=Bajo; combinaciones intermedias=Medio,
     subiendo un nivel si la severidad es Grave).
   - residual_risk: nivel remanente TRAS los "existing_controls" de la fila
     (si no hay controles declarados, igual al risk_level). El riesgo cero no
     existe en aventura: nunca "Nulo" ni vacío.
4. "proposed_actions" de cada fila: DERÍVALAS de los controles,
   mantenimientos, capacitaciones y protocolos que el cliente ya describió;
   NUNCA inventes recursos o prácticas que el cliente no tenga.
5. "methodology": si el cliente no declaró una metodología propia, describe la
   del Anexo A con las escalas de la regla 3 (contexto → identificación →
   valoración probabilidad×severidad → controles → riesgo residual). Eso es
   texto metodológico estándar, no un dato del cliente.
6. "scope": además del alcance, incorpora el CONTEXTO del análisis derivado
   del contexto real del cliente: responsable del análisis (el rol que lidera
   el SGS), lugares y fronteras de la operación, duración típica, interfaces
   (transporte, alimentación, autoridades, apoyo médico) y competencias o
   vestimenta exigidas al participante. Omite lo que el contexto no soporte.
7. COBERTURA EN DOS PLANOS (obligatoria): además de las filas por actividad,
   incluye filas de riesgos de PROCESOS/NEGOCIO y continuidad derivadas del
   contexto real (p. ej. dependencia de proveedores o repuestos, temporada de
   lluvias/estacionalidad, rotación o escasez de personal, fallas de
   comunicación radio-base, pérdida de RNT o incumplimiento legal, daño
   reputacional), con activity = "Negocio / Procesos", valoradas igual que
   las demás.
8. ESCENARIOS DEL CONTEXTO COLOMBIANO: cuando apliquen a la geografía y a la
   operación declaradas, incluye como filas valoradas: creciente súbita /
   avenida torrencial (operación en río), tormenta eléctrica, sismo, y
   robo/hurto en zonas de operación.
9. "opportunities": son oportunidades de mejora reales derivadas del contexto;
   estructura CADA una con impact, actions, responsible, timeline e indicator
   derivados de los planes y recursos del cliente. Sin base para una celda =>
   null.

PRECEDENCIA DE FUENTES (crítico):
- El contexto incluye un "inventario" con la operación REAL del cliente,
  agrupada por categoría. Si el inventario tiene ítems en las categorías
  "actividad", "vehiculo", "equipo" o "riesgo", esos ítems son la ÚNICA fuente
  para las filas de la matriz. En ese caso NO uses onboarding_data.activities
  para generar filas: IGNÓRALO.
- Usa onboarding_data.activities SOLO si el inventario no tiene ningún ítem en
  esas cuatro categorías.

CÓMO MAPEAR EL INVENTARIO:
- "riesgo": genera UNA fila por cada ítem (peligro ya identificado por el
  cliente), conservando su nombre y atributos.
- "actividad": genera al menos una fila por cada actividad del inventario.
- "vehiculo"/"equipo": genera filas para los peligros que se deriven de cada uno
  (si hay una cuatrimoto, debe aparecer su riesgo de volcamiento).
- Deben aparecer TODOS los ítems relevantes del inventario, no una muestra.

=== CONTEXTO DE LA EMPRESA (onboarding_data + inventario operativo real) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 6.1.1 / Anexo A) ===
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

-- ---------------------------------------------------------------------
-- MA-03 · equipos v3: tipo y frecuencia de inspección = prescripción.
-- ---------------------------------------------------------------------

update public.prompt_versions
set is_active = false
where module = 'generation' and document_type = 'manual_inspeccion_equipos';

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'manual_inspeccion_equipos',
  'v3',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (turismo de aventura),
numeral 8.1 (control operacional) y Anexo A. Tu trabajo NO es redactar prosa
libre, sino EXTRAER y ESTRUCTURAR las variables del Manual de inspección y
mantenimiento de equipos: los EQUIPOS salen exclusivamente de los datos del
cliente; el RÉGIMEN DE INSPECCIÓN lo prescribes tú como contenido técnico.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema de abajo.
2. DATOS DEL CLIENTE: NUNCA inventes equipos, estados, criterios ni fechas que
   el cliente no haya dado. Si un dato propio del cliente no está en el
   contexto, deja el campo en null. El sistema lo marcará como [PENDIENTE].
3. "equipment_items" DEBE derivarse EXCLUSIVAMENTE de las claves
   equipo_<actividad> de "activity_fields" (p.ej. equipo_rafting, equipo_buceo).
   Genera una fila por cada equipo/elemento LISTADO dentro de esas claves,
   asociado a su actividad. IGNORA por completo cualquier mención de actividades o
   equipos que aparezca en "scope", "activities" u otros campos: si una actividad
   NO tiene su clave equipo_<actividad> con contenido, NO generes ninguna fila
   para ella. No inventes equipos que el cliente no listó.
4. PRESCRIPCIÓN TÉCNICA OBLIGATORIA: "inspection_type" y "frequency" son
   prescripciones de este manual, NO datos que se le piden al cliente.
   Asígnalas en el 100% de las filas; PROHIBIDO dejarlas en null:
   - Usa lo que el cliente describió para ese equipo o para equipos similares
     ("inspección visual diaria/antes de cada salida" → previa a uso;
     "revisión técnica mensual/trimestral/semestral" → periódica).
   - Si el cliente no describió nada, prescribe el estándar de la industria
     según la naturaleza del equipo: EPP y equipo usado en cada salida
     (cascos, chalecos, arneses, calzado, remos, embarcaciones) → "previa a
     uso" con frecuencia "antes de cada salida"; equipo técnico, de rescate,
     de comunicación o de respaldo → "periódica" con frecuencia mensual,
     trimestral o semestral según su criticidad; todo equipo tras golpe,
     sobrecarga o evento crítico → revisión "especial" (menciónalo donde el
     schema lo permita).
5. "state" usa el conjunto {Ok, A revisar, En cuarentena, De baja}; por defecto
   "Ok" solo si el cliente no indica otro estado. "inspection_type" usa
   {previa a uso, especial, periódica}.

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

-- El patrón fable5 de cobertura de equipos decía "nunca se asigna una
-- frecuencia inventada": con la decisión de Jan el régimen es prescripción
-- técnica del manual. Se reformula manteniendo la exigencia de cobertura.
update public.generation_patterns
set description =
  'Cobertura total de la matriz: cada equipo listado debe tener asignados tipo de inspección '
  '(previa a uso / periódica / especial) y frecuencia (antes de cada salida, diaria, mensual, '
  'trimestral, semestral o anual). El régimen de inspección es PRESCRIPCIÓN TÉCNICA del manual: '
  'se asigna siempre, tomando lo que el cliente describió para ese equipo o, en su defecto, el '
  'estándar del fabricante/industria para ese tipo de equipo. Lo que nunca se inventa son los '
  'equipos mismos ni estados/fechas que el cliente no declaró.'
where source = 'fable5-engine'
  and document_type = 'manual_inspeccion_equipos'
  and description like 'Cobertura total%';
