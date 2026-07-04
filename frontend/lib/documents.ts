/**
 * Metadatos de presentación de los documentos núcleo del MVP.
 * Refleja el registro del backend (generators/factory.py). Es solo presentación;
 * la fuente de verdad de la generación sigue en el backend.
 */
export type DocumentType =
  | "politica_seguridad"
  | "matriz_riesgos"
  | "plan_emergencias"
  | "gestion_incidentes";

export interface DocumentMeta {
  type: DocumentType;
  title: string;
  numeral: string;
  engine: "docx" | "xlsx";
  description: string;
}

export const DOCUMENTS: DocumentMeta[] = [
  {
    type: "politica_seguridad",
    title: "Política de seguridad",
    numeral: "5.2",
    engine: "docx",
    description:
      "Declaración de compromiso de la dirección con la seguridad en las actividades de aventura.",
  },
  {
    type: "matriz_riesgos",
    title: "Matriz de riesgos y oportunidades",
    numeral: "6.1.1",
    engine: "xlsx",
    description:
      "Valoración de peligros por actividad, controles y oportunidades de mejora.",
  },
  {
    type: "plan_emergencias",
    title: "Plan de respuesta a emergencias",
    numeral: "8.2",
    engine: "docx",
    description:
      "Escenarios de emergencia, protocolo de comunicación y coordinación de respuesta.",
  },
  {
    type: "gestion_incidentes",
    title: "Gestión de incidentes",
    numeral: "8.3",
    engine: "docx",
    description:
      "Procedimiento de reporte, investigación y acciones correctivas, con formato de reporte.",
  },
];

export type DocStatus =
  | "pending"
  | "generating"
  | "generated"
  | "approved"
  | "rejected"
  | "needs_correction";

export const STATUS_LABEL: Record<DocStatus, string> = {
  pending: "Pendiente",
  generating: "Generando",
  generated: "Generado",
  approved: "Aprobado",
  rejected: "Rechazado",
  needs_correction: "Requiere corrección",
};
