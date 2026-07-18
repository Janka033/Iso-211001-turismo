/**
 * Diccionario field_key → frase legible para las vistas de calidad/revisión.
 *
 * El backend trabaja con claves técnicas: los nombres de las variables Pydantic
 * de cada documento (`legal_representative`, `safety_objectives`, …) y los
 * `field_key` de `extraction_checklist`. Al cliente NO se le muestran esas
 * claves crudas — se traducen aquí a lenguaje humano.
 *
 * Es solo presentación: la fuente de verdad sigue siendo el backend. Si una
 * clave no está mapeada, `fieldLabel` la "humaniza" (guiones bajos → espacios,
 * primera letra en mayúscula) para nunca mostrar una cadena rota.
 *
 * Claves de la Parte B del checklist llevan sufijo `_<slug de actividad>`
 * (p. ej. `edades_permitidas_rafting`); el resolutor lo separa y anexa el
 * nombre de la actividad: "Edad mínima y máxima · Rafting".
 */

/** Nombre presentable de cada actividad de aventura (slug → etiqueta). */
export const ACTIVITY_LABELS: Record<string, string> = {
  rafting: "Rafting",
  rapel: "Rápel",
  espeleologia: "Espeleología",
  parapente: "Parapente",
  cabalgata: "Cabalgata",
  canyoning: "Canyoning",
  buceo: "Buceo",
  canopy: "Canopy",
  senderismo: "Senderismo",
  atv: "ATV / cuatrimoto",
  kayak: "Kayak",
  ciclomontanismo: "Ciclomontañismo",
  escalada: "Escalada",
};

/**
 * Frases legibles por clave base. Cubre las variables Pydantic de los 7 tipos
 * de documento y los field_key transversales/por-actividad del checklist.
 */
