"""DocumentFactory (patrón Factory).

Mapea cada ``document_type`` a su especificación: el schema Pydantic de sus
variables, su generador concreto y el numeral de la norma para el RAG. Es el
único lugar que hay que tocar para añadir un documento nuevo del MVP.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

from app.modules.generation.generators.base import DocumentGenerator
from app.modules.generation.generators.risk_matrix import RiskMatrixGenerator
from app.modules.generation.generators.security_policy import SecurityPolicyGenerator
from app.modules.generation.schemas import RiskMatrixVariables, SecurityPolicyVariables


@dataclass(frozen=True)
class DocumentSpec:
    document_type: str
    title: str
    numeral: str                       # numeral de la norma para el RAG
    variables_model: type[BaseModel]
    generator: DocumentGenerator


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
    ),
}


def get_spec(document_type: str) -> DocumentSpec | None:
    return _REGISTRY.get(document_type)


def supported_types() -> list[str]:
    return list(_REGISTRY.keys())
