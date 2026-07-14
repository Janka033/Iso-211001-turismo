# DESIGN.md — Sistema visual ColAdventure

> Fuente de verdad de tokens y reglas visuales. Los tokens viven en
> `frontend/tailwind.config.ts`; este documento define su uso.
> Estado: **la landing ya usa este sistema**; dashboard/onboarding/login siguen
> en el sistema anterior (`brand` verde / `accent` amarillo) hasta su migración.

## Paleta

Tres anclas definidas por producto; escalas canónicas de Tailwind (las anclas
son exactamente blue-600 / orange-500 / sky-500 — nada re-derivado a mano).

### `marca` — azul de marca (Tailwind blue)

Primario de UI: enlaces, fondos oscuros de secciones, focos, chips de numeral.

| Token | Hex | Uso principal |
|---|---|---|
| marca-50 | #EFF6FF | fondos suaves de bloques informativos |
| marca-100 | #DBEAFE | superficies "tú lo cuentas" |
| marca-200 | #BFDBFE | bordes/líneas de ruta sobre claro |
| marca-300 | #93C5FD | detalles sobre oscuro |
| marca-400 | #60A5FA | texto secundario sobre marca-950 |
| marca-500 | #3B82F6 | anillos de foco |
| **marca-600** | **#2563EB** | **primario: enlaces, hover de nav, eyebrows** |
| marca-700 | #1D4ED8 | hover de primario |
| marca-800 | #1E40AF | — |
| marca-900 | #1E3A8A | texto sobre marca-50/100 |
| marca-950 | #172554 | fondos oscuros (hero, franjas, footer); texto sobre naranja |

### `naranja` — acento (Tailwind orange)

CTA y momentos de energía. **Siempre con texto oscuro `marca-950`** (contraste
AA ~6:1; blanco sobre naranja-500 falla AA en texto pequeño).

| Token | Hex | Uso principal |
|---|---|---|
| naranja-100 | #FFEDD5 | fondos suaves de acento |
| naranja-300 | #FDBA74 | — |
| naranja-400 | #FB923C | texto/acentos mono sobre marca-950; hover de CTA |
| **naranja-500** | **#F97316** | **CTA primario (texto marca-950)** |
| naranja-600 | #EA580C | pressed/borde de CTA |

### `cielo` — estado "completo" (Tailwind sky)

Éxito, generado, completitud. **NUNCA verde para estados** — el verde queda
reservado a las ilustraciones de paisaje (contenido, no UI).

| Token | Hex | Uso principal |
|---|---|---|
| cielo-100 | #E0F2FE | fondos de badge "completo" |
| **cielo-500** | **#0EA5E9** | **barras/indicadores de completitud** |
| cielo-600 | #0284C7 | sellos "Generado", texto de éxito |
| cielo-700 | #0369A1 | texto de éxito sobre claro |

### Neutros y funcionales (se conservan del sistema anterior)

- `papel` #FBF9F4 — fondo cálido de marketing (el mundo documento).
- `tinta` #16211B — titulares sobre claro.
- `slate-*` — grises de cuerpo/bordes (familia fría única, no mezclar cálidos).
- `flag` (coral #E4572E / #C74624 / #FCE4DB) — EXCLUSIVO de `[PENDIENTE:…]`.
  Funcional, nunca decorativo. No se sustituye por naranja: el naranja invita
  (CTA), el coral advierte (dato faltante).

## Tipografía (sin cambios)

- **Archivo** (display, 600–900): titulares. Tracking negativo en tamaños XL.
- **Public Sans** (cuerpo): párrafos ≤ ~65 caracteres de ancho.
- **IBM Plex Mono**: numerales de la norma, `[PENDIENTE]`, sellos, eyebrows.
- Titulares largos con `text-balance`.

## Movimiento

- **Easing permitido**: `ease-out`, `cubic-bezier(0.32, 0.72, 0, 1)` (decel
  suave). **Prohibido**: bounce/elastic/overshoot (curvas con parámetros > 1),
  `linear` en transiciones de UI.
- Duraciones: 150–300 ms interacción; 400–700 ms entradas de sección.
- Animar solo `transform` y `opacity` (GPU-safe).
- Toda animación de entrada respeta `prefers-reduced-motion` (estado final
  estático).
- Feedback de presión en CTAs: `active:scale-[0.98]`.

## Reglas de aplicación

1. Un solo acento por vista (naranja); `cielo` es estado, no decoración.
2. Nada de blobs con blur ni gradientes decorativos uniformes; la profundidad
   sale de superficie, borde fino y sombra teñida del fondo (no negro puro).
3. Sombras teñidas: sobre papel usar sombras con matiz marca-950, no negras.
4. Las ilustraciones de paisaje (`components/landing/scenes.tsx`) conservan sus
   colores propios de territorio: son contenido regional, no tokens de UI.

## Migración pendiente (no hecha)

`brand-*` → `marca-*`, `accent-*` → `naranja-*`, verdes de estado → `cielo-*`
en dashboard, onboarding, login y `globals.css` (`.btn-primary`, `.eyebrow`,
`.numeral-chip`…). Hacerla vista por vista tras la validación con Felipe.
