"""Endpoints del módulo quality.

El router solo recibe el request, toma ``tenant_id``/``token`` del JWT (nunca
del body) y delega en el service. Lanzar/ver evaluaciones puede cualquier
usuario del tenant; DECIDIR exige rol admin/superadmin (require_role), y la
policy de UPDATE de quality_reviews lo refuerza en DB.
"""

from fastapi import APIRouter, Depends, status

from app.core.security import (
    CurrentUser,
    get_current_user,
    get_tenant_id,
    require_role,
)
from app.modules.quality import service
from app.modules.quality.schemas import (
    AuditReadiness,
    QualityReviewOut,
    RemediationOut,
    RemediationRequest,
    ReviewDecisionOut,
    ReviewDecisionRequest,
)

router = APIRouter(prefix="/quality", tags=["quality"])


@router.get("/readiness", response_model=AuditReadiness)
async def audit_readiness(
    user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),  # 401 si el JWT no trae el claim
) -> AuditReadiness:
    """Veredicto de preparación documental: ¿está el expediente listo para
    presentar a la auditoría? Agrega los documentos de la ruta y lista lo que
    aún falta. No garantiza la certificación (esa la da un organismo acreditado)."""
    return await service.get_readiness(tenant_id, user.token)


@router.post(
    "/evaluations/{document_id}",
    response_model=QualityReviewOut,
    status_code=status.HTTP_201_CREATED,
)
async def evaluate_document(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),  # 401 si el JWT no trae el claim
) -> QualityReviewOut:
    """Evalúa con la IA un documento ya generado (completitud, coherencia,
    alertas) y persiste el resultado con su snapshot de reproducibilidad."""
    return await service.evaluate(document_id, tenant_id, user.token)


@router.post("/reviews/{review_id}/decision", response_model=ReviewDecisionOut)
async def decide_review(
    review_id: str,
    payload: ReviewDecisionRequest,
    user: CurrentUser = Depends(require_role("admin", "superadmin")),
    tenant_id: str = Depends(get_tenant_id),  # 401 si el JWT no trae el claim
) -> ReviewDecisionOut:
    """Aprobar, rechazar o pedir corrección de un documento evaluado."""
    return await service.decide(review_id, payload, tenant_id, user)


@router.post("/reviews/{review_id}/remediation", response_model=RemediationOut)
async def remediate_review(
    review_id: str,
    payload: RemediationRequest,
    user: CurrentUser = Depends(get_current_user),  # la empresa subsana sus datos
    tenant_id: str = Depends(get_tenant_id),  # 401 si el JWT no trae el claim
) -> RemediationOut:
    """Responder una corrección solicitada: guarda los datos aportados por la
    empresa (onboarding_data) y regenera el documento en una versión nueva."""
    return await service.remediate(review_id, payload, tenant_id, user)