export const FIELD_LABELS: Record<string, string> = {
  // — Transversales (aparecen en varios documentos) —
  company_name: "Nombre de la empresa",
  nit: "NIT",
  scope: "Alcance",
  activities: "Actividades de aventura",
  legal_representative: "Representante legal",
  approval_date: "Fecha de aprobación",
  review_frequency: "Frecuencia de revisión",
  objective: "Objetivo",
  responsible: "Responsable",
  responsibles: "Responsables",

  // — Política de seguridad (PO-01, 5.2) —
  management_commitment: "Compromiso de la dirección",
  purpose_alignment: "Alineación con el propósito de la empresa",
  objectives_framework: "Marco para los objetivos de seguridad",
  safety_objectives: "Objetivos de seguridad",
  legal_commitment: "Compromiso de cumplimiento legal",
  continuous_improvement: "Compromiso de mejora continua",
  communication: "Comunicación de la política",

  // — Matriz de riesgos (MT-04, 6.1.1) —
  methodology: "Metodología de evaluación de riesgos",
  risks: "Riesgos identificados",
  opportunities: "Oportunidades identificadas",
  hazard: "Peligro",
  risk_description: "Descripción del riesgo",
  affected: "Personas afectadas",
  probability: "Probabilidad",
  severity: "Severidad",
  risk_level: "Nivel de riesgo",
  existing_controls: "Controles existentes",
  proposed_actions: "Acciones propuestas",
  residual_risk: "Riesgo residual",

  // — Plan de emergencias (PL-01, 8.2) —
  general_objective: "Objetivo general",
  emergency_scenarios: "Escenarios de emergencia",
  communication_protocol: "Protocolo de comunicación",
  emergency_contacts: "Contactos de emergencia",
  evacuation_resources: "Recursos de evacuación",
  external_coordination: "Coordinación con organismos externos",
  training_drills: "Capacitaciones y simulacros",
  scenario: "Escenario",
  response_steps: "Pasos de respuesta",
  resources: "Recursos",

  // — Gestión de incidentes (PR-02, 8.3) —
  incident_classification: "Clasificación de incidentes",
  procedure_steps: "Pasos del procedimiento",
  corrective_actions_process: "Proceso de acciones correctivas",
  record_retention: "Retención de registros",

  // — Manual de perfiles y cargos (MA-02) —
  org_structure: "Estructura organizacional",
  role_profiles: "Perfiles de cargo",
  role: "Cargo",
  level: "Nivel del cargo",
  purpose: "Propósito del cargo",
  functions: "Funciones",
  requirements: "Requisitos",
  reports_to: "Reporta a",

  // — Comunicación, participación y consulta (PR-07) —
  communication_matrix: "Matriz de comunicación",
  participation: "Participación",
  consultation: "Consulta",
  representation: "Representación",
  performance_evaluation: "Evaluación del desempeño",
  records: "Registros",
  topic: "Tema",
  method: "Método",
  channel: "Canal",
  audience: "Audiencia",
  frequency: "Frecuencia",

  // — Manual de inspección de equipos (MA-03, 8.1) —
  role_obligations: "Obligaciones por rol",
  equipment_items: "Equipos a inspeccionar",
  maintenance_types: "Tipos de mantenimiento",
  equipment: "Equipo",
  state: "Estado del equipo",
  inspection_type: "Tipo de inspección",

  // — Micro-preguntas de granularidad del onboarding (por documento) —
  communication_channels: "Canales de divulgación",
  activity_step_breakdown: "Actividad paso a paso (peligro/riesgo)",
  risk_factors: "Riesgos por factor",
  business_risks: "Riesgos del negocio",
  equipment_maintenance: "Mantenimiento por equipo",
  participation_consultation: "Participación y consulta",
  incident_report_fields: "Campos del reporte de incidentes",

  // — Alcance del SGSTA (4.3) —
  scope_statement: "Declaración del alcance",
  locations_detail: "Ubicación de la operación",
  site_characteristics: "Características del entorno",
  norm_exclusions: "Aplicabilidad de los requisitos de la norma",

  // — Acta de compromiso (5.1) —
  management_signer: "Firmante del acta de compromiso",
  city: "Ciudad de firma",
  acta_date: "Fecha de firma del acta",
  signer_name: "Nombre del firmante",
  signer_role: "Cargo del firmante",
  signer_phone: "Teléfono del firmante",
  signer_email: "Correo del firmante",

  // — Procedimiento de riesgos y oportunidades (6.1.1) —
  risk_management_lead: "Líder y frecuencia de la gestión de riesgos",
  responsible_role: "Cargo que lidera la gestión de riesgos",
  follow_up_frequency: "Frecuencia de seguimiento",

  // — Matriz de objetivos de seguridad (6.2) —
  policy_statement: "Política que enmarca los objetivos",
  objectives: "Filas de la matriz de objetivos",
  origin: "Origen del objetivo",
  objective: "Objetivo de seguridad",
  indicator_name: "Nombre del indicador",
  formula: "Fórmula del indicador",
  frequency: "Frecuencia de medición",
  goal: "Meta",

  // — Matriz de partes interesadas (4.2) —
  stakeholder_needs: "Partes interesadas y sus necesidades",
  stakeholder_compliance: "Cumplimiento a las partes interesadas",
  stakeholders: "Filas de la matriz de partes interesadas",
  elaborated_by: "Responsable de diligenciar",

  // — Checklist Parte A del plan de emergencias (8.2) —
  brigada_emergencias: "Brigada de emergencias",
  capacitaciones_personal_emergencias: "Capacitaciones del personal en emergencias",
  equipos_emergencia: "Equipos para atención de emergencias",
  organismos_apoyo: "Organismos de apoyo y sus teléfonos",
  hospital_cercano: "Hospital o centro de salud más cercano",
  vehiculos_evacuacion: "Vehículos para evacuación",

  // — Checklist Parte B, base por actividad (lleva sufijo _<slug>) —
  ruta_descripcion: "Descripción de la ruta",
  grupo_participantes: "Participantes por grupo (mín. y máx.)",
  edades_permitidas: "Edad mínima y máxima permitida",
  competencias_requeridas_participante: "Competencias requeridas al participante",
  restricciones_salud: "Restricciones de salud",
  equipos_operacion: "Equipos de operación",
  equipos_rescate: "Equipos de rescate",
  indumentaria: "Indumentaria requerida",
  seguro_contratado: "Seguro contratado",
  politica_cancelacion: "Política de cancelación",

  // — Checklist por actividad, categorías de 0021 (lleva sufijo _<slug>) —
  equipo: "Equipos",
  competencias: "Competencias del personal",
  emergencias: "Respuesta a emergencias",
  riesgos: "Riesgos",
  seguimiento: "Seguimiento y control",
};

/** Convierte una clave desconocida en una frase legible como último recurso. */
function humanize(key: string): string {
  const words = key.replace(/_/g, " ").trim();
  return words.charAt(0).toUpperCase() + words.slice(1);
}

/**
 * Traduce un field_key a una frase legible para el usuario.
 *
 * Orden de resolución:
 *   1. Coincidencia exacta en el diccionario.
 *   2. Clave con sufijo de actividad (`base_<slug>`) → "Base · Actividad".
 *   3. Humanización (fallback): guiones bajos → espacios, capitaliza.
 */
export function fieldLabel(key: string | null | undefined): string {
  if (!key) return "Campo sin identificar";

  const exact = FIELD_LABELS[key];
  if (exact) return exact;

  // Separa un posible sufijo de actividad: base_<slug>.
  for (const [slug, activity] of Object.entries(ACTIVITY_LABELS)) {
    const suffix = `_${slug}`;
    if (key.endsWith(suffix)) {
      const base = key.slice(0, -suffix.length);
      const baseLabel = FIELD_LABELS[base] ?? humanize(base);
      return `${baseLabel} · ${activity}`;
    }
  }

  return humanize(key);
}
