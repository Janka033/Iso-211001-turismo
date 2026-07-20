"""DocumentFactory (patrón Factory).

Mapea cada ``document_type`` a su especificación: el schema Pydantic de sus
variables, su generador concreto y el numeral de la norma para el RAG. Es el
único lugar que hay que tocar para añadir un documento nuevo del MVP.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

from app.modules.generation.generators.acciones_correctivas import (
    AccionesCorrectivasGenerator,
)
from app.modules.generation.generators.acta_compromiso import ActaCompromisoGenerator
from app.modules.generation.generators.alcance import AlcanceGenerator
from app.modules.generation.generators.auditoria_interna import (
    AuditoriaInternaGenerator,
)
from app.modules.generation.generators.base import DocumentGenerator
from app.modules.generation.generators.communication_procedure import (
    CommunicationProcedureGenerator,
)
from app.modules.generation.generators.control_documental import (
    ControlDocumentalGenerator,
)
from app.modules.generation.generators.control_operacional import (
    ControlOperacionalGenerator,
)
from app.modules.generation.generators.emergency_plan import EmergencyPlanGenerator
from app.modules.generation.generators.equipment_manual import EquipmentManualGenerator
from app.modules.generation.generators.incident_management import (
    IncidentManagementGenerator,
)
from app.modules.generation.generators.matriz_indicadores import (
    MatrizIndicadoresGenerator,
)
from app.modules.generation.generators.objetivos_seguridad import (
    ObjetivosSeguridadGenerator,
)
from app.modules.generation.generators.partes_interesadas import (
    PartesInteresadasGenerator,
)
from app.modules.generation.generators.procedimiento_riesgos import (
    ProcedimientoRiesgosGenerator,
)
from app.modules.generation.generators.profiles_manual import ProfilesManualGenerator
from app.modules.generation.generators.requisitos_legales import (
    RequisitosLegalesGenerator,
)
from app.modules.generation.generators.revision_direccion import (
    RevisionDireccionGenerator,
)
from app.modules.generation.generators.risk_matrix import RiskMatrixGenerator
from app.modules.generation.generators.security_policy import SecurityPolicyGenerator
from app.modules.generation.schemas import (
    AccionesCorrectivasVariables,
    ActaCompromisoVariables,
    AlcanceVariables,
    AuditoriaInternaVariables,
    CommunicationProcedureVariables,
    ControlDocumentalVariables,
    ControlOperacionalVariables,
    EmergencyPlanVariables,
    EquipmentManualVariables,
    IncidentManagementVariables,
    MatrizIndicadoresVariables,
    MatrizObjetivosVariables,
    MatrizPartesInteresadasVariables,
    MatrizRequisitosLegalesVariables,
    ProcedimientoRiesgosVariables,
    ProfilesManualVariables,
    RevisionDireccionVariables,
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
    "acciones_correctivas_mejora": DocumentSpec(
        document_type="acciones_correctivas_mejora",
        title="Procedimiento de acciones correctivas y de mejora",
        numeral="10.1",
        variables_model=AccionesCorrectivasVariables,
        generator=AccionesCorrectivasGenerator(),
        # 9.2/9.3: auditoría interna y revisión por la dirección son las
        # fuentes principales de no conformidades que este procedimiento cierra.
        extra_rag_numerales=("9.2",),
    ),
    "auditoria_interna": DocumentSpec(
        document_type="auditoria_interna",
        title="Procedimiento de auditoría interna",
        numeral="9.2",
        variables_model=AuditoriaInternaVariables,
        generator=AuditoriaInternaGenerator(),
    ),
    "matriz_indicadores": DocumentSpec(
        document_type="matriz_indicadores",
        title="Matriz de indicadores de desempeño",
        numeral="9.1",
        variables_model=MatrizIndicadoresVariables,
        generator=MatrizIndicadoresGenerator(),
        # 6.2: los objetivos de seguridad son la fuente de los indicadores.
        extra_rag_numerales=("6.2",),
    ),
    "revision_direccion": DocumentSpec(
        document_type="revision_direccion",
        title="Procedimiento de revisión por la dirección",
        numeral="9.3",
        variables_model=RevisionDireccionVariables,
        generator=RevisionDireccionGenerator(),
        # 9.1/9.2/10.1: indicadores, auditoría y acciones son las entradas que
        # la revisión por la dirección analiza.
        extra_rag_numerales=("9.1", "9.2"),
    ),
    "alcance_sgsta": DocumentSpec(
        document_type="alcance_sgsta",
        title="Alcance del SGSTA",
        numeral="4.3",
        variables_model=AlcanceVariables,
        generator=AlcanceGenerator(),
        # 4.1/4.2 (contexto y partes interesadas) delimitan qué debe cubrir
        # el alcance; amplían el contexto normativo del RAG.
        extra_rag_numerales=("4.1", "4.2"),
    ),
    "acta_compromiso": DocumentSpec(
        document_type="acta_compromiso",
        title="Acta de compromiso de la alta dirección",
        numeral="5.1",
        variables_model=ActaCompromisoVariables,
        generator=ActaCompromisoGenerator(),
    ),
    "matriz_partes_interesadas": DocumentSpec(
        document_type="matriz_partes_interesadas",
        title="Matriz de partes interesadas",
        numeral="4.2",
        variables_model=MatrizPartesInteresadasVariables,
        generator=PartesInteresadasGenerator(),
        # 4.1 (contexto interno/externo) delimita qué partes son relevantes.
        extra_rag_numerales=("4.1",),
    ),
    "procedimiento_riesgos_oportunidades": DocumentSpec(
        document_type="procedimiento_riesgos_oportunidades",
        title="Procedimiento de gestión de riesgos y oportunidades",
        numeral="6.1.1",
        variables_model=ProcedimientoRiesgosVariables,
        generator=ProcedimientoRiesgosGenerator(),
        # Anexo A: proceso de gestión del riesgo, base del procedimiento.
        extra_rag_numerales=("A",),
    ),
    "matriz_requisitos_legales": DocumentSpec(
        document_type="matriz_requisitos_legales",
        title="Matriz de requisitos legales",
        numeral="6.1.3",
        variables_model=MatrizRequisitosLegalesVariables,
        generator=RequisitosLegalesGenerator(),
    ),
    "matriz_objetivos_seguridad": DocumentSpec(
        document_type="matriz_objetivos_seguridad",
        title="Matriz de objetivos de seguridad",
        numeral="6.2",
        variables_model=MatrizObjetivosVariables,
        generator=ObjetivosSeguridadGenerator(),
        # 5.2: la política es el marco de los objetivos (columna del molde).
        extra_rag_numerales=("5.2",),
    ),
    "control_operacional": DocumentSpec(
        document_type="control_operacional",
        title="Planificación y control operacional",
        numeral="8.1",
        variables_model=ControlOperacionalVariables,
        generator=ControlOperacionalGenerator(),
        # Anexo A: proceso de gestión del riesgo, base de los controles.
        extra_rag_numerales=("A",),
    ),
    "control_informacion_documentada": DocumentSpec(
        document_type="control_informacion_documentada",
        title="Procedimiento de control de la información documentada",
        numeral="7.5.1",
        variables_model=ControlDocumentalVariables,
        generator=ControlDocumentalGenerator(),
        # 7.5.2/7.5.3: creación, actualización y control de la información
        # documentada, complemento directo del 7.5.1.
        extra_rag_numerales=("7.5.2", "7.5.3"),
    ),
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
