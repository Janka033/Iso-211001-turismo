# ColAdventure

SaaS multi-tenant de cumplimiento **NTC-ISO 21101** (turismo de aventura, Colombia).
La IA extrae datos a JSON estructurado y `python-docx`/`openpyxl` los inyectan en
plantillas fijas — la IA **no** redacta libre. Eso es lo que nos hace auditables.

Contexto completo en [`CLAUDE.md`](./CLAUDE.md) (Claude Code) y [`AGENTS.md`](./AGENTS.md) (Codex).

## Estructura

```
backend/        FastAPI (monolito modular: router → service → repository)
frontend/       Next.js 14 (App Router) + TypeScript + Tailwind
supabase/       Migraciones SQL versionadas (schema + RLS + access token hook)
scripts/        seed_knowledge.py (vectoriza la norma + ACOTUR a knowledge_chunks)
knowledge-base/ PDFs fuente (no versionados — copyright ICONTEC)
```

## Arranque local

Requisitos: Python 3.11+, Node 18+, [Supabase CLI](https://supabase.com/docs/guides/cli), Docker (Supabase + Redis).

```bash
# 1. Base de datos local (aplica las migraciones de supabase/migrations/)
supabase start

# 2. Backend
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env        # rellenar secrets
uvicorn app.main:app --reload

# 3. Frontend
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

## Comandos

| Acción            | Comando                                              |
| ----------------- | ---------------------------------------------------- |
| Backend dev       | `cd backend && uvicorn app.main:app --reload`        |
| Frontend dev      | `cd frontend && npm run dev`                         |
| Lint backend      | `ruff check backend/`                                |
| Lint frontend     | `cd frontend && npm run lint`                        |
| Tests backend     | `pytest backend/tests/`                              |
| Seed conocimiento | `python scripts/seed_knowledge.py --source norma`    |

## Base de conocimiento

La norma NTC-ISO 21101 y el Módulo 2 de ACOTUR van a `knowledge_chunks` (pgvector)
vía `scripts/seed_knowledge.py`. Coloca los PDFs en `knowledge-base/` (no se versionan).

> ⚠️ **Legal:** la NTC-ISO 21101 es copyright de ICONTEC ("prohibida su reproducción").
> Confirmar con Felipe el derecho a indexar/servir contenido derivado antes del lanzamiento comercial.
