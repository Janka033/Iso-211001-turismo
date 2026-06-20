# ColAdventure — Frontend

Guía para el desarrollador de frontend. Explica **qué hay hoy, qué funciona, cómo
se conecta al backend y qué sigue**. Para el contexto del producto completo ver el
[`README.md`](../README.md) raíz y [`CLAUDE.md`](../CLAUDE.md).

> **TL;DR del producto:** SaaS multi-tenant que automatiza el cumplimiento de la
> norma NTC-ISO 21101 (turismo de aventura). El cliente registra su operación
> real (inventario + onboarding) y el backend genera documentos auditables
> (.docx/.xlsx) con IA. El frontend es el panel donde el cliente captura sus datos
> y genera/descarga esos documentos.

---

## Stack

- **Next.js 14** (App Router) + **TypeScript** + **Tailwind CSS**
- **Supabase JS** (`@supabase/ssr`) para auth (sesión + JWT)
- Deploy previsto: **Vercel**

## Arranque

```bash
cd frontend
npm install
cp .env.local.example .env.local   # rellenar (ver abajo)
npm run dev                         # http://localhost:3000
```

`.env.local` necesita:

| Variable | Para qué |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | Base del backend FastAPI (p.ej. `http://localhost:8000`) |
| `NEXT_PUBLIC_SUPABASE_URL` | Proyecto Supabase (auth) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Clave pública (anon / `sb_publishable_…`) |

> El backend local actualmente apunta a **Supabase Cloud**. Usuario demo para
> probar: `demo@aventuraandina.com` / `coladventure123`.

Comandos: `npm run dev` · `npm run build` · `npm run lint`

---

## Estructura

```
app/
  page.tsx                      Landing pública (hero por departamento de Colombia)
  login/page.tsx                Login + signup (Supabase auth)
  onboarding/page.tsx           Onboarding conversacional (alimenta onboarding_data)
  dashboard/
    layout.tsx                  Shell del panel (sidebar)
    page.tsx                    Home del panel
    documents-grid.tsx          Generar + descargar los 4 documentos del MVP
    inventario/                 CRUD del inventario operativo + evidencia (fotos)
    logout-button.tsx
components/
  logo.tsx
  landing/                      department-hero, scenes (landing simbólica por región)
  dashboard/sidebar.tsx         Navegación del panel
  onboarding/onboarding-chat.tsx
lib/
  api.ts                        apiBase() — lee NEXT_PUBLIC_API_URL
  documents.ts                  Metadatos de los 4 documentos (espejo del backend)
  inventory.ts                  Categorías y tipos del inventario (espejo del backend)
  departments.ts                Datos de los 18 departamentos para la landing
  supabase/{client,server}.ts   Clientes Supabase (browser / server)
middleware.ts                   Protege rutas /dashboard (redirige a /login sin sesión)
```

---

## Cómo se habla con el backend

El backend es un FastAPI (monolito modular). Patrón de llamada desde el cliente:

```ts
import { apiBase } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

const supabase = createClient();
const { data: { session } } = await supabase.auth.getSession();

const res = await fetch(`${apiBase()}/inventory`, {
  headers: { Authorization: `Bearer ${session.access_token}` },
});
```

**Reglas clave:**
- Toda llamada protegida va con `Authorization: Bearer <access_token>` (el JWT de
  Supabase). El backend saca el `tenant_id` del JWT — **nunca** se manda en el body.
- `apiBase()` lanza error claro si falta `NEXT_PUBLIC_API_URL`.

### Endpoints disponibles

| Método | Ruta | Para qué |
| --- | --- | --- |
| `POST` | `/auth/signup` | Registro |
| `GET`  | `/auth/me` | Datos del usuario/tenant |
| `GET`  | `/onboarding` | Estado del onboarding |
| `PUT`  | `/onboarding` | Merge incremental de respuestas → `onboarding_data` |
| `GET`  | `/inventory` | Lista ítems del inventario (filtro opcional `?category=`) |
| `POST` | `/inventory` | Crea ítem (`category`, `name`, `attributes`) |
| `PUT`  | `/inventory/{id}` | Edita ítem |
| `DELETE` | `/inventory/{id}` | Borra ítem (**204** = borrado real; **404** = no existe/no es tuyo) |
| `POST` | `/inventory/{id}/evidence` | Sube foto de evidencia (multipart) |
| `GET`  | `/inventory/{id}/evidence` | Lista evidencias (URLs firmadas temporales) |
| `GET`  | `/generation/document-types` | Tipos de documento soportados |
| `POST` | `/generation/{document_type}` | Genera el documento (devuelve estado + completitud + `pending_fields`) |
| `GET`  | `/generation/{document_type}/download?version=N` | URL firmada para descargar |

