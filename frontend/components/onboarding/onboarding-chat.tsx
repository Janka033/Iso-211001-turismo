"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { apiBase } from "@/lib/api";
import { fieldLabel } from "@/lib/field-labels";
import { ROUTE_TITLES } from "@/lib/route";
import { createClient } from "@/lib/supabase/client";

/**
 * Onboarding conversacional REAL, conectado a `POST /onboarding/chat`.
 * 1) El empresario marca sus actividades (13 chips → slugs de ACTIVIDADES.md).
 * 2) La IA pregunta; el backend decide qué campo sigue y extrae lo que el
 *    cliente dijo (nunca inventa). Cada turno persiste en `onboarding_data`.
 * El panel "Datos extraídos" y el progreso se arman DINÁMICAMENTE desde la
 * respuesta del backend (no desde una lista fija de pasos).
 */

const supabase = createClient();

// slug (lo que consume el backend) -> etiqueta legible.
const ACTIVITIES: { slug: string; label: string }[] = [
  { slug: "rafting", label: "Rafting" },
  { slug: "rapel", label: "Rápel" },
  { slug: "espeleologia", label: "Espeleología" },
  { slug: "parapente", label: "Parapente" },
  { slug: "cabalgata", label: "Cabalgata" },
  { slug: "canyoning", label: "Canyoning / Torrentismo" },
  { slug: "buceo", label: "Buceo" },
  { slug: "canopy", label: "Canopy / Tirolesa" },
  { slug: "senderismo", label: "Senderismo / Trekking" },
  { slug: "atv", label: "Cuatrimotos / ATV" },
  { slug: "kayak", label: "Kayak" },
  { slug: "ciclomontanismo", label: "Ciclomontañismo" },
  { slug: "escalada", label: "Escalada" },
];

const ACTIVITY_LABEL: Record<string, string> = Object.fromEntries(
  ACTIVITIES.map((a) => [a.slug, a.label]),
);

// Claves de `onboarding_data` que NO son campos universales a mostrar como fila:
// estructuras internas (dicts anidados) o metadatos del flujo. El resto de las
// claves presentes se muestran con su etiqueta de `field-labels.ts` — así un
// campo nuevo capturado por el backend aparece SOLO en el panel sin tener que
// mantener aquí una lista paralela (era la causa de que `company_purpose` y
// otros campos guardados no se vieran).
const PANEL_SKIP_KEYS = new Set<string>([
  "activity_fields",
  "absent_fields",
  "staff_roles",
  "document_codes",
  "remediation_fields",
]);

// Prefijo del field_key por actividad (`<prefijo>_<slug>`) -> etiqueta.
// Incluye los campos del cuestionario "Información Técnica de Actividades".
const CATEGORY_LABELS: Record<string, string> = {
  equipo: "Equipo",
  competencias: "Competencias",
  emergencias: "Emergencias",
  riesgos: "Riesgos",
  seguimiento: "Seguimiento",
  edades_permitidas: "Edades permitidas",
  restricciones_salud: "Restricciones de salud",
  ruta_descripcion: "Ruta",
  grupo_participantes: "Grupo (mín–máx)",
  competencias_requeridas_participante: "Competencias del participante",
  equipos_operacion: "Equipos de operación",
  equipos_rescate: "Equipos de rescate",
  indumentaria: "Indumentaria",
  seguro_contratado: "Seguro",
  politica_cancelacion: "Política de cancelación",
};

interface OnboardingData {
  activities?: string[];
  activity_fields?: Record<string, string>;
  absent_fields?: string[];
  [key: string]: unknown;
}

interface CurrentStep {
  step_order: number;
  total: number;
  document_type: string | null;
  title: string;
  numeral: string | null;
  fields_done: number;
  fields_total: number;
}

