"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { apiBase } from "@/lib/api";
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

const UNIVERSAL_LABELS: Record<string, string> = {
  activities: "Actividades",
  main_region: "Región principal",
  locations: "Ubicaciones",
  scope: "Alcance",
  certified_guides: "Guías certificados",
  legal_representative: "Representante legal",
  nit: "NIT",
  rnt_status: "Estado del RNT",
  rnt_number: "Número de RNT",
  emergency_contacts: "Contactos de emergencia",
  brigada_emergencias: "Brigada de emergencias",
  capacitaciones_personal_emergencias: "Capacitaciones en emergencias",
  equipos_emergencia: "Equipos de emergencia",
  organismos_apoyo: "Organismos de apoyo",
  hospital_cercano: "Hospital más cercano",
  vehiculos_evacuacion: "Vehículos de evacuación",
  existing_controls: "Controles actuales",
  management_commitment: "Compromiso de la dirección",
};

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
  [key: string]: unknown;
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
}

interface Bubble {
  role: "ai" | "user";
  text: string;
  tone?: "warning";
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
  const [textVal, setTextVal] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [history, loading]);

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
    setHistory((h) => [
      ...h,
      {
        role: "ai",
        // Si el interceptor rechazó la respuesta, se marca como advertencia y el
        // texto es la explicación del requisito ISO + cómo replantear.
        tone: resp.blocked ? "warning" : undefined,
        text:
          resp.safety_note ??
          resp.next_question ??
          "¡Listo! Con esto puedo preparar tus documentos. Lo que falte lo marcaré como [PENDIENTE] para que lo completes.",
      },
    ]);
  }

  async function startChat() {
    if (selected.length === 0) return;
    setPhase("chat");
    setHistory([{ role: "ai", text: GREETING }]);
    const resp = await postChat({ message: null, activities: selected });
    if (resp) applyResponse(resp);
  }

  async function sendAnswer() {
    const text = textVal.trim();
    if (!text || loading) return;
    setHistory((h) => [...h, { role: "user", text }]);
    setTextVal("");
    const resp = await postChat({ message: text });
    if (resp) applyResponse(resp);
  }

  function toggle(slug: string) {
    setSelected((s) => (s.includes(slug) ? s.filter((x) => x !== slug) : [...s, slug]));
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
                    ? "bg-brand-600 text-white"
                    : "border border-slate-200 bg-white text-slate-600 hover:border-brand-300"
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
          onClick={startChat}
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
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-slate-700">Datos capturados</span>
            <span className="font-semibold text-brand-700">{Math.round(completeness)}%</span>
          </div>
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-brand-600 transition-all duration-500"
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
                <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-brand-600 px-4 py-2.5 text-sm text-white">
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

        <div className="border-t border-slate-100 bg-slate-50/60 px-5 py-4">
          {!completed ? (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void sendAnswer();
              }}
              className="flex gap-2"
            >
              <input
                className="input"
                placeholder="Escribe tu respuesta…"
                value={textVal}
                onChange={(e) => setTextVal(e.target.value)}
                disabled={loading}
                autoFocus
              />
              <button type="submit" disabled={loading || !textVal.trim()} className="btn-primary">
                Enviar
              </button>
            </form>
          ) : (
            <Link href="/dashboard" className="btn-accent btn-lg w-full justify-center">
              Generar mis documentos
            </Link>
          )}
          {error && <p className="mt-3 text-xs text-amber-600">{error}</p>}
        </div>
      </div>

      {/* Panel de datos extraídos (dinámico) */}
      <aside className="card h-fit p-5">
        <h2 className="text-sm font-semibold text-slate-900">Datos extraídos</h2>
        <p className="mt-1 text-xs text-slate-500">
          Lo que la IA va capturando de tu operación.
        </p>
        <ExtractedPanel data={data} activities={selected} />
      </aside>
    </div>
  );
}

function ExtractedPanel({ data, activities }: { data: OnboardingData; activities: string[] }) {
  const universalEntries = Object.entries(UNIVERSAL_LABELS)
    .map(([key, label]) => [label, formatValue(data[key])] as const)
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
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-700">
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
    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-gradient text-white shadow-card">
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
