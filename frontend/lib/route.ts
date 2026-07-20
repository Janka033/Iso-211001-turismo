/**
 * Tipos y presentación de la ruta guiada (GET /onboarding/roadmap).
 * La fuente de verdad es el backend (document_roadmap + estado derivado);
 * aquí solo viven los agrupadores visuales (unidades por numeral).
 */

export interface RoadmapStep {
  step_order: number;
  document_type: string;
  title: string;
  numeral: string;
  generator_ready: boolean;
  status: string; // 'pendiente' | 'generated' | 'approved' | …
  completeness: number | null;
  last_score: number | null;
  // Generado Y en orden (prefijo contiguo desde el inicio). Un doc generado
  // fuera de secuencia NO es `complete`: en el mapa sale bloqueado, no "Generado".
  complete: boolean;
}

export interface RoadmapResponse {
  steps: RoadmapStep[];
  current_step: number | null;
  total: number;
}

/** Unidades tipo Duolingo: el capítulo de la norma al que pertenece el paso. */
export interface RouteUnit {
  chapter: string; // primer nivel del numeral ("4", "5", …)
  title: string;
  subtitle: string;
}

export const UNITS: RouteUnit[] = [
  {
    chapter: "4",
    title: "Tu empresa y su contexto",
    subtitle: "Qué cubre tu sistema y quiénes se relacionan con él",
  },
  {
    chapter: "5",
    title: "Liderazgo",
    subtitle: "El compromiso de la dirección, la política y los cargos",
  },
  {
    chapter: "6",
    title: "Planificación",
    subtitle: "Riesgos, requisitos legales y objetivos medibles",
  },
  {
    chapter: "7",
    title: "Apoyo",
    subtitle: "Comunicación y control de los documentos",
  },
  {
    chapter: "8",
    title: "Operación",
    subtitle: "Controles, equipos, emergencias e incidentes",
  },
];

/** Títulos por tipo de documento (presentación; espejo de document_roadmap). */
export const ROUTE_TITLES: Record<string, string> = {
  alcance_sgsta: "Alcance del SGSTA",
  matriz_partes_interesadas: "Matriz de partes interesadas",
  acta_compromiso: "Acta de compromiso",
  politica_seguridad: "Política de seguridad",
  manual_perfiles_cargos: "Manual de perfiles y cargos",
  procedimiento_riesgos_oportunidades: "Procedimiento de riesgos y oportunidades",
  matriz_riesgos: "Matriz de riesgos y oportunidades",
  matriz_requisitos_legales: "Matriz de requisitos legales",
  matriz_objetivos_seguridad: "Matriz de objetivos de seguridad",
  comunicacion_participacion_consulta: "Comunicación, participación y consulta",
  control_informacion_documentada: "Control de la información documentada",
  manual_inspeccion_equipos: "Inspección y mantenimiento de equipos",
  control_operacional: "Planificación y control operacional",
  plan_emergencias: "Plan de respuesta a emergencias",
  gestion_incidentes: "Gestión de incidentes",
};

export function chapterOf(numeral: string): string {
  return numeral.split(".")[0] ?? numeral;
}

/** Estado visual de un nodo del mapa (derivado, nunca fuente de verdad). */
export type NodeState = "locked" | "soon" | "current" | "done" | "crown";

export function nodeState(step: RoadmapStep, currentStep: number | null): NodeState {
  // "Hecho" exige estar COMPLETO (generado y en orden). Un doc generado fuera de
  // secuencia no es `complete` => cae a "locked", no a "done" (era el bug del
  // paso adelantado que aparecía "Generado" con los previos bloqueados).
  if (step.complete) {
    return step.last_score !== null && step.last_score >= 80 ? "crown" : "done";
  }
  if (!step.generator_ready) return "soon";
  if (currentStep !== null && step.step_order === currentStep) return "current";
  return "locked";
}

/** Estrellas del score del Auditor: <60 = 1, 60-79 = 2, ≥80 = 3. */
export function stars(score: number | null): number | null {
  if (score === null) return null;
  if (score >= 80) return 3;
  if (score >= 60) return 2;
  return 1;
}
