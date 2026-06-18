# CLAUDE.md — ColAdventure

> Contexto persistente para Claude Code y Codex. Se carga en cada sesión.
> Para Codex: ver `AGENTS.md` (mismo contexto). Skills en `.claude/skills/` (Claude Code) y `.agents/skills/` (Codex).

## Qué es ColAdventure

SaaS multi-tenant que automatiza el cumplimiento de la **NTC-ISO 21101** (sistema de gestión de seguridad para turismo de aventura) en Colombia. Una empresa de turismo responde un onboarding conversacional; la IA extrae sus datos operativos y el sistema genera el árbol documental que necesita para certificarse ante un organismo acreditado por ONAC y mantener su RNT.

**Regla mental central:** la IA NO redacta documentos libremente. Extrae variables a un JSON estructurado, se valida con Pydantic, y `python-docx`/`openpyxl` inyectan esas variables en plantillas fijas. La IA controla el contenido inteligente; el sistema controla estructura, formato y coherencia. Esto es lo que evita alucinaciones y nos hace auditables.

## Stack

- **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind CSS
- **Backend:** FastAPI (Python 3.11+), jobs async con BackgroundTasks (Celery en Fase 2)
- **DB:** Supabase (PostgreSQL 15 + pgvector); JSONB para datos sin esquema fijo
- **Caché/sesión:** Redis (contexto conversacional por tenant)
- **IA:** Gemini 2.5 Flash (primario); Claude/OpenAI como fallback vía patrón Strategy
- **Validación IA:** Pydantic v2
- **Generación:** python-docx (.docx), openpyxl (.xlsx) — inyección en plantillas, no texto libre
- **Deploy:** Vercel (front), Railway (back), Supabase Cloud (DB)

## Arquitectura: monolito modular

Un solo proceso FastAPI. Cada módulo tiene `router.py`, `service.py`, `repository.py`, `schemas.py`. Módulos: `auth`, `onboarding`, `generation`, `dashboard`, `assistant`, `admin`, `notifications`.

**Cadena obligatoria:** router → service → repository → DB. El router nunca llama a la DB. La lógica vive en service. El repository es el ÚNICO que habla con Supabase. Un módulo nunca importa el repository de otro; se comunican vía services.

**Patrones:** Strategy (`AIProvider`), Repository (acceso a DB), Factory (`DocumentFactory` → generador .docx/.xlsx), Template Method (generadores), Observer (onboarding).

## Reglas de oro (no negociables)

1. **La IA solo devuelve JSON estructurado.** Nunca redacta el documento final. Valida con Pydantic antes de inyectar en plantilla.
2. **RLS en Supabase desde el día 1.** Aislamiento de tenants a nivel de DB, no solo de aplicación. Ver skill `supabase-rls`.
3. **Checklist, prompts y plantillas son datos, no código.** Viven en DB (`extraction_checklist`, `prompt_versions`, `templates`), nunca hardcodeados.
4. **Separación estricta `onboarding_data` (lo que dijo el cliente) vs `ai_outputs` (lo que interpretó la IA).** Nunca mezclar en el mismo JSONB. Así se regenera sin perder datos del cliente.
5. **Todo acceso a DB pasa por un repository.** Los endpoints nunca tocan Supabase directo.
6. **Cada documento generado guarda su snapshot de reproducibilidad** (`prompt_hash`, `prompt_version`, `rag_chunks_ids`, `template_version`, `model_version`, `variables_snapshot`).
7. **Ningún cambio normativo se despliega solo.** Pasa por `regulatory_changes` con aprobación humana.
8. **Toda llamada a IA pasa por un `AIProvider`.** Nunca el SDK de Gemini directo desde un service.

## Modelo de datos (tablas clave)

`tenants`, `companies`, `onboarding_data` (JSONB, datos crudos del cliente), `ai_outputs` (JSONB, derivados de IA — separado), `extraction_checklist`, `document_status`, `documents` (+ snapshot de reproducibilidad), `document_history`, `chat_messages`, `knowledge_chunks` (pgvector: `source`, `numeral`, `content`, `embedding vector(768)`), `audit_feedback`, `generation_patterns`, `templates`, `prompt_versions`, `regulatory_changes`.

## Convenciones de código

- Python: archivos `snake_case`, clases `PascalCase`, funciones/vars `snake_case`
- TS/React: archivos `kebab-case`, componentes `PascalCase`
- DB: tablas `snake_case` plural, columnas `snake_case`
- Env vars: `UPPER_SNAKE_CASE` — nunca en el repo
- Commits: Conventional Commits. Ramas: `feature/`, `fix/`, `chore/`

**Reglas duras:**
- Todos los endpoints FastAPI tipados con Pydantic. Sin `Any`, sin `dict` sin tipar.
- Toda función que llame a Supabase vive en `repository.py`.
- Los prompts se cargan desde `prompt_versions` (DB), nunca inline en el código.
- Todo endpoint de escritura toma `tenant_id` del JWT, NUNCA del body.
- Tests en `tests/{module}/`, al menos 1 test de integración por endpoint.

## Anti-alucinación (crítico para auditoría)

- Salida de IA en JSON estricto; el prompt incluye el schema Pydantic esperado.
- Validación Pydantic antes de cualquier inyección en plantilla.
- Campos sin dato del cliente → placeholder visible `[PENDIENTE: descripción]`. NUNCA inventar valores.
- `generation_patterns` alimenta el contexto con patrones de rechazo reales de auditores.
- Ver skill `iso-document-generator` para el flujo completo.

## Foco actual del sprint: MVP validado

Objetivo: probar que el motor genera documentos que Felipe (experto ISO/legal, primer cliente) aprueba como "presentables a auditoría", para su empresa real.

**Documentos núcleo del MVP (en este orden):**
1. Política de seguridad (5.2)
2. Matriz de riesgos y oportunidades (6.1.1 + Anexo A)
3. Plan/procedimiento de respuesta a emergencias (8.2)
4. Procedimiento y formato de gestión de incidentes (8.3)

**Definición de "validado" (Definition of Done):**
- Genera el set núcleo sin inventar nada (faltantes = `[PENDIENTE]`).
- Felipe aprueba cada documento, o marca correcciones puntuales.
- Cada corrección se resuelve regenerando (plantilla/variables), sin tocar lógica.
- Cada documento guarda su snapshot de reproducibilidad.
- Meta: ≥80% aprobados por Felipe en la primera pasada.

No construir el árbol documental completo ni features de escala hasta validar este núcleo.

## Base de conocimiento (los PDFs)

La norma NTC-ISO 21101 y el Módulo 2 de ACOTUR (evidencias por numeral) son **datos del producto**, no contexto del agente. Van a `knowledge_chunks` (pgvector) vía `scripts/seed_knowledge.py`, fragmentados por numeral. Guarda los PDFs fuente en `/knowledge-base/` para que el seed los procese; no los pegues en el contexto de Claude Code/Codex (gastan tokens y el agente no los necesita para escribir código — necesita el schema y la estrategia de chunking, no la norma entera).

⚠️ **Legal:** la NTC-ISO 21101 es copyright de ICONTEC ("prohibida su reproducción"). Confirmar con Felipe que se tiene derecho a indexar y servir contenido derivado de la norma antes del lanzamiento comercial.

## Qué NO hacer

- No dejes que la IA escriba el documento final en prosa libre.
- No hardcodees checklist, prompts ni plantillas.
- No mezcles `onboarding_data` con `ai_outputs`.
- No llames a Supabase desde un router o service.
- No pongas `tenant_id` en el body de un request.
- No despliegues cambios normativos sin aprobación.