Categorías de inventario (`lib/inventory.ts`): `vehiculo`, `equipo`,
`salida_emergencia`, `guia`, `actividad`, `riesgo`, `contacto_emergencia`, `otro`.
Documentos del MVP (`lib/documents.ts`): `politica_seguridad` (5.2),
`matriz_riesgos` (6.1.1, xlsx), `plan_emergencias` (8.2), `gestion_incidentes` (8.3).

---

## Qué FUNCIONA hoy (end-to-end, verificado contra cloud)

- **Auth** (login/signup) y protección de `/dashboard` vía `middleware.ts`.
- **Landing** pública con hero por departamento.
- **Onboarding conversacional** → persiste en `onboarding_data`.
- **Inventario operativo**: CRUD de ítems por categoría + subida/visualización de
  **fotos de evidencia** (cámara en móvil). Es la base de la **trazabilidad**.
- **Generación de documentos**: desde `documents-grid.tsx` se dispara la generación
  y se descarga el .docx/.xlsx. El motor ya **lee el inventario** y genera listas
  dinámicas reales (N salidas de emergencia, vehículos, riesgos), sin inventar
  datos (los faltantes salen como `[PENDIENTE]`).

---

## Dónde se necesita ayuda (frontend) — TODO

Esto es lo que está crudo o pendiente de pulir. Orden sugerido, no estricto:

1. **Pulir el panel de documentos** (`documents-grid.tsx`): mostrar mejor el estado
   (`pending`/`generating`/`generated`), la **completitud %** y la lista de
   `pending_fields` que devuelve el backend, con feedback de carga/errores.
2. **UX del inventario** (`inventario/`): validación de formularios por categoría
   (cada categoría tiene `attributes` distintos), mejor galería de evidencias,
   estados de carga/optimistic UI, manejo de errores de subida.
3. **Manejo de errores y reintentos**: la generación con IA puede devolver `502`
   transitorio (alta demanda del modelo) — conviene reintento con feedback claro.
4. **Estados vacíos y onboarding guiado**: qué ve un tenant nuevo sin inventario ni
   documentos.
5. **Responsive / accesibilidad**: revisar el panel en móvil (la captura de fotos
   ya usa cámara, pero el resto del dashboard necesita repaso).
6. **Diseño / design system**: consolidar tokens de Tailwind, componentes
   reutilizables (botones, inputs, cards, badges de estado). Hoy hay estilos
   repartidos por página.
7. **Vistas placeholder en el sidebar**: "Asistente IA" y "Configuración" aún no
   existen (ver siguiente sección).

---

## Qué viene después (roadmap)

- **Fase 4 — Panel de trazabilidad por numeral**: vista que, para cada numeral de
  la norma, muestre qué ítems del inventario y qué evidencias lo respaldan, pensada
  para el consultor/auditor. (Es la siguiente prioridad de producto.)
- **Asistente IA**: chat sobre la norma (RAG ya está sembrado en el backend).
- **Configuración**: datos de la empresa, equipo, etc.
- **Flujo de aprobación de documentos**: estados `approved`/`rejected` (el backend
  ya los contempla en `DocStatus`).

---

## Convenciones

- Archivos de componentes en **kebab-case**, componentes en **PascalCase**.
- Tipos compartidos con el backend viven en `lib/*` y son **espejo** del backend;
  la **fuente de verdad** siempre es el backend (no dupliques lógica de negocio).
- Nunca metas secretos en el repo. Solo `NEXT_PUBLIC_*` son visibles en el cliente.
- El `tenant_id` jamás se manda desde el cliente; sale del JWT en el backend.
