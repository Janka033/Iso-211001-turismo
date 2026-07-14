"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { CampoHeader, CampoMain, ErrorNote, StatusBadge } from "@/components/campo/ui";
import {
  authToken,
  createSalida,
  listActivityProfiles,
  listSalidas,
  type ActivityProfile,
  type Salida,
  type SalidaCreated,
} from "@/lib/campo";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("es-CO", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function SalidasClient() {
  const router = useRouter();
  const [salidas, setSalidas] = useState<Salida[]>([]);
  const [profiles, setProfiles] = useState<ActivityProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [justCreated, setJustCreated] = useState<SalidaCreated | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [ss, ps] = await Promise.all([listSalidas(), listActivityProfiles()]);
      setSalidas(ss);
      setProfiles(ps);
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

  return (
    <>
      <CampoHeader subtitle="Operación en terreno" title="Salidas" backHref="/campo" />
      <CampoMain>
        <ErrorNote>{error}</ErrorNote>

        {justCreated ? (
          <ShareLink
            created={justCreated}
            onClose={() => {
              setJustCreated(null);
              void load();
            }}
          />
        ) : creating ? (
          <CreateForm
            profiles={profiles}
            onCancel={() => setCreating(false)}
            onCreated={(s) => {
              setCreating(false);
              setJustCreated(s);
            }}
          />
        ) : (
          <button onClick={() => setCreating(true)} className="btn-marca w-full">
            + Crear salida
          </button>
        )}

        <div className="mt-6 space-y-3">
          {loading ? (
            <p className="text-sm text-slate-500">Cargando salidas…</p>
          ) : salidas.length === 0 ? (
            <p className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
              Aún no hay salidas. Crea la primera para compartir el enlace de
              registro con los turistas.
            </p>
          ) : (
            salidas.map((s) => (
              <Link
                key={s.id}
                href={`/campo/salidas/${s.id}`}
                className="card flex items-center justify-between gap-3 p-4 transition-shadow hover:shadow-card-hover active:scale-[0.99]"
              >
                <span className="min-w-0">
                  <span className="block truncate font-medium text-marca-950">
                    {s.route_name || "Salida sin nombre de ruta"}
                  </span>
                  <span className="mt-0.5 block text-sm text-slate-500">
                    {formatDate(s.scheduled_start)} · cupo {s.capacity}
                  </span>
                </span>
                <StatusBadge status={s.status} />
              </Link>
            ))
          )}
        </div>
      </CampoMain>
    </>
  );
}

function CreateForm({
  profiles,
  onCancel,
  onCreated,
}: {
  profiles: ActivityProfile[];
  onCancel: () => void;
  onCreated: (s: SalidaCreated) => void;
}) {
  const [activityId, setActivityId] = useState(profiles[0]?.id ?? "");
  const [routeName, setRouteName] = useState("");
  const [start, setStart] = useState("");
  const [capacity, setCapacity] = useState(10);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!activityId) {
      setError("Primero crea una actividad en el inventario de la empresa.");
      return;
    }
    setSubmitting(true);
    try {
      const created = await createSalida({
        activity_profile_id: activityId,
        route_name: routeName.trim() || null,
        scheduled_start: new Date(start).toISOString(),
        capacity,
      });
      onCreated(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={submit} className="card space-y-4 p-5">
      <h2 className="font-display text-base font-bold text-marca-950">Nueva salida</h2>
      <ErrorNote>{error}</ErrorNote>

      <div>
        <label className="label">Actividad</label>
        <select
          className="input"
          value={activityId}
          onChange={(e) => setActivityId(e.target.value)}
        >
          {profiles.length === 0 && <option value="">Sin actividades</option>}
          {profiles.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="label">Nombre de la ruta (opcional)</label>
        <input
          className="input"
          value={routeName}
          onChange={(e) => setRouteName(e.target.value)}
          placeholder="Cañón del río Suárez"
        />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="label">Fecha y hora</label>
          <input
            className="input"
            type="datetime-local"
            value={start}
            onChange={(e) => setStart(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="label">Cupo</label>
          <input
            className="input"
            type="number"
            min={1}
            max={200}
            value={capacity}
            onChange={(e) => setCapacity(Number(e.target.value))}
            required
          />
        </div>
      </div>

      <div className="flex gap-2">
        <button type="button" onClick={onCancel} className="btn-secondary flex-1">
          Cancelar
        </button>
        <button type="submit" disabled={submitting} className="btn-marca flex-1">
          {submitting ? "Creando…" : "Crear"}
        </button>
      </div>
    </form>
  );
}

function ShareLink({
  created,
  onClose,
}: {
  created: SalidaCreated;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  const url = `${origin}${created.public_registration_path}`;
  const waText = encodeURIComponent(
    `¡Hola! Para tu actividad, completa tu registro y firma el consentimiento aquí: ${url}`,
  );

  async function copy() {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="card space-y-4 p-5">
      <div className="flex items-center gap-2">
        <span className="text-2xl">✅</span>
        <h2 className="font-display text-base font-bold text-marca-950">
          Salida creada
        </h2>
      </div>
      <p className="text-sm text-slate-600">
        Comparte este enlace con los turistas para que se registren y firmen el
        consentimiento. Guárdalo: por seguridad no se puede recuperar después.
      </p>

      <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
        <p className="break-all font-mono text-xs text-slate-700">{url}</p>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <button onClick={copy} className="btn-secondary">
          {copied ? "¡Copiado!" : "Copiar enlace"}
        </button>
        <a
          href={`https://wa.me/?text=${waText}`}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-naranja text-center"
        >
          WhatsApp
        </a>
      </div>

      <button onClick={onClose} className="w-full text-sm text-slate-500 hover:text-marca-700">
        Listo
      </button>
    </div>
  );
}
