/**
 * Cliente del flujo público del turista (link/QR, sin auth). Espejo de los
 * schemas del backend `salidas` (RegistroTuristaIn, PublicConsentOut,
 * FirmaConsentimientoIn). El token de la URL identifica la salida; el backend
 * deriva el tenant de él, nunca del body.
 */
import { apiBase } from "@/lib/api";

export type DocumentType = "CC" | "TI" | "CE" | "PA";
export type BloodType =
  | "A+"
  | "A-"
  | "B+"
  | "B-"
  | "AB+"
  | "AB-"
  | "O+"
  | "O-";

export const DOCUMENT_TYPES: { id: DocumentType; label: string }[] = [
  { id: "CC", label: "Cédula de ciudadanía" },
  { id: "TI", label: "Tarjeta de identidad" },
  { id: "CE", label: "Cédula de extranjería" },
  { id: "PA", label: "Pasaporte" },
];

export const BLOOD_TYPES: BloodType[] = [
  "A+",
  "A-",
  "B+",
  "B-",
  "AB+",
  "AB-",
  "O+",
  "O-",
];

export interface EmergencyContact {
  nombre: string;
  parentesco: string;
  telefono: string;
}

export interface Guardian {
  nombre: string;
  documento: string;
  parentesco: string;
  telefono: string;
}

export interface MedicalConditions {
  cardiaca: boolean;
  respiratoria: boolean;
  diabetes: boolean;
  epilepsia: boolean;
  embarazo: boolean;
  cirugia_reciente: boolean;
  otras?: string | null;
}

export const MEDICAL_CONDITION_LABELS: {
  key: keyof Omit<MedicalConditions, "otras">;
  label: string;
}[] = [
  { key: "cardiaca", label: "Condición cardíaca" },
  { key: "respiratoria", label: "Condición respiratoria (asma…)" },
  { key: "diabetes", label: "Diabetes" },
  { key: "epilepsia", label: "Epilepsia" },
  { key: "embarazo", label: "Embarazo" },
  { key: "cirugia_reciente", label: "Cirugía reciente" },
];

export interface RegistroTuristaIn {
  document_type: DocumentType;
  document_number: string;
  full_name: string;
  birth_date: string; // YYYY-MM-DD
  nationality?: string | null;
  phone: string;
  email: string;
  guardian?: Guardian | null;
  emergency_contacts: EmergencyContact[];
  eps: string;
  arl?: string | null;
  blood_type: BloodType;
  allergies: string;
  medical_conditions: MedicalConditions;
  current_medications?: string | null;
  activity_specific: Record<string, string | number | boolean>;
  declares_truthful: boolean;
  accepts_data_processing: boolean;
  received_risk_info: boolean;
  declares_sober: boolean;
}

export interface RegistroTuristaOut {
  participante_id: string;
  salida_id: string;
  status: string;
}

export interface PublicConsent {
  activity_name: string | null;
  template_version: number;
  body_md: string;
}

export interface FirmaConsentimientoOut {
  consentimiento_id: string;
  participante_id: string;
  template_version: number;
  signed_by_guardian: boolean;
  signed_at: string;
  participante_status: string;
}

/** Extrae el mensaje de error del backend (FastAPI: {detail}) sin romper. */
async function detailOrThrow(res: Response, fallback: string): Promise<never> {
  const body = (await res.json().catch(() => null)) as { detail?: unknown } | null;
  const detail =
    body && typeof body.detail === "string" ? body.detail : fallback;
  throw new Error(detail);
}

export async function fetchConsent(token: string): Promise<PublicConsent> {
  const res = await fetch(
    `${apiBase()}/public/salidas/${token}/consentimiento`,
  );
  if (!res.ok) {
    if (res.status === 404 || res.status === 410) {
      await detailOrThrow(res, "El enlace de registro no es válido o ya venció.");
    }
    await detailOrThrow(res, "No se pudo cargar el consentimiento.");
  }
  return (await res.json()) as PublicConsent;
}

export async function submitRegistro(
  token: string,
  payload: RegistroTuristaIn,
): Promise<RegistroTuristaOut> {
  const res = await fetch(`${apiBase()}/public/salidas/${token}/registro`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) await detailOrThrow(res, "No se pudo completar el registro.");
  return (await res.json()) as RegistroTuristaOut;
}

export async function submitFirma(
  token: string,
  payload: {
    participante_id: string;
    accepted_privacy: boolean;
    accepted_risk_info: boolean;
    signature_png_base64: string;
  },
): Promise<FirmaConsentimientoOut> {
  const res = await fetch(
    `${apiBase()}/public/salidas/${token}/consentimientos`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  if (!res.ok) await detailOrThrow(res, "No se pudo registrar la firma.");
  return (await res.json()) as FirmaConsentimientoOut;
}
