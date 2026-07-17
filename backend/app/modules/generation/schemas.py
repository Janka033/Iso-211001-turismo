"""Modelos Pydantic del módulo de generación.

Dos familias de modelos:

- API: ``GenerateRequest`` / ``GeneratedDocument`` (entrada/salida HTTP).
- Variables de documento: el JSON ESTRICTO que la IA debe devolver. Se valida
  con Pydantic ANTES de tocar la plantilla (anti-alucinación). Todo campo es
  opcional: lo que la IA no extraiga queda en ``None`` / lista vacía y el
  generador lo sustituye por ``[PENDIENTE: ...]``. La IA NUNCA inventa.
"""

from pydantic import BaseModel, Field, field_validator, model_validator


class AIVariablesModel(BaseModel):
    """Base de los modelos que validan la SALIDA de la IA.

    El prompt permite "null (o lista vacía)" para lo que falte, pero un campo
    ``list[...]`` no acepta null: la IA que obedece literalmente provocaría un
    502. Aquí se eliminan las claves en null ANTES de validar, de modo que
    apliquen los defaults del modelo (None / lista vacía). No relaja el schema:
    tipos incorrectos siguen fallando en la validación.
    """

    @model_validator(mode="before")
    @classmethod
    def _drop_nulls(cls, data: object) -> object:
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v is not None}
        return data


class GenerateRequest(BaseModel):
    """Cuerpo del POST de generación. NO lleva tenant_id: sale del JWT."""

    regenerate: bool = Field(
        default=False,
        description="Si ya existe el documento, crea una nueva versión.",
    )


class GeneratedDocument(BaseModel):
    """Resultado de una generación. Refleja el snapshot de reproducibilidad."""

    document_id: str
    document_type: str
    version: int
    status: str
    storage_path: str | None = None
    completeness: float = Field(description="% de campos requeridos con dato (0-100).")
    pending_fields: list[str] = Field(
        default_factory=list,
        description="Campos que quedaron como [PENDIENTE] por falta de dato del cliente.",
    )
    prompt_version: str | None = None
    template_version: str | None = None


class DownloadResponse(BaseModel):
    """URL firmada y temporal para descargar un documento generado."""

    url: str


# ---------------------------------------------------------------------------
# Variables de documento (salida de la IA, validada por Pydantic)
# ---------------------------------------------------------------------------


class SecurityPolicyVariables(AIVariablesModel):
    """Variables de la Política de seguridad (numeral 5.2).

    Es el contrato JSON que la IA debe cumplir. ``model_json_schema()`` se
    inyecta en el prompt para que el modelo conozca la forma esperada.
    """

    company_name: str | None = Field(
        default=None, description="Razón social de la empresa."
    )
    nit: str | None = Field(default=None, description="NIT de la empresa.")
    scope: str | None = Field(
        default=None,
        description="Alcance: actividades de aventura y ubicaciones de operación.",
    )
    activities: list[str] = Field(
        default_factory=list,
        description="Actividades de turismo de aventura que ofrece la empresa.",
    )
    management_commitment: str | None = Field(
        default=None,
        description="Compromiso de la alta dirección con la seguridad.",
    )
    purpose_alignment: str | None = Field(
        default=None,
        description=(
            "Apropiación del propósito organizacional (principio 5.2.a): cómo "
            "la política se alinea con el propósito de la organización."
        ),
    )
    objectives_framework: str | None = Field(
        default=None,
        description=(
            "Marco para los objetivos de seguridad (principio 5.2.b): cómo la "
            "política orienta el establecimiento de objetivos y metas. Es el "
            "enunciado del principio, NO los objetivos en sí."
        ),
    )
    safety_objectives: list[str] = Field(
        default_factory=list,
        description=(
            "Objetivos de seguridad de la organización (6.2), cada uno como "
            "enunciado completo. Incluir SIEMPRE el objetivo medible definido "
            "por la dirección si está en el contexto; no volcar aquí fragmentos "
            "sueltos de los principios de la política."
        ),
    )
    legal_commitment: str | None = Field(
        default=None,
        description="Compromiso de cumplimiento legal y reglamentario aplicable.",
    )
    continuous_improvement: str | None = Field(
        default=None,
        description="Compromiso de mejora continua del sistema de gestión.",
    )
    communication: str | None = Field(
        default=None,
        description="Cómo se comunica y está disponible la política.",
    )
    legal_representative: str | None = Field(
        default=None,
        description="Representante legal que aprueba la política.",
    )
    approval_date: str | None = Field(
        default=None,
        description=(
            "Fecha de aprobación de ESTE documento (YYYY-MM-DD), SOLO si el "
            "cliente la indicó explícitamente. NUNCA derivarla de otras fechas "
            "del contexto (p. ej. la fecha de aprobación del SGS)."
        ),
    )