interface ChatResponse {
  next_question: string | null;
  next_field: { field_key: string; activity: string | null } | null;
  extracted: Record<string, string>;
  data: OnboardingData;
  completeness: number;
  completed: boolean;
  // Interceptor de seguridad: true si la respuesta se rechazó por incumplir la
  // norma (no se guardó nada); safety_note explica el requisito ISO.
  blocked?: boolean;
  safety_note?: string | null;
  // Ruta guiada (Fase 2/3): el paso activo y los documentos con datos
  // completos listos para generar. null/[] cuando la ruta no está sembrada.
  current_step?: CurrentStep | null;
  ready_to_generate?: string[];
  // Validación proactiva: avisos de datos que parecen mal puestos o
  // incongruentes (no bloquean; invitan a confirmar o corregir).
  data_warnings?: string[];
}

interface Bubble {
  role: "ai" | "user";
  text: string;
  tone?: "warning";
}

// Transcript persistido (GET /onboarding/chat/history) para rehidratar el hilo
// al recargar. Solo user/assistant: el saludo lo repone el frontend.
interface StoredMessage {
  role: "user" | "assistant";
  content: string;
}

// Best-effort: si el transcript no está disponible, se cae al saludo + la
// pregunta pendiente (comportamiento previo), nunca rompe el arranque.
async function fetchHistory(token: string): Promise<StoredMessage[]> {
  try {
    const res = await fetch(`${apiBase()}/onboarding/chat/history`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return [];
    return (await res.json()) as StoredMessage[];
  } catch {
    return [];
  }
}

const GREETING =
  "¡Hola! Soy tu asistente de cumplimiento. Con base en tus actividades te haré unas preguntas para preparar tus documentos de seguridad. Nunca invento datos: lo que falte quedará como [PENDIENTE].";

type Phase = "activities" | "chat";

export function OnboardingChat() {
  const [phase, setPhase] = useState<Phase>("activities");
  const [selected, setSelected] = useState<string[]>([]);

  const [history, setHistory] = useState<Bubble[]>([]);
  const [data, setData] = useState<OnboardingData>({});
  const [completeness, setCompleteness] = useState(0);
  const [completed, setCompleted] = useState(false);
  // Ruta guiada: el paso activo (barra "Paso X de Y") y los documentos listos
  // para generar. `generatedNow` recuerda los generados desde el chat en esta
  // sesión para no repetir la tarjeta de celebración.
  const [currentStep, setCurrentStep] = useState<CurrentStep | null>(null);
  const [readyDocs, setReadyDocs] = useState<string[]>([]);
  const [generatedNow, setGeneratedNow] = useState<string[]>([]);
  const [generating, setGenerating] = useState<string | null>(null);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [textVal, setTextVal] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Mientras resolvemos si el tenant ya tiene actividades, no renderizamos aún
  // (evita el "flash" de la pantalla de selección al recargar y luego saltar a chat).
  const [initializing, setInitializing] = useState(true);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [history, loading]);

  // Al montar: si el tenant YA tiene actividades persistidas, se salta la
  // pantalla de selección y se retoma el chat directamente (F5 no debe devolver
  // a "¿Qué actividades ofreces?"). Se resuelve con un turno sin mensaje (no
  // llama a la IA): trae actividades + estado dinámico + la próxima pregunta.
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const {
          data: { session },
        } = await supabase.auth.getSession();
        if (!session) return;
        const res = await fetch(`${apiBase()}/onboarding/chat`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({ message: null }),
        });
        if (!res.ok || !alive) return;
        const resp = (await res.json()) as ChatResponse;
        const acts = resp.data.activities ?? [];
        if (!alive || acts.length === 0) return;
        setSelected(acts);
        setData(resp.data);
        setCompleteness(resp.completeness);
        setCompleted(resp.completed);
        setCurrentStep(resp.current_step ?? null);
        setReadyDocs(resp.ready_to_generate ?? []);
        // Rehidrata la conversación previa desde `chat_messages`. El POST de
        // arriba ya sembró la primera pregunta si hacía falta, por eso el
        // transcript se pide DESPUÉS. El saludo es constante del cliente; si no
        // hay transcript (degradado o tenant nuevo), se cae a la pregunta
        // pendiente actual — el comportamiento de siempre.
        const past = await fetchHistory(session.access_token);
        if (!alive) return;
        const bubbles: Bubble[] = [{ role: "ai", text: GREETING }];
        if (past.length > 0) {
          for (const m of past) {
            bubbles.push({ role: m.role === "user" ? "user" : "ai", text: m.content });
          }
        } else if (resp.next_question) {
          bubbles.push({ role: "ai", text: resp.next_question });
        }
        setHistory(bubbles);
        setPhase("chat");
      } catch {
        /* sin actividades o sin sesión: se muestra la pantalla de selección */
      } finally {
        if (alive) setInitializing(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  // Un turno contra el backend. `message` null en el turno inicial.
  async function postChat(body: { message: string | null; activities?: string[] }) {
    setLoading(true);
    setError(null);
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) {
        setError("Tu sesión expiró. Vuelve a iniciar sesión para continuar.");
        return null;
      }
      const res = await fetch(`${apiBase()}/onboarding/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        setError(
          res.status === 503
            ? "El asistente de IA no está disponible en este momento."
            : "No se pudo procesar tu respuesta. Intenta de nuevo.",
        );
        return null;
      }
      return (await res.json()) as ChatResponse;
    } catch {
      setError("No se pudo conectar con el servidor.");
      return null;
    } finally {
      setLoading(false);
    }
  }

  function applyResponse(resp: ChatResponse) {
    setData(resp.data);
    setCompleteness(resp.completeness);
    setCompleted(resp.completed);
    setCurrentStep(resp.current_step ?? null);
    setReadyDocs(resp.ready_to_generate ?? []);
    setHistory((h) => {
      const next: Bubble[] = [
        ...h,
        {
          role: "ai",
          // Si el interceptor rechazó la respuesta, se marca como advertencia y
          // el texto es la explicación del requisito ISO + cómo replantear.
          tone: resp.blocked ? "warning" : undefined,
          text:
            resp.safety_note ??
            resp.next_question ??
            "¡Listo! Con esto puedo preparar tus documentos. Lo que falte lo marcaré como [PENDIENTE] para que lo completes.",
        },
      ];
      // Avisos de validación: cada dato dudoso como burbuja ámbar, para que el
      // cliente confirme o corrija sin perder el hilo.
      for (const warning of resp.data_warnings ?? []) {
        next.push({ role: "ai", tone: "warning", text: warning });
      }
      return next;
    });
  }

  // Confirma la selección de actividades: las PERSISTE (el turno inicial guarda
  // onboarding_data) e inicializa el chat estrictamente con ese contexto. Sirve
  // para el primer arranque y para volver tras modificarlas (conserva el
  // historial en ese caso, solo cambia el set de actividades).
  async function commitActivities() {
    if (selected.length === 0) return;
    const firstTime = history.length === 0;
    setPhase("chat");
    setHistory((h) =>
      firstTime
        ? [{ role: "ai", text: GREETING }]
        : [
            ...h,
            {
              role: "ai",
              text: "Actualicé tus actividades. Con base en ellas, seguimos.",
            },
          ],
    );
    const resp = await postChat({ message: null, activities: selected });
    if (resp) applyResponse(resp);
  }

  async function sendAnswer() {
    const text = textVal.trim();
    if (!text || loading) return;
    setHistory((h) => [...h, { role: "user", text }]);
    setTextVal("");
    // El textarea auto-creciente vuelve a su altura mínima al enviar.
    if (inputRef.current) inputRef.current.style.height = "auto";
    const resp = await postChat({ message: text });
    if (resp) {
      applyResponse(resp);
    } else {
      // El envío falló: se RESTAURA lo escrito para que el cliente solo
      // reintente con Enter — nunca debe reescribir una respuesta larga.
      setTextVal(text);
    }
  }

  // Genera un documento cuyo paso quedó completo, sin salir del chat
  // (celebración: el CTA grande del cierre de paso).
  async function generateDoc(docType: string) {
    setGenerating(docType);
    setGenerateError(null);
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) throw new Error("sesión");
      const res = await fetch(`${apiBase()}/generation/${docType}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        // 409 = fuera de secuencia o datos insuficientes: el backend explica el
        // motivo (secuencia estricta). Se muestra tal cual al cliente.
        let detail =
          "No se pudo generar el documento. Intenta de nuevo o hazlo desde el panel.";
        try {
          const body = (await res.json()) as { detail?: string };
          if (body?.detail) detail = body.detail;
        } catch {
          /* respuesta sin cuerpo JSON */
        }
        setGenerateError(detail);
        return;
      }
      setGeneratedNow((g) => [...g, docType]);
      setHistory((h) => [
        ...h,
        {
          role: "ai",
          text: `🎉 ¡Generé tu ${ROUTE_TITLES[docType] ?? docType}! Puedes verlo en tu ruta o descargarlo desde Documentos. Sigamos con el siguiente paso.`,
        },
      ]);
      // Sincronización en tiempo real: al generar, el paso activo avanza. Se
      // re-pide el estado (sin mensaje, sin IA) para refrescar la barra, el paso
      // actual y el siguiente documento a generar, y mostrar su primera pregunta.
      const resp = await postChat({ message: null });
      if (resp) applyResponse(resp);
    } catch {
      setGenerateError(
        "No se pudo generar el documento. Intenta de nuevo o hazlo desde el panel.",
      );
    } finally {
      setGenerating(null);
    }
  }

  function toggle(slug: string) {
    setSelected((s) => (s.includes(slug) ? s.filter((x) => x !== slug) : [...s, slug]));
  }

  // Aún resolviendo si retomar el chat: no pintamos nada decisivo todavía.
  if (initializing) {
    return (
      <div className="card flex h-40 items-center justify-center p-6">
        <p className="text-sm text-slate-400">Cargando tu onboarding…</p>
      </div>
    );
  }

  if (phase === "activities") {
    return (
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-slate-900">
          ¿Qué actividades de aventura ofrece tu empresa?
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Elige todas las que apliquen. Con esto personalizamos las preguntas y los documentos.
        </p>
        <div className="mt-5 flex flex-wrap gap-2">
          {ACTIVITIES.map((a) => {
            const on = selected.includes(a.slug);
            return (
              <button
                key={a.slug}
                type="button"
                onClick={() => toggle(a.slug)}
                aria-pressed={on}
                className={`rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors ${
                  on
                    ? "bg-marca-600 text-white"
                    : "border border-slate-200 bg-white text-slate-600 hover:border-marca-300"
                }`}
              >
                {a.label}
              </button>
            );
          })}
        </div>
        <button
          type="button"
          disabled={selected.length === 0}
          onClick={commitActivities}
          className="btn-primary mt-6"
        >
          Comenzar ({selected.length})
        </button>
      </div>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      {/* Conversación */}
      <div className="card flex h-[560px] flex-col overflow-hidden">
        <div className="border-b border-slate-100 px-5 py-4">
          {/* Ruta guiada: el paso activo con su propio anillo de progreso.
              Sin ruta sembrada (currentStep null) se muestra solo el global. */}
          {currentStep && (
            <div className="mb-3 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-slate-900">
                  {currentStep.step_order === 0
                    ? currentStep.title
                    : `Paso ${currentStep.step_order} de ${currentStep.total} — ${currentStep.title}`}
                </p>
                {currentStep.numeral && (
                  <p className="text-xs text-slate-400">
                    Numeral {currentStep.numeral}
                  </p>
                )}
              </div>
              {currentStep.fields_total > 0 && (
                <span className="badge shrink-0 bg-marca-50 text-marca-700">
                  {currentStep.fields_done} / {currentStep.fields_total} datos
                </span>
              )}
            </div>
          )}
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-slate-700">Datos capturados</span>
            <span className="font-semibold text-marca-700">{Math.round(completeness)}%</span>
          </div>
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-marca-600 transition-all duration-500"
              style={{ width: `${completeness}%` }}
            />
          </div>
        </div>

        <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-5 py-5">
          {history.map((b, i) =>
            b.role === "ai" ? (
              <div key={i} className="flex items-start gap-3">
                <Avatar tone={b.tone} />
                <div
                  className={`max-w-[80%] rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm ${
                    b.tone === "warning"
                      ? "border border-amber-200 bg-amber-50 text-amber-800"
                      : "bg-slate-100 text-slate-700"
                  }`}
                >
                  {b.text}
                </div>
              </div>
            ) : (
              <div key={i} className="flex justify-end">
                <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-marca-600 px-4 py-2.5 text-sm text-white">
                  {b.text}
                </div>
              </div>
            ),
          )}
          {loading && (
            <div className="flex items-start gap-3">
              <Avatar />
              <div className="rounded-2xl rounded-tl-sm bg-slate-100 px-4 py-2.5 text-sm text-slate-400">
                Escribiendo…
              </div>
            </div>
          )}
        </div>

        {/* Celebración de cierre de paso: documentos con datos completos aún
            sin generar. CTA grande sin salir del chat. */}
        {readyDocs.filter((d) => !generatedNow.includes(d)).length > 0 && (
          <div className="border-t border-accent-100 bg-accent-50 px-5 py-3">
            {readyDocs
              .filter((d) => !generatedNow.includes(d))
              .map((docType) => (
                <div
                  key={docType}
                  className="flex flex-wrap items-center justify-between gap-2 py-1"
                >
                  <p className="text-sm font-medium text-slate-800">
                    ✦ ¡Completaste los datos de{" "}
                    <span className="font-semibold">
                      {ROUTE_TITLES[docType] ?? docType}
                    </span>
                    !
                  </p>
                  <button
                    type="button"
                    onClick={() => void generateDoc(docType)}
                    disabled={generating !== null}
                    className="btn-primary px-3 py-1.5 text-xs"
                  >
                    {generating === docType ? "Generando…" : "Generar mi documento"}
                  </button>
                </div>
              ))}
            {generateError && (
              <p className="mt-1 text-xs text-amber-700">{generateError}</p>
            )}
          </div>
        )}

        <div className="border-t border-slate-100 bg-slate-50/60 px-5 py-4">
          {!completed ? (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void sendAnswer();
              }}
              className="flex items-end gap-2"
            >
              {/* Textarea auto-creciente: las respuestas detalladas (objetivos
                  SMART, desglose de riesgos, matriz de comunicación) necesitan
                  varias líneas. Enter envía; Shift+Enter hace salto de línea. */}
              <textarea
                ref={inputRef}
                className="input max-h-48 min-h-[2.5rem] flex-1 resize-none overflow-y-auto"
                placeholder="Escribe tu respuesta… (Shift+Enter para salto de línea)"
                value={textVal}
                rows={1}
                maxLength={8000}
                onChange={(e) => {
                  setTextVal(e.target.value);
                  e.target.style.height = "auto";
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 192)}px`;
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    if (!loading && textVal.trim()) void sendAnswer();
                  }
                }}
                disabled={loading}
                autoFocus
              />
              <button type="submit" disabled={loading || !textVal.trim()} className="btn-primary">
                Enviar
              </button>
            </form>
          ) : (
            <Link href="/dashboard/ruta" className="btn-marca w-full justify-center">
              Ver tu ruta a la certificación
            </Link>
          )}
          {error && <p className="mt-3 text-xs text-amber-600">{error}</p>}
        </div>
      </div>

      {/* Panel de datos extraídos: cabecera fija, lista con scroll interno y
          botón sticky al pie. La tarjeta se acota a la ventana para que la lista
          crezca hacia adentro (scroll propio) sin estirar ni desbordar la página. */}
      <aside className="card flex h-fit max-h-[calc(100vh-8rem)] flex-col overflow-hidden lg:sticky lg:top-6">
        <div className="shrink-0 px-5 pt-5">
          <h2 className="text-sm font-semibold text-slate-900">Datos extraídos</h2>
          <p className="mt-1 text-xs text-slate-500">
            Lo que la IA va capturando de tu operación.
          </p>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-5">
          <ExtractedPanel data={data} activities={selected} />
        </div>

        {/* Botón fijo al pie con fondo opaco: siempre visible sin importar el
            scroll interno. Permite volver a la selección; al confirmar se
            re-persiste y el chat continúa con el nuevo contexto. */}
        <div className="sticky bottom-0 shrink-0 border-t border-slate-100 bg-white px-5 py-4">
          <button
            type="button"
            onClick={() => setPhase("activities")}
            className="btn-secondary w-full justify-center"
          >
            Agregar o modificar actividades
          </button>
        </div>
      </aside>
    </div>
  );
}

function ExtractedPanel({ data, activities }: { data: OnboardingData; activities: string[] }) {
  // Campos que el cliente declaró no tener: se muestran como "No aplica" (una
  // respuesta válida), no se ocultan como si faltaran.
  const absent = new Set(data.absent_fields ?? []);
  // Se recorren las claves REALMENTE presentes en el estado (no una lista fija):
  // se descartan las estructurales y los dicts anidados, y cada una se etiqueta
  // con `field-labels.ts`. El orden lo fija el backend (identidad primero).
  const universalEntries = Object.keys(data)
    .filter((key) => !PANEL_SKIP_KEYS.has(key))
    .filter((key) => {
      const v = data[key];
      return !(v !== null && typeof v === "object" && !Array.isArray(v));
    })
    .map((key) => {
      const value = absent.has(key) ? "No aplica" : formatValue(data[key]);
      return [fieldLabel(key), value] as const;
    })
    .filter(([, value]) => value !== null);

  const activityFields = data.activity_fields ?? {};

  return (
    <div className="mt-4 space-y-4">
      <dl className="space-y-3">
        {universalEntries.length === 0 && (
          <p className="text-xs text-slate-400">Aún no hay datos capturados.</p>
        )}
        {universalEntries.map(([label, value]) => (
          <div key={label} className="flex items-start justify-between gap-3">
            <dt className="text-sm text-slate-500">{label}</dt>
            <dd className="max-w-[160px] text-right text-sm font-medium text-slate-800">
              {value}
            </dd>
          </div>
        ))}
      </dl>

      {activities.map((slug) => {
        const rows = Object.entries(CATEGORY_LABELS)
          .map(([cat, catLabel]) => [catLabel, activityFields[`${cat}_${slug}`]] as const)
          .filter(([, v]) => Boolean(v));
        if (rows.length === 0) return null;
        return (
          <div key={slug} className="border-t border-slate-100 pt-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-marca-700">
              {ACTIVITY_LABEL[slug] ?? slug}
            </p>
            <dl className="mt-2 space-y-2">
              {rows.map(([catLabel, v]) => (
                <div key={catLabel} className="flex items-start justify-between gap-3">
                  <dt className="text-sm text-slate-500">{catLabel}</dt>
                  <dd className="max-w-[160px] text-right text-sm font-medium text-slate-800">
                    {v}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        );
      })}
    </div>
  );
}

function formatValue(value: unknown): string | null {
  if (value === null || value === undefined) return null;
  if (Array.isArray(value)) return value.length ? value.join(", ") : null;
  const str = String(value).trim();
  return str.length ? str : null;
}

function Avatar({ tone }: { tone?: "warning" }) {
  if (tone === "warning") {
    return (
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-amber-100 text-amber-600 shadow-card">
        <svg viewBox="0 0 20 20" className="h-4 w-4" fill="none" aria-hidden="true">
          <path
            d="M10 7v4m0 3h.01M10 2.5 18 16H2L10 2.5Z"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
    );
  }
  return (
    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-marca-gradient text-white shadow-card">
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" aria-hidden="true">
        <path
          d="M12 3v4m0 10v4m9-9h-4M7 12H3m13.5-5.5-2.8 2.8m-3.4 3.4-2.8 2.8m9-0-2.8-2.8M9.3 9.3 6.5 6.5"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
      </svg>
    </span>
  );
}
