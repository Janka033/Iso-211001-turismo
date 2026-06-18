# AGENTS.md — ColAdventure (Codex)

Contexto y reglas del repo para OpenAI Codex. El contexto completo está en `CLAUDE.md` — léelo. Este archivo resume lo operativo.
> Si prefieres una sola fuente de verdad: `ln -s CLAUDE.md AGENTS.md`.

## Qué es

SaaS multi-tenant de cumplimiento NTC-ISO 21101 (turismo de aventura, Colombia). La IA extrae datos a JSON estructurado y `python-docx`/`openpyxl` los inyectan en plantillas fijas — la IA NO redacta libre. Eso es lo que nos hace auditables.

## Comandos

- Backend: `cd backend && uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm run dev`
- Lint: `ruff check backend/` · `npm run lint` (frontend)
- Tests: `pytest backend/tests/` — corre los tests antes de abrir PR
- DB local: Supabase CLI + Redis en Docker

## Reglas de oro (no negociables)

1. La IA solo devuelve JSON; valida con Pydantic antes de inyectar en plantilla. Nunca texto libre.
2. RLS en Supabase desde el día 1 (ver `.agents/skills/supabase-rls`).
3. Checklist, prompts y plantillas viven en DB, no hardcodeados.
4. Nunca mezclar `onboarding_data` (cliente) con `ai_outputs` (IA).
5. Todo acceso a DB pasa por `repository.py`. Routers/services nunca tocan Supabase.
6. Cada documento guarda snapshot de reproducibilidad.
7. `tenant_id` siempre del JWT, nunca del body.
8. Toda llamada a IA pasa por un `AIProvider` (nunca el SDK de Gemini directo).

## Convenciones

Python `snake_case` / clases `PascalCase`; TS/React archivos `kebab-case` / componentes `PascalCase`; tablas `snake_case` plural; env vars `UPPER_SNAKE`; Conventional Commits; ramas `feature/`, `fix/`, `chore/`. Endpoints FastAPI siempre tipados con Pydantic. Tests en `tests/{module}/`, ≥1 de integración por endpoint.

## Foco actual

MVP validado: generar los 4 documentos núcleo (política 5.2, matriz de riesgos 6.1.1, emergencias 8.2, incidentes 8.3) para la empresa de Felipe, que él aprueba como presentables a auditoría. No construir el árbol completo ni escala hasta validar esto.

## PDFs / base de conocimiento

La norma y el módulo ACOTUR van a `knowledge_chunks` vía `scripts/seed_knowledge.py`. No los cargues en el contexto del agente. Detalle en `CLAUDE.md`.
