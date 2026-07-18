/**
 * Metadatos de presentación de los documentos núcleo del MVP.
 * Refleja el registro del backend (generators/factory.py). Es solo presentación;
 * la fuente de verdad de la generación sigue en el backend.
 */
export type DocumentType =
  | "alcance_sgsta"
  | "matriz_partes_interesadas"
  | "acta_compromiso"
  | "politica_seguridad"
  | "manual_perfiles_cargos"
  | "procedimiento_riesgos_oportunidades"
  | "matriz_riesgos"
  | "matriz_objetivos_seguridad"
  | "comunicacion_participacion_consulta"
  | "control_informacion_documentada"
  | "manual_inspeccion_equipos"
  | "control_operacional"
  | "plan_emergencias"
  | "gestion_incidentes";

export interface DocumentMeta {
  type: DocumentType;
  title: string;
  numeral: string;
  engine: "docx" | "xlsx";
  description: string;
}

// En el orden de la ruta guiada (document_roadmap). La matriz de requisitos
// legales (6.1.3) se añadirá cuando exista su generador.
export const DOCUMENTS: DocumentMeta[] = [
  {
    type: "alcance_sgsta",
    title: "Alcance del SGSTA",
    numeral: "4.3",
    engine: "docx",
    description:
      "Qué cubre tu sistema de gestión: servicios, ubicaciones, entorno y aplicabilidad de la norma.",
  },
  {
    type: "matriz_partes_interesadas",
    title: "Matriz de partes interesadas",
    numeral: "4.2",
    engine: "xlsx",
    description:
      "Quién se relaciona con tu operación, qué necesita y espera, y cómo les cumples.",
  },
  {
    type: "acta_compromiso",
    title: "Acta de compromiso",
    numeral: "5.1",
    engine: "docx",
    description:
      "El compromiso firmado de la alta dirección con el sistema de gestión de seguridad.",
  },
  {
    type: "procedimiento_riesgos_oportunidades",
    title: "Procedimiento de riesgos y oportunidades",
    numeral: "6.1.1",
    engine: "docx",
    description:
      "El paso a paso para identificar, evaluar, tratar y hacer seguimiento a riesgos y oportunidades.",
  },
  {
    type: "matriz_objetivos_seguridad",
    title: "Matriz de objetivos de seguridad",
    numeral: "6.2",
    engine: "xlsx",
    description:
      "Tus objetivos de seguridad con indicador, fórmula, meta, responsable y frecuencia de medición.",
  },
  {
    type: "control_informacion_documentada",
    title: "Control de la información documentada",
    numeral: "7.5.1",
    engine: "docx",
    description:
      "Cómo se crean, distribuyen, protegen y retienen los documentos del sistema.",
  },
  {
    type: "control_operacional",
    title: "Planificación y control operacional",
    numeral: "8.1",
    engine: "xlsx",
    description:
      "Por actividad: normas aplicables, aspectos a controlar y cómo se controlan.",
  },
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
  {
    type: "manual_perfiles_cargos",
    title: "Manual de perfiles y funciones de cargo",
    numeral: "5.3",
    engine: "docx",
    description:
      "Estructura organizacional y perfil de cada cargo (funciones, competencias, nivel).",
  },
  {
    type: "comunicacion_participacion_consulta",
    title: "Comunicación, participación y consulta",
    numeral: "7.4",
    engine: "docx",
    description:
      "Matriz de comunicación del SGS y mecanismos de participación y consulta del personal.",
  },
  {
    type: "manual_inspeccion_equipos",
    title: "Inspección y mantenimiento de equipos",
    numeral: "8.1",
    engine: "docx",
    description:
      "Control de equipos por actividad, estados y tipos de mantenimiento, según el equipo real.",
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
