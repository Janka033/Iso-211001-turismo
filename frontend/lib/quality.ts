/**
 * Tipos y etiquetas de la vista de revisión de calidad. Reflejan la tabla
 * quality_reviews (DB) y los schemas del módulo quality del backend; es solo
 * presentación — la fuente de verdad de la evaluación sigue en el backend.
 */
import type { DocumentType } from "@/lib/documents";

export interface QualityAlert {
  pattern_type: string | null;
  pattern: string;
  detail: string | null;
}

export interface SuggestedCorrection {
  field: string | null;
  issue: string;
  suggestion: string | null;
}

export interface QualityEvaluation {
  score: number;
  completeness: {
    missing_required_fields: string[];
    missing_optional_fields: string[];
    comment: string | null;
  };
  coherence: {
    coherent: boolean;
    issues: string[];
  };
  alerts: QualityAlert[];
  observations: string[];
  suggested_corrections: SuggestedCorrection[];
}

export type ReviewStatus =
  | "pending_review"
  | "approved"
  | "rejected"
  | "needs_correction";

export type ReviewDecision = Exclude<ReviewStatus, "pending_review">;

export interface QualityReview {
  id: string;
  document_id: string;
  score: number;
  evaluation: QualityEvaluation;
  review_status: ReviewStatus;
  review_notes: string | null;
  reviewed_at: string | null;
  created_at: string;
}

/** Un documento generado con su última evaluación de calidad (si existe). */
export interface ReviewableDocument {
  id: string;
  document_type: DocumentType;
  version: number;
  created_at: string;
  review: QualityReview | null;
}

export const REVIEW_STATUS_LABEL: Record<ReviewStatus, string> = {
  pending_review: "Pendiente de revisión",
  approved: "Aprobado",
  rejected: "Rechazado",
  needs_correction: "Corrección solicitada",
};

/**
 * Nivel de cumplimiento normativo a partir del score del Auditor (0-100).
 * Un score no es "completitud": un documento puede tener 100% de campos con
 * texto y aun así incumplir la norma. Umbrales de producto:
 *   Rojo    0-59  → requiere ajustes críticos
 *   Amarillo 60-89 → aceptable con observaciones
 *   Verde   90-100 → cumplimiento óptimo
 */
export interface ComplianceLevel {
  label: string;
  /** clase de color de la barra (fondo). */
  bar: string;
  /** clase de color del texto del porcentaje. */
  text: string;
}

export function complianceLevel(score: number): ComplianceLevel {
  if (score >= 90) {
    return { label: "Cumplimiento óptimo", bar: "bg-emerald-500", text: "text-emerald-700" };
  }
  if (score >= 60) {
    return { label: "Aceptable con observaciones", bar: "bg-amber-500", text: "text-amber-700" };
  }
  return { label: "Requiere ajustes críticos", bar: "bg-rose-500", text: "text-rose-700" };
}