class RiskEntry(AIVariablesModel):
    """Una fila de la matriz de riesgos (un peligro de una actividad)."""

    activity: str | None = Field(default=None, description="Actividad de aventura.")
    hazard: str | None = Field(
        default=None, description="Peligro o amenaza identificada."
    )
    risk_description: str | None = Field(
        default=None, description="Descripción del riesgo (qué puede pasar)."
    )
    affected: str | None = Field(
        default=None, description="Quién/qué se ve afectado (turistas, guías, equipos)."
    )
    probability: str | None = Field(
        default=None, description="Probabilidad (Baja / Media / Alta)."
    )
    severity: str | None = Field(
        default=None, description="Severidad de la consecuencia (Leve / Moderada / Grave)."
    )
    risk_level: str | None = Field(
        default=None, description="Nivel de riesgo resultante (Bajo / Medio / Alto)."
    )
    existing_controls: str | None = Field(
        default=None, description="Controles existentes."
    )
    proposed_actions: str | None = Field(
        default=None,
        description=(
            "Acciones de tratamiento propuestas para reducir este riesgo. "
            "DERÍVALAS de los controles, mantenimientos, capacitaciones y "
            "protocolos que el cliente ya describió en su contexto; NUNCA "
            "inventes recursos o prácticas que el cliente no tenga."
        ),
    )
    responsible: str | None = Field(
        default=None, description="Responsable de la acción."
    )
    residual_risk: str | None = Field(
        default=None, description="Riesgo residual tras los controles."
    )


class OpportunityEntry(AIVariablesModel):
    """Una oportunidad de mejora con su tratamiento (tabla del 6.1.1)."""

    opportunity: str | None = Field(
        default=None, description="Oportunidad de mejora identificada."
    )
    impact: str | None = Field(
        default=None,
        description="Impacto esperado en la seguridad o en el negocio.",
    )
    actions: str | None = Field(
        default=None,
        description=(
            "Acciones concretas para aprovecharla. DERÍVALAS de los planes y "
            "recursos que el cliente ya describió; NUNCA inventes recursos que "
            "no tenga."
        ),
    )
    responsible: str | None = Field(
        default=None, description="Responsable del seguimiento."
    )
    timeline: str | None = Field(
        default=None, description="Cronograma o plazo de ejecución."
    )
    indicator: str | None = Field(
        default=None, description="Indicador de avance o eficacia."
    )


class RiskMatrixVariables(AIVariablesModel):
    """Variables de la Matriz de riesgos y oportunidades (numeral 6.1.1 + Anexo A).

    ``risks`` es estructurado (filas de la matriz); el generador lo resuelve por
    su cuenta. El resto son campos planos.
    """

    company_name: str | None = Field(
        default=None, description="Razón social de la empresa."
    )
    scope: str | None = Field(
        default=None, description="Alcance de la valoración de riesgos."
    )
    methodology: str | None = Field(
        default=None,
        description="Metodología de valoración (cómo se cruzan probabilidad y severidad).",
    )
    risks: list[RiskEntry] = Field(
        default_factory=list,
        description="Filas de la matriz: un peligro por fila.",
    )
    opportunities: list[OpportunityEntry] = Field(
        default_factory=list,
        description=(
            "Oportunidades de mejora identificadas (6.1.1), cada una con su "
            "tratamiento estructurado."
        ),
    )

    @field_validator("opportunities", mode="before")
    @classmethod
    def _coerce_opportunities(cls, value: object) -> object:
        # Snapshots anteriores guardaban list[str]; se re-validan como la
        # entrada estructurada mínima (solo el enunciado) sin romper el render.
        if isinstance(value, list):
            return [
                {"opportunity": item} if isinstance(item, str) else item
                for item in value
            ]
        return value


class EmergencyScenario(AIVariablesModel):
    """Un escenario de emergencia y su respuesta (fila del plan)."""

    scenario: str | None = Field(
        default=None, description="Tipo de emergencia (p.ej. accidente en rafting)."
    )
    activity: str | None = Field(
        default=None, description="Actividad asociada al escenario."
    )
    response_steps: str | None = Field(
        default=None, description="Pasos de respuesta ante la emergencia."
    )
    responsible: str | None = Field(
        default=None, description="Responsable de coordinar la respuesta."
    )
    resources: str | None = Field(
        default=None, description="Recursos/equipos necesarios para la respuesta."
    )


