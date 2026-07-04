-- =====================================================================
-- Dimensión POR ACTIVIDAD de extraction_checklist (Parte B).
--
-- Hasta ahora la checklist solo tenía la Parte A (transversal, 0007–0010).
-- Este cambio agrega la columna `activity` (NULL = universal / Parte A) y
-- siembra los requisitos específicos de las 13 actividades de aventura
-- (fuente: ACTIVIDADES.md — Resolución 0612/2024 + NTS-AV 010–015 + ACOTUR).
--
-- Regla de oro 3: checklist es DATO, no código. Vive aquí, nunca hardcodeado.
--
-- No rompe los 4 documentos ya en producción: la selección activity-aware
-- llega en la Fase 2. Mientras tanto, get_checklist filtra `activity IS NULL`
-- (guarda en generation/repository.py y quality/repository.py), así los 4
-- documentos siguen viendo EXACTAMENTE su Parte A y las filas Parte B quedan
-- latentes.
-- =====================================================================

-- 1. Columna nueva. NULL = fila universal (Parte A); un slug = fila por actividad.
alter table public.extraction_checklist
  add column if not exists activity text;

-- 2. La identidad de una fila de checklist pasa a ser (document_type, field_key,
--    activity). `nulls not distinct` (PG15+) mantiene la Parte A única sobre
--    (document_type, field_key) —todos sus `activity` son NULL y se tratan como
--    iguales— y deja coexistir las filas por actividad. Postgres del proyecto: 17.
alter table public.extraction_checklist
  drop constraint if exists extraction_checklist_document_type_field_key_key;
alter table public.extraction_checklist
  add constraint extraction_checklist_doc_field_activity_key
  unique nulls not distinct (document_type, field_key, activity);

-- Índice para la consulta activity-aware de la Fase 2 (universal + actividades).
create index if not exists idx_extraction_checklist_doc_activity
  on public.extraction_checklist (document_type, activity);

-- 3. Seed Parte B. field_key = <categoria>_<slug>; activity = <slug>.
--    `b` = 13 actividades × 5 categorías extractables (NO se siembra `base`,
--    que es referencia normativa, no un campo que se le pregunta al cliente).
--    `m` = mapeo categoría → document_type(s) destino (ACTIVIDADES.md):
--      equipo       -> matriz_riesgos + plan_emergencias
--      competencias -> politica_seguridad + matriz_riesgos
--      emergencias  -> plan_emergencias
--      riesgos      -> matriz_riesgos
--      seguimiento  -> gestion_incidentes  ("el que corresponda")
--    El JOIN expande las categorías que alimentan 2 documentos => ~91 filas.
insert into public.extraction_checklist
  (document_type, numeral, field_key, description, required, activity)
select
  m.document_type,
  m.numeral,
  b.categoria || '_' || b.slug,
  b.description,
  true,
  b.slug
