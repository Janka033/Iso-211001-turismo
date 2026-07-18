"""Generador .docx del Procedimiento de gestión de riesgos y oportunidades (6.1.1).

Calca el molde del kit MinCIT: objetivo, alcance, definiciones, aclaraciones
y la tabla de 7 actividades (identificar → registrar → evaluar → tratar →
seguir). Toda la metodología es contenido normativo FIJO (los ejemplos del
molde son los exigidos); la IA solo aporta identidad, el cargo que lidera la
gestión, la frecuencia de seguimiento y la aprobación.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.modules.generation.generators.base import (
    DocumentGenerator,
    ResolvedField,
    resolve_code,
)
from app.modules.generation.generators.felipe_docx import FelipeDocxBuilder
from app.modules.generation.schemas import ProcedimientoRiesgosVariables

_OBJECTIVE = (
    "Establecer el paso a paso para la identificación, evaluación, controles o "
    "tratamiento, acciones, seguimiento y evaluación de los riesgos y/u "
    "oportunidades que se presentan en las actividades que desarrolla el "
    "prestador de servicios turísticos."
)

_SCOPE = (
    "Aplica para clientes/participantes, colaboradores, proveedores, "
    "subcontratistas, visitantes y demás partes interesadas que llegan a las "
    "instalaciones o reciben servicios por parte del prestador de servicios "
    "turísticos hasta que se retiran del mismo."
)

_DEFINITIONS: tuple[tuple[str, str], ...] = (
    (
        "Análisis del entorno externo",
        "Evaluación de factores externos que pueden afectar la organización, "
        "tales como condiciones económicas, cambios en la legislación, "
        "políticas gubernamentales y dinámicas de mercado.",
    ),
    (
        "Análisis del entorno interno",
        "Evaluación de los aspectos internos de una organización, incluyendo "
        "su estructura financiera, procesos operativos y controles internos, "
        "para identificar posibles áreas de vulnerabilidad y riesgo.",
    ),
    (
        "Análisis del riesgo",
        "Proceso para comprender la naturaleza del riesgo y determinar el "
        "nivel de riesgo (Guía ISO 73:2009).",
    ),
    (
        "Evaluación del riesgo",
        "Proceso de comparación de los resultados del análisis del riesgo con "
        "los criterios de riesgo para determinar si el riesgo y/o su magnitud "
        "son aceptables o tolerables (NTC ISO Guía 73:2015).",
    ),
    (
        "Gestión del riesgo",
        "Actividades coordinadas para dirigir y controlar una organización en "
        "lo relativo al riesgo (NTC ISO Guía 73:2015).",
    ),
    (
        "Identificación del riesgo",
        "Proceso de hallar, reconocer y describir riesgos (Guía ISO 73:2009).",
    ),
    (
        "Valoración del riesgo",
        "Magnitud de un riesgo o combinación de riesgos, expresada en "
        "términos de la combinación de impacto y su posibilidad (Guía ISO "
        "73:2009).",
    ),
    (
        "Oportunidad",
        "Situación o conjunto de circunstancias favorables que pueden "
        "aprovecharse para lograr un resultado positivo para la organización.",
    ),
)

_CLARIFICATIONS = (
    "El prestador de servicios turísticos debe seguir un enfoque sistemático "
    "para gestionar los riesgos y oportunidades tanto a nivel organizacional "
    "como en cada actividad de turismo de aventura. La herramienta \"Matriz "
    "de riesgos y oportunidades\" documenta los riesgos y oportunidades "
    "generales que afectan a la organización, considerando su estrategia y "
    "objetivos. Dado que cada actividad de turismo de aventura presenta "
    "riesgos únicos, es necesario además un análisis específico por "
    "actividad, con la identificación de riesgos, evaluación, tratamiento y "
    "seguimiento acordes con este procedimiento. Los riesgos climáticos a que "
    "hace referencia la NTC-ISO 21101 están incluidos como riesgos "
    "ambientales en la tabla de clasificación de riesgos."
)

# Actividades del molde: (nº, título y descripción, responsable fijo o None
# => cargo del cliente, registro).
_STEPS: tuple[tuple[str, str, str | None, str], ...] = (
    (
        "1",
        "Definir tipo de mapa de riesgos. Seleccionar el análisis "
        "organizacional (riesgos y oportunidades generales del prestador) y "
        "el análisis por actividad de turismo de aventura, que se realiza "
        "para cada actividad ofrecida.",
        None,
        "Matriz de riesgos y oportunidades",
    ),
    (
        "2",
        "Análisis del contexto de la actividad de turismo de aventura. Antes "
        "de identificar los riesgos de cada actividad, realizar el análisis "
        "del contexto de cada una de las actividades que ofrece el prestador, "
        "registrando la actividad y sus condiciones de operación.",
        None,
        "Contexto de la actividad de turismo de aventura",
    ),
    (
        "3",
        "Identificación de los riesgos u oportunidades. Identificar los "
        "riesgos y oportunidades de las actividades de la organización y de "
        "cada actividad de turismo de aventura, especificando si el análisis "
        "corresponde a la organización o a una actividad concreta.",
        "Todos los líderes de procesos",
        "Contexto de la actividad y matriz de riesgos y oportunidades",
    ),
    (
        "4",
        "Registro del riesgo / oportunidad. Registrar en la matriz: fecha de "
        "detección, proceso, actividad o procedimiento, tipo de situación "
        "(riesgo u oportunidad) y fuente según la tabla de clasificación de "
        "riesgos.",
        "Todos los líderes de procesos",
        "Matriz de riesgos y oportunidades y tabla de clasificación",
    ),
    (
        "5",
        "Evaluación del riesgo / oportunidad. Aplicar la metodología "
        "establecida con base en los criterios de probabilidad e impacto y "
        "determinar la valoración resultante de cada riesgo u oportunidad.",
        None,
        "Matriz de riesgos y oportunidades",
    ),
    (
        "6",
        "Tratamiento de riesgos / oportunidades. Según la valoración, definir "
        "la opción de manejo (implementar plan, definir plan, evaluar "
        "costo/beneficio o considerar) y las acciones para mitigar el riesgo "
        "o potencializar la oportunidad, con responsable y fecha.",
        None,
        "Matriz de riesgos y oportunidades",
    ),
    (
        "7",
        "Seguimiento y evaluación. Realizar el seguimiento de los riesgos y "
        "oportunidades con la frecuencia definida, registrando fecha, avance "
        "y estado de las acciones y el resultado alcanzado.",
        None,
        "Matriz de riesgos y oportunidades",
    ),
)


class ProcedimientoRiesgosGenerator(DocumentGenerator):
    template_version = "procedimiento-riesgos-docx-v1"
    engine = "docx"
    static_sections = (
        "Objetivo, alcance, definiciones (Guía ISO 73 / NTC ISO Guía 73) y "
        "aclaraciones del molde MinCIT, incluida la nota de riesgos "
        "climáticos como riesgos ambientales",
        "Tabla de las 7 actividades del procedimiento (definir tipo de "
        "matriz, contexto por actividad, identificación, registro, "
        "evaluación por probabilidad e impacto, tratamiento y seguimiento) "
        "con sus registros asociados",
    )

    def _render(
        self,
        resolved: dict[str, ResolvedField],
        variables: BaseModel,
        document_code: str | None,
    ) -> bytes:
        assert isinstance(variables, ProcedimientoRiesgosVariables)

        def val(key: str) -> str:
            field = resolved[key]
            return field.value if isinstance(field.value, str) else "\n".join(field.value)

        approval_date = (variables.approval_date or "").strip() or (
            "[PENDIENTE: fecha de aprobación]"
        )
        legal_rep = (variables.legal_representative or "").strip()
        responsible = val("responsible_role")
        frequency = val("follow_up_frequency")

        b = FelipeDocxBuilder(
            code=resolve_code(document_code),
            title="Procedimiento de gestión de riesgos y oportunidades",
            company=val("company_name"),
            norm_reference="NTC-ISO 21101 — numeral 6.1.1",
            approval_date=approval_date,
        )

        b.section("1. Objetivo", _OBJECTIVE)
        b.section("2. Alcance", _SCOPE)
        b.heading("3. Definiciones")
        for term, definition in _DEFINITIONS:
            b.doc.add_paragraph(f"{term}: {definition}", style="List Bullet")
        b.section("4. Aclaraciones", _CLARIFICATIONS)
        b.section(
            "5. Responsable y frecuencia de seguimiento",
            f"La gestión de riesgos y oportunidades es liderada por: "
            f"{responsible}. El seguimiento formal de los riesgos y "
            f"oportunidades se realiza con frecuencia: {frequency}.",
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
