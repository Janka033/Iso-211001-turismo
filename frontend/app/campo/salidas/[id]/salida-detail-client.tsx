"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  CampoHeader,
  CampoMain,
  ErrorNote,
  OkNote,
  StatusBadge,
} from "@/components/campo/ui";
import {
  authToken,
  createIncident,
  deviceId,
  getManifiesto,
  syncEventos,
  updateSalidaStatus,
  type EventType,
  type Manifiesto,
  type Participante,
  type SalidaStatus,
} from "@/lib/campo";

export function SalidaDetailClient({ salidaId }: { salidaId: string }) {
  const router = useRouter();
  const [data, setData] = useState<Manifiesto | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);
  // Eventos ya registrados en esta sesión: "<tipo>:<participanteId?>".
  const [done, setDone] = useState<Set<string>>(new Set());
  const [showIncident, setShowIncident] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await getManifiesto(salidaId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  }, [salidaId]);

  useEffect(() => {
    authToken().then((t) => {
      if (!t) router.replace("/login");
      else void load();
    });
  }, [router, load]);

  function flash(msg: string) {
    setOk(msg);
    setTimeout(() => setOk(null), 2500);
  }

  async function logEvent(
    eventType: EventType,
    opts: { participanteId?: string; note?: string; key?: string } = {},
  ) {
    setError(null);
    try {
      await syncEventos(salidaId, [
        {
          id: deviceId(),
          event_type: eventType,
          participante_id: opts.participanteId ?? null,
          note: opts.note ?? null,
          occurred_at: new Date().toISOString(),
        },
      ]);
      if (opts.key) setDone((s) => new Set(s).add(opts.key!));
      flash("Registrado.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo registrar el evento.");
    }
  }

  async function changeStatus(status: SalidaStatus) {
    setError(null);
    try {
      await updateSalidaStatus(salidaId, status);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo cambiar el estado.");
    }
  }

  if (loading) {
    return (
      <>
        <CampoHeader subtitle="Salida" title="Cargando…" backHref="/campo/salidas" />
      </>
    );
  }

  if (!data) {
    return (
      <>
        <CampoHeader subtitle="Salida" title="Salida" backHref="/campo/salidas" />
        <CampoMain>
          <ErrorNote>{error ?? "No se encontró la salida."}</ErrorNote>
        </CampoMain>
      </>
    );
  }

  const { salida, participantes } = data;

  return (
    <>
      <CampoHeader
        subtitle="Salida"
        title={salida.route_name || "Recorrido"}
        backHref="/campo/salidas"
      />
      <CampoMain>
        <ErrorNote>{error}</ErrorNote>
        {ok && <OkNote>{ok}</OkNote>}

        {/* Estado del recorrido */}
        <section className="card p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500">Estado del recorrido</p>
              <StatusBadge status={salida.status} />
            </div>
            {salida.status === "programada" && (
              <button onClick={() => changeStatus("en_curso")} className="btn-marca">
                Iniciar
              </button>
            )}
            {salida.status === "en_curso" && (
              <button onClick={() => changeStatus("finalizada")} className="btn-secondary">
                Finalizar
              </button>
            )}
          </div>
        </section>

        {/* Verificación de equipos → deriva al flujo del mecánico */}
        <Link
          href="/campo/equipos"
          className="card mt-4 flex items-center gap-3 p-4 transition-shadow hover:shadow-card-hover active:scale-[0.99]"
        >
          <span className="text-2xl">🛠️</span>
          <span className="text-sm text-slate-600">
            Verifica los equipos y vehículos antes de salir
          </span>
        </Link>

        {/* Manifiesto: inducción + check-in por participante */}
        <section className="mt-4">
          <h2 className="mb-2 font-display text-base font-bold text-marca-950">
            Participantes ({participantes.length})
          </h2>
          {participantes.length === 0 ? (
            <p className="rounded-xl border border-dashed border-slate-300 p-5 text-center text-sm text-slate-500">
              Nadie se ha registrado todavía.
            </p>
          ) : (
            <div className="space-y-2">
              {participantes.map((p) => (
                <ParticipanteRow
                  key={p.id}
                  p={p}
                  done={done}
                  onInduccion={() =>
                    logEvent("induccion", {
                      participanteId: p.id,
                      key: `induccion:${p.id}`,
                    })
                  }
                  onCheckIn={() =>
                    logEvent("check_in", {
                      participanteId: p.id,
                      key: `check_in:${p.id}`,
                    })
                  }
                />
              ))}
            </div>
          )}
        </section>

        {/* Recorrido */}
        <section className="card mt-4 space-y-3 p-5">
          <h2 className="font-display text-base font-bold text-marca-950">Recorrido</h2>
          <button
            onClick={() => logEvent("punto_control")}
            className="btn-secondary w-full"
          >
            📍 Registrar punto de control
          </button>
          <button
            onClick={() => logEvent("fin_recorrido", { key: "fin_recorrido" })}
            className="btn-secondary w-full"
          >
            🏁 Fin del recorrido
          </button>
        </section>

        {/* Emergencia / incidente */}
        <section className="mt-4 rounded-2xl border border-flag-500/30 bg-flag-100/40 p-5">
          <h2 className="font-display text-base font-bold text-flag-600">Emergencia</h2>
          <p className="mt-1 text-sm text-slate-600">
            Si se presenta un problema, activa el plan y registra el incidente con
            fotos.
          </p>
          {!showIncident ? (
            <button
              onClick={() => {
                void logEvent("emergencia_activada");
                setShowIncident(true);
              }}
              className="btn mt-3 w-full rounded-xl bg-flag-500 px-5 py-3 text-base text-white hover:bg-flag-600 active:scale-[0.99]"
            >
              🚨 Activar emergencia y reportar
            </button>
          ) : (
            <IncidentForm
              salidaId={salidaId}
              onDone={() => {
                setShowIncident(false);
                flash("Incidente registrado.");
              }}
              onCancel={() => setShowIncident(false)}
            />
          )}
        </section>
      </CampoMain>
    </>
  );
}

