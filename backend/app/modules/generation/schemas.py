"""Modelos Pydantic del módulo de generación.

Dos familias de modelos:

- API: ``GenerateRequest`` / ``GeneratedDocument`` (entrada/salida HTTP).
- Variables de documento: el JSON ESTRICTO que la IA debe devolver. Se valida
  con Pydantic ANTES de tocar la plantilla (anti-alucinación). Todo campo es
  opcional: lo que la IA no extraiga queda en ``None`` / lista vacía y el
  generador lo sustituye por ``[PENDIENTE: ...]``. La IA NUNCA inventa.
"""

from pydantic import BaseModel, Field


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


# ---------------------------------------------------------------------------
# Variables de documento (salida de la IA, validada por Pydantic)
# ---------------------------------------------------------------------------


class SecurityPolicyVariables(BaseModel):
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
    safety_objectives: list[str] = Field(
        default_factory=list,
        description="Objetivos de seguridad de la organización.",
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
        default=None, description="Fecha de aprobación (YYYY-MM-DD)."
    )


class RiskEntry(BaseModel):
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
        default=None, description="Acciones de tratamiento propuestas."
    )
    responsible: str | None = Field(
        default=None, description="Responsable de la acción."
    )
    residual_risk: str | None = Field(
        default=None, description="Riesgo residual tras los controles."
    )


class RiskMatrixVariables(BaseModel):
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
    opportunities: list[str] = Field(
        default_factory=list,
        description="Oportunidades de mejora identificadas (6.1.1).",
    )
