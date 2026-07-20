"""Generador .docx del Procedimiento de acciones correctivas y de mejora (10.1).

Calca el molde del kit MinCIT: objetivo, alcance, definiciones, aclaraciones
(fuentes de no conformidad y oportunidad de mejora) y la tabla de 6 actividades
(identificar → registrar → tratamiento y análisis de causas → plan de acción →
seguimiento → evaluación de eficacia y cierre). Todo eso es contenido FIJO; la
IA solo aporta identidad, el cargo responsable del sistema y la aprobación.

Cierra el ciclo PDCA junto con la auditoría interna (9.2): las no conformidades
que la auditoría detecta se tratan y cierran con este procedimiento.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.modules.generation.generators.base import (
    DocumentGenerator,
    ResolvedField,
    resolve_code,
)
from app.modules.generation.generators.felipe_docx import FelipeDocxBuilder
from app.modules.generation.schemas import AccionesCorrectivasVariables

_OBJECTIVE = (
    "Establecer los lineamientos para la determinación, descripción y "
    "seguimiento de acciones correctivas y/o de mejora identificadas por la "
    "organización, permitiendo eliminar las causas de las no conformidades "
    "presentadas o el aprovechamiento de las causas que generen acciones de "
    "mejora."
)

_SCOPE = (
    "Inicia cuando se identifica una no conformidad u oportunidad de mejora en "
    "los procesos, actividades, áreas y demás comprendidos en el sistema de "
    "gestión de seguridad de turismo de aventura de la organización; comprende "
    "la definición, descripción y seguimiento, y termina con el cierre de las "
    "acciones correctivas o de mejora definidas."
)

_DEFINITIONS: tuple[tuple[str, str], ...] = (
    (
        "Acción correctiva",
        "Acción para eliminar la causa de una no conformidad y evitar que "
        "vuelva a ocurrir. (Fuente: NTC-ISO 21101:2020).",
    ),
    (
        "Auditoría",
        "Proceso sistemático, independiente y documentado para obtener las "
        "evidencias de auditoría y evaluarlas de manera objetiva con el fin de "
        "determinar el grado en el que se cumplen los criterios de auditoría. "
        "(Fuente: NTC-ISO 21101:2020).",
    ),
    (
        "Corrección",
        "Acción inmediata para eliminar una no conformidad detectada. (Fuente: "
        "ISO 9000:2015).",
    ),
    (
        "Eficacia",
        "Medida en que se realizan las actividades planificadas y se logran los "
        "resultados previstos. (Fuente: NTC-ISO 21101:2020).",
    ),
    (
        "Fuente de verificación",
        "Documentos o registros que permiten verificar el cumplimiento de "
        "actividades. (Fuente: NTC-ISO 9001:2015).",
    ),
    (
        "Hallazgos de la auditoría",
        "Resultados de la evaluación de la evidencia de auditoría recopilada "
        "frente a los criterios de auditoría. (Fuente: GTC-ISO 19011:2018).",
    ),
    (
        "Mejora continua",
        "Actividad recurrente para mejorar el desempeño. (Fuente: NTC-ISO "
        "21101:2020).",
    ),
    (
        "No conformidad",
        "Incumplimiento de un requisito. (Fuente: NTC-ISO 21101:2020).",
    ),
    (
        "Proceso",
        "Conjunto de actividades interrelacionadas o que interactúan, que "
        "transforman las entradas en salidas. (Fuente: NTC-ISO 21101:2020).",
    ),
    (
        "Riesgo",
        "Efecto de la incertidumbre. Un efecto es una desviación de aquello "
        "que se espera, ya sea positivo o negativo. (Fuente: NTC-ISO "
        "21101:2020).",
    ),
)

_CLARIFICATIONS: tuple[str, ...] = (
    "Las principales fuentes de las no conformidades y oportunidades de mejora "
    "en la organización pueden presentarse en: resultados de auditorías "
    "internas y externas; incumplimiento de legislación u otros requisitos "
    "aplicables; análisis de los resultados de simulacros; resultados del "
    "seguimiento y la medición; revisión por la dirección; materialización de "
    "riesgos; quejas de los clientes y partes interesadas; y cualquier otra "
    "pertinente.",
    "Los líderes del proceso deben asegurarse de que se realicen las "
    "correcciones y se tomen las acciones necesarias sin demoras injustificadas.",
)

_MATRIZ = "Matriz de acciones correctivas y de mejora"
_LIDER = "Líder del proceso"
# Actividades del molde: (nº, descripción, responsable fijo o None => cargo
# responsable del cliente, registro).
_STEPS: tuple[tuple[str, str, str | None, str], ...] = (
    (
        "1",
        "Identificar la no conformidad u oportunidad de mejora, de acuerdo con "
        "las fuentes descritas en las aclaraciones del presente procedimiento "
        "(auditorías, resultados de procesos, medición de indicadores, "
        "evaluación legal y otras fuentes).",
        None,
        "Informes de auditorías internas y externas; resultados de procesos; "
        "medición de indicadores; evaluación legal",
    ),
    (
        "2",
        "Registrar la no conformidad u oportunidad de mejora. El responsable "
        "del proceso registra en el formato Matriz de acciones correctivas y de "
        "mejora la sección «Descripción del hallazgo»: ID, fecha, proceso, "
        "origen/fuente, tipo de hallazgo (no conformidad u oportunidad de "
        "mejora) y descripción. Se revisa además si existen o pueden ocurrir no "
        "conformidades similares.",
        None,
        _MATRIZ,
    ),
    (
        "3",
        "Tratamiento y análisis. Se registra la corrección o solución inmediata "
        "a la no conformidad y si se generaron consecuencias (no aplica para "
        "oportunidades de mejora). Luego el líder del proceso realiza el "
        "análisis de causas con la Guía de análisis de causas para encontrar la "
        "causa raíz y la registra. Para las oportunidades de mejora no se "
        "analizan ni registran causas.",
        _LIDER,
        f"{_MATRIZ}; Guía de análisis de causas",
    ),
    (
        "4",
        "Establecer el plan de acción. Se definen las acciones necesarias para "
        "eliminar las causas de la no conformidad o para desarrollar la "
        "oportunidad de mejora, con responsables y fechas máximas de ejecución.",
        _LIDER,
        _MATRIZ,
    ),
    (
        "5",
        "Realizar el seguimiento a la ejecución de las acciones. Se registran "
        "los avances y la evidencia del plan de acción: fecha de seguimiento, "
        "observaciones (por cada actividad, incluidas las correcciones) y "
        "estado de la actividad (en proceso o finalizada).",
        _LIDER,
        _MATRIZ,
    ),
    (
        "6",
        "Realizar la evaluación de la eficacia. Una acción correctiva es eficaz "
        "si se eliminan las causas del incumplimiento y la no conformidad no "
        "vuelve a presentarse; una acción de mejora es eficaz si se logró la "
        "mejora deseada. Se registra la eficacia y su justificación, y se "
        "establece el estado: Abierta (falta ejecutar alguna etapa o "
        "determinar la eficacia) o Cerrada (todas las etapas ejecutadas, "
        "incluida la eficacia). Una acción cerrada sin eficacia obliga a abrir "
        "una nueva.",
        None,
        _MATRIZ,
    ),
)


class AccionesCorrectivasGenerator(DocumentGenerator):
    template_version = "acciones-correctivas-docx-v1"
    engine = "docx"
    static_sections = (
        "Objetivo, alcance y definiciones del molde MinCIT (acción correctiva, "
        "corrección, eficacia, hallazgos, mejora continua, no conformidad, "
        "riesgo, entre otras)",
        "Aclaraciones del molde: fuentes de no conformidad y oportunidad de "
        "mejora (auditorías, requisitos legales, simulacros, seguimiento y "
        "medición, revisión por la dirección, materialización de riesgos, "
        "quejas) y la obligación de actuar sin demoras injustificadas",
        "Tabla de las 6 actividades del procedimiento (identificar, registrar, "
        "tratamiento y análisis de causas, plan de acción, seguimiento y "
        "evaluación de eficacia con el cierre) y sus registros asociados",
    )

    def _render(
        self,
        resolved: dict[str, ResolvedField],
        variables: BaseModel,
        document_code: str | None,
    ) -> bytes:
        assert isinstance(variables, AccionesCorrectivasVariables)

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
            title="Procedimiento de acciones correctivas y de mejora",
            company=val("company_name"),
            norm_reference="NTC-ISO 21101 — numeral 10.1",
            approval_date=approval_date,
        )

        b.section("1. Objetivo", _OBJECTIVE)
        b.section("2. Alcance", _SCOPE)
        b.heading("3. Definiciones")
        for term, definition in _DEFINITIONS:
            b.doc.add_paragraph(f"{term}: {definition}", style="List Bullet")
        b.heading("4. Aclaraciones")
        for clarification in _CLARIFICATIONS:
            b.doc.add_paragraph(clarification, style="List Bullet")
        b.section(
            "5. Responsable",
            f"La gestión de las acciones correctivas y de mejora del SGSTA es "
            f"responsabilidad de: {responsible}.",
        )
        b.heading("6. Descripción de actividades")
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
