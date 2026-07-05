"""Genera MUESTRAS de los 7 documentos del MVP con datos de ejemplo.

Sirve para mostrarle a Felipe el FORMATO auditable de cada documento SIN
necesidad de Gemini ni Supabase: invoca los generadores reales directamente
con variables de una empresa ficticia y escribe los archivos en ``samples/``.

Es un preview del formato, no del flujo completo (RAG + IA). Para validar el
flujo end-to-end hay que sembrar la norma y correr el endpoint.

Uso:
    python scripts/generate_samples.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.modules.generation.generators.factory import get_spec, supported_types  # noqa: E402
from app.modules.generation.schemas import (  # noqa: E402
    CommunicationEntry,
    CommunicationProcedureVariables,
    EmergencyPlanVariables,
    EmergencyScenario,
    EquipmentInspectionItem,
    EquipmentManualVariables,
    IncidentManagementVariables,
    ProfilesManualVariables,
    RiskEntry,
    RiskMatrixVariables,
    RoleProfile,
    SecurityPolicyVariables,
)

OUT_DIR = ROOT / "samples"

# Empresa ficticia de ejemplo (NO datos reales de Felipe).
_SAMPLES = {
    "politica_seguridad": SecurityPolicyVariables(
        company_name="Aventura Andina SAS",
        nit="900.123.456-7",
        scope="Operación de rafting y canopy en Santander, Colombia.",
        activities=["Rafting nivel III-IV", "Canopy", "Senderismo guiado"],
        management_commitment=(
            "La alta dirección se compromete a proteger la seguridad de turistas, "
            "guías y comunidad, asignando los recursos necesarios."
        ),
        safety_objectives=[
            "Cero accidentes graves anuales",
            "100% del personal certificado en primeros auxilios",
        ],
        legal_commitment=(
            "Cumplir la normativa de turismo de aventura y los requisitos legales "
            "aplicables en Colombia."
        ),
        continuous_improvement=(
            "Revisar y mejorar el sistema de gestión de seguridad cada seis meses."
        ),
        communication="Publicada en la sede, el sitio web y socializada con el personal.",
        legal_representative="María Gómez",
        approval_date="2026-06-18",
    ),
    "matriz_riesgos": RiskMatrixVariables(
        company_name="Aventura Andina SAS",
        scope="Rafting en el río Suárez y canopy en el cañón.",
        methodology="Matriz 3x3: probabilidad (Baja/Media/Alta) × severidad (Leve/Moderada/Grave).",
        risks=[
            RiskEntry(
                activity="Rafting",
                hazard="Volcamiento de balsa",
                risk_description="Caída al agua con riesgo de ahogamiento o golpes.",
                affected="Turistas y guías",
                probability="Media",
                severity="Grave",
                risk_level="Alto",
                existing_controls="Chalecos y cascos certificados; guía por balsa.",
                proposed_actions="Briefing obligatorio; verificación de equipos pre-salida.",
                responsible="Coordinador de operaciones",
                residual_risk="Medio",
            ),
            RiskEntry(
                activity="Canopy",
                hazard="Falla de línea o arnés",
                risk_description="Caída desde altura.",
                affected="Turistas",
                probability="Baja",
                severity="Grave",
                risk_level="Medio",
                existing_controls="Inspección diaria de líneas y arneses.",
                proposed_actions="Registro de mantenimiento y doble anclaje.",
                responsible="Técnico de equipos",
                residual_risk="Bajo",
            ),
        ],
        opportunities=[
            "Certificar a los guías en rescate acuático.",
            "Implementar registro digital de inspecciones.",
        ],
    ),
    "plan_emergencias": EmergencyPlanVariables(
        company_name="Aventura Andina SAS",
        scope="Rafting y canopy en Santander.",
        general_objective="Responder de forma oportuna y coordinada ante emergencias.",
        emergency_scenarios=[
            EmergencyScenario(
                scenario="Volcamiento de balsa",
                activity="Rafting",
                response_steps="Activar rescate acuático, recuento de personas, primeros auxilios.",
                responsible="Guía líder",
                resources="Cuerdas de rescate, botiquín, radio.",
            ),
            EmergencyScenario(
                scenario="Caída en canopy",
                activity="Canopy",
                response_steps="Detener operación, asegurar a la persona, evacuar y llamar 123.",
                responsible="Técnico de equipos",
                resources="Kit de rescate vertical, camilla.",
            ),
        ],
        communication_protocol="Cadena de notificación: guía → coordinador → línea 123 → ARL.",
        emergency_contacts=["Bomberos 119", "Ambulancia 125", "Línea de emergencias 123"],
        evacuation_resources="Rutas señalizadas hasta el punto de embarque y vía principal.",
        external_coordination="Hospital regional, Defensa Civil y Cruz Roja seccional.",
        training_drills="Simulacro semestral por escenario.",
        review_frequency="Revisión anual y tras cada incidente mayor.",
        legal_representative="María Gómez",
        approval_date="2026-06-18",
    ),
    "gestion_incidentes": IncidentManagementVariables(
        company_name="Aventura Andina SAS",
        scope="Todas las actividades de turismo de aventura ofrecidas.",
        objective="Gestionar incidentes para atenderlos y prevenir su recurrencia.",
        incident_classification=[
            "Casi-accidente (sin lesiones ni daños)",
            "Incidente (lesiones leves o daños menores)",
            "Accidente (lesiones graves o daños mayores)",
        ],
        procedure_steps=[
            "Reportar el evento al coordinador en el menor tiempo posible.",
            "Registrar el evento en el formato de reporte de incidentes.",
            "Atender y asegurar a las personas afectadas.",
            "Investigar la causa raíz.",
            "Definir e implementar acciones correctivas.",
            "Verificar la eficacia de las acciones.",
            "Documentar lecciones aprendidas.",
        ],
        responsible="Coordinador HSE",
        corrective_actions_process="Análisis de causa raíz, plan de acción y verificación de cierre.",
        record_retention="Registros conservados 5 años en archivo digital.",
        review_frequency="Revisión anual del procedimiento.",
        legal_representative="María Gómez",
        approval_date="2026-06-18",
    ),
    "manual_perfiles_cargos": ProfilesManualVariables(
        company_name="Aventura Andina SAS",
        objective="Definir el perfil, las funciones y los requisitos de cada cargo.",
        scope="Todo el personal directivo y operativo de la empresa.",
        org_structure=(
            "Nivel directivo: Gerente. Nivel operativo: Coordinador de operaciones, "
            "Técnico de equipos y Guías."
        ),
        role_profiles=[
            RoleProfile(
                role="Gerente",
                level="Directivo",
                purpose="Dirigir la organización y asignar recursos al SGS.",
                functions=[
                    "Aprobar la política y los objetivos de seguridad",
                    "Asignar los recursos del sistema de gestión",
                ],
                requirements="Profesional con 3 años de experiencia en turismo.",
                reports_to="Junta de socios",
            ),
            RoleProfile(
                role="Guía de rafting",
                level="Operativo",
                purpose="Conducir la actividad con seguridad.",
                functions=[
                    "Realizar el briefing de seguridad",
                    "Inspeccionar el equipo antes de cada salida",
                ],
                requirements="Certificado en rescate acuático y primeros auxilios.",
                reports_to="Coordinador de operaciones",
            ),
        ],
    ),
    "comunicacion_participacion_consulta": CommunicationProcedureVariables(
        company_name="Aventura Andina SAS",
        objective="Regular la comunicación, participación y consulta del SGS.",
        scope="Todo el personal y las partes interesadas.",
        responsibles="Gerente y Coordinador de operaciones.",
        communication_matrix=[
            CommunicationEntry(
                topic="Política de seguridad",
                method="Inducción y cartelera",
                channel="Presencial / física",
                audience="Todo el personal",
                frequency="Anual y al ingreso",
            ),
            CommunicationEntry(
                topic="Procedimientos operativos",
                method="Reunión operativa",
                channel="Presencial",
                audience="Guías y coordinación",
                frequency="Mensual",
            ),
        ],
        participation="Reuniones mensuales de seguridad con todo el equipo.",
        consultation="Consulta previa a cambios de rutas o equipos.",
        representation="Un guía representa al personal en asuntos de seguridad.",
        performance_evaluation="Encuesta anual y seguimiento de acuerdos.",
        records="Actas de reunión y registros de asistencia.",
    ),
    "manual_inspeccion_equipos": EquipmentManualVariables(
        company_name="Aventura Andina SAS",
        objective="Controlar la inspección y el mantenimiento del equipo de seguridad.",
        scope="Todo el equipo usado en las actividades de aventura.",
        role_obligations=(
            "Gerencia aprueba el programa; el Coordinador lo programa; "
            "los Guías inspeccionan antes de cada uso."
        ),
        equipment_items=[
            EquipmentInspectionItem(
                activity="Rafting",
                equipment="Balsas, remos, chalecos y cascos",
                state="Ok",
                inspection_type="previa a uso",
                frequency="Cada salida",
            ),
            EquipmentInspectionItem(
                activity="Canopy",
                equipment="Líneas, arneses y poleas",
                state="Ok",
                inspection_type="periódica trimestral",
                frequency="Trimestral",
            ),
        ],
        maintenance_types=[
            "Revisión previa a cada uso",
            "Revisión especial (tras un evento)",
            "Revisión periódica trimestral",
        ],
    ),
}


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for document_type in supported_types():
        spec = get_spec(document_type)
        assert spec is not None
        variables = _SAMPLES[document_type]
        result = spec.generator.generate(variables)
        out = OUT_DIR / f"{document_type}.{spec.generator.engine}"
        out.write_bytes(result.content)
        flag = "OK" if not result.pending_fields else f"PENDIENTES: {result.pending_fields}"
        print(f"  [{document_type}] -> {out.relative_to(ROOT)}  ({flag})")
    print(f"\nMuestras generadas en {OUT_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
