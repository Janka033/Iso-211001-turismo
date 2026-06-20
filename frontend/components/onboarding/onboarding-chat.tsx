"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { apiBase } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

/**
 * Onboarding conversacional conectado al backend.
 * La IA pregunta, el empresario responde con chips o texto; cada respuesta se
 * persiste en `onboarding_data` vía `PUT /onboarding` (merge incremental). El
 * panel "Datos extraídos" y el progreso reflejan lo capturado.
 */

const supabase = createClient();

type StepType = "chips" | "multi" | "text";

interface Step {
  key: string;
  /** Campo del schema OnboardingPayload del backend. */
  field: string;
  label: string;
  question: string;
  type: StepType;
  options?: string[];
  placeholder?: string;
}

const STEPS: Step[] = [
  {
    key: "actividades",
    field: "activities",
    label: "Actividades",
    question: "¿Qué actividades de aventura ofrece tu empresa? Elige todas las que apliquen.",
    type: "multi",
    options: ["Rafting", "Parapente", "Canopy", "Senderismo", "Buceo", "Escalada", "Espeleología", "Kayak"],
  },
  {
    key: "region",
    field: "main_region",
    label: "Región",
    question: "¿En qué departamento operan principalmente?",
    type: "chips",
    options: ["Santander", "Antioquia", "Huila", "Magdalena", "Meta", "Quindío", "Otro"],
  },
  {
    key: "guias",
    field: "certified_guides",
    label: "Guías certificados",
    question: "¿Cuántos guías certificados tiene tu operación?",
    type: "chips",
    options: ["1 a 3", "4 a 10", "11 a 25", "Más de 25"],
  },
  {
    key: "representante",
    field: "legal_representative",
    label: "Representante legal",
    question: "¿Quién es el representante legal de la empresa?",
    type: "text",
    placeholder: "Nombre y apellido",
  },
  {
    key: "rnt",
    field: "rnt_status",
    label: "Estado del RNT",
    question: "¿Tu Registro Nacional de Turismo (RNT) está vigente?",
    type: "chips",
    options: ["Vigente", "Por renovar", "Aún no lo tengo"],
  },
];

interface Bubble {
  role: "ai" | "user";
  text: string;
}

const GREETING =
  "¡Hola! Soy tu asistente de cumplimiento. Te haré algunas preguntas sobre tu operación para preparar tus documentos de seguridad. Nunca invento datos: lo que falte quedará como [PENDIENTE].";

