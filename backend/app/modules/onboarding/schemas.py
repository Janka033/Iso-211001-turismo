"""Modelos Pydantic del módulo onboarding.

``onboarding_data`` guarda los datos CRUDOS del cliente (lo que dijo), separados
de ``ai_outputs`` (lo que interpreta la IA). La generación los lee como contexto.
Todos los campos son opcionales: el onboarding es incremental y NUNCA inventa;
lo que falte queda vacío y el motor lo marca como ``[PENDIENTE]``.

Los campos llevan límites de tamaño (``max_length``) para acotar el payload:
defensa básica contra entradas abusivas.
"""

from pydantic import BaseModel, Field


class OnboardingPayload(BaseModel):
    """Datos operativos crudos capturados en el onboarding conversacional."""

    activities: list[str] = Field(
        default_factory=list,
        max_length=40,
        description="Actividades de turismo de aventura que ofrece la empresa.",
    )
    main_region: str | None = Field(
        default=None, max_length=120, description="Departamento o zona principal."
    )
    locations: list[str] = Field(
        default_factory=list,
        max_length=60,
        description="Ubicaciones específicas de operación (ríos, cañones, sedes).",
    )
    scope: str | None = Field(
        default=None, max_length=4000, description="Alcance operativo del cliente."
    )
    certified_guides: str | None = Field(
        default=None,
        max_length=300,
        description="Número o rango de guías certificados y sus certificaciones.",
    )
    legal_representative: str | None = Field(
        default=None, max_length=200, description="Representante legal de la empresa."
    )
    nit: str | None = Field(default=None, max_length=40, description="NIT de la empresa.")
    rnt_status: str | None = Field(
        default=None,
        max_length=120,
        description="Estado del RNT (vigente / por renovar / no lo tiene).",
    )
    rnt_number: str | None = Field(
        default=None, max_length=60, description="Número de Registro Nacional de Turismo."
    )
    emergency_contacts: list[str] = Field(
        default_factory=list,
        max_length=40,
        description="Contactos de emergencia (bomberos, ambulancia, rescate, ARL).",
    )
    existing_controls: str | None = Field(
        default=None,
        max_length=4000,
        description="Medidas o controles de seguridad que ya aplica la empresa.",
    )
    management_commitment: str | None = Field(
        default=None,
        max_length=4000,
        description="Compromiso de la dirección con la seguridad.",
    )
    # ------------------------------------------------------------------
    # Granularidad por documento (NTC-ISO 21101). Cada campo alimenta la
    # extracción de variables de su documento; los nombres coinciden con la
    # variable destino cuando el mapeo es 1:1 (safety_objectives,
    # opportunities, incident_classification, communication_matrix) para que
    # la IA los mapee sin ambigüedad. Texto CRUDO del cliente, nunca de la IA.
    # ------------------------------------------------------------------
    # Política de seguridad (5.2)
    safety_objectives: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Objetivos de seguridad medibles: indicador, meta numérica y plazo.",
    )
    approval_date: str | None = Field(
        default=None,
        max_length=120,
        description="Fecha oficial de aprobación de la política por la gerencia.",
    )
    communication_channels: list[str] = Field(
        default_factory=list,
        max_length=30,
        description="Canales de divulgación de la política y normas de seguridad.",
    )
    # Matriz de riesgos y oportunidades (6.1.1)
    activity_step_breakdown: str | None = Field(
        default=None,
        max_length=4000,
        description=(
            "Desglose paso a paso de la actividad, con el peligro (fuente) y el "
            "riesgo (consecuencia) de cada paso."
        ),
    )
    risk_factors: str | None = Field(
        default=None,
        max_length=4000,
        description=(
            "Riesgos por factor: ambiental, humano, de materiales/equipos y "
            "organizativo."
        ),
    )
    business_risks: list[str] = Field(
        default_factory=list,
        max_length=30,
        description="Riesgos del negocio y sus procesos (no operativos).",
    )
    opportunities: list[str] = Field(
        default_factory=list,
        max_length=30,
        description="Oportunidades de mejora identificadas y su plan.",
    )
    # Inspección y mantenimiento de equipos (8.1)
    equipment_maintenance: str | None = Field(
        default=None,
        max_length=4000,
        description=(
            "Por cada equipo: frecuencia de inspección, tipo (visual/técnica) y "
            "mantenimiento."
        ),
    )
    # Comunicación, participación y consulta (7.4)
    communication_matrix: str | None = Field(
        default=None,
        max_length=4000,
        description="Qué se comunica, a quién, por qué canal y con qué frecuencia.",
    )
    participation_consultation: str | None = Field(
        default=None,
        max_length=4000,
        description="Mecanismos formales de participación y consulta del personal.",
    )
    # Gestión de incidentes (8.3)
    incident_classification: list[str] = Field(
        default_factory=list,
        max_length=30,
        description="Clasificación de eventos: incidente vs accidente y categorías.",
    )
    incident_report_fields: list[str] = Field(
        default_factory=list,
        max_length=40,
        description="Campos que registran en el reporte de un incidente.",
    )
    # Preparación y respuesta ante emergencias (PL-01, 8.2). Fuente: cuestionario
    # "Caracterización para el Plan de Respuesta a Emergencias" (Calidad
    # Turística Colombiana). Responden alertas reales de generation_patterns.
    brigada_emergencias: str | None = Field(
        default=None,
        max_length=4000,
        description="Brigada de emergencias: existencia, roles que la integran y contactos.",
    )
    capacitaciones_personal_emergencias: list[str] = Field(
        default_factory=list,
        max_length=40,
        description=(
            "Capacitaciones del personal en emergencias (primeros auxilios, "
            "evacuación y rescate, manejo de incendios, autorrescate, otras)."
        ),
    )
    equipos_emergencia: list[str] = Field(
        default_factory=list,
        max_length=60,
        description=(
            "Equipos para atención de emergencias (botiquín, camilla con "
            "inmovilizadores, sistema de comunicación con su descripción, otros)."
        ),
    )
    organismos_apoyo: list[str] = Field(
        default_factory=list,
        max_length=40,
        description="Organismos de apoyo identificados y sus teléfonos.",
    )
    hospital_cercano: str | None = Field(
        default=None,
        max_length=1000,
        description=(
            "Hospital o centro de salud más cercano: nombre, ubicación, "
            "distancia y tiempo de acceso."
        ),
    )
    vehiculos_evacuacion: str | None = Field(
        default=None,
        max_length=2000,
        description="Vehículos disponibles para evacuación: tipo y contacto del encargado.",
    )
    # Alcance del SGSTA (4.3). Fuente: taller "Alcance del SGSTA" del kit
    # MinCIT (servicios/ubicación ya se capturan en identidad; estas dos
    # preguntas completan el taller).
    site_characteristics: str | None = Field(
        default=None,
        max_length=2000,
        description=(
            "Características especiales de la zona de operación (zona rural, "
            "reserva o área natural protegida, ribera de río, montaña)."
        ),
    )
    norm_exclusions: str | None = Field(
        default=None,
        max_length=2000,
        description=(
            "Requisitos de la NTC-ISO 21101 que el cliente declara no "
            "aplicables y su justificación, o su declaración de que aplican todos."
        ),
    )
    # Acta de compromiso de la alta dirección (5.1). Molde del kit MinCIT.
    management_signer: str | None = Field(
        default=None,
        max_length=1000,
        description=(
            "Firmante del acta de compromiso: nombre, cargo, teléfono, correo, "
            "y ciudad y fecha de la firma."
        ),
    )
    # Matriz de partes interesadas (4.2). Fuente: taller "Comprensión de las
    # partes interesadas" del kit MinCIT.
    stakeholder_needs: str | None = Field(
        default=None,
        max_length=4000,
        description=(
            "Partes interesadas de la operación con las necesidades y "
            "expectativas de cada una (proveedores, gubernamentales, ONG, "
            "clientes, colaboradores, propietarios, comunidad)."
        ),
    )
    stakeholder_compliance: str | None = Field(
        default=None,
        max_length=4000,
        description=(
            "Evaluación del cliente sobre si cumple los requisitos de cada "
            "parte interesada, con acciones, responsables y fechas para lo que "
            "se cumple parcialmente o no se cumple."
        ),
    )
    # Datos POR ACTIVIDAD (Parte B). Clave = field_key del checklist
    # (p.ej. ``equipo_rafting``), valor = lo que dijo el cliente. Flexible pero
    # tipado (dict[str, str], no ``dict`` a secas): cada actividad elegida aporta
    # sus campos sin tener que declarar una columna por actividad. La generación
    # los recibe como parte de ``onboarding_data`` sin cambios en su código.
    activity_fields: dict[str, str] = Field(
        default_factory=dict,
        description="Respuestas por actividad, indexadas por field_key del checklist.",
    )
    # Organigrama del cliente: cargo -> nº de personas (p.ej. {"gerente": "1",
    # "guia": "5"}). Alimenta el Manual de perfiles y funciones de cargo (MA-02).
    staff_roles: dict[str, str] = Field(
        default_factory=dict,
        description="Cargos del equipo y número de personas por cargo.",
    )
    # Códigos CONFIRMADOS del SGS del cliente: document_type -> código (p.ej.
    # {"matriz_riesgos": "MT-04"}). Solo códigos que el cliente confirmó; los
    # tipos sin entrada salen con [PENDIENTE: código por confirmar] — el
    # sistema nunca adivina la numeración del sistema documental del cliente.
    document_codes: dict[str, str] = Field(
        default_factory=dict,
        description="Códigos confirmados del sistema documental del cliente, por document_type.",
    )
    # Subsanaciones: respuestas del cliente a correcciones de calidad cuyos
    # field_key NO son campos del onboarding (p.ej. ``safety_objectives``,
    # variables de documento). Son datos CRUDOS del cliente —nunca de la IA— y
    # la generación los recibe como parte de ``onboarding_data`` para que la
    # extracción los use al regenerar.
    remediation_fields: dict[str, str] = Field(
        default_factory=dict,
        description="Respuestas de subsanación indexadas por field_key de la corrección.",
    )


