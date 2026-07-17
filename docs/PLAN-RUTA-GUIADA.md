# Plan: ruta guiada por pasos — "un paso, un documento"

> Pedido de Jan tras la sesión con Felipe (2026-07-17): el software debe
> guiar al empresario POR PASOS ("Paso 1: alcance… ¿arrancamos?"), un
> documento por paso, hasta cubrir el árbol documental del kit MinCIT.
> Fuente de verdad del corpus: Drive "Formularios" — verificado hoy contra
> el espejo local `knowledge-base/formatos/` (cero archivos nuevos desde
> 2026-07-13). Clasificación por archivo: `docs/ARBOL-DOCUMENTAL.md`.

## La ruta de 15 pasos (Fase GEN del árbol)

Orden = el orden natural de implementación de la norma (el mismo que usan la
Guía de implementación MinCIT y las capacitaciones). El alcance va primero
porque es variable de entrada de todos los demás.

| Paso | Documento | Numeral | Hoy |
|---|---|---|---|
| 1 | Alcance del SGSTA | 4.3 | **NUEVO** (1 página; alimenta a todos) |
| 2 | Matriz de partes interesadas | 4.2 | **NUEVO** |
| 3 | Acta de compromiso de la gerencia | 5.1 | **NUEVO** (corto, firma del gerente) |
| 4 | Política de seguridad (PO-01) | 5.2 | ✅ existe |
| 5 | Manual de perfiles de cargos (MA-02) | 5.3 | ✅ existe |
| 6 | Procedimiento de riesgos y oportunidades | 6.1.1 | **NUEVO** |
| 7 | Matriz de riesgos y oportunidades (MT-04) | 6.1.1 | ✅ existe |
| 8 | Matriz de requisitos legales | 6.1.3 | **NUEVO** (RNT, NTS-AV, SNGRD por actividad) |
| 9 | Matriz de objetivos de seguridad | 6.2 | **NUEVO** (las variables ya viven en PO-01) |
| 10 | Comunicación, participación y consulta (PR-07) | 7.4 | ✅ existe |
| 11 | Procedimiento de control de información documentada | 7.5.1 | **NUEVO** (el listado maestro sale gratis de `documents`) |
| 12 | Planificación y control operacional | 8.1 | **NUEVO** (normas + aspectos a controlar por actividad) |
| 13 | Manual de inspección de equipos (MA-03) | 8.1 | ✅ existe |
| 14 | Plan de emergencias (PL-01) | 8.2 | ✅ existe |
| 15 | Gestión de incidentes (PR-02) | 8.3 | ✅ existe |

**Fase 2 de la ruta (después de validar los 15):** proveedores (8.1),
auditoría interna (9.2), revisión por la dirección (9.3), acciones
correctivas y de mejora (10.1), caracterización de procesos (4.4). Los
formatos VIVOS (asistencia, EPP, encuesta, mantenimiento…) siguen el roadmap
de sprints terreno del ARBOL-DOCUMENTAL — no son pasos de esta ruta, son la
app diaria.

## Cómo cambia el software (fases de construcción)

### Fase 0 — Prerrequisitos de conocimiento (½ día)
- Aplicar **0044** (`knowledge_chunks` acepta source `guias`) — escrita,
  bloqueada por permiso.
- Re-correr `seed_knowledge.py --source guias` (319 chunks ya validados).
- Seed nuevo `formatos_mincit`: instrucciones de diligenciamiento de cada
  molde .docx/.xlsx del kit → chunks por numeral (el RAG del paso N recibe
  el "cómo se llena" oficial de ese documento).

### Fase 1 — La ruta como DATO (1 día)
- Migración: tabla `document_roadmap` (step_order, document_type, title,
  numeral, enabled). Los pasos son datos, no código (regla de oro 3): Felipe
  puede reordenar o agregar pasos sin deploy.
- `extraction_checklist` ya mapea field_key → document_type: es el puente
  que agrupa las preguntas de cada paso.

### Fase 2 — Onboarding guiado por pasos (2-3 días) ⭐ el corazón del pedido
- `onboarding/service.py`: el backend (autoridad del flujo) agrupa los
  pendientes por el documento del PASO ACTIVO: primero los universales
  mínimos (identidad de la empresa), luego SOLO los campos del paso en curso.
- Respuesta del chat gana `current_step {n, total, document_type, title,
  fields_done/fields_total}` para que el frontend pinte el progreso.
- Al completar los campos de un paso, el chat lo anuncia y OFRECE generar:
  "Listo el paso 7: tenemos todo para tu Matriz de riesgos. ¿La genero?"
  → confirmación del usuario → genera → muestra score de calidad → paso
  siguiente. (La generación y la calidad ya existen; solo se orquestan.)
- Prompt onboarding v6 (migración): anuncia el paso al abrir la pregunta
  ("Paso 4 de 15 — Política de seguridad: …") y mantiene TODAS las reglas
  v5 (aptitud, correcciones, multi-actividad, confirmaciones).
- GET `/onboarding/roadmap`: estado de los 15 pasos (datos %, generado,
  score, aprobado) — la fuente del stepper y del dashboard de cumplimiento.

### Fase 3 — Frontend: stepper de la ruta (2 días)
- Vista "Tu ruta a la certificación": 15 tarjetas-paso con estado
  (bloqueado → en captura → listo para generar → generado → aprobado),
  la actual resaltada, CTA "continuar en el chat" / "generar" / "descargar".
- El chat muestra la píldora del paso activo sobre el input.

### Fase 4 — Los 8 documentos nuevos (5-8 días, uno a uno)
Por cada documento (orden: 4.3 → 6.2 → 5.1 → 4.2 → 6.1.1 → 6.1.3 → 7.5.1 → 8.1):
1. Molde del kit (`formatos/<numeral>/…`) → plantilla del generador
   (FelipeDocxBuilder / builder xlsx ya existentes).
2. Schema Pydantic de variables + generador + registro en `_REGISTRY`.
3. Filas de `extraction_checklist` (las preguntas del paso) — desde los
   talleres del kit (el taller de alcance, el de partes interesadas…).
4. Prompt v1 en `prompt_versions` (migración por doc).
5. Test + generación real en el tenant piloto.
La calidad (Auditor) los evalúa GRATIS: ya es genérica por document_type.
El más barato primero: 6.2 objetivos (variables ya capturadas por PO-01) y
5.1 acta (media página con datos que ya tenemos).

### Fase 5 — Cierre (1 día)
- `document_codes` para los 8 tipos nuevos (dato por tenant, nunca se
  adivina), export con logo/código por tenant, memoria y docs.

## Riesgos y decisiones para Felipe
- **Orden de los pasos**: propuesto arriba; Felipe puede reordenarlo (por
  eso es dato).
- **Cuota Gemini**: 15 generaciones + evaluaciones por tenant multiplican
  llamadas; visto el free tier, presupuestar el paso a plan pago antes de
  onboardear clientes reales.
- **Matriz de requisitos legales (paso 8)**: el contenido legal base por
  actividad (Res. 0612/2024, NTS-AV) debe validarlo Felipe — el motor no
  inventa normas.
- El onboarding actual (lineal) sigue funcionando durante la transición: el
  modo guiado es una reorganización del MISMO checklist, no un rompimiento.