function ParticipanteRow({
  p,
  done,
  onInduccion,
  onCheckIn,
}: {
  p: Participante;
  done: Set<string>;
  onInduccion: () => void;
  onCheckIn: () => void;
}) {
  const inducted = done.has(`induccion:${p.id}`);
  const checked = done.has(`check_in:${p.id}`);
  return (
    <div className="card p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-medium text-marca-950">{p.full_name}</p>
          <p className="text-xs text-slate-500">
            {p.document_type} {p.document_number}
          </p>
        </div>
        {p.has_medical_alert && (
          <span className="shrink-0 rounded-full bg-flag-100 px-2 py-0.5 text-xs font-medium text-flag-600">
            ⚠ Alerta médica
          </span>
        )}
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <button
          onClick={onInduccion}
          disabled={inducted}
          className={`rounded-lg px-3 py-2 text-sm font-medium ${
            inducted
              ? "bg-cielo-100 text-cielo-700"
              : "border border-slate-300 text-slate-700 hover:bg-slate-50"
          }`}
        >
          {inducted ? "✓ Inducción" : "Inducción"}
        </button>
        <button
          onClick={onCheckIn}
          disabled={checked}
          className={`rounded-lg px-3 py-2 text-sm font-medium ${
            checked
              ? "bg-cielo-100 text-cielo-700"
              : "border border-slate-300 text-slate-700 hover:bg-slate-50"
          }`}
        >
          {checked ? "✓ Check-in" : "Check-in"}
        </button>
      </div>
    </div>
  );
}

function IncidentForm({
  salidaId,
  onDone,
  onCancel,
}: {
  salidaId: string;
  onDone: () => void;
  onCancel: () => void;
}) {
  const [location, setLocation] = useState("");
  const [circumstances, setCircumstances] = useState("");
  const [response, setResponse] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (circumstances.trim().length < 10) {
      setError("Describe qué pasó con un poco más de detalle.");
      return;
    }
    setSubmitting(true);
    try {
      await createIncident(salidaId, {
        occurred_at: new Date().toISOString(),
        location: location.trim() || "Sin ubicación precisa",
        circumstances: circumstances.trim(),
        emergency_response: response.trim() || null,
        evidence_paths: [],
      });
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo registrar el incidente.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={submit} className="mt-4 space-y-3">
      <ErrorNote>{error}</ErrorNote>
      <div>
        <label className="label">¿Dónde ocurrió?</label>
        <input
          className="input"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="Km 15 del río"
        />
      </div>
      <div>
        <label className="label">¿Qué pasó?</label>
        <textarea
          className="input min-h-[90px]"
          value={circumstances}
          onChange={(e) => setCircumstances(e.target.value)}
          placeholder="Describe las circunstancias del incidente."
          required
        />
      </div>
      <div>
        <label className="label">¿Qué se hizo de inmediato? (opcional)</label>
        <textarea
          className="input min-h-[70px]"
          value={response}
          onChange={(e) => setResponse(e.target.value)}
          placeholder="Atención prestada, llamada a red de apoyo…"
        />
      </div>
      <div className="flex gap-2">
        <button type="button" onClick={onCancel} className="btn-secondary flex-1">
          Cancelar
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="btn flex-1 rounded-xl bg-flag-500 px-5 py-3 text-base text-white hover:bg-flag-600"
        >
          {submitting ? "Guardando…" : "Registrar incidente"}
        </button>
      </div>
    </form>
  );
}
