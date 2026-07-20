"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { apiBase } from "@/lib/api";
import {
  chapterOf,
  nodeState,
  type NodeState,
  type RoadmapResponse,
  type RoadmapStep,
  stars,
  UNITS,
} from "@/lib/route";
import { createClient } from "@/lib/supabase/client";

const supabase = createClient();

/**
 * El mapa de la ruta a la certificación (Fase 3, experiencia tipo Duolingo):
 * camino vertical de nodos agrupados por unidades = capítulos de la norma.
 * El estado de cada nodo se DERIVA de la respuesta del backend (documentos
 * reales + score del Auditor); aquí nada se inventa ni se cachea.
 */
export function RouteMap() {
  const [roadmap, setRoadmap] = useState<RoadmapResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const {
          data: { session },
        } = await supabase.auth.getSession();
        if (!session) {
          if (alive) setError("Tu sesión expiró. Vuelve a iniciar sesión.");
          return;
        }
        const res = await fetch(`${apiBase()}/onboarding/roadmap`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (!res.ok) throw new Error(String(res.status));
        const body = (await res.json()) as RoadmapResponse;
        if (alive) setRoadmap(body);
      } catch {
        if (alive) setError("No pudimos cargar tu ruta. Recarga la página.");
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  if (error) {
    return (
      <div className="mt-6 rounded-xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {error}
      </div>
    );
  }
  if (!roadmap) {
    return (
      <div className="card mt-6 flex h-48 items-center justify-center">
        <p className="text-sm text-slate-400">Cargando tu ruta…</p>
      </div>
    );
  }

  // El avance cuenta pasos COMPLETOS (generados y en orden), no cualquier doc
  // con estado: así el tablero y el chat reflejan el mismo progreso real.
  const completed = roadmap.steps.filter((s) => s.complete).length;
  const pct = roadmap.total ? Math.round((completed / roadmap.total) * 100) : 0;
  const allDone = completed === roadmap.total;

  return (
    <div className="mt-6">
      {/* Barra global: camino a la certificación */}
      <div className="card p-5">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-slate-700">
            Camino a la certificación
          </p>
          <span className="badge bg-marca-50 text-marca-700">
            {completed} / {roadmap.total} documentos
          </span>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-marca-600 transition-all duration-500"
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-sm font-semibold text-slate-900">{pct}%</span>
        </div>
        {allDone && (
          <p className="mt-3 rounded-lg bg-accent-50 px-3 py-2 text-sm font-medium text-accent-700">
            🏆 Paquete completo: tus {roadmap.total} documentos están generados.
          </p>
        )}
      </div>

      {/* Unidades con su tramo del camino */}
      <div className="mt-8 space-y-10">
        {UNITS.map((unit) => {
          const steps = roadmap.steps.filter(
            (s) => chapterOf(s.numeral) === unit.chapter,
          );
          if (steps.length === 0) return null;
          const unitDone = steps.every((s) => s.complete);
          return (
            <section key={unit.chapter}>
              <div className="flex items-center gap-3">
                <span
                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-sm font-bold ${
                    unitDone
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-marca-100 text-marca-700"
                  }`}
                >
                  {unitDone ? "✓" : unit.chapter}
                </span>
                <div>
                  <h2 className="text-sm font-bold uppercase tracking-wide text-slate-900">
                    {unit.title}
                  </h2>
                  <p className="text-xs text-slate-500">{unit.subtitle}</p>
                </div>
              </div>

              <ol className="relative mt-4 space-y-3 pl-4">
                {/* la línea del camino */}
                <span
                  aria-hidden
                  className="absolute bottom-4 left-[2.35rem] top-2 w-0.5 rounded bg-slate-200"
                />
                {steps.map((step) => (
                  <StepNode
                    key={step.document_type}
                    step={step}
                    state={nodeState(step, roadmap.current_step)}
                  />
                ))}
              </ol>
            </section>
          );
        })}
      </div>
    </div>
  );
}

function StepNode({ step, state }: { step: RoadmapStep; state: NodeState }) {
  const done = state === "done" || state === "crown";
  const starCount = stars(step.last_score);

  return (
    <li className="relative flex items-start gap-4">
      <NodeCircle state={state} order={step.step_order} />
      <div
        className={`min-w-0 flex-1 rounded-2xl border p-4 transition-colors ${
          state === "current"
            ? "border-marca-200 bg-white shadow-card"
            : done
              ? "border-slate-100 bg-white"
              : "border-slate-100 bg-slate-50/60"
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="min-w-0">
            <p
              className={`truncate text-sm font-semibold ${
                state === "locked" || state === "soon"
                  ? "text-slate-500"
                  : "text-slate-900"
              }`}
            >
              Paso {step.step_order} · {step.title}
            </p>
            <p className="text-xs text-slate-400">Numeral {step.numeral}</p>
          </div>
          <div className="flex items-center gap-2">
            {starCount !== null && <Stars count={starCount} />}
            <StateBadge state={state} />
          </div>
        </div>

        {state === "current" && (
          <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
            <p className="text-xs text-slate-500">
              Este es tu paso actual: responde sus preguntas en el chat.
            </p>
            <Link href="/onboarding" className="btn-primary px-3 py-1.5 text-xs">
              Continuar con este paso
            </Link>
          </div>
        )}
        {done && (
          <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
            <p className="text-xs text-slate-500">
              {state === "crown"
                ? "Aprobado por el Auditor: tercera estrella."
                : starCount !== null && starCount < 3
                  ? "Mejora este documento para la tercera estrella (Calidad)."
                  : "Documento generado."}
            </p>
            <Link
              href="/dashboard#documentos"
              className="btn-secondary px-3 py-1.5 text-xs"
            >
              Ver documento
            </Link>
          </div>
        )}
        {state === "soon" && (
          <p className="mt-2 text-xs text-slate-400">
            Próximamente: este documento estará disponible pronto en tu ruta.
          </p>
        )}
      </div>
    </li>
  );
}

function NodeCircle({ state, order }: { state: NodeState; order: number }) {
  const base =
    "relative z-10 mt-1 flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-sm font-bold";
  switch (state) {
    case "crown":
      return (
        <span className={`${base} bg-amber-400 text-white shadow-card`} title="Aprobado (≥80)">
          👑
        </span>
      );
    case "done":
      return (
        <span className={`${base} bg-emerald-500 text-white shadow-card`} title="Generado">
          <svg viewBox="0 0 20 20" className="h-5 w-5" fill="none" aria-hidden>
            <path
              d="m5 10.5 3.5 3.5L15 7"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
      );
    case "current":
      return (
        <span className={`${base} bg-marca-600 text-white shadow-card`} title="Paso actual">
          <span
            aria-hidden
            className="absolute inset-0 animate-ping rounded-full bg-marca-400 opacity-30"
          />
          <span className="relative">{order}</span>
        </span>
      );
    case "soon":
      return (
        <span className={`${base} bg-slate-200 text-slate-400`} title="Próximamente">
          {order}
        </span>
      );
    default:
      return (
        <span className={`${base} bg-slate-200 text-slate-400`} title="Bloqueado">
          <svg viewBox="0 0 20 20" className="h-4 w-4" fill="none" aria-hidden>
            <rect x="5" y="9" width="10" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
            <path d="M7 9V6.5a3 3 0 0 1 6 0V9" stroke="currentColor" strokeWidth="1.5" />
          </svg>
        </span>
      );
  }
}

function StateBadge({ state }: { state: NodeState }) {
  switch (state) {
    case "crown":
      return <span className="badge bg-amber-50 text-amber-700">Aprobado</span>;
    case "done":
      return <span className="badge bg-emerald-50 text-emerald-700">Generado</span>;
    case "current":
      return <span className="badge bg-marca-50 text-marca-700">En curso</span>;
    case "soon":
      return <span className="badge bg-slate-100 text-slate-500">Próximamente</span>;
    default:
      return <span className="badge bg-slate-100 text-slate-500">Bloqueado</span>;
  }
}

function Stars({ count }: { count: number }) {
  return (
    <span
      className="text-xs tracking-tight"
      title={`${count} de 3 estrellas (score del Auditor)`}
      aria-label={`${count} de 3 estrellas`}
    >
      {"★".repeat(count)}
      <span className="text-slate-300">{"★".repeat(3 - count)}</span>
    </span>
  );
}