from (values
  -- (slug, categoria, description)  — texto fiel a ACTIVIDADES.md
  ('rafting','equipo','Balsa, remos, chaleco salvavidas (PFD), casco, embarcación/kayak de seguridad, cuerda y equipo de rescate (longitudes y diámetros según NTS-AV 010).'),
  ('rafting','competencias','Guía con tarjeta profesional + certificación en primeros auxilios + formación y experiencia en rafting.'),
  ('rafting','emergencias','Recuperación de nadador, posición de nado defensivo, rescate con cuerda, comunicación a base.'),
  ('rafting','riesgos','Volcamiento, nadador en rápido, atrapamiento, hidráulicos, hipotermia, colisión con rocas, creciente súbita.'),
  ('rafting','seguimiento','Inspección pre-descenso de equipo, registro de incidentes, simulacro de rescate; criterios de aptitud por clase de rápido y edades.'),

  ('rapel','equipo','Cuerdas (dinámicas/estáticas), arnés, descensor, mosquetones de seguro, casco, guantes, anclajes.'),
  ('rapel','competencias','Técnicas de anclaje, montaje de reuniones y rescate en cuerda; primeros auxilios.'),
  ('rapel','emergencias','Rescate en cuerda, descuelgue de accidentado.'),
  ('rapel','riesgos','Fallo de anclaje o cuerda, caída, descontrol de descenso, golpe contra pared.'),
  ('rapel','seguimiento','Inspección de cuerdas y anclajes, registro de incidentes, simulacro.'),

  ('espeleologia','equipo','Casco con iluminación + luz de respaldo, arnés, cuerdas, descensores/ascensores, EPP; clasificación de la cavidad.'),
  ('espeleologia','competencias','Progresión vertical y rescate en cavernas; primeros auxilios.'),
  ('espeleologia','emergencias','Rescate vertical, evacuación de lesionado, protocolo de extravío, hipotermia.'),
  ('espeleologia','riesgos','Caída en pozos, hipotermia, extravío, inundación súbita, mala calidad del aire, derrumbe.'),
  ('espeleologia','seguimiento','Inspección de equipo vertical, registro de incidentes, simulacro.'),

  ('parapente','equipo','Ala biplaza certificada, arneses, separadores, paracaídas de emergencia homologado, mosquetones, casco, radio; bitácora de revisión del ala.'),
  ('parapente','competencias','Título biplaza y licencia deportiva vigente; zona de vuelo inscrita en Aerocivil por un aeroclub adscrito a la federación.'),
  ('parapente','emergencias','Uso de paracaídas de emergencia, aterrizaje en árbol/agua, caída en cableado, pérdida de comunicación.'),
  ('parapente','riesgos','Plegada del ala, turbulencia/rotores, cizalladura, colisión en ladera, aterrizaje fuera de zona, viento fuera de rango.'),
  ('parapente','seguimiento','Bitácora de revisión periódica del ala, registro de plegadas/abortos, simulacro.'),

  ('cabalgata','equipo','Montura y arreos en buen estado, casco; control del estado de salud del animal.'),
  ('cabalgata','competencias','Manejo equino (NTS-GT 011); primeros auxilios.'),
  ('cabalgata','emergencias','Control del animal, atención de caídas, evacuación.'),
  ('cabalgata','riesgos','Caída del jinete, coz o mordedura, desbocamiento, terreno irregular.'),
  ('cabalgata','seguimiento','Control del estado del animal, registro de incidentes, mantenimiento de arreos.'),

  ('canyoning','equipo','Cuerdas, arnés, descensor, mosquetones, casco, neopreno, cuerdas de rescate.'),
  ('canyoning','competencias','Anclajes, rescate en cuerda y lectura de caudal (NTS-GT 013); primeros auxilios.'),
  ('canyoning','emergencias','Rescate en cuerda, descuelgue, evacuación de cañón.'),
  ('canyoning','riesgos','Fallo de anclaje, caída, hidráulicos, hipotermia, atrapamiento de cuerda.'),
  ('canyoning','seguimiento','Inspección de equipo y anclajes, registro de incidentes, simulacro; control de caudal y clima.'),

  ('buceo','equipo','Regulador, BCD, tanque, computador/profundímetro, manómetro, traje, sistema de aire de reserva; mantenimiento y pruebas hidrostáticas de cilindros.'),
  ('buceo','competencias','Certificación de buceo (PADI/NAUI/SSI o equivalente), divemaster/instructor según rol; O₂ de emergencia y RCP.'),
  ('buceo','emergencias','Ascenso de emergencia, suministro de O₂, evacuación a cámara hiperbárica.'),
  ('buceo','riesgos','Enfermedad descompresiva, barotrauma, pánico/ahogamiento, corrientes, fallo de equipo de aire.'),
  ('buceo','seguimiento','Control de mantenimiento y pruebas hidrostáticas, bitácora de inmersiones, simulacro de O₂.'),

  ('canopy','equipo','Cable de acero, poleas, arnés, sistema de frenado, líneas de vida/doble conexión, casco, guantes; inspección de tensión y puntos fijos.'),
  ('canopy','competencias','Trabajo en alturas y rescate en línea; primeros auxilios.'),
  ('canopy','emergencias','Rescate en línea, evacuación desde plataforma.'),
  ('canopy','riesgos','Fallo de cable/anclaje/polea, colisión en plataforma, frenado deficiente, caída desde altura.'),
  ('canopy','seguimiento','Inspección de tensión de cable, poleas y puntos fijos; registro de incidentes; simulacro de rescate en línea.'),

  ('senderismo','equipo','Botiquín, GPS/mapa, comunicaciones, equipo de abrigo, hidratación.'),
  ('senderismo','competencias','Guía de alta montaña; primeros auxilios en zonas remotas (WFR).'),
  ('senderismo','emergencias','Evacuación, hipotermia/mal de altura, extravío, tormenta eléctrica.'),
  ('senderismo','riesgos','Extravío, caídas, hipotermia/mal de altura, deshidratación, cruces de río.'),
  ('senderismo','seguimiento','Registro de incidentes, control de botiquín y comunicaciones, simulacro.'),

  ('atv','equipo','Casco, protecciones, vehículo con mantenimiento documentado, kit de herramientas.'),
  ('atv','competencias','Licencia y manejo del vehículo; briefing de manejo al participante.'),
  ('atv','emergencias','Atención de caídas y colisión, evacuación.'),
  ('atv','riesgos','Volcamiento, colisión, atropello, terreno inestable, velocidad excesiva.'),
  ('atv','seguimiento','Mantenimiento documentado del vehículo, registro de incidentes, registro de aptitud y briefing.'),

  ('kayak','equipo','Kayak, pala, chaleco (PFD), casco, faldón.'),
  ('kayak','competencias','Autorrescate y técnicas de rescate; primeros auxilios.'),
  ('kayak','emergencias','Recuperación en agua, autorrescate, comunicación.'),
  ('kayak','riesgos','Volcamiento, atrapamiento, hidráulicos, hipotermia.'),
  ('kayak','seguimiento','Inspección de equipo, registro de incidentes, simulacro.'),

  ('ciclomontanismo','equipo','Bicicleta con mantenimiento, casco, protecciones, kit de reparación.'),
  ('ciclomontanismo','competencias','Manejo técnico y mecánica básica; primeros auxilios.'),
  ('ciclomontanismo','emergencias','Atención de caídas, evacuación.'),
  ('ciclomontanismo','riesgos','Caída, colisión, terreno técnico, fallo mecánico.'),
  ('ciclomontanismo','seguimiento','Mantenimiento de bicicletas, registro de incidentes, briefing.'),

  ('escalada','equipo','Cuerdas, arnés, casco, sistema de aseguramiento, mosquetones, anclajes/seguros, pies de gato.'),
  ('escalada','competencias','Técnicas de aseguramiento y rescate en pared; primeros auxilios.'),
  ('escalada','emergencias','Rescate en pared, descuelgue, evacuación.'),
  ('escalada','riesgos','Caída, fallo de anclaje o seguro, desprendimiento de roca, golpe.'),
  ('escalada','seguimiento','Inspección de equipo y anclajes, registro de incidentes, simulacro.')
) as b(slug, categoria, description)
join (values
  ('equipo','matriz_riesgos','6.1.1'),
  ('equipo','plan_emergencias','8.2'),
  ('competencias','politica_seguridad','5.2'),
  ('competencias','matriz_riesgos','6.1.1'),
  ('emergencias','plan_emergencias','8.2'),
  ('riesgos','matriz_riesgos','6.1.1'),
  ('seguimiento','gestion_incidentes','8.3')
) as m(categoria, document_type, numeral)
  on m.categoria = b.categoria
on conflict on constraint extraction_checklist_doc_field_activity_key do nothing;
