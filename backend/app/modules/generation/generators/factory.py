"""DocumentFactory (patrón Factory).

Mapea cada ``document_type`` a su especificación: el schema Pydantic de sus
variables, su generador concreto y el numeral de la norma para el RAG. Es el
único lugar que hay que tocar para añadir un documento nuevo del MVP.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

from app.modules.generation.generators.base import DocumentGenerator
from app.modules.generation.generators.emergency_plan import EmergencyPlanGenerator
from app.modules.generation.generators.incident_management import (
    IncidentManagementGenerator,
)
from app.modules.generation.generators.risk_matrix import RiskMatrixGenerator
from app.modules.generation.generators.security_policy import SecurityPolicyGenerator
from app.modules.generation.schemas import (
    EmergencyPlanVariables,
    IncidentManagementVariables,
    RiskMatrixVariables,
    SecurityPolicyVariables,
)


@dataclass(frozen=True)
class DocumentSpec:
    document_type: str
    title: str
    numeral: str                       # numeral principal de la norma
    variables_model: type[BaseModel]
    generator: DocumentGenerator
    # Numerales adicionales para el RAG (p. ej. anexos). El principal siempre
    # se consulta; estos amplían el contexto normativo del documento.
    extra_rag_numerales: tuple[str, ...] = ()

    @property
    def rag_numerales(self) -> tuple[str, ...]:
        return (self.numeral, *self.extra_rag_numerales)


_REGISTRY: dict[str, DocumentSpec] = {
    "politica_seguridad": DocumentSpec(
        document_type="politica_seguridad",
        title="Política de seguridad",
        numeral="5.2",
        variables_model=SecurityPolicyVariables,
        generator=SecurityPolicyGenerator(),
    ),
    "matriz_riesgos": DocumentSpec(
        document_type="matriz_riesgos",
        title="Matriz de riesgos y oportunidades",
        numeral="6.1.1",
        variables_model=RiskMatrixVariables,
        generator=RiskMatrixGenerator(),
        # La matriz del MVP es "6.1.1 + Anexo A" (proceso de gestión del riesgo).
        extra_rag_numerales=("A",),
    ),
    "plan_emergencias": DocumentSpec(
        document_type="plan_emergencias",
        title="Plan de respuesta a emergencias",
        numeral="8.2",
        variables_model=EmergencyPlanVariables,
        generator=EmergencyPlanGenerator(),
    ),
    "gestion_incidentes": DocumentSpec(
        document_type="gestion_incidentes",
        title="Procedimiento de gestión de incidentes",
        numeral="8.3",
        variables_model=IncidentManagementVariables,
        generator=IncidentManagementGenerator(),
    ),
}


def get_spec(document_type: str) -> DocumentSpec | None:
    return _REGISTRY.get(document_type)


def supported_types() -> list[str]:
    return list(_REGISTRY.keys())
