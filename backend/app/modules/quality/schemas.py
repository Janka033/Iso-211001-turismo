"""Modelos Pydantic del módulo de calidad.

Dos familias de modelos:

- API: ``QualityReviewOut`` / ``ReviewDecisionRequest`` (entrada/salida HTTP).
- Evaluación: ``QualityEvaluation`` es el JSON ESTRICTO que la IA debe devolver
  al evaluar un documento generado. Se valida con Pydantic ANTES de persistir
  (anti-alucinación). La IA no decide nada: evalúa contra la checklist, los
  patrones de auditoría y la norma que se le entregan; la decisión final es
  del revisor humano.
"""

from typing import Literal

from pydantic import BaseModel, Field

ReviewDecision = Literal["approved", "rejected", "needs_correction"]


class ReviewDecisionRequest(BaseModel):
    """Decisión del revisor sobre una evaluación. NO lleva tenant_id: sale del JWT."""

    decision: ReviewDecision = Field(
        description="Aprobar, rechazar o pedir corrección del documento."
    )
    notes: str | None = Field(
        default=None, description="Notas del revisor (qué corregir y por qué)."
    )


class ReviewDecisionOut(BaseModel):
    """Resultado de aplicar la decisión del revisor."""

    review_id: str
    review_status: str
    document_id: str
    document_type: str
    document_status: str


# ---------------------------------------------------------------------------
# Evaluación (salida de la IA, validada por Pydantic)
# ---------------------------------------------------------------------------


class CompletenessCheck(BaseModel):
    """a) Completitud: ¿faltan variables? Se mide contra la checklist de extracción."""

    missing_required_fields: list[str] = Field(
        default_factory=list,
        description="field_key OBLIGATORIOS de la checklist sin dato (null o vacío).",
    )
    missing_optional_fields: list[str] = Field(
        default_factory=list,
        description="field_key opcionales de la checklist sin dato.",
    )
    comment: str | None = Field(
        default=None, description="Resumen del estado de completitud."
    )


class CoherenceCheck(BaseModel):
    """b) Coherencia del contenido con el numeral ISO correspondiente."""

    coherent: bool = Field(
        description="True si el contenido cubre lo que el numeral exige."
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Incoherencias o vacíos frente al numeral de la norma.",
    )


class QualityAlert(BaseModel):
    """c) Alerta activada por un patrón de auditoría entregado en el contexto."""

    pattern_type: str | None = Field(
        default=None,
        description="Tipo del patrón que la activa (rechazo/requisito).",
    )
    pattern: str = Field(description="Descripción del patrón de auditoría activado.")
    detail: str | None = Field(
        default=None, description="Por qué se activa en este documento."
    )


class SuggestedCorrection(BaseModel):
    """Una corrección puntual sugerida al revisor."""

    field: str | None = Field(
        default=None,
        description="field_key del campo al que aplica (si es puntual).",
    )
    issue: str = Field(description="Qué está mal o qué falta.")
    suggestion: str | None = Field(
        default=None, description="Cómo corregirlo, en términos accionables."
    )


class QualityEvaluation(BaseModel):
    """Contrato JSON de la evaluación. ``model_json_schema()`` se inyecta en el
    prompt para que el modelo conozca la forma esperada."""

    score: float = Field(ge=0, le=100, description="Calidad global (0-100).")
    completeness: CompletenessCheck
    coherence: CoherenceCheck
    alerts: list[QualityAlert] = Field(default_factory=list)
    observations: list[str] = Field(
        default_factory=list,
        description="Observaciones generales para el revisor.",
    )
    suggested_corrections: list[SuggestedCorrection] = Field(default_factory=list)


class QualityReviewOut(BaseModel):
    """Una evaluación persistida, con su estado de revisión."""

    review_id: str
    document_id: str
    document_type: str
    document_version: int
    score: float
    evaluation: QualityEvaluation
    review_status: str
    prompt_version: str | None = None
    model_version: str | None = None
    created_at: str | None = None
