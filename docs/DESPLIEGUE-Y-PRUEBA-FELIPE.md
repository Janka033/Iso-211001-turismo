# Despliegue y prueba con Felipe

> Guía operativa para dejar ColAdventure en línea y correr la prueba de punta a
> punta con el cliente piloto. Estado a 2026-07-14.

## 1. Qué está listo

- **Backend** (FastAPI): módulos `auth`, `onboarding`, `generation`, `inventory`,
  `quality`, `salidas` (operación de terreno + registro público del turista).
  Suite completa: **140 passed, 2 skipped** (los 2 skip son tests de integración
  RLS que requieren Supabase local).
- **Frontend** (Next.js 14): landing, login, onboarding, dashboard, y las
  pantallas nuevas:
  - **Turista (pública, sin login):** `/registro/[token]` — registro + salud +
    consentimiento + firma digital.
  - **Terreno (staff):** `/campo`, `/campo/equipos`, `/campo/salidas`,
    `/campo/salidas/[id]`.
- **Migraciones** 0031–0033 aplicadas al remoto; consentimiento v1 de Felipe
  sembrado para todos los tenants.
- **Smoke test** en navegador (Playwright): landing carga, el flujo público
  responde contra el backend, `/campo` exige sesión. 7/7 OK.

## 2. Variables de entorno

> ⚠️ **Nunca** subir claves al repo. Todo lo real vive en el panel de cada
> plataforma. Los `.env.example` son la plantilla.

### Backend (Railway)

| Variable | Valor en producción |
|---|---|
| `SUPABASE_URL` | `https://dhekcfjpnjbonjjgmmxi.supabase.co` |
| `SUPABASE_ANON_KEY` | anon key del proyecto |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role (Settings → API) — solo seed/provisioning |
| `SUPABASE_JWKS_URL` | `https://dhekcfjpnjbonjjgmmxi.supabase.co/auth/v1/.well-known/jwks.json` |
| `SUPABASE_JWT_AUDIENCE` | `authenticated` |
| `GEMINI_API_KEY` | **la clave rotada 2026-07-14** (la vieja quedó revocada) |
| `GEMINI_MODEL` | `gemini-2.5-flash` |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` |
| `ENVIRONMENT` | `production` |
| `CORS_ORIGINS` | **el dominio del frontend en Vercel** (ver ⚠️ abajo) |

> ⚠️ **Acción pendiente:** actualizar `GEMINI_API_KEY` en Railway con la clave
> nueva. El `.env` local ya está actualizado, pero Railway usa su propia copia.

### Frontend (Vercel)

| Variable | Valor en producción |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://dhekcfjpnjbonjjgmmxi.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | anon key (pública) |
| `NEXT_PUBLIC_API_URL` | **la URL del backend en Railway** (p. ej. `https://coladventure-api.up.railway.app`) |

## 3. CORS: el punto crítico del flujo público

El turista abre `https://<frontend>/registro/<token>` y su navegador hace
`fetch` **directo al backend** (`NEXT_PUBLIC_API_URL`). Es una petición
cross-origin: si el backend no autoriza el dominio del frontend, el registro y
la firma fallan con error de CORS aunque todo lo demás esté bien.

**Regla:** `CORS_ORIGINS` (backend) debe incluir exactamente el origen del
frontend. Es una lista separada por comas. Ejemplo:

```
CORS_ORIGINS=https://coladventure.vercel.app,https://app.coladventure.co
```

Sin `www` ni barra final. Si usas dominio propio, incluye ambos (el de Vercel y
el propio) mientras migras.

## 4. Pasos de despliegue

### Backend → Railway
1. Root del servicio: `backend/`. Railway autodetecta Python; arranque:
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
2. Cargar todas las variables de la tabla del backend.
3. Deploy. Verificar: `GET https://<backend>/health` → `{"status":"ok"}`.

### Frontend → Vercel
1. **Root Directory = `frontend`** (es un monorepo; sin esto Vercel no
   encuentra el `package.json`).
2. Framework: Next.js (autodetectado). Build: `next build`.
3. Cargar las 3 variables `NEXT_PUBLIC_*`.
4. Deploy. Abrir la URL: la landing debe cargar.
5. Copiar el dominio final y ponerlo en `CORS_ORIGINS` del backend (paso 3).

## 5. Prueba de punta a punta con Felipe

> Es el mismo flujo del flujograma 3 (recepción) + turista + guía. ~10 min.

**A. Staff crea la salida (recepción/coordinador)**
1. Entrar a `https://<frontend>/login` con la cuenta del tenant de Felipe.
2. Ir a **Terreno** (sidebar) → **Salidas** → **Crear salida**.
   - Elegir la actividad, poner ruta, fecha/hora y cupo → **Crear**.
3. En la pantalla de éxito, **Copiar enlace** o **WhatsApp**. Ese enlace es
   `https://<frontend>/registro/<token>`.

**B. Turista se registra y firma (desde el celular)**
4. Abrir el enlace en el teléfono (sin login).
5. Llenar datos + salud + declaraciones → **Continuar al consentimiento**.
   - Si la fecha de nacimiento es de un menor, aparecen los campos del acudiente.
6. Leer el consentimiento (texto v1 de Felipe), marcar las 2 casillas, **firmar**
   en el recuadro con el dedo → **Firmar y finalizar**. Debe aparecer la
   confirmación "¡Registro completo!".

**C. Guía opera el recorrido**
7. Volver al staff → **Terreno** → **Salidas** → abrir la salida creada.
8. Ver el **manifiesto** con el turista registrado (alerta médica si aplica).
9. **Iniciar** el recorrido; marcar **inducción** y **check-in** del turista;
   registrar **punto de control**; probar **activar emergencia** → reportar un
   incidente de prueba; **fin del recorrido** y **finalizar**.

**D. Revisión de equipos (mecánico)**
10. **Terreno** → **Revisión de equipos**: marcar B/C/MC de cada equipo del
    inventario y **Sincronizar revisión**.

### Verificación de evidencia (auditoría)
La firma queda inmutable con hash + IP + user-agent (Ley 527/1999). Para
confirmarlo, el registro del consentimiento debe existir en `consentimientos`
con `signed_at`, `signature_path` y `signed_document_hash`.

## 6. Cuota de IA (recordatorio del ensayo E2E)

La generación de documentos consume cuota de Gemini. Con el free tier (20
req/día) un onboarding + generación se agota rápido. Confirmar que el proyecto
de la clave en producción tiene **billing activo** (plan "Paid" en AI Studio /
Cloud Console → Billing) antes de la sesión con Felipe.

## 7. Limitaciones conocidas (no bloquean la prueba)

- La **revisión de equipos** no adjunta foto todavía (el endpoint de evidencia
  está atado a una salida; la revisión matinal general va sin salida).
- El registro del turista aún no pide los **campos condicionales por actividad**
  (`activity_specific` viaja vacío); los demás datos de salud sí se capturan.
- Los eventos de terreno se sincronizan en línea (el modelo de datos ya es
  idempotente y offline-first, pero la cola offline del cliente es trabajo
  futuro).