class EmergencyPlanVariables(AIVariablesModel):
    """Variables del Plan de respuesta a emergencias (numeral 8.2).

    ``emergency_scenarios`` es estructurado; el resto son campos planos.
    """

    company_name: str | None = Field(
        default=None, description="Razón social de la empresa."
    )
    scope: str | None = Field(
        default=None, description="Alcance del plan: actividades y ubicaciones cubiertas."
    )
    general_objective: str | None = Field(
        default=None,
        description=(
            "Objetivo general DEL PLAN DE EMERGENCIAS (prepararse y responder "
            "ante emergencias). NUNCA copiar objetivos etiquetados para otros "
            "documentos del contexto (p. ej. el del manual de inspección MA-03)."
        ),
    )
    emergency_scenarios: list[EmergencyScenario] = Field(
        default_factory=list,
        description="Escenarios de emergencia identificados y su respuesta.",
    )
    communication_protocol: str | None = Field(
        default=None,
        description=(
            "Protocolo de comunicación y cadena de notificación en emergencia. "
            "Integra, SI el cliente los describió: la verificación de "
            "funcionalidad/carga/cobertura de los equipos de comunicación "
            "antes de cada salida, las zonas sin cobertura de la ruta, la "
            "clasificación de la emergencia por grados (derivada de la "
            "clasificación de eventos del cliente, comunicando el grado al "
            "activar) y cómo se informa a los participantes del plan antes de "
            "la actividad (p. ej. charla de seguridad) y cómo se recaba su "
            "información de salud y contacto previa. NUNCA inventes equipos o "
            "prácticas que el cliente no tenga."
        ),
    )
    emergency_contacts: list[str] = Field(
        default_factory=list,
        description="Contactos de emergencia (bomberos, ambulancia, rescate, ARL).",
    )
    evacuation_resources: str | None = Field(
        default=None,
        description=(
            "Rutas de evacuación y recursos disponibles: puntos de salida de "
            "la ruta, vehículos y equipos de evacuación (camilla, "
            "inmovilizadores, linternas, botiquines…) que el cliente listó — "
            "todos los que describió, ninguno que no tenga."
        ),
    )
    external_coordination: str | None = Field(
        default=None,
        description="Coordinación con servicios externos (hospitales, defensa civil).",
    )
    training_drills: str | None = Field(
        default=None, description="Capacitación del personal y simulacros."
    )
    review_frequency: str | None = Field(
        default=None, description="Frecuencia de revisión y actualización del plan."
    )
    legal_representative: str | None = Field(
        default=None, description="Representante legal que aprueba el plan."
    )
    approval_date: str | None = Field(
        default=None,
        description=(
            "Fecha de aprobación de ESTE documento (YYYY-MM-DD), SOLO si el "
            "cliente la indicó explícitamente. NUNCA derivarla de otras fechas "
            "del contexto (p. ej. la fecha de aprobación del SGS)."
        ),
    )


class IncidentManagementVariables(AIVariablesModel):
    """Variables del Procedimiento de gestión de incidentes (numeral 8.3).

    El documento incluye el procedimiento (contenido inteligente) y un FORMATO
    de reporte de incidentes (estructura fija, en blanco para diligenciar)."""

    company_name: str | None = Field(
        default=None, description="Razón social de la empresa."
    )
    scope: str | None = Field(
        default=None, description="Alcance del procedimiento de gestión de incidentes."
    )
    objective: str | None = Field(
        default=None, description="Objetivo del procedimiento."
    )
    incident_classification: list[str] = Field(
        default_factory=list,
        description=(
            "Clasificación de eventos (casi-accidente, incidente, accidente y "
            "grados de severidad), usando las categorías que el cliente "
            "definió."
        ),
    )
    procedure_steps: list[str] = Field(
        default_factory=list,
        description=(
            "Pasos del procedimiento (reportar, registrar, investigar, "
            "cerrar). El paso de reporte debe enumerar el contenido mínimo "
            "del informe según el numeral 8.3 de la norma (fecha, hora y "
            "lugar; actividad; personas involucradas; condiciones "
            "ambientales, equipo usado y circunstancias particulares; "
            "descripción; atención brindada; causa probable; fuente de la "
            "información) COMBINADO con los campos que el cliente ya "
            "registra, y distinguir el informe de INCIDENTE del informe de "
            "ACCIDENTE (este último con datos, edad y nacionalidad de la "
            "víctima, quiénes intervinieron y medidas correctivas)."
        ),
    )
    responsible: str | None = Field(
        default=None, description="Responsable de la gestión de incidentes."
    )
    corrective_actions_process: str | None = Field(
        default=None,
        description="Cómo se definen y siguen las acciones correctivas.",
    )
    record_retention: str | None = Field(
        default=None, description="Conservación y custodia de los registros."
    )
    review_frequency: str | None = Field(
        default=None, description="Frecuencia de revisión del procedimiento."
    )
    legal_representative: str | None = Field(
        default=None, description="Representante legal que aprueba el procedimiento."
    )
    approval_date: str | None = Field(
        default=None,
        description=(
            "Fecha de aprobación de ESTE documento (YYYY-MM-DD), SOLO si el "
            "cliente la indicó explícitamente. NUNCA derivarla de otras fechas "
            "del contexto (p. ej. la fecha de aprobación del SGS)."
        ),
    )


