"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { CampoHeader, CampoMain, ErrorNote, OkNote } from "@/components/campo/ui";
import {
  authToken,
  deviceId,
  listInventory,
  syncGeneralChecks,
  type CheckStatus,
  type InventoryItem,
} from "@/lib/campo";

// Revisión de estado por ítem antes de sincronizar (fase "pre" = matinal).
interface Draft {
  status: CheckStatus | null;
  note: string;
}

const STATUS_BUTTONS: { value: CheckStatus; label: string; hint: string }[] = [
  { value: "B", label: "B", hint: "Bien" },
  { value: "C", label: "C", hint: "Cambiar" },
  { value: "MC", label: "MC", hint: "Mantto." },
];

export function EquiposClient() {
  const router = useRouter();
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Equipos y vehículos del inventario: lo que el mecánico revisa.
      const [equipos, vehiculos] = await Promise.all([
        listInventory("equipo"),
        listInventory("vehiculo"),
      ]);
      setItems([...equipos, ...vehiculos]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    authToken().then((t) => {
      if (!t) router.replace("/login");
      else void load();
    });
  }, [router, load]);

  function setStatus(itemId: string, status: CheckStatus) {
    setDrafts((d) => ({
      ...d,
      [itemId]: { status, note: d[itemId]?.note ?? "" },
    }));
  }
  function setNote(itemId: string, note: string) {
    setDrafts((d) => ({
      ...d,
      [itemId]: { status: d[itemId]?.status ?? null, note },
    }));
  }

  const reviewed = Object.values(drafts).filter((d) => d.status).length;

  async function sync() {
    setError(null);
    setOk(null);
    const checks = items
      .filter((it) => drafts[it.id]?.status)
      .map((it) => ({
        id: deviceId(),
        item_id: it.id,
        phase: "pre" as const,
        status: drafts[it.id].status as CheckStatus,
        note: drafts[it.id].note.trim() || null,
        evidence_paths: [],
        checked_at: new Date().toISOString(),
      }));
    if (checks.length === 0) {
      setError("Marca el estado de al menos un equipo antes de sincronizar.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await syncGeneralChecks(checks);
      setOk(`Revisión sincronizada: ${res.inserted} equipo(s). Avisa al guía.`);
      setDrafts({});
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo sincronizar la revisión.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <CampoHeader
        subtitle="Operación en terreno"
        title="Revisión de equipos"
        backHref="/campo"
      />
      <CampoMain>
        <ErrorNote>{error}</ErrorNote>
        {ok && <OkNote>{ok}</OkNote>}

        {loading ? (
          <p className="text-sm text-slate-500">Cargando equipos…</p>
        ) : items.length === 0 ? (
          <p className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
            No hay equipos ni vehículos en el inventario. Agrégalos desde el panel
            de la empresa para poder revisarlos.
          </p>
        ) : (
          <>
            <p className="mb-3 text-sm text-slate-500">
              Marca el estado de cada equipo. Revisados: {reviewed}/{items.length}.
            </p>
            <div className="space-y-2">
              {items.map((it) => {
                const draft = drafts[it.id];
                const needsNote = draft?.status === "C" || draft?.status === "MC";
                return (
                  <div key={it.id} className="card p-4">
                    <div className="flex items-center justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate font-medium text-marca-950">{it.name}</p>
                        <p className="text-xs capitalize text-slate-400">{it.category}</p>
                      </div>
                      <div className="flex shrink-0 gap-1">
                        {STATUS_BUTTONS.map((b) => (
                          <button
                            key={b.value}
                            onClick={() => setStatus(it.id, b.value)}
                            className={statusClass(b.value, draft?.status === b.value)}
                            title={b.hint}
                          >
                            {b.label}
                          </button>
                        ))}
                      </div>
                    </div>
                    {needsNote && (
                      <input
                        className="input mt-3"
                        value={draft?.note ?? ""}
                        onChange={(e) => setNote(it.id, e.target.value)}
                        placeholder="Observación (qué falla, qué cambiar)…"
                      />
                    )}
                  </div>
                );
              })}
            </div>

            <div className="sticky bottom-4 mt-6">
              <button
                onClick={sync}
                disabled={submitting || reviewed === 0}
                className="btn-marca w-full shadow-card-hover"
              >
                {submitting
                  ? "Sincronizando…"
                  : `Sincronizar revisión (${reviewed})`}
              </button>
            </div>
          </>
        )}
      </CampoMain>
    </>
  );
}

function statusClass(value: CheckStatus, active: boolean): string {
  const base =
    "h-9 w-11 rounded-lg text-sm font-bold transition-colors border";
  if (!active) return `${base} border-slate-200 bg-white text-slate-500 hover:bg-slate-50`;
  if (value === "B") return `${base} border-cielo-500 bg-cielo-100 text-cielo-700`;
  if (value === "C") return `${base} border-naranja-500 bg-naranja-100 text-naranja-600`;
  return `${base} border-flag-500 bg-flag-100 text-flag-600`;
}
