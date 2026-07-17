# Revisión técnica y normativa — motivos de `coherente=False` (para Felipe)

Fecha: 2026-07-16 · Tenant de prueba: "Rafting Fonce E2E" (datos de rafting río Fonce, San Gil, nivel auditoría) · Evaluador con completitud determinista (fix `9ff4ce1`).

Contexto: tras eliminar los "faltantes fantasma", el `coherente=False` que persiste es el **juicio de coherencia de la IA contra la norma (RAG) y los patrones de auditoría reales** (`generation_patterns`, derivados de tus capacitaciones). Ya no hay errores de payload: cada motivo de abajo es un hallazgo de contenido que pedimos validar (¿exigencia real de auditoría → subsanar/plantilla? ¿o exceso de celo del evaluador → ajustar patrón?).

## Scores finales de la ronda (2026-07-16, tras 2 iteraciones de derivación)

| Documento | Inicial | Final | Coherente |
|---|---|---|---|
| Manual de perfiles y cargos | 95 | 95 | ✔ |
| Política de seguridad | 85 | 85 | ✔ |
| Gestión de incidentes | 55 | **85** | ✔ (informes 8.3.e/j + diferenciación incidente/accidente) |
| Comunicación, participación y consulta | 60 | 78 | ✖ (1 issue: retroalimentación del participante 7.4.3) |
| Matriz de riesgos | 30 | 75 | ✖ (metodología/estructura de plantilla) |
| Plan de emergencias | 40 | 55* | **✔** (los 2 issues de coherencia resueltos) |
| Inspección de equipos | 45 | 55 | ✖ (kayak sin datos + criterios por equipo) |

Promedio: **58.6 → 75.4**. (*) El score del plan quedó dominado por las 6 alertas de patrones que requieren artefactos del cliente o plantilla (mapa UTM, fichas PON, formato de botiquín) — no derivables sin inventar; recordar la varianza del evaluador ±10-15 (no usar el score puntual como gate). Para superar 80 global se necesitan tus decisiones de las preguntas de abajo y/o subsanación del cliente.

## Por documento

### Plan de respuesta a emergencias (8.2)

**Issues de coherencia (vs norma):**
1. No detalla cómo se recaba/almacena/usa la información mínima de participantes (identificación, contacto de emergencia, salud). *Nota técnica: la plataforma YA lo hace en el registro del turista con firma; falta reflejarlo en el documento.*
2. No explicita cómo se informa a los participantes del plan antes de la actividad (más allá de la charla de seguridad).

**Alertas por patrones de auditoría (tus capacitaciones):**
3. Falta mapa técnico de la ruta (coordenadas UTM 18N, curvas de nivel, zonas de riesgo, salidas de emergencia). → **Requiere artefacto del cliente**; no derivable.
4. Botiquín sin formato de revisión, control de caducidad, esquema de dos niveles ni referencia a la Res. 0705 de 2007. → Parcialmente plantilla, parcialmente dato.
5. Sin procedimiento de verificación de comunicaciones antes de cada salida (cobertura/carga/registro). → Derivable de los radios VHF + satelital que el cliente declaró (ajustado en esta ronda).
6. Sin clasificación de emergencias por grados 1–4 con comunicación del grado al activar. → Derivable de la clasificación de eventos del cliente (ajustado en esta ronda).
7. Sin PON/fichas cortas plastificadas por amenaza (hipotermia, atrapamiento, extravío/desaparición, fallecimiento…). → **Candidato a plantilla** (estructura normativa) + dato del cliente por amenaza.
8. Puntos ciegos de comunicación no identificados formalmente; faltan linternas en equipos de emergencia. → Parcialmente derivable ("tramo sin señal celular" declarado).

### Procedimiento de gestión de incidentes (8.3)

1. El paso de reporte no incluye condiciones ambientales, equipo y circunstancias (8.3.e) ni la fuente de la información (8.3.j). → **Contenido normativo del formato**; ajustado en esta ronda para que el procedimiento lo enumere.
2. Sin formatos diferenciados: informe de INCIDENTE vs informe de ACCIDENTE (datos, edad y nacionalidad de la víctima, quiénes intervinieron, medidas correctivas). → Ajustado en esta ronda; validar si el FORMATO anexo también debe duplicarse (cambio de plantilla).

### Manual de inspección y mantenimiento de equipos (8.1)

1. Filas de `equipment_items` con tipo de inspección sin definir donde el cliente sí lo describió (mapeo de extracción; RESUELTO en esta ronda: 6 → 2 pendientes).
2. Kayak de seguridad sin frecuencia ni tipo de inspección: **el cliente no lo especificó** → queda [PENDIENTE] correcto; candidato a subsanación.
3. (v3) Las variables no detallan los **criterios/métodos específicos** de cada inspección (el cliente sí los dio para algunos equipos: "prueba de presión 24 h", "revisión metro a metro") — exigiría un campo nuevo `criteria` en la fila del control y su columna en la plantilla → **decisión de plantilla contigo**.

### Matriz de riesgos y oportunidades (6.1.1) — score 75, sin regenerar

Hallazgos del evaluador (todos de tus patrones): contexto de la matriz incompleto (responsable del análisis, fecha, interfaces, vestimenta); actividades sin clasificar rutinaria/no rutinaria; peligros sin clasificación formal por 4 factores; metodología sin definiciones cualitativas de probabilidad/consecuencia ni revisión anual/30 días; faltan escenarios obligatorios del contexto colombiano (robos/hurtos, sismos, avenidas torrenciales); oportunidades sin estructura (impacto/acciones/responsable/cronograma/indicador). *La estructura por fila (peligro/riesgo/controles/residual) fue elogiada.* → La mayoría son **estructura de plantilla o metodología estándar**, no datos del cliente: decide cuáles subimos a plantilla/prompt.

### Comunicación, participación y consulta (7.4) — score 78

1. Falta el mecanismo específico para que los PARTICIPANTES aporten información que afecte la seguridad (7.4.3). → Derivable parcialmente (declaración de salud pre-embarque); validar si basta o requiere buzón/encuesta post-actividad.

## Preguntas concretas para Felipe

1. ¿Mapa técnico UTM y fichas PON plastificadas son exigencia de primera auditoría o hallazgo menor? (Definen si van a plantilla ya o a fase 2.)
2. ¿El formato de reporte anexo debe partirse en dos (incidente/accidente) como piden tus patrones?
3. Metodología de la matriz: ¿estandarizamos las definiciones cualitativas (Raro <5%… / insignificante…catastrófico) en la plantilla para todos los tenants?
4. ¿Escenarios "contexto colombiano" (robos, sismos, avenidas) deben inyectarse siempre como filas sugeridas de la matriz?
