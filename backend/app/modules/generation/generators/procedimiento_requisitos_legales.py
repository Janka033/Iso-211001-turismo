"""Generador .docx del Procedimiento de requisitos legales (6.1.3).

Calca el molde del kit MinCIT: objetivo, alcance, las 4 definiciones (decreto,
decreto ley, ley, resolución) y la tabla de 7 actividades (generalidades →
consulta e identificación → elaboración de la matriz → actualización →
comunicación → evaluación del cumplimiento → plan de intervención). Todo eso es
contenido FIJO; la IA solo aporta identidad, el cargo responsable del sistema y
la aprobación. Complementa la Matriz de requisitos legales (MT-03), que este
procedimiento describe cómo elaborar, mantener y evaluar.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.modules.generation.generators.base import (
    DocumentGenerator,
    ResolvedField,
    resolve_code,
)
from app.modules.generation.generators.felipe_docx import FelipeDocxBuilder
from app.modules.generation.schemas import ProcedimientoRequisitosLegalesVariables

_OBJECTIVE = (
    "Identificar, documentar, tener acceso, cumplir y evaluar los requisitos "
    "legales que le sean aplicables a la organización."
)

_SCOPE = (
    "Este documento aplica para la normatividad legal en los aspectos "
    "turísticos, ambientales, sociales, culturales, económicos y laborales, así "
    "como para la normatividad en los ámbitos nacional, regional y local."
)

_DEFINITIONS: tuple[tuple[str, str], ...] = (
    (
        "Decreto",
        "Decisión de un gobernante o de una autoridad, o de un tribunal o juez, "
        "sobre la materia o negocio en que tengan competencia. (Fuente: Real "
        "Academia Española RAE).",
    ),
    (
        "Decreto Ley",
        "Disposición legislativa provisional que puede dictar el Gobierno en "
        "caso de extraordinaria y urgente necesidad, y que requiere para su "
        "definitiva eficacia la ratificación ulterior por parte del órgano "
        "legislativo. (Fuente: Real Academia Española RAE).",
    ),
    (
        "Ley",
        "Precepto dictado por la autoridad competente, en que se manda o "
        "prohíbe algo en consonancia con la justicia y para el bien de los "
        "gobernados. (Fuente: Real Academia Española RAE).",
    ),
    (
        "Resolución",
        "Acto administrativo que plasma la voluntad de la administración "
        "pública en un documento que puede ser particular, general, obligatorio "
        "y permanente, y que puede prohibir, permitir, modificar, sustituir o "
        "sancionar. (Fuente: Policía Nacional de Colombia).",
    ),
)

# Actividades del molde: (nº, descripción, responsable fijo o None => cargo
# responsable del cliente, registro).
_MATRIZ = "Matriz de requisitos legales"
_STEPS: tuple[tuple[str, str, str | None, str], ...] = (
    (
        "1",
        "Generalidades. La organización debe cumplir la legislación vigente que "
        "le sea aplicable atendiendo a las particularidades locales, y "
        "específicamente respecto a: la operación de la organización; los planes "
        "de ordenamiento territorial; la accesibilidad de las instalaciones; la "
        "protección de datos personales; la prevención de la explotación sexual "
        "comercial de niños, niñas y adolescentes (ESCNNA) y de la trata de "
        "personas; las zonas de carga y descarga; el uso de recursos naturales; "
        "y la disposición de residuos y vertimientos. Si se realiza alguna otra "
        "actividad que requiera una licencia o autorización adicional a la de la "
        "actividad habitual, esta debe estar en posesión de la organización.",
        None,
        _MATRIZ,
    ),
    (
        "2",
        "Consulta e identificación de la legislación aplicable. El responsable "
        "del sistema de gestión y los líderes de proceso identifican la "
        "normatividad legal aplicable consultando, según el componente, fuentes "
        "oficiales: turísticas y de seguridad (MinCIT, MinTrabajo, ICONTEC, "
        "Parques Nacionales, DIMAR, Aeronáutica Civil, FONTUR, SIC); ambientales "
        "(MinAmbiente, Corporaciones Autónomas Regionales, Secretarías de Salud "
        "y de Medio Ambiente); culturales (MinCultura, Secretaría de Cultura); "
        "económicas (MinTrabajo, Banco de la República, MinCIT, DIAN); y "
        "laborales (MinTrabajo, MinSalud, Servicio Público de Empleo, ARL), "
        "además de las demás páginas que la organización considere necesario "
        "consultar.",
        None,
        _MATRIZ,
    ),
    (
        "3",
        "Elaboración de la matriz de requisitos legales y otros. Una vez "
        "identificada la normatividad legal aplicable, el responsable del "
        "sistema de gestión elabora la matriz de requisitos legales, en la cual "
        "se determina la forma de dar cumplimiento y se realiza la posterior "
        "evaluación. La alta dirección garantiza la disponibilidad de los "
        "recursos necesarios para cumplir con las exigencias del sistema de "
        "gestión y los demás requisitos identificados en la matriz.",
        None,
        _MATRIZ,
    ),
    (
        "4",
        "Actualización de la matriz legal. El responsable del sistema de "
        "gestión, en conjunto con los líderes de proceso, actualiza la matriz "
        "cada vez que se identifique un cambio en la normatividad legal "
        "aplicable, nuevas disposiciones que se deban cumplir, o como mínimo "
        "cada seis meses. Se evalúa si los nuevos requisitos son de aplicación "
        "para la empresa, si permiten asegurar el cumplimiento futuro de la "
        "política de seguridad y si afectan las autorizaciones existentes; en "
        "caso afirmativo, se incluyen en la matriz legal.",
        None,
        _MATRIZ,
    ),
    (
        "5",
        "Comunicación de los requisitos legales y otros requisitos. El "
        "responsable del sistema de gestión comunica la información pertinente "
        "sobre los requisitos legales y otros requisitos a empleados, "
        "proveedores, participantes en las actividades y demás partes "
        "interesadas, por diferentes canales de comunicación, tales como el "
        "inicio y el desarrollo de la actividad, capacitaciones y correo "
        "electrónico.",
        None,
        f"{_MATRIZ}; correo electrónico; lista de asistencia",
    ),
    (
        "6",
        "Evaluación del cumplimiento de los requisitos legales. El responsable "
        "del sistema de gestión planifica y gestiona la evaluación del "
        "cumplimiento de los requisitos legales aplicables como mínimo una vez "
        "al año. Se verifica en la matriz si los requisitos se cumplen, están en "
        "proceso o no se cumplen; la evaluación puede realizarse por componente "
        "(ambiental, sociocultural, económico u otro), registrando su fecha de "
        "evaluación sin exceder el plazo establecido. Si se presentan hallazgos "
        "de cumplimiento parcial o de no cumplimiento, se establece el plan de "
        "intervención.",
        None,
        _MATRIZ,
    ),
    (
        "7",
        "Elaboración, ejecución y seguimiento del plan de intervención. De "
        "acuerdo con los resultados de la evaluación, cuando no se cumple con "
        "los requisitos legales se elabora un plan de intervención que "
        "establece las acciones a realizar, la fecha de ejecución y el "
        "responsable. Se realiza el respectivo seguimiento y se registra su "
        "estado hasta el cierre del hallazgo.",
        None,
        _MATRIZ,
    ),
)


class RequisitosLegalesProcedimientoGenerator(DocumentGenerator):
    template_version = "procedimiento-requisitos-legales-docx-v1"
    engine = "docx"
    static_sections = (
        "Objetivo, alcance y las 4 definiciones del molde MinCIT (decreto, "
        "decreto ley, ley y resolución)",
        "Tabla de las 7 actividades del procedimiento (generalidades, consulta "
        "e identificación de la legislación, elaboración de la matriz de "
        "requisitos legales, actualización de la matriz, comunicación de los "
        "requisitos, evaluación del cumplimiento y plan de intervención) con "
        "sus registros asociados",
        "Frecuencias del molde: actualización de la matriz mínimo cada seis "
        "meses y evaluación del cumplimiento mínimo una vez al año",
    )

    def _render(
        self,
        resolved: dict[str, ResolvedField],
        variables: BaseModel,
        document_code: str | None,
    ) -> bytes:
        assert isinstance(variables, ProcedimientoRequisitosLegalesVariables)

        def val(key: str) -> str:
            field = resolved[key]
            return field.value if isinstance(field.value, str) else "\n".join(field.value)

        approval_date = (variables.approval_date or "").strip() or (
            "[PENDIENTE: fecha de aprobación]"
        )
        legal_rep = (variables.legal_representative or "").strip()
        responsible = val("responsible_role")

        b = FelipeDocxBuilder(
            code=resolve_code(document_code),
            title="Procedimiento de requisitos legales",
            company=val("company_name"),
            norm_reference="NTC-ISO 21101 — numeral 6.1.3",
            approval_date=approval_date,
        )

        b.section("1. Objetivo", _OBJECTIVE)
        b.section("2. Alcance", _SCOPE)
        b.heading("3. Definiciones")
        for term, definition in _DEFINITIONS:
            b.doc.add_paragraph(f"{term}: {definition}", style="List Bullet")
        b.section(
            "4. Responsable",
            f"La identificación, actualización y evaluación de los requisitos "
            f"legales del SGSTA es responsabilidad de: {responsible}.",
        )
        b.heading("5. Descripción de actividades")
        b.table(
            ["No", "Actividad", "Responsable", "Registro"],
            [
                [num, activity, fixed_resp or responsible, registro]
                for num, activity, fixed_resp, registro in _STEPS
            ],
        )

        b.signatures(approved=(legal_rep, "Representante legal" if legal_rep else ""))
        b.change_control()
        return b.render()
