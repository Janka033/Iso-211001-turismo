"use client";

import { useCallback, useEffect, useState } from "react";

import { apiBase } from "@/lib/api";
import {
  CATEGORY_LABEL,
  ITEM_CATEGORIES,
  type CategoryId,
  type Evidence,
  type InventoryItem,
} from "@/lib/inventory";
import { createClient } from "@/lib/supabase/client";

const supabase = createClient();

async function authToken(): Promise<string | null> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

export function InventoryClient() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [filter, setFilter] = useState<CategoryId | "all">("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [evidenceFor, setEvidenceFor] = useState<InventoryItem | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const t = await authToken();
      if (!t) throw new Error("Sesión expirada, vuelve a entrar.");
      const res = await fetch(`${apiBase()}/inventory`, {
        headers: { Authorization: `Bearer ${t}` },
      });
      if (!res.ok) throw new Error("No se pudo cargar el inventario.");
      setItems((await res.json()) as InventoryItem[]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error inesperado");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function remove(id: string) {
    const t = await authToken();
    if (!t) return;
    await fetch(`${apiBase()}/inventory/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${t}` },
    });
    setItems((xs) => xs.filter((x) => x.id !== id));
  }

  const visible = filter === "all" ? items : items.filter((i) => i.category === filter);
  const countOf = (c: CategoryId) => items.filter((i) => i.category === c).length;

  return (
    <div>
      {/* Filtros + acción */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="-mx-1 flex flex-wrap gap-2">
          <Chip active={filter === "all"} onClick={() => setFilter("all")}>
            Todos ({items.length})
          </Chip>
          {ITEM_CATEGORIES.map((c) => (
            <Chip key={c.id} active={filter === c.id} onClick={() => setFilter(c.id)}>
              {c.label} ({countOf(c.id)})
            </Chip>
          ))}
        </div>
        <button onClick={() => setShowForm(true)} className="btn-accent shrink-0">
          + Agregar ítem
        </button>
      </div>

      {error && (
        <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>
      )}

      {/* Lista */}
      <div className="mt-6">
        {loading ? (
          <p className="text-sm text-slate-500">Cargando inventario…</p>
        ) : visible.length === 0 ? (
          <EmptyState onAdd={() => setShowForm(true)} />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {visible.map((item) => (
              <ItemCard
                key={item.id}
                item={item}
                onEvidence={() => setEvidenceFor(item)}
                onDelete={() => remove(item.id)}
              />
            ))}
          </div>
        )}
      </div>

      {showForm && (
        <NewItemModal
          onClose={() => setShowForm(false)}
          onCreated={(it) => {
            setItems((xs) => [it, ...xs]);
            setShowForm(false);
          }}
        />
      )}

      {evidenceFor && (
        <EvidenceModal
          item={evidenceFor}
          onClose={() => setEvidenceFor(null)}
          onCountChange={(n) =>
            setItems((xs) =>
              xs.map((x) => (x.id === evidenceFor.id ? { ...x, evidence_count: n } : x)),
            )
          }
        />
      )}
    </div>
  );
}

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`shrink-0 rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
        active
          ? "bg-brand-600 text-white"
          : "border border-slate-200 bg-white text-slate-600 hover:border-brand-300"
      }`}
    >
      {children}
    </button>
  );
}

function ItemCard({
  item,
  onEvidence,
  onDelete,
}: {
  item: InventoryItem;
  onEvidence: () => void;
  onDelete: () => void;
}) {
  const attrs = Object.entries(item.attributes ?? {}).filter(([, v]) => v != null && v !== "");
  return (
    <article className="card flex flex-col p-5">
      <div className="flex items-start justify-between gap-2">
        <span className="badge bg-brand-50 text-brand-700">{CATEGORY_LABEL[item.category]}</span>
        <button
          onClick={onDelete}
          className="text-xs text-slate-400 hover:text-rose-600"
          title="Eliminar"
        >
          Eliminar
        </button>
      </div>
      <h3 className="mt-3 text-base font-semibold text-slate-900">{item.name}</h3>

      {attrs.length > 0 && (
        <dl className="mt-3 space-y-1 text-sm">
          {attrs.map(([k, v]) => (
            <div key={k} className="flex justify-between gap-3">
              <dt className="text-slate-500">{k}</dt>
              <dd className="text-right font-medium text-slate-700">{String(v)}</dd>
            </div>
          ))}
        </dl>
      )}

      <button onClick={onEvidence} className="btn-secondary mt-4 w-full">
        {item.evidence_count > 0 ? `Fotos (${item.evidence_count})` : "Agregar fotos"}
      </button>
    </article>
  );
}

