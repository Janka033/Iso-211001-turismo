"""Generador .docx del Procedimiento de auditoría interna (9.2).

Calca el molde del kit MinCIT (basado en la GTC-ISO 19011): objetivo, alcance,
las 20 definiciones, las aclaraciones (frecuencia mínima anual, perfil del
auditor interno, independencia) y la tabla de 11 actividades (programar →
aprobar → asignar auditor → divulgar → plan → preparación → apertura →
ejecución → cierre → informe → comunicación). Todo eso es contenido FIJO; la IA
solo aporta identidad, el cargo responsable del sistema y la aprobación.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.modules.generation.generators.base import (
    DocumentGenerator,
    ResolvedField,
    resolve_code,
)
from app.modules.generation.generators.felipe_docx import FelipeDocxBuilder
from app.modules.generation.schemas import AuditoriaInternaVariables

_OBJECTIVE = (
    "Establecer las disposiciones necesarias para la planificación, "
    "preparación, ejecución y mejora de las auditorías internas al sistema de "
    "gestión de la seguridad de turismo de aventura (SGSTA) de la "
    "organización, con base en los lineamientos de la GTC-ISO 19011."
)

_SCOPE = (
    "Aplica para todos los procesos, servicios y/o actividades que se realizan "
    "en la organización."
)

_DEFINITIONS: tuple[tuple[str, str], ...] = (
    (
        "Acción correctiva",
        "Acción para eliminar la causa de una no conformidad y evitar que "
        "vuelva a ocurrir. (Fuente: NTC-ISO 21101:2020).",
    ),
    (
        "Alcance de la auditoría",
        "Extensión y límites de una auditoría. (Fuente: NTC-ISO 9001:2015).",
    ),
    ("Auditado", "Organización que es auditada. (Fuente: GTC-ISO 19011)."),
    ("Auditor", "Persona que lleva a cabo una auditoría. (Fuente: GTC-ISO 19011)."),
    (
        "Auditoría",
        "Proceso sistemático, independiente y documentado para obtener las "
        "evidencias de auditoría y evaluarlas de manera objetiva con el fin de "
        "determinar el grado en el que se cumplen los criterios de auditoría. "
        "(Fuente: GTC-ISO 19011).",
    ),
    (
        "Conclusiones de la auditoría",
        "Resultado de la auditoría, tras considerar los objetivos de la "
        "auditoría y todos los hallazgos de la auditoría. (Fuente: GTC-ISO 19011).",
    ),
    ("Conformidad", "Cumplimiento de un requisito. (Fuente: NTC-ISO 21101:2020)."),
    (
        "Criterios de auditoría",
        "Conjunto de políticas, procedimientos o requisitos usados como "
        "referencia frente a la cual se compara la evidencia de la auditoría. "
        "(Fuente: GTC-ISO 19011).",
    ),
    (
        "Evidencia de la auditoría",
        "Registros, declaraciones de hechos o cualquier otra información que es "
        "pertinente para los criterios de auditoría y que es verificable. "
        "(Fuente: GTC-ISO 19011).",
    ),
    (
        "Evidencia objetiva",
        "Datos que respaldan la existencia o veracidad de algo. (Fuente: "
        "NTC-ISO 9001:2015).",
    ),
    (
        "Equipo auditor",
        "Uno o más auditores que llevan a cabo una auditoría, con el apoyo, si "
        "es necesario, de expertos técnicos. (Fuente: GTC-ISO 19011).",
    ),
    (
        "Experto técnico",
        "Persona que aporta conocimientos o experiencia específicos al equipo "
        "auditor. (Fuente: GTC-ISO 19011).",
    ),
    (
        "Hallazgos de la auditoría",
        "Resultados de la evaluación de la evidencia de auditoría recopilada "
        "frente a los criterios de auditoría. (Fuente: GTC-ISO 19011).",
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
        "Programa de la auditoría",
        "Conjunto de una o más auditorías planificadas para un periodo de "
        "tiempo determinado y dirigidas hacia un propósito específico. (Fuente: "
        "NTC-ISO 9001:2015).",
    ),
    (
        "Plan de auditoría",
        "Descripción de las actividades y de los detalles acordados de una "
        "auditoría. (Fuente: GTC-ISO 19011).",
    ),
    (
        "Requisito",
        "Necesidad o expectativa establecida, generalmente implícita u "
        "obligatoria. (Fuente: NTC-ISO 21101:2020).",
    ),
    (
        "Seguimiento",
        "Determinación del estado de un sistema, un proceso o una actividad. "
        "(Fuente: NTC-ISO 21101:2020).",
    ),
    (
        "Sistema de gestión",
        "Conjunto de elementos de una organización que están interrelacionados "
        "o que interactúan para establecer políticas y objetivos y procesos "
        "para lograr estos objetivos. (Fuente: NTC-ISO 21101:2020).",
    ),
)

_CLARIFICATIONS: tuple[str, ...] = (
    "Se programará como mínimo una (1) auditoría interna en el año, que cubra "
    "todos los procesos del SGSTA y todos los requisitos de la norma de "
    "referencia.",
    "El programa anual de auditorías debe ser aprobado por la alta dirección o "
    "por el cargo del líder del sistema de gestión de seguridad de turismo de "
    "aventura, a fin de garantizar el conocimiento de las metodologías, de las "
    "prioridades y de las auditorías a ser desarrolladas.",
    "Para establecer el programa de auditorías se tiene en cuenta: el alcance "
    "de las auditorías; el cumplimiento del objetivo de auditorías previas; las "
    "no conformidades en los procesos; las actividades que conforman los "
    "procesos; la importancia de los procesos en cuestión; los resultados de "
    "auditorías anteriores; y los resultados de las evaluaciones de los riesgos "
    "realizadas sobre las actividades de la organización.",
    "Cuando se selecciona un auditor interno se verifica que cumpla un perfil "
    "mínimo. Educación: mínimo tecnólogo en cualquier área administrativa, de "
    "turismo o ingeniería. Formación: mínimo curso de auditores internos bajo "
    "la GTC-ISO 19011 y fundamentos de la NTC-ISO 21101:2020. Experiencia: si "
    "el auditor es contratado externamente, deberá demostrar mínimo 3 "
    "auditorías o 30 horas de auditoría interna en el sector turismo; si hace "
    "parte del personal de la organización, deberá contar con mínimo 6 meses de "
    "trabajo en la empresa.",
    "El auditor interno no puede auditar su propio trabajo. Siempre que sea "
    "posible, las auditorías deben ser realizadas por trabajadores "
    "independientes de los que tengan responsabilidad directa en la actividad "
    "examinada.",
    "Nota: en caso de requerir un auditor técnico experto, el perfil será "
    "definido por el prestador de servicios turísticos.",
    "Cuando se contrate la ejecución de las auditorías internas con personal "
    "externo, este podrá utilizar sus propios formatos, siempre y cuando se "
    "evidencie como mínimo plan de auditoría, notas de auditoría e informe de "
    "auditoría, y hayan sido avalados por el responsable del sistema de gestión "
    "de seguridad de turismo de aventura.",
)

# Actividades del molde: (nº, descripción, responsable fijo o None => cargo
# responsable del cliente, registro).
_AUDITOR = "Auditor interno"
_STEPS: tuple[tuple[str, str, str | None, str], ...] = (
    (
        "1",
        "Programar las auditorías internas. El responsable del sistema de "
        "gestión elabora el programa anual de auditorías internas a través del "
        "formato Programa de Auditorías, asegurándose de que se realice por lo "
        "menos una auditoría interna a todo el SGSTA durante el año. El programa "
        "contempla la frecuencia, los métodos, las responsabilidades y los "
        "requisitos o norma a auditar, y tiene en cuenta los procesos con "
        "hallazgos en la auditoría anterior. Si se materializa algún riesgo, se "
        "incluye en el programa para verificar las acciones tomadas.",
        None,
        "Programa de auditorías",
    ),
    (
        "2",
        "Aprobar el programa anual de auditorías. El responsable de aprobación "
        "revisa el programa: si lo aprueba, se continúa con el procedimiento; si "
        "no, se regresa a la actividad anterior y se ajusta según sus "
        "observaciones. Nota: si el PST tiene un solo cargo, se omite esta "
        "actividad.",
        None,
        "Programa de auditorías",
    ),
    (
        "3",
        "Asignar auditor. Se selecciona un auditor interno (contratado "
        "externamente o colaborador de la empresa) que cumpla el perfil "
        "definido en las aclaraciones del presente procedimiento, para asegurar "
        "la objetividad y la imparcialidad del proceso.",
        None,
        "Hoja de vida con soportes del auditor",
    ),
    (
        "4",
        "Divulgar el programa anual de auditorías. Se comunica el programa a fin "
        "de garantizar la disponibilidad de personal e información en cada uno "
        "de los procesos y la adecuada planificación.",
        None,
        "No aplica",
    ),
    (
        "5",
        "Elaborar el plan de auditoría. Al acercarse la fecha de la auditoría se "
        "diligencia el formato Plan de Auditoría, en el que se establece el "
        "detalle de la ejecución, los criterios, objetivos y alcances, para que "
        "lo conozcan los colaboradores que serán auditados.",
        _AUDITOR,
        "Plan de auditoría",
    ),
    (
        "6",
        "Preparación de la auditoría. Elaboración de las listas de verificación "
        "o del formato para notas de auditoría.",
        _AUDITOR,
        "Lista de verificación",
    ),
    (
        "7",
        "Desarrollar la reunión de apertura, en la cual se confirma el plan de "
        "auditoría y se coordina la logística necesaria con los auditados.",
        _AUDITOR,
        "Plan de auditoría",
    ),
    (
        "8",
        "Desarrollar la auditoría. Se aplican los formatos establecidos, "
        "verificando cada evidencia y cumpliendo con los objetivos y criterios "
        "establecidos en el plan de auditoría.",
        _AUDITOR,
        "Lista de verificación",
    ),
    (
        "9",
        "Realizar la reunión de cierre de auditoría y presentar los hallazgos "
        "identificados de forma general.",
        _AUDITOR,
        "No aplica",
    ),
    (
        "10",
        "Generar el informe de auditoría, que debe contener: fecha de "
        "realización, equipo auditor, objeto, alcance y criterios; hallazgos "
        "(no conformidad, observación, oportunidades de mejora y fortalezas) y "
        "conclusiones.",
        "Auditor líder y auditor(es) acompañante(s)",
        "Informe de auditoría",
    ),
    (
        "11",
        "Comunicar el informe a los involucrados. Se comunican los resultados de "
        "la auditoría con los líderes de proceso o responsables del sistema de "
        "gestión de seguridad de turismo de aventura.",
        "Auditor líder y auditor(es) acompañante(s)",
        "No aplica",
    ),
)


class AuditoriaInternaGenerator(DocumentGenerator):
    template_version = "auditoria-interna-docx-v1"
    engine = "docx"
    static_sections = (
        "Objetivo, alcance y las 20 definiciones del molde MinCIT/GTC-ISO 19011 "
        "(acción correctiva, auditoría, hallazgos, no conformidad, programa y "
        "plan de auditoría, entre otras)",
        "Aclaraciones del molde: frecuencia mínima de una auditoría interna al "
        "año que cubra todos los procesos y requisitos, perfil mínimo del "
        "auditor interno (educación, formación GTC-ISO 19011, experiencia), "
        "independencia (no auditar el propio trabajo) y uso de formatos de "
        "auditores externos",
        "Tabla de las 11 actividades del procedimiento (programar, aprobar, "
        "asignar auditor, divulgar, plan de auditoría, preparación, apertura, "
        "ejecución, cierre, informe y comunicación) con sus registros asociados",
    )

    def _render(
        self,
        resolved: dict[str, ResolvedField],
        variables: BaseModel,
        document_code: str | None,
    ) -> bytes:
        assert isinstance(variables, AuditoriaInternaVariables)

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
            title="Procedimiento de auditoría interna",
            company=val("company_name"),
            norm_reference="NTC-ISO 21101 — numeral 9.2",
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
            f"La programación y aprobación de las auditorías internas del SGSTA "
            f"es responsabilidad de: {responsible}.",
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
