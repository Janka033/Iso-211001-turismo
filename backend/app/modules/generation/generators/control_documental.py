"""Generador .docx del Procedimiento de control de la información documentada (7.5.1).

Calca el molde del kit MinCIT: objetivo, alcance, definiciones, aclaraciones
y la tabla de 9 actividades (identificar necesidad → crear/modificar →
distribuir → almacenar → controlar → recuperar → obsoletos). La metodología y
los tiempos de retención (2 años SGSTA / 20 años SST) son contenido FIJO; la
IA solo aporta identidad, cargo responsable, almacenamiento real y aprobación.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.modules.generation.generators.base import (
    DocumentGenerator,
    ResolvedField,
    resolve_code,
)
from app.modules.generation.generators.felipe_docx import FelipeDocxBuilder
from app.modules.generation.schemas import ControlDocumentalVariables

_OBJECTIVE = (
    "Determinar las actividades necesarias para asegurar el control de la "
    "información documentada de todos los procesos del sistema de gestión de "
    "seguridad del turismo de aventura."
)

_SCOPE = (
    "Este procedimiento inicia desde la identificación de la necesidad de "
    "creación y/o actualización de la información documentada hasta el "
    "control de la misma."
)

_DEFINITIONS: tuple[tuple[str, str], ...] = (
    (
        "Documento",
        "Información y el medio en el que está sostenida (NTC ISO 9001:2015).",
    ),
    (
        "Documento externo",
        "Información que apoya las actividades de la organización y hace "
        "parte del SGSTA sin ser elaborada por sus procesos: circulares, la "
        "norma NTC-ISO 21101, leyes y decretos, entre otros.",
    ),
    (
        "Documento obsoleto",
        "Documento que ha perdido su vigencia por las actualizaciones o "
        "modificaciones de las versiones iniciales.",
    ),
    (
        "Formato",
        "Plantilla utilizada para la toma de datos y/o el registro de "
        "actividades realizadas.",
    ),
    (
        "Control de cambios",
        "Proceso para gestionar y controlar los cambios que se realizan a "
        "los documentos.",
    ),
    (
        "Almacenamiento / conservación",
        "Medidas preventivas o correctivas adoptadas para asegurar la "
        "integridad física y funcional de los documentos.",
    ),
    (
        "Distribución de documentos",
        "Actividades tendientes a garantizar que los documentos lleguen a su "
        "destinatario.",
    ),
    (
        "Disposición de documentos",
        "Decisión resultante de la valoración del documento con miras a su "
        "conservación total, eliminación, selección y/o reproducción.",
    ),
)

_CLARIFICATIONS = (
    "Los documentos externos se identifican y controlan en la lista maestra "
    "de documentos. La información documentada del SGSTA comprende la "
    "requerida por la norma NTC-ISO 21101:2020 y la requerida por la "
    "organización según sus necesidades y características, y se enmarca en "
    "los siguientes tipos de documentos: manuales, procedimientos, formatos, "
    "guías, instructivos, políticas y programas, entre otros."
)

# Actividades del molde: (nº, descripción, responsable fijo o None => cargo
# del cliente, registro).
_STEPS: tuple[tuple[str, str, str | None, str], ...] = (
    (
        "1",
        "Identificar las necesidades de creación o actualización de "
        "información documentada. Cualquier colaborador puede identificar la "
        "necesidad de crear, modificar, acceder o inactivar un documento o "
        "formato, y la comunica (verbal, telefónica o escrita) al "
        "responsable del sistema de gestión para su gestión.",
        "Todos los colaboradores del PST",
        "Correo electrónico (si aplica)",
    ),
    (
        "2",
        "Revisar y autorizar la solicitud. El responsable del sistema, junto "
        "con el responsable del proceso donde aplica el documento, revisa la "
        "conveniencia, adecuación y viabilidad de la solicitud y la aprueba "
        "o rechaza.",
        None,
        "N/A",
    ),
    (
        "3",
        "Realizar la creación o modificación de documentos según la "
        "estructura y características del tipo de documento (encabezado, "
        "código, versión y control de cambios del sistema documental).",
        None,
        "Listado maestro de documentos; matriz de requisitos legales (cuando aplique)",
    ),
    (
        "4",
        "Distribución de la información documentada. Se asigna a cada "
        "proceso y/o colaborador que deba implementar el documento, con "
        "permiso de acceso en la herramienta, y se registra en el listado "
        "maestro de documentos.",
        "Responsable de cada proceso",
        "Listado maestro de documentos",
    ),
    (
        "5",
        "Almacenar y proteger los documentos. Los electrónicos se almacenan "
        "y protegen en la herramienta; los físicos se mantienen en carpetas "
        "bajo condiciones ambientales controladas (humedad, calor excesivo, "
        "intemperie).",
        "Responsable de cada proceso",
        "Documentos y registros físicos",
    ),
    (
        "6",
        "Control de la información documentada: confidencialidad (clasificar "
        "el documento como confidencial, interno, externo o público en el "
        "listado maestro), disponibilidad (listado maestro actualizado con "
        "la ubicación de la documentación vigente) e integridad.",
        None,
        "Lista maestra de documentos",
    ),
    (
        "7",
        "Recuperación de la información documentada. Se realiza en la "
        "herramienta tecnológica, que conserva las últimas versiones de los "
        "documentos del SGSTA, con copia de seguridad de respaldo.",
        "No aplica",
        "Herramienta tecnológica",
    ),
    (
        "8",
        "Documentos obsoletos o registros que cumplan el tiempo de "
        "retención. Los registros del SGSTA se salvaguardan mínimo dos (2) "
        "años o el tiempo que la alta dirección considere necesario; los "
        "registros de seguridad y salud en el trabajo se conservan mínimo "
        "veinte (20) años, de manera física o digital.",
        None,
        "Documentos obsoletos",
    ),
    (
        "9",
        "Disponer de los documentos obsoletos. Para prevenir su uso no "
        "intencionado se destruyen, eliminan o archivan previa autorización "
        "del responsable del proceso; los electrónicos obsoletos quedan en "
        "una sección aparte con acceso solo de la alta dirección o el "
        "responsable del sistema.",
        None,
        "Documentos obsoletos",
    ),
)


class ControlDocumentalGenerator(DocumentGenerator):
    template_version = "control-documental-docx-v1"
    engine = "docx"
    static_sections = (
        "Objetivo, alcance, definiciones y aclaraciones del molde MinCIT "
        "(documentos externos en la lista maestra; tipos de documentos del "
        "SGSTA)",
        "Tabla de las 9 actividades del procedimiento (identificar "
        "necesidad, revisar y autorizar, crear/modificar, distribuir, "
        "almacenar y proteger, controlar, recuperar, obsoletos y su "
        "disposición) con sus registros asociados",
        "Tiempos de retención del molde: registros del SGSTA mínimo 2 años "
        "y registros de seguridad y salud en el trabajo mínimo 20 años",
    )

    def _render(
        self,
        resolved: dict[str, ResolvedField],
        variables: BaseModel,
        document_code: str | None,
    ) -> bytes:
        assert isinstance(variables, ControlDocumentalVariables)

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
            title="Procedimiento de control de la información documentada",
            company=val("company_name"),
            norm_reference="NTC-ISO 21101 — numeral 7.5.1",
            approval_date=approval_date,
        )

        b.section("1. Objetivo", _OBJECTIVE)
        b.section("2. Alcance", _SCOPE)
        b.heading("3. Definiciones")
        for term, definition in _DEFINITIONS:
            b.doc.add_paragraph(f"{term}: {definition}", style="List Bullet")
        b.section("4. Aclaraciones", _CLARIFICATIONS)
        b.section(
            "5. Responsable y almacenamiento",
            f"El control de la información documentada es responsabilidad de: "
            f"{responsible}. Almacenamiento de los documentos del sistema: "
            f"{val('storage_description')}.",
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
