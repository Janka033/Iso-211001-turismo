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
