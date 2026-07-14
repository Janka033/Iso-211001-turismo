/**
 * Cliente de las pantallas de terreno (staff autenticado). Espejo de los
 * endpoints del módulo `salidas`. Todas las llamadas van con el JWT de
 * Supabase; el backend deriva tenant_id del token y RLS acota por rol.
 */
import { apiBase } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

const supabase = createClient();

export async function authToken(): Promise<string | null> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await authToken();
  if (!token) throw new Error("Tu sesión expiró. Vuelve a iniciar sesión.");
  const res = await fetch(`${apiBase()}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { detail?: unknown } | null;
    const detail =
      body && typeof body.detail === "string"
        ? body.detail
        : `Error ${res.status}`;
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** UUID de dispositivo para sync idempotente (32-40 chars, sin guiones). */
export function deviceId(): string {
  return crypto.randomUUID().replace(/-/g, "");
}

// ---------------------------------------------------------------------------
// Actividades y salidas
// ---------------------------------------------------------------------------

export interface ActivityProfile {
  id: string;
  name: string;
  activity_type: string;
  min_age: number | null;
  max_age: number | null;
  difficulty: string | null;
  duration_minutes: number | null;
  location: string | null;
}

export type SalidaStatus = "programada" | "en_curso" | "finalizada" | "cancelada";

export interface Salida {
  id: string;
  activity_profile_id: string;
  route_name: string | null;
  scheduled_start: string;
  capacity: number;
  status: SalidaStatus;
  qr_token_expires_at: string;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface SalidaCreated extends Salida {
  public_token: string;
  public_registration_path: string;
}

export const listActivityProfiles = () =>
  req<ActivityProfile[]>("/activity-profiles");

export const listSalidas = (status?: SalidaStatus) =>
  req<Salida[]>(`/salidas${status ? `?status_filter=${status}` : ""}`);

export const createSalida = (payload: {
  activity_profile_id: string;
  route_name: string | null;
  scheduled_start: string;
  capacity: number;
}) =>
  req<SalidaCreated>("/salidas", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const updateSalidaStatus = (id: string, status: SalidaStatus) =>
  req<Salida>(`/salidas/${id}/estado`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });

// ---------------------------------------------------------------------------
// Manifiesto
// ---------------------------------------------------------------------------

export interface Participante {
  id: string;
  full_name: string;
  document_type: string;
  document_number: string;
  phone: string;
  status: string;
  has_medical_alert: boolean;
}

export interface Manifiesto {
  salida: Salida;
  participantes: Participante[];
}

export const getManifiesto = (salidaId: string) =>
  req<Manifiesto>(`/salidas/${salidaId}/manifiesto`);

// ---------------------------------------------------------------------------
// Eventos de terreno (offline-friendly, idempotente por id de dispositivo)
// ---------------------------------------------------------------------------

export type EventType =
  | "check_in"
  | "inicio_recorrido"
  | "punto_control"
  | "novedad"
  | "induccion"
  | "emergencia_activada"
  | "pon_paso"
  | "emergencia_cerrada"
  | "fin_recorrido";

export const syncEventos = (
  salidaId: string,
  eventos: {
    id: string;
    event_type: EventType;
    participante_id?: string | null;
    note?: string | null;
    occurred_at: string;
  }[],
) =>
  req<{ received: number; inserted: number }>(`/salidas/${salidaId}/eventos`, {
    method: "POST",
    body: JSON.stringify({ eventos }),
  });

// ---------------------------------------------------------------------------
// Revisión de equipos (B / C / MC)
// ---------------------------------------------------------------------------

export type CheckPhase = "pre" | "post";
export type CheckStatus = "B" | "C" | "MC";

export const CHECK_STATUS_LABEL: Record<CheckStatus, string> = {
  B: "Buen estado",
  C: "Cambiar",
  MC: "Mantenimiento",
};

export interface EquipmentCheck {
  id: string;
  item_id: string;
  phase: string;
  status: string;
  quantity: number | null;
  note: string | null;
  evidence_paths: string[];
  checked_by: string;
  checked_at: string;
}

interface CheckIn {
  id: string;
  item_id: string;
  phase: CheckPhase;
  status: CheckStatus;
  quantity?: number | null;
  note?: string | null;
  evidence_paths: string[];
  checked_at: string;
}

/** Revisión general matinal (sin salida): mecánico / logística. */
export const syncGeneralChecks = (checks: CheckIn[]) =>
  req<{ received: number; inserted: number }>("/equipos/revisiones", {
    method: "POST",
    body: JSON.stringify({ checks }),
  });

/** Revisión ligada a una salida (fase pre/post). */
export const syncSalidaChecks = (salidaId: string, checks: CheckIn[]) =>
  req<{ received: number; inserted: number }>(
    `/salidas/${salidaId}/equipos/revisiones`,
    { method: "POST", body: JSON.stringify({ checks }) },
  );

// ---------------------------------------------------------------------------
// Incidentes
// ---------------------------------------------------------------------------

export interface IncidentOut {
  id: string;
  salida_id: string | null;
  activity_type: string;
  occurred_at: string;
  location: string;
  status: string;
  circumstances: string | null;
  created_at: string;
}

export const createIncident = (
  salidaId: string,
  payload: {
    occurred_at: string;
    location: string;
    circumstances: string;
    emergency_response?: string | null;
    evidence_paths: string[];
  },
) =>
  req<IncidentOut>(`/salidas/${salidaId}/incidentes`, {
    method: "POST",
    body: JSON.stringify({ involved_participants: [], ...payload }),
  });

// ---------------------------------------------------------------------------
// Inventario (para elegir el equipo a revisar)
// ---------------------------------------------------------------------------

export interface InventoryItem {
  id: string;
  category: string;
  name: string;
}

export const listInventory = (category?: string) =>
  req<InventoryItem[]>(`/inventory${category ? `?category=${category}` : ""}`);

// ---------------------------------------------------------------------------
// Evidencia (foto de terreno)
// ---------------------------------------------------------------------------

export async function uploadEvidencia(
  salidaId: string,
  file: File,
): Promise<string> {
  const token = await authToken();
  if (!token) throw new Error("Tu sesión expiró. Vuelve a iniciar sesión.");
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${apiBase()}/salidas/${salidaId}/evidencias`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  if (!res.ok) throw new Error("No se pudo subir la evidencia.");
  const body = (await res.json()) as { storage_path: string };
  return body.storage_path;
}