class OnboardingState(BaseModel):
    """Estado del onboarding: datos + avance calculado."""

    data: OnboardingPayload
    completeness: float = Field(
        description="% de campos esperados del onboarding con dato (0-100)."
    )
    completed: bool = Field(
        description="True si todos los campos esperados tienen dato."
    )


# ---------------------------------------------------------------------------
# Onboarding conversacional (POST /onboarding/chat)
# ---------------------------------------------------------------------------


class OnboardingChatRequest(BaseModel):
    """Un turno del onboarding conversacional."""

    message: str | None = Field(
        default=None,
        max_length=8000,
        description="Última respuesta del cliente (texto libre). Vacío en el turno inicial.",
    )
    activities: list[str] | None = Field(
        default=None,
        max_length=40,
        description="Actividades elegidas (slugs). Fija/actualiza el set por actividad.",
    )


class OnboardingField(BaseModel):
    """Campo objetivo de la siguiente pregunta."""

    field_key: str
    activity: str | None = Field(
        default=None, description="Slug de la actividad si es un campo Parte B; None si universal."
    )


class OnboardingExtraction(BaseModel):
    """Salida ESTRICTA de la IA por turno (se valida antes de persistir).

    La IA solo EXTRAE lo que el cliente dijo (nunca inventa) y REDACTA la
    siguiente pregunta; NO decide el flujo: el backend valida ``next_field_key``
    contra los campos realmente pendientes y manda si difiere.

    Además actúa como INTERCEPTOR de seguridad: antes de extraer, juzga si la
    respuesta describe una práctica que VIOLA un requisito obligatorio de la
    NTC-ISO 21101 (contexto normativo provisto). Si es así, marca
    ``compliant=false`` y NO extrae el dato ofensivo; el backend rechaza el
    turno y pide replantear (nunca guarda una práctica no conforme).
    """

    # --- Interceptor de cumplimiento (se evalúa ANTES de extraer) ---
    compliant: bool = Field(
        default=True,
        description=(
            "false SOLO si la respuesta describe una práctica que incumple un "
            "requisito obligatorio de seguridad de la norma (p. ej. renunciar a "
            "restricciones de edad/salud, atención de heridos improvisada). En "
            "duda, true."
        ),
    )
    safety_issue: str | None = Field(
        default=None,
        max_length=600,
        description="Qué de la respuesta incumple la norma (frase breve). Solo si compliant=false.",
    )
    iso_requirement: str | None = Field(
        default=None,
        max_length=600,
        description="Requisito de la NTC-ISO 21101 que aplica (breve). Solo si compliant=false.",
    )
    rephrase_hint: str | None = Field(
        default=None,
        max_length=600,
        description="Cómo debería replantear su respuesta el cliente. Solo si compliant=false.",
    )

    extracted: dict[str, str] = Field(
        default_factory=dict,
        description="field_key -> valor extraído de la última respuesta. Omite lo que no se dijo.",
    )
    staff_roles: dict[str, str] = Field(
        default_factory=dict,
        description="Cargo -> nº de personas; solo si el cliente lo menciona. No inventar.",
    )
    next_field_key: str | None = Field(
        default=None, description="field_key que la IA propone preguntar (de la lista pendiente)."
    )
    next_question: str | None = Field(
        default=None,
        description="Redacción natural de la próxima pregunta; None si ya no queda nada.",
    )
    completed: bool = Field(
        default=False, description="La IA cree que ya no falta nada (el backend lo reconfirma)."
    )


