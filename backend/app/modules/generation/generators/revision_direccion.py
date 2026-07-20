"""Generador .docx del Procedimiento de revisión por la dirección (9.3).

Calca el molde del kit MinCIT: objetivo, alcance, definiciones y la tabla de 6
actividades (programación → preparación → análisis de las entradas → resultados
y toma de decisiones → conclusiones → comunicación). Las entradas de la revisión
(estado de acciones previas, cambios de contexto, desempeño en seguridad —no
conformidades, seguimiento y medición, resultados de auditoría— y oportunidades
de mejora) son contenido FIJO. La IA solo aporta identidad, el cargo responsable
que prepara la revisión y la aprobación.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.modules.generation.generators.base import (
    DocumentGenerator,
    ResolvedField,
    resolve_code,
)
from app.modules.generation.generators.felipe_docx import FelipeDocxBuilder
from app.modules.generation.schemas import RevisionDireccionVariables

_OBJECTIVE = (
    "Establecer y definir los aspectos correspondientes para la realización de "
    "la revisión por la dirección al sistema de gestión de seguridad de turismo "
    "de aventura (SGSTA) de la organización, por medio del análisis de la "
    "información de entrada y que tenga como resultado la toma de decisiones "
    "para mejorar continuamente."
)

_SCOPE = (
    "El procedimiento aplica para la revisión que realiza la dirección a todo "
    "el sistema de gestión de seguridad de turismo de aventura (SGSTA) para "
    "asegurar su continua idoneidad, adecuación y eficacia, en el periodo "
    "objeto de análisis."
)

_DEFINITIONS: tuple[tuple[str, str], ...] = (
    (
        "Adecuación",
        "Capacidad de los procesos, productos o sistemas para cumplir con los "
        "requisitos y expectativas establecidas por normativas, estándares, "
        "clientes y otras partes interesadas. (Fuente: adaptado de la ISO "
        "14001:2015).",
    ),
    (
        "Alta dirección",
        "Persona o grupo de personas que dirige y controla una organización al "
        "más alto nivel. (Fuente: NTC-ISO 21101:2020).",
    ),
    ("Desempeño", "Resultado medible. (Fuente: NTC-ISO 21101:2020)."),
    (
        "Eficacia",
        "Medida en que se realizan las actividades planificadas y se logran los "
        "resultados previstos. (Fuente: NTC-ISO 21101:2020).",
    ),
    (
        "Idoneidad",
        "Cuando el SGSTA es adecuado, apropiado, apto. (Fuente: adaptado de la "
        "RAE).",
    ),
    (
        "Mejora continua",
        "Actividad recurrente para mejorar el desempeño. (Fuente: NTC-ISO "
        "21101:2020).",
    ),
    ("Objetivo", "Resultado a lograr. (Fuente: NTC-ISO 21101:2020)."),
    (
        "Procedimiento",
        "Forma específica de llevar a cabo una actividad o un proceso. (Fuente: "
        "NTC-ISO 21101:2020).",
    ),
)

_FORMATO = "Formato de revisión por la dirección"
_DIRECCION = "Alta dirección"
# Actividades del molde: (nº, descripción, responsable fijo o None => cargo
# responsable del cliente, registro).
_STEPS: tuple[tuple[str, str, str | None, str], ...] = (
    (
        "1",
        "Programación de la revisión por la dirección. La alta dirección "
        "determina realizar como mínimo una vez al año la revisión por la "
        "dirección al SGSTA.",
        _DIRECCION,
        "No aplica",
    ),
    (
        "2",
        "Preparación de la revisión por la dirección. El responsable del "
        "sistema de gestión y/o los líderes de procesos recopilan con "
        "anticipación toda la información de entrada en el formato de revisión "
        "por la dirección, y la presentan el día de la reunión.",
        None,
        _FORMATO,
    ),
    (
        "3",
        "Análisis de la información de entrada. En la reunión, los responsables "
        "presentan la información requerida: a) el estado de las acciones de las "
        "revisiones por la dirección anteriores (si aplica); b) los cambios en "
        "los asuntos externos e internos pertinentes para el SGSTA; c) "
        "información sobre el desempeño en seguridad, incluidas las tendencias: "
        "las no conformidades y medidas correctivas, los resultados del "
        "seguimiento y la medición, y los resultados de la auditoría; y d) las "
        "oportunidades de mejora continua. Se analiza cada reporte y se "
        "registran el análisis y las propuestas de decisión en el formato.",
        _DIRECCION,
        f"Evidencias de información de entrada; {_FORMATO}",
    ),
    (
        "4",
        "Resultados y toma de decisiones. Tras el análisis, la alta dirección "
        "toma decisiones relacionadas con las oportunidades de mejora continua "
        "y la necesidad de introducir cambios al SGSTA. A cada decisión se le "
        "asigna responsable, tiempo de ejecución y responsable de seguimiento, "
        "y se registra en el formato.",
        _DIRECCION,
        _FORMATO,
    ),
    (
        "5",
        "Conclusiones. Se definen las conclusiones de la revisión por la "
        "dirección en cuanto a la adecuación, idoneidad y eficacia del SGSTA.",
        _DIRECCION,
        _FORMATO,
    ),
    (
        "6",
        "Comunicar a los responsables de ejecutar las decisiones tomadas. Se "
        "comunican al personal implicado los resultados del proceso de revisión "
        "y sus compromisos frente a las decisiones establecidas.",
        None,
        "Medio de comunicación",
    ),
)


class RevisionDireccionGenerator(DocumentGenerator):
    template_version = "revision-direccion-docx-v1"
    engine = "docx"
    static_sections = (
        "Objetivo, alcance y definiciones del molde MinCIT (adecuación, alta "
        "dirección, desempeño, eficacia, idoneidad, mejora continua, entre otras)",
        "Las entradas obligatorias de la revisión por la dirección (estado de "
        "acciones previas, cambios de contexto interno y externo, desempeño en "
        "seguridad —no conformidades y medidas correctivas, seguimiento y "
        "medición, resultados de auditoría— y oportunidades de mejora continua)",
        "Tabla de las 6 actividades del procedimiento (programación, "
        "preparación, análisis de entradas, resultados y decisiones, "
        "conclusiones sobre adecuación/idoneidad/eficacia, y comunicación) con "
        "sus registros asociados",
    )

    def _render(
        self,
        resolved: dict[str, ResolvedField],
        variables: BaseModel,
        document_code: str | None,
    ) -> bytes:
        assert isinstance(variables, RevisionDireccionVariables)

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
            title="Procedimiento de revisión por la dirección",
            company=val("company_name"),
            norm_reference="NTC-ISO 21101 — numeral 9.3",
            approval_date=approval_date,
        )

        b.section("1. Objetivo", _OBJECTIVE)
        b.section("2. Alcance", _SCOPE)
        b.heading("3. Definiciones")
        for term, definition in _DEFINITIONS:
            b.doc.add_paragraph(f"{term}: {definition}", style="List Bullet")
        b.section("4. Aclaraciones", "No aplica.")
        b.section(
            "5. Responsable",
            f"La alta dirección lidera la revisión por la dirección del SGSTA; "
            f"su preparación y el seguimiento de las decisiones son "
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
