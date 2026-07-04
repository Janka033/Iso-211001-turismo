"""DocumentFactory (patrón Factory).

Mapea cada ``document_type`` a su especificación: el schema Pydantic de sus
variables, su generador concreto y el numeral de la norma para el RAG. Es el
único lugar que hay que tocar para añadir un documento nuevo del MVP.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

from app.modules.generation.generators.base import DocumentGenerator
from app.modules.generation.generators.communication_procedure import (
    CommunicationProcedureGenerator,
)
from app.modules.generation.generators.emergency_plan import EmergencyPlanGenerator
from app.modules.generation.generators.equipment_manual import EquipmentManualGenerator
from app.modules.generation.generators.incident_management import (
    IncidentManagementGenerator,
)
from app.modules.generation.generators.profiles_manual import ProfilesManualGenerator
from app.modules.generation.generators.risk_matrix import RiskMatrixGenerator
from app.modules.generation.generators.security_policy import SecurityPolicyGenerator
from app.modules.generation.schemas import (
    CommunicationProcedureVariables,
    EmergencyPlanVariables,
    EquipmentManualVariables,
    IncidentManagementVariables,
    ProfilesManualVariables,
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
    "manual_perfiles_cargos": DocumentSpec(
        document_type="manual_perfiles_cargos",
        title="Manual de perfiles y funciones de cargo",
        numeral="5.3",
        variables_model=ProfilesManualVariables,
        generator=ProfilesManualGenerator(),
        # 7.2: competencia/formación del personal, base de los perfiles de cargo.
        extra_rag_numerales=("7.2",),
    ),
    "comunicacion_participacion_consulta": DocumentSpec(
        document_type="comunicacion_participacion_consulta",
        title="Procedimiento de comunicación, participación y consulta",
        numeral="7.4",
        variables_model=CommunicationProcedureVariables,
        generator=CommunicationProcedureGenerator(),
    ),
    "manual_inspeccion_equipos": DocumentSpec(
        document_type="manual_inspeccion_equipos",
        title="Manual de inspección y mantenimiento de equipos",
        numeral="8.1",
        variables_model=EquipmentManualVariables,
        generator=EquipmentManualGenerator(),
        # Anexo A: proceso de gestión del riesgo, base del control de equipos.
        extra_rag_numerales=("A",),
    ),
}


def get_spec(document_type: str) -> DocumentSpec | None:
    return _REGISTRY.get(document_type)


def supported_types() -> list[str]:
    return list(_REGISTRY.keys())