class RoadmapStep(BaseModel):
    """Un paso de la ruta guiada con el estado del tenant (derivado, no cacheado)."""

    step_order: int
    document_type: str
    title: str
    numeral: str
    generator_ready: bool = Field(
        description="El motor ya sabe generar este documento (existe en _REGISTRY)."
    )
    status: str = Field(
        description=(
            "Estado del documento para el tenant: 'pendiente' o el estado real "
            "de document_status (generated, approved…)."
        )
    )
    completeness: float | None = Field(
        default=None, description="% de campos obligatorios con dato en la última generación."
    )
    last_score: float | None = Field(
        default=None, description="Score de la evaluación de calidad más reciente (0-100)."
    )


class RoadmapResponse(BaseModel):
    """La ruta completa: fuente del stepper del frontend."""

    steps: list[RoadmapStep]
    current_step: int | None = Field(
        description="step_order del primer paso sin documento generado; None si todos generados."
    )
    total: int


class CurrentStepInfo(BaseModel):
    """El paso de la ruta guiada al que pertenece la próxima pregunta.

    ``step_order`` 0 = fase de identidad ("Conozcamos tu empresa"), antes de
    entrar a los documentos. ``fields_done``/``fields_total`` son el anillo de
    progreso del paso en el frontend.
    """

    step_order: int
    total: int
    document_type: str | None = None
    title: str
    numeral: str | None = None
    fields_done: int
    fields_total: int