# ---------------------------------------------------------------------------
# MA-02 · Manual de perfiles y funciones de cargo (numerales 5.3 y 7.2)
# ---------------------------------------------------------------------------


class RoleProfile(AIVariablesModel):
    """Perfil de un cargo (fila estructurada del manual)."""

    role: str | None = Field(
        default=None, description="Cargo (p.ej. Gerente, Coordinador Operativo, Guía)."
    )
    level: str | None = Field(
        default=None,
        description=(
            "Nivel: Directivo, Administrativo u Operativo. Directivo SOLO para "
            "la dirección/gerencia; reportar al representante legal no hace "
            "Directivo a un cargo."
        ),
    )
    purpose: str | None = Field(
        default=None, description="Objetivo o propósito del cargo."
    )
    functions: list[str] = Field(
        default_factory=list, description="Funciones y responsabilidades del cargo."
    )
    requirements: str | None = Field(
        default=None, description="Requisitos y competencias (formación, experiencia)."
    )
    reports_to: str | None = Field(
        default=None, description="Cargo al que reporta."
    )


class ProfilesManualVariables(AIVariablesModel):
    """Variables del Manual de perfiles y funciones de cargo (MA-02).

    ``role_profiles`` es estructurado (un perfil por cargo); el resto son
    campos planos. Se apoya en ``staff_roles`` del onboarding (qué cargos existen).
    """

    company_name: str | None = Field(
        default=None, description="Razón social de la empresa."
    )
    objective: str | None = Field(
        default=None, description="Objetivo del manual de perfiles y funciones."
    )
    scope: str | None = Field(default=None, description="Alcance del manual.")
    org_structure: str | None = Field(
        default=None,
        description="Estructura organizacional (niveles directivo y operativo, cargos).",
    )
    role_profiles: list[RoleProfile] = Field(
        default_factory=list, description="Perfil y funciones por cada cargo."
    )
    legal_representative: str | None = Field(
        default=None, description="Representante legal que aprueba el manual."
    )
    approval_date: str | None = Field(
        default=None,
        description=(
            "Fecha de aprobación de ESTE documento (YYYY-MM-DD), SOLO si el "
            "cliente la indicó explícitamente; nunca derivada de otras fechas."
        ),
    )


# ---------------------------------------------------------------------------
# PR-07 · Procedimiento de comunicación, participación y consulta (numeral 7.4)
# ---------------------------------------------------------------------------


class CommunicationEntry(AIVariablesModel):
    """Una fila de la matriz de comunicación (4.1)."""

    topic: str | None = Field(default=None, description="Qué se comunica.")
    method: str | None = Field(default=None, description="Cómo se comunica.")
    channel: str | None = Field(default=None, description="Vía o medio de comunicación.")
    audience: str | None = Field(default=None, description="A quién se comunica.")
    frequency: str | None = Field(default=None, description="Con qué frecuencia.")