function EmptyState({ onAdd }: { onAdd: () => void }) {
  return (
    <div className="card flex flex-col items-center gap-3 p-10 text-center">
      <p className="text-sm text-slate-600">
        Aún no hay ítems en esta categoría. Registra tu operación real para que la IA la
        use y el consultor la vea respaldada con evidencia.
      </p>
      <button onClick={onAdd} className="btn-primary">
        + Agregar el primero
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Modal: nuevo ítem (con atributos dinámicos)
// ---------------------------------------------------------------------------

interface AttrRow {
  key: string;
  value: string;
}

function NewItemModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (item: InventoryItem) => void;
}) {
  const [category, setCategory] = useState<CategoryId>("vehiculo");
  const [name, setName] = useState("");
  const [rows, setRows] = useState<AttrRow[]>([{ key: "", value: "" }]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const t = await authToken();
      if (!t) throw new Error("Sesión expirada.");
      const attributes: Record<string, string> = {};
      for (const r of rows) {
        if (r.key.trim()) attributes[r.key.trim()] = r.value;
      }
      const res = await fetch(`${apiBase()}/inventory`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${t}` },
        body: JSON.stringify({ category, name: name.trim(), attributes }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail ?? "No se pudo crear el ítem.");
      onCreated(body as InventoryItem);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="Agregar ítem al inventario" onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label">Categoría</label>
          <select
            className="input"
            value={category}
            onChange={(e) => setCategory(e.target.value as CategoryId)}
          >
            {ITEM_CATEGORIES.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-slate-400">
            {ITEM_CATEGORIES.find((c) => c.id === category)?.hint}
          </p>
        </div>

        <div>
          <label className="label">Nombre</label>
          <input
            className="input"
            placeholder="Ej: Cuatrimoto Honda TRX, Salida norte…"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            autoFocus
          />
        </div>

        <div>
          <label className="label">Detalles (opcional)</label>
          <div className="space-y-2">
            {rows.map((r, i) => (
              <div key={i} className="flex gap-2">
                <input
                  className="input"
                  placeholder="Atributo (ej: estado)"
                  value={r.key}
                  onChange={(e) =>
                    setRows((xs) => xs.map((x, j) => (j === i ? { ...x, key: e.target.value } : x)))
                  }
                />
                <input
                  className="input"
                  placeholder="Valor (ej: operativa)"
                  value={r.value}
                  onChange={(e) =>
                    setRows((xs) => xs.map((x, j) => (j === i ? { ...x, value: e.target.value } : x)))
                  }
                />
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setRows((xs) => [...xs, { key: "", value: "" }])}
            className="mt-2 text-sm font-medium text-brand-700 hover:text-brand-800"
          >
            + otro detalle
          </button>
        </div>

        {error && <p className="text-sm text-rose-700">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancelar
          </button>
          <button type="submit" disabled={busy || !name.trim()} className="btn-primary">
            {busy ? "Guardando…" : "Guardar ítem"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// Modal: evidencia (fotos)
// ---------------------------------------------------------------------------

function EvidenceModal({
  item,
  onClose,
  onCountChange,
}: {
  item: InventoryItem;
  onClose: () => void;
  onCountChange: (n: number) => void;
}) {
  const [photos, setPhotos] = useState<Evidence[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [caption, setCaption] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const t = await authToken();
      if (!t) return;
      const res = await fetch(`${apiBase()}/inventory/${item.id}/evidence`, {
        headers: { Authorization: `Bearer ${t}` },
      });
      if (res.ok) setPhotos((await res.json()) as Evidence[]);
    } finally {
      setLoading(false);
    }
  }, [item.id]);

  useEffect(() => {
    void load();
  }, [load]);

  async function upload(file: File) {
    setUploading(true);
    setError(null);
    try {
      const t = await authToken();
      if (!t) throw new Error("Sesión expirada.");
      const fd = new FormData();
      fd.append("file", file);
      if (caption.trim()) fd.append("caption", caption.trim());
      const res = await fetch(`${apiBase()}/inventory/${item.id}/evidence`, {
        method: "POST",
        headers: { Authorization: `Bearer ${t}` },
        body: fd,
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail ?? "No se pudo subir la foto.");
      setCaption("");
      const next = [body as Evidence, ...photos];
      setPhotos(next);
      onCountChange(next.length);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al subir");
    } finally {
      setUploading(false);
    }
  }

  return (
    <Modal title={`Evidencia · ${item.name}`} onClose={onClose}>
      <label className="flex cursor-pointer flex-col items-center gap-2 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center hover:border-brand-400">
        <span className="text-sm font-medium text-slate-700">
          {uploading ? "Subiendo…" : "Toca para tomar o subir una foto"}
        </span>
        <span className="text-xs text-slate-400">JPG, PNG o WEBP · hasta 8 MB</span>
        <input
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          disabled={uploading}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) void upload(f);
            e.target.value = "";
          }}
        />
      </label>
      <input
        className="input mt-2"
        placeholder="Descripción de la foto (opcional)"
        value={caption}
        onChange={(e) => setCaption(e.target.value)}
      />

      {error && <p className="mt-2 text-sm text-rose-700">{error}</p>}

      <div className="mt-4">
        {loading ? (
          <p className="text-sm text-slate-500">Cargando fotos…</p>
        ) : photos.length === 0 ? (
          <p className="text-sm text-slate-500">Sin fotos aún.</p>
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {photos.map((p) => (
              <figure key={p.id} className="overflow-hidden rounded-xl border border-slate-200">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={p.url ?? ""}
                  alt={p.caption ?? "Evidencia"}
                  className="aspect-square w-full object-cover"
                />
                {p.caption && (
                  <figcaption className="px-2 py-1 text-xs text-slate-500">{p.caption}</figcaption>
                )}
              </figure>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// Modal genérico
// ---------------------------------------------------------------------------

function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/40 p-0 backdrop-blur-sm sm:items-center sm:p-6"
      onClick={onClose}
    >
      <div
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-t-3xl bg-white p-6 shadow-card-hover sm:rounded-3xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700" aria-label="Cerrar">
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