class OnboardingChatResponse(BaseModel):
    """Respuesta de un turno: qué se extrajo + la próxima pregunta + avance."""

    next_question: str | None = Field(
        description="Próxima pregunta a mostrar; None si el onboarding está completo."
    )
    next_field: OnboardingField | None = Field(
        default=None, description="Campo objetivo de la próxima pregunta."
    )
    extracted: dict[str, str] = Field(
        default_factory=dict,
        description="Lo extraído en ESTE turno (para refrescar el panel de datos).",
    )
    data: OnboardingPayload = Field(description="Estado completo actualizado del onboarding.")
    completeness: float = Field(description="% de campos esperados con dato (0-100).")
    completed: bool = Field(description="True si no quedan campos esperados por responder.")
    # Interceptor de seguridad: true si la respuesta se rechazó por no conforme
    # con la norma. Cuando es true, NO se guardó nada y ``next_field`` re-pregunta
    # el mismo campo; ``safety_note`` explica el requisito ISO.
    blocked: bool = Field(
        default=False,
        description="True si la respuesta fue rechazada por incumplir la norma (nada se guardó).",
    )
    safety_note: str | None = Field(
        default=None,
        description="Explicación del rechazo por seguridad (requisito ISO + cómo replantear).",
    )
    # Ruta guiada (Fase 2): a qué paso pertenece la próxima pregunta y qué
    # documentos ya tienen sus datos completos y esperan el botón "Generar".
    current_step: CurrentStepInfo | None = Field(
        default=None,
        description="Paso activo de la ruta guiada; None si la ruta no está configurada.",
    )
    ready_to_generate: list[str] = Field(
        default_factory=list,
        description="document_types con datos completos y sin documento generado.",
    )