class CommunicationProcedureVariables(AIVariablesModel):
    """Variables del Procedimiento de comunicación, participación y consulta (PR-07).

    ``communication_matrix`` es estructurado; el resto son campos planos.
    """

    company_name: str | None = Field(
        default=None, description="Razón social de la empresa."
    )
    objective: str | None = Field(
        default=None,
        description=(
            "Objetivo del procedimiento: asegurar la comunicación, "
            "participación y consulta en seguridad (7.4). Es texto normativo "
            "estándar, no un dato operativo: DERÍVALO de las actividades y el "
            "alcance reales del cliente; no lo dejes null por falta de "
            "mención literal."
        ),
    )
    scope: str | None = Field(
        default=None,
        description=(
            "Alcance del procedimiento: a quién aplica (personal, "
            "participantes, partes interesadas) y en qué operaciones. "
            "DERÍVALO del alcance y las actividades reales del cliente; no lo "
            "dejes null por falta de mención literal."
        ),
    )
    responsibles: str | None = Field(
        default=None, description="Responsables del proceso de comunicación."
    )
    communication_matrix: list[CommunicationEntry] = Field(
        default_factory=list,
        description="Matriz de comunicación: qué/cómo/vía/a quién/frecuencia.",
    )
    participation: str | None = Field(
        default=None, description="Mecanismos de participación del personal (4.2)."
    )
    consultation: str | None = Field(
        default=None, description="Mecanismos de consulta al personal (4.3)."
    )
    representation: str | None = Field(
        default=None,
        description="Representación del personal en asuntos de seguridad (4.4).",
    )
    performance_evaluation: str | None = Field(
        default=None, description="Cómo se evalúa el desempeño del proceso."
    )
    records: str | None = Field(
        default=None, description="Registros que deja el procedimiento."
    )
    legal_representative: str | None = Field(
        default=None, description="Representante legal que aprueba el procedimiento."
    )
    approval_date: str | None = Field(
        default=None,
        description=(
            "Fecha de aprobación de ESTE documento (YYYY-MM-DD), SOLO si el "
            "cliente la indicó explícitamente; nunca derivada de otras fechas."
        ),
    )


# ---------------------------------------------------------------------------
# MA-03 · Manual de inspección y mantenimiento de equipos (numeral 8.1 + Anexo A)
# ---------------------------------------------------------------------------


class EquipmentInspectionItem(AIVariablesModel):
    """Una fila del control de equipos (derivada de ``activity_fields``)."""

    activity: str | None = Field(
        default=None, description="Actividad de aventura a la que pertenece el equipo."
    )
    equipment: str | None = Field(
        default=None, description="Equipo o elemento de seguridad."
    )
    state: str | None = Field(
        default=None, description="Estado: Ok / A revisar / En cuarentena / De baja."
    )
    inspection_type: str | None = Field(
        default=None,
        description=(
            "Tipo de revisión: previa a uso / especial / periódica. DERÍVALO "
            "del texto del cliente para ese equipo: 'inspección visual "
            "diaria/antes de cada salida' → previa a uso (visual); 'revisión "
            "técnica mensual/trimestral/semestral' → periódica (técnica). "
            "Null SOLO si el cliente no describió ninguna revisión del equipo."
        ),
    )
    frequency: str | None = Field(
        default=None,
        description=(
            "Frecuencia de inspección/mantenimiento. DERÍVALA del texto del "
            "cliente para ese equipo (diaria, semanal, mensual, semestral…); "
            "null SOLO si el cliente no la indicó."
        ),
    )


class EquipmentManualVariables(AIVariablesModel):
    """Variables del Manual de inspección y mantenimiento de equipos (MA-03).

    ``equipment_items`` es estructurado y se deriva de ``activity_fields`` del
    onboarding (equipo_rafting, equipo_buceo, …): NO se captura data nueva.
    """

    company_name: str | None = Field(
        default=None, description="Razón social de la empresa."
    )
    objective: str | None = Field(
        default=None,
        description=(
            "Objetivo del manual: asegurar la inspección y el mantenimiento "
            "de los equipos de la operación (8.1). Es texto normativo "
            "estándar, no un dato operativo: DERÍVALO de las actividades y "
            "los equipos reales del cliente; no lo dejes null por falta de "
            "mención literal."
        ),
    )
    scope: str | None = Field(
        default=None,
        description=(
            "Alcance del manual: qué equipos y actividades cubre y a quién "
            "aplica. DERÍVALO de los equipos y actividades reales del "
            "cliente; no lo dejes null por falta de mención literal."
        ),
    )
    role_obligations: str | None = Field(
        default=None,
        description="Obligaciones por rol (Gerencia, Coordinador, Guía).",
    )
    equipment_items: list[EquipmentInspectionItem] = Field(
        default_factory=list,
        description="Control de equipos por actividad (derivado del equipo real del cliente).",
    )
    maintenance_types: list[str] = Field(
        default_factory=list,
        description="Tipos de mantenimiento (revisión previa a uso, especial, periódica).",
    )
    legal_representative: str | None = Field(
        default=None, description="Representante legal que aprueba el manual."
    )
    approval_date: str | None = Field(
        default=None,
        description=(
            "Fecha de aprobación de ESTE documento (YYYY-MM-DD), SOLO si el "
            "cliente la indicó explícitamente; nunca derivada de otras fechas."
        ),
    )