export function OnboardingChat() {
  const [history, setHistory] = useState<Bubble[]>([
    { role: "ai", text: GREETING },
    { role: "ai", text: STEPS[0].question },
  ]);
  const [step, setStep] = useState(0);
  const [extracted, setExtracted] = useState<Record<string, string>>({});
  const [multiSel, setMultiSel] = useState<string[]>([]);
  const [textVal, setTextVal] = useState("");
  const [saveError, setSaveError] = useState(false);

  const done = step >= STEPS.length;
  const progress = Math.round((Object.keys(extracted).length / STEPS.length) * 100);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [history]);

  // Persiste un campo en onboarding_data vía el backend (merge incremental).
  async function persist(field: string, value: string | string[]) {
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) return; // sin sesión no persistimos (la ruta está protegida)
      const res = await fetch(`${apiBase()}/onboarding`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ [field]: value }),
      });
      setSaveError(!res.ok);
    } catch {
      setSaveError(true);
    }
  }

  function answer(displayText: string, value: string | string[]) {
    const current = STEPS[step];
    const next: Bubble[] = [...history, { role: "user", text: displayText }];

    if (step + 1 < STEPS.length) {
      next.push({ role: "ai", text: STEPS[step + 1].question });
    } else {
      next.push({
        role: "ai",
        text: "¡Listo! Con esto puedo preparar tu política de seguridad, matriz de riesgos, plan de emergencias y gestión de incidentes. Lo que falte lo marcaré como [PENDIENTE] para que lo completes.",
      });
    }

    setHistory(next);
    setExtracted((e) => ({ ...e, [current.key]: displayText }));
    setStep(step + 1);
    setMultiSel([]);
    setTextVal("");
    void persist(current.field, value);
  }

  const current = done ? null : STEPS[step];

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      {/* Conversación */}
      <div className="card flex h-[560px] flex-col overflow-hidden">
        {/* Barra de progreso */}
        <div className="border-b border-slate-100 px-5 py-4">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-slate-700">Datos capturados</span>
            <span className="font-semibold text-brand-700">{progress}%</span>
          </div>
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-brand-600 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Mensajes */}
        <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-5 py-5">
          {history.map((b, i) =>
            b.role === "ai" ? (
              <div key={i} className="flex items-start gap-3">
                <Avatar />
                <div className="max-w-[80%] rounded-2xl rounded-tl-sm bg-slate-100 px-4 py-2.5 text-sm text-slate-700">
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
        </div>

        {/* Entrada */}
        <div className="border-t border-slate-100 bg-slate-50/60 px-5 py-4">
          {current?.type === "chips" && (
            <div className="flex flex-wrap gap-2">
              {current.options!.map((o) => (
                <button
                  key={o}
                  type="button"
                  onClick={() => answer(o, o)}
                  className="chip transition-colors hover:border-brand-400 hover:text-brand-700"
                >
                  {o}
                </button>
              ))}
            </div>
          )}

          {current?.type === "multi" && (
            <div>
              <div className="flex flex-wrap gap-2">
                {current.options!.map((o) => {
                  const on = multiSel.includes(o);
                  return (
                    <button
                      key={o}
                      type="button"
                      onClick={() =>
                        setMultiSel((s) => (on ? s.filter((x) => x !== o) : [...s, o]))
                      }
                      aria-pressed={on}
                      className={`rounded-full px-3 py-1 text-sm font-medium transition-colors ${
                        on
                          ? "bg-brand-600 text-white"
                          : "border border-slate-200 bg-white text-slate-600 hover:border-brand-300"
                      }`}
                    >
                      {o}
                    </button>
                  );
                })}
              </div>
              <button
                type="button"
                disabled={multiSel.length === 0}
                onClick={() => answer(multiSel.join(", "), multiSel)}
                className="btn-primary mt-3"
              >
                Continuar
              </button>
            </div>
          )}

          {current?.type === "text" && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (textVal.trim()) answer(textVal.trim(), textVal.trim());
              }}
              className="flex gap-2"
            >
              <input
                className="input"
                placeholder={current.placeholder}
                value={textVal}
                onChange={(e) => setTextVal(e.target.value)}
                autoFocus
              />
              <button type="submit" disabled={!textVal.trim()} className="btn-primary">
                Enviar
              </button>
            </form>
          )}

          {done && (
            <Link href="/dashboard" className="btn-accent btn-lg w-full justify-center">
              Generar mis documentos
            </Link>
          )}

          {saveError && (
            <p className="mt-3 text-xs text-amber-600">
              No se pudo guardar en el servidor; tus respuestas siguen en pantalla.
            </p>
          )}
        </div>
      </div>

      {/* Panel de datos extraídos */}
      <aside className="card h-fit p-5">
        <h2 className="text-sm font-semibold text-slate-900">Datos extraídos</h2>
        <p className="mt-1 text-xs text-slate-500">
          Lo que la IA va capturando de tu operación.
        </p>
        <dl className="mt-4 space-y-3">
          {STEPS.map((s) => {
            const val = extracted[s.key];
            return (
              <div key={s.key} className="flex items-start justify-between gap-3">
                <dt className="text-sm text-slate-500">{s.label}</dt>
                <dd className="text-right">
                  {val ? (
                    <span className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-800">
                      <CheckDot />
                      <span className="max-w-[150px] truncate">{val}</span>
                    </span>
                  ) : (
                    <span className="badge bg-accent-50 text-accent-600">[PENDIENTE]</span>
                  )}
                </dd>
              </div>
            );
          })}
        </dl>
      </aside>
    </div>
  );
}

function Avatar() {
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

function CheckDot() {
  return (
    <span className="flex h-4 w-4 items-center justify-center rounded-full bg-brand-100 text-brand-700">
      <svg viewBox="0 0 16 16" className="h-3 w-3" fill="none">
        <path d="M3.5 8.5l3 3 6-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </span>
  );
}
