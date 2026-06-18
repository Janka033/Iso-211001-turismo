"""Genera MUESTRAS de los 4 documentos núcleo del MVP con datos de ejemplo.

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
    EmergencyPlanVariables,
    EmergencyScenario,
    IncidentManagementVariables,
    RiskEntry,
    RiskMatrixVariables,
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
