-- =====================================================================
-- generation_patterns: gaps del prompt "Fable 5 Engine" (2026-07-17).
--
-- Jan aportó un prompt de reglas por numeral ISO 21101. La mayoría ya
-- existía como patrones de las capacitaciones (sesion-XX); aquí entran
-- SOLO los 8 gaps reales, reformulados para respetar la regla
-- anti-alucinación: el patrón exige que el documento DEFINA el campo,
-- pero el valor lo aporta el cliente o queda [PENDIENTE]/subsanación.
-- Nunca se impone un dato operativo inventado.
--
-- Excluido a propósito (ver docs/integracion-fable5-2026-07-17.md):
--   - "Zero-Null Policy" inciso (a) — derivar de "buenas prácticas de
--     industria" contradice la regla de oro anti-alucinación.
--   - Escala Severidad{Leve..Catastrófica}×Probabilidad{Baja,Media,Alta}
--     — choca con la metodología de sesion-15 y con la pregunta 3
--     pendiente de Felipe (revision-coherencia-2026-07-16).
--
-- Rollback: delete from generation_patterns where source = 'fable5-engine';
-- =====================================================================

insert into public.generation_patterns (document_type, numeral, pattern_type, description, source)
values
  (
    'matriz_riesgos', '6.1.1', 'requisito',
    'Ninguna fila de la matriz se acepta con valoración incompleta: consecuencia/severidad, '
    'probabilidad, nivel de riesgo inicial y riesgo residual deben quedar diligenciados en el '
    '100% de las filas, usando las definiciones cualitativas de la metodología declarada. Si el '
    'cliente no aportó base para valorar un riesgo, el campo queda [PENDIENTE] y se subsana con '
    'él; nunca se inventa la valoración.',
    'fable5-engine'
  ),
  (
    'gestion_incidentes', '8.3', 'requisito',
    'Todo accidente, y todo incidente con potencial significativo, abre investigación con técnica '
    'de análisis de causa raíz (p. ej. los 5 porqués) y un plazo máximo definido en el '
    'procedimiento para emitir el acta/informe de investigación (referencia de auditoría: no '
    'mayor a 5 días hábiles). Reponer o corregir lo inmediato no cierra el evento: se exige '
    'causa raíz y acción correctiva verificable.',
    'fable5-engine'
  ),
  (
    'gestion_incidentes', '8.3', 'requisito',
    'El procedimiento define explícitamente el período de retención y conservación de los '
    'registros de incidentes (formatos diligenciados y actas de investigación) y su ubicación en '
    'la matriz de control de registros. El período lo confirma el cliente (referencia de '
    'industria: mínimo 5 años); si no lo ha definido, queda [PENDIENTE] para subsanación.',
    'fable5-engine'
  ),
  (
    'plan_emergencias', '8.2', 'requisito',
    'El plan incluye una cláusula de protección de datos personales: cómo se recaban, dónde se '
    'almacenan y quién puede acceder en emergencia a las fichas médicas y datos de contacto de '
    'los participantes, con acceso restringido y confidencialidad conforme a la Ley 1581 de 2012. '
    'Si el registro del participante se hace en una plataforma digital, el plan describe ese '
    'mecanismo real, no uno genérico en papel.',
    'fable5-engine'
  ),
  (
    'manual_inspeccion_equipos', '8.1', 'requisito',
    'Cobertura total de la matriz: cada equipo listado debe tener asignados tipo de inspección '
    '(preoperacional / periódica / especial) y frecuencia (antes de cada salida, diaria, mensual, '
    'trimestral, semestral o anual). Un equipo sin tipo o frecuencia es hallazgo; si el cliente '
    'no lo definió, el campo queda [PENDIENTE] para subsanación — nunca se asigna una frecuencia '
    'inventada.',
    'fable5-engine'
  ),
  (
    'manual_inspeccion_equipos', '8.1', 'requisito',
    'El programa de inspección preoperacional asigna explícitamente las obligaciones del guía o '
    'líder de actividad: verificar cada equipo antes del uso, registrar la revisión en el control '
    'de entrada/salida y retirar a cuarentena cualquier equipo con duda razonable, sin necesidad '
    'de autorización previa.',
    'fable5-engine'
  ),
  (
    'manual_inspeccion_equipos', '8.1', 'requisito',
    'El manual incorpora criterios de vida útil máxima por tipo de equipo según el fabricante y '
    'criterios de baja/decomiso automático (vencimiento de vida útil, daño estructural, '
    'exposición a evento crítico), vinculados a la hoja de vida individual del equipo.',
    'fable5-engine'
  ),
  (
    'manual_perfiles_cargos', '5.3', 'requisito',
    'El perfil de la alta dirección/gerencia define requisitos propios: experiencia mínima en '
    'dirección de operaciones (referencia: 3-5 años) y formación en sistemas de gestión de '
    'seguridad. Cada perfil operativo declara sus certificaciones vigentes exigibles (primeros '
    'auxilios/WFR, rescate específico de la actividad, tarjeta o certificación de guía) '
    'soportadas en la hoja de vida.',
    'fable5-engine'
  );
