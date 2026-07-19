"use client";

import { useEffect, useState } from "react";

import { apiBase } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

const supabase = createClient();

interface ReadinessItem {
  document_type: string;
  title: string;
  numeral: string;
  state: string;
  detail: string;
  score: number | null;
}

interface AuditReadiness {
  ready: boolean;
  total: number;
  ready_count: number;
  threshold: number;
  blockers: string[];
  items: ReadinessItem[];
  summary: string;
}

/**
 * Veredicto de PREPARACIÓN DOCUMENTAL para la auditoría (GET /quality/readiness).
 * Responde "¿tu expediente está listo para presentar?" y lista lo que falta.
 * Es honesto: NO promete la certificación (esa la da un organismo acreditado
 * sobre la evidencia operativa real), solo el estado del expediente documental.
 */
export function AuditReadinessCard() {
  const [data, setData] = useState<AuditReadiness | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const {
          data: { session },
        } = await supabase.auth.getSession();
        if (!session) return;
        const res = await fetch(`${apiBase()}/quality/readiness`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (!res.ok) throw new Error(String(res.status));
        if (alive) setData((await res.json()) as AuditReadiness);
      } catch {
        if (alive) setError("No pudimos evaluar tu preparación. Recarga la página.");
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  if (error) {
    return (
      <div className="card border border-rose-100 bg-rose-50 p-4 text-sm text-rose-700">
        {error}
      </div>
    );
  }
  if (!data) {
    return (
      <div className="card flex h-28 items-center justify-center">
        <p className="text-sm text-slate-400">Evaluando tu preparación…</p>
      </div>
    );
  }

  const pct = data.total ? Math.round((data.ready_count / data.total) * 100) : 0;
  const ready = data.ready;

  return (
    <div
      className={`card border p-5 ${
        ready ? "border-emerald-200 bg-emerald-50/40" : "border-accent-200 bg-accent-50/40"
      }`}
    >
      <div className="flex items-start gap-3">
        <span
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-lg ${
            ready ? "bg-emerald-100 text-emerald-700" : "bg-accent-100 text-accent-700"
          }`}
          aria-hidden
        >
          {ready ? "🏆" : "🚦"}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-display text-lg font-bold text-tinta">
              ¿Listo para la auditoría?
            </h2>
            <span
              className={`badge ${
                ready ? "bg-emerald-100 text-emerald-700" : "bg-accent-100 text-accent-700"
              }`}
            >
              {data.ready_count} / {data.total} documentos
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-600">{data.summary}</p>
        </div>
      </div>

      {/* Barra de preparación */}
      <div className="mt-4 flex items-center gap-3">
        <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-white/70">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              ready ? "bg-emerald-500" : "bg-accent-500"
            }`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="text-sm font-semibold text-slate-900">{pct}%</span>
      </div>

      {/* Qué falta */}
      {data.blockers.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Antes de presentar, resuelve:
          </p>
          <ul className="mt-2 space-y-1.5">
            {data.blockers.map((b, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                <span className="mt-0.5 text-accent-500" aria-hidden>
                  •
                </span>
                <span>{b}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Disclaimer honesto: preparación documental, no la certificación */}
      <p className="mt-4 border-t border-slate-200/70 pt-3 text-xs text-slate-400">
        Verificamos que tu <span className="font-medium">expediente documental</span>{" "}
        esté completo, coherente y sin pendientes (score del Auditor ≥{" "}
        {Math.round(data.threshold)}). La certificación la otorga un organismo
        acreditado por la ONAC, que además revisa tu evidencia operativa en terreno.
      </p>
    </div>
  );
}
