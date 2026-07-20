"""Generador .docx del Procedimiento de identificación y selección de personal (5.3).

Calca el molde del kit MinCIT: objetivo, alcance, las 11 definiciones, las
aclaraciones y la tabla de 7 actividades (identificar perfiles/roles →
seleccionar y contratar → entregar EPP → inducción/reinducción → programa de
formación → toma de conciencia → desvinculación). Todo eso es contenido FIJO; la
IA solo aporta identidad, el cargo responsable del proceso y la aprobación.
Complementa al Manual de perfiles y funciones de cargos (MA-02): este describe
CÓMO se identifican, seleccionan y forman las personas para esos perfiles.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.modules.generation.generators.base import (
    DocumentGenerator,
    ResolvedField,
    resolve_code,
)
from app.modules.generation.generators.felipe_docx import FelipeDocxBuilder
from app.modules.generation.schemas import ProcedimientoSeleccionPersonalVariables

_OBJECTIVE = (
    "Identificar los perfiles, seleccionar el personal idóneo para la "
    "organización y fortalecer las competencias, con el fin de proporcionar y "
    "mantener un recurso humano competente en los diferentes cargos, facilitar "
    "su formación y garantizar el desempeño de los colaboradores y la toma de "
    "conciencia con el sistema de gestión de seguridad de turismo de aventura."
)

_SCOPE = (
    "Aplica para todos los colaboradores y demás partes interesadas que deseen "
    "vincularse laboral o contractualmente con la organización."
)

_DEFINITIONS: tuple[tuple[str, str], ...] = (
    (
        "Ambiente de trabajo",
        "Conjunto de condiciones bajo las cuales se realiza el trabajo; pueden "
        "incluir factores físicos, sociales, psicológicos y ambientales "
        "(temperatura, iluminación, ergonomía, estrés laboral, atmósfera en el "
        "trabajo). (Fuente: NTC-ISO 9001:2015).",
    ),
    (
        "ARL",
        "Compañías aseguradoras de vida o mutuales autorizadas por la "
        "Superintendencia Financiera para explotar el ramo de los seguros, "
        "destinadas a prevenir, proteger y atender a los trabajadores de los "
        "efectos de las enfermedades y accidentes que puedan ocurrirles con "
        "ocasión o como consecuencia del trabajo. (Fuente: Alcaldía de Bogotá).",
    ),
    (
        "Capacitación",
        "Conjunto de procesos organizados de educación no formal e informal "
        "dirigidos a prolongar y complementar la educación inicial mediante la "
        "generación de conocimientos, el desarrollo de habilidades y el cambio "
        "de actitudes, para incrementar la capacidad individual y colectiva. "
        "(Fuente: Departamento Administrativo de la Función Pública, Concepto "
        "263321 de 2021).",
    ),
    (
        "Certificación de la experiencia",
        "La experiencia se acredita mediante la presentación de constancias "
        "expedidas por la autoridad competente de las respectivas instituciones "
        "oficiales o privadas. (Fuente: Función Pública, Concepto 061421 de 2021).",
    ),
    (
        "Competencia",
        "Capacidad para aplicar conocimientos y habilidades con el fin de lograr "
        "los resultados previstos. (Fuente: NTC-ISO 21101:2020).",
    ),
    (
        "Consciencia",
        "Conocimiento reflexivo de las cosas; capacidad de reconocer la realidad "
        "circundante y de relacionarse con ella. (Fuente: Real Academia Española).",
    ),
    (
        "Educación",
        "Proceso de formación permanente, personal, cultural y social que se "
        "fundamenta en una concepción integral de la persona humana, de su "
        "dignidad, de sus derechos y de sus deberes. (Fuente: Ministerio de "
        "Educación de Colombia, Sistema Educativo Colombiano).",
    ),
    (
        "Eficacia",
        "Medida en que se realizan las actividades planificadas y se logran los "
        "resultados previstos. (Fuente: NTC-ISO 21101:2020).",
    ),
    (
        "EPS",
        "Entidades responsables de la afiliación y prestación del plan "
        "obligatorio de salud a sus beneficiarios. (Fuente: Ministerio de Salud "
        "y Protección Social).",
    ),
    (
        "Experiencia",
        "Conocimientos, habilidades y destrezas adquiridas o desarrolladas "
        "mediante el ejercicio de una profesión, arte u oficio. (Fuente: Función "
        "Pública, Concepto 061421 de 2021).",
    ),
    (
        "Formación",
        "Conjunto de acciones formativas que capacitan para el desempeño "
        "cualificado de las diversas profesiones, el acceso al empleo y la "
        "participación en la vida social, cultural y económica. (Fuente: Real "
        "Academia Española; OIT, Recomendación 57 de 1939).",
    ),
)

_CLARIFICATIONS: tuple[str, ...] = (
    "No se podrá firmar el contrato hasta que el aspirante haya entregado la "
    "totalidad de registros y/o documentos solicitados en el perfil de "
    "competencia.",
    "Si le falta formación al aspirante, se incluye en el programa de formación "
    "para fortalecer sus competencias y que cumpla con el perfil definido.",
)

# Actividades del molde: (nº, descripción, responsable fijo o None => cargo
# responsable del cliente, registro).
_STEPS: tuple[tuple[str, str, str | None, str], ...] = (
    (
        "1",
        "Identificar perfiles, roles, responsabilidades y autoridad. Se define "
        "el perfil de cada cargo según las necesidades del PST (educación, "
        "formación y experiencia) en el formato Perfil de competencia. El rol se "
        "clasifica en tres categorías: Directivo (mayores responsabilidades y "
        "autoridad para tomar decisiones sobre el SGSTA), Medio (responsabilidades "
        "y autoridad intermedias; puede tomar algunas decisiones e informa a su "
        "jefe inmediato) y Apoyo (responsabilidades y autoridad mínimas; ejecuta "
        "lo que le asigne su jefe inmediato). De acuerdo con el rol se asignan "
        "las responsabilidades y la autoridad frente al SGSTA y al enfoque de "
        "seguridad y salud en el trabajo.",
        None,
        "Matriz de perfil de competencia",
    ),
    (
        "2",
        "Seleccionar y contratar al personal. El responsable de área comunica la "
        "necesidad de personal y el responsable del proceso y/o el gerente la "
        "aprueba. Se convoca a los aspirantes por diferentes medios o referidos, "
        "dando prioridad a la contratación de base local en condiciones justas y "
        "equitativas conforme a la legislación vigente. Se reciben y verifican "
        "las hojas de vida frente al perfil (educación, experiencia y formación) "
        "y se confirman las referencias; se realiza una entrevista y se "
        "selecciona al aspirante que más se ajuste. Se legaliza la contratación "
        "y se firma el contrato según la modalidad acordada; las evidencias se "
        "archivan en la carpeta del personal y se entrega copia al empleado. La "
        "hoja de vida se sistematiza en la herramienta tecnológica y se asegura "
        "la afiliación al sistema de seguridad social según la normatividad "
        "vigente.",
        None,
        "Matriz de perfil de competencia; hoja de vida; contrato; registro de "
        "afiliación; base de datos de colaboradores",
    ),
    (
        "3",
        "Entregar EPP. Verificada la conformidad de la dotación, el responsable "
        "entrega a los colaboradores sus elementos de protección personal y "
        "registra la evidencia de la entrega en el formato correspondiente.",
        None,
        "Entrega de dotación y EPP",
    ),
    (
        "4",
        "Realizar inducción y/o reinducción. Al colaborador vinculado se le "
        "realiza la inducción según su cargo, con el siguiente contenido mínimo: "
        "información general del PST, normatividad legal aplicable, directrices "
        "estratégicas (misión, visión, políticas), el sistema de gestión de "
        "seguridad de turismo de aventura, las funciones y las responsabilidades "
        "y autoridad del cargo, los programas de gestión, la seguridad y salud "
        "en el trabajo, el plan de bienestar y el apoyo y participación con la "
        "comunidad. Se realiza reinducción por lo menos una vez al año o cuando "
        "se presenten cambios en el cargo o en el SGSTA.",
        None,
        "Listas de asistencia de inducción / reinducción",
    ),
    (
        "5",
        "Realizar el programa de formación. Mínimo una vez al año o cuando se "
        "requiera, el PST identifica los temas de formación: formación general "
        "(para lograr los objetivos estratégicos) y formación específica por "
        "competencia (revisando cada perfil para recopilar las necesidades). La "
        "evaluación de la formación es opcional y se deja registro o "
        "justificación de su no realización. Se hace seguimiento al programa con "
        "la frecuencia del indicador definido y, según los resultados, se decide "
        "si se toman acciones para fortalecer las competencias.",
        None,
        "Programa de formación; lista de asistencia",
    ),
    (
        "6",
        "Concientizar al personal sobre la toma de conciencia. Se realizan "
        "actividades de formación y/o campañas de sensibilización y de "
        "participación para que las personas que trabajan bajo el control de la "
        "organización estén al tanto de la política de seguridad de turismo de "
        "aventura, de su contribución a la eficacia del SGSTA (incluidos los "
        "beneficios de mejorar la seguridad) y de las consecuencias de no "
        "cumplir con los requisitos del sistema de gestión.",
        None,
        "Campañas; programa de formación",
    ),
    (
        "7",
        "Desvincular — retiro del personal (opcional). La desvinculación o "
        "finalización del contrato puede darse por retiro o renuncia voluntaria "
        "o por terminación del contrato, cumpliendo en todos los casos la "
        "normatividad legal aplicable. Se diligencia el formato de paz y salvo; "
        "para el contrato laboral, una vez efectivo el retiro se desafilia al "
        "empleado de la seguridad social integral y parafiscal, se le notifica "
        "por escrito la realización del examen de egreso y se realiza la "
        "liquidación y el pago correspondiente.",
        None,
        "(Opcional) Formato paz y salvo",
    ),
)


class SeleccionPersonalGenerator(DocumentGenerator):
    template_version = "procedimiento-seleccion-personal-docx-v1"
    engine = "docx"
    static_sections = (
        "Objetivo, alcance y las 11 definiciones del molde MinCIT (ambiente de "
        "trabajo, ARL, capacitación, competencia, educación, EPS, experiencia, "
        "formación, entre otras)",
        "Aclaraciones del molde: no se firma el contrato hasta que el aspirante "
        "entregue la totalidad de los documentos del perfil, y si le falta "
        "formación se incluye en el programa de formación",
        "Tabla de las 7 actividades del procedimiento (identificar perfiles y "
        "roles, seleccionar y contratar, entregar EPP, inducción y reinducción, "
        "programa de formación, toma de conciencia y desvinculación) con sus "
        "registros asociados",
    )

    def _render(
        self,
        resolved: dict[str, ResolvedField],
        variables: BaseModel,
        document_code: str | None,
    ) -> bytes:
        assert isinstance(variables, ProcedimientoSeleccionPersonalVariables)

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
            title="Procedimiento de identificación y selección de personal",
            company=val("company_name"),
            norm_reference="NTC-ISO 21101 — numeral 5.3",
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
            f"La identificación de perfiles, la selección, la formación y la "
            f"toma de conciencia del personal es responsabilidad de: {responsible}.",
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
