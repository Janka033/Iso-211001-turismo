"""Pipeline E2E contra el backend local: onboarding rico -> 7 docs -> evaluación.

Uso: py scripts/e2e_pipeline.py <email> <password> <fase> [tipo1,tipo2,...]
  fase: load | generate | evaluate | all
  El 4to argumento (opcional) limita generate/evaluate a esos document_type
  (ahorra cuota Gemini al iterar un solo documento).

Lee SUPABASE_URL/ANON_KEY de frontend/.env.local. El PUT /onboarding no gasta
IA; generate y evaluate consumen ~1 request Gemini por documento.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
API = "http://localhost:8000"

DOC_TYPES = [
    "politica_seguridad",
    "matriz_riesgos",
    "plan_emergencias",
    "gestion_incidentes",
    "manual_perfiles_cargos",
    "comunicacion_participacion_consulta",
    "manual_inspeccion_equipos",
]

# ---------------------------------------------------------------------------
# Datos operativos de la empresa de prueba (nivel auditoría, sin vacíos).
# ---------------------------------------------------------------------------

ONBOARDING = {
    "activities": ["rafting"],
    "main_region": "Santander",
    "locations": [
        "Río Fonce, tramo Puente Viejo - Playa El Gallineral (San Gil)",
        "Sede operativa: Calle 12 # 9-45, San Gil, Santander",
    ],
    "scope": (
        "Operación de rafting recreativo en el río Fonce (clase II-III), tramo "
        "Puente Viejo a Playa El Gallineral (11 km, 2.5 horas de navegación), "
        "para grupos de turistas nacionales y extranjeros entre 12 y 65 años. "
        "Incluye transporte terrestre desde la sede en San Gil hasta el punto de "
        "embarque, charla de seguridad obligatoria, equipamiento completo y "
        "acompañamiento de guías certificados en cada balsa. Operamos de "
        "miércoles a domingo, con 3 salidas diarias (8:00, 10:30 y 14:00) y "
        "máximo 4 balsas por salida."
    ),
    "certified_guides": (
        "6 guías con certificación de la Federación Internacional de Rafting "
        "(IRF) nivel Guide clase II-III y curso de primeros auxilios en áreas "
        "remotas (WFA) vigente"
    ),
    "staff_roles": {
        "gerente general": "1",
        "coordinador de operaciones y seguridad": "1",
        "guia de rafting": "6",
        "auxiliar logistico y conductor": "2",
        "recepcionista y ventas": "1",
    },
    "legal_representative": "Juan Carlos Guevara Perdomo",
    "nit": "901.456.789-1",
    "rnt_status": "Vigente",
    "rnt_number": "87654",
    "emergency_contacts": [
        "Bomberos San Gil: 119 / (607) 724 2222",
        "Cruz Roja Santander: 132",
        "Defensa Civil San Gil: 144",
        "Policía Nacional: 123",
        "ARL Sura línea de emergencias: 01 8000 511 414",
    ],
    "brigada_emergencias": (
        "Sí. Brigada de emergencias conformada por 4 personas: el coordinador de "
        "operaciones y seguridad la lidera (Carlos Rojas, 310 555 0101), dos "
        "guías brigadistas con curso de rescate en aguas rápidas R3 (Andrés "
        "Prada, 310 555 0102 y Laura Mejía, 310 555 0103) y un auxiliar "
        "logístico brigadista de primeros auxilios (Pedro Silva, 310 555 0104). "
        "Se reúne mensualmente y lidera los simulacros semestrales."
    ),
    "capacitaciones_personal_emergencias": [
        "Primeros auxilios en áreas remotas (WFA) - todos los guías, renovación anual",
        "Rescate en aguas rápidas R3 - 4 de 6 guías, certificación Rescue 3 International",
        "RCP y manejo de DEA - todo el personal operativo, semestral",
        "Manejo de incendios con extintores - todo el personal, anual con Bomberos San Gil",
        "Autorrescate y rescate de nadador en río - todos los guías, entrenamiento trimestral",
    ],
    "equipos_emergencia": [
        "Botiquín tipo B en cada balsa y botiquín central tipo A en la sede",
        "Camilla rígida con inmovilizadores de cabeza y cuello (punto intermedio del tramo)",
        "2 cuerdas de rescate (throw bags) de 20 m por balsa",
        "Radios VHF impermeables (1 por guía + base en sede) canal 16",
        "Teléfono satelital para el tramo sin señal celular",
        "Kit de inmovilización: férulas moldeables y collar cervical",
        "Oxígeno portátil en el vehículo de apoyo",
    ],
    "organismos_apoyo": [
        "Bomberos San Gil: 119 - convenio de apoyo en rescate acuático",
        "Cruz Roja seccional Santander: 132",
        "Defensa Civil San Gil: 144 - apoyo en crecientes y evacuaciones",
        "Hospital Regional de San Gil: (607) 724 5555",
    ],
    "hospital_cercano": (
        "Hospital Regional de San Gil (ESE), Carrera 5 # 9-102, San Gil. A 15 "
        "minutos del punto de desembarque y 20 minutos de la sede. Nivel II con "
        "urgencias 24 horas."
    ),
    "vehiculos_evacuacion": (
        "Camioneta 4x4 Toyota Hilux (placa XYZ-123) equipada con camilla, "
        "conducida por el auxiliar logístico de turno (Pedro Silva, 310 555 "
        "0104), estacionada en el punto intermedio durante cada salida. Bus de "
        "transporte de pasajeros (placa ABC-456) disponible en el punto de "
        "desembarque como segundo vehículo."
    ),
    "existing_controls": (
        "Inspección visual diaria de balsas, remos, chalecos y cascos antes de "
        "cada salida con lista de chequeo firmada; charla de seguridad "
        "obligatoria de 20 minutos con demostración de posición de nado "
        "defensivo; verificación del nivel del río con la escala del puente y "
        "cierre de operación por encima de 1.8 m o tormenta eléctrica; máximo 8 "
        "pasajeros por balsa más guía; ratio de 1 guía de seguridad en kayak "
        "por cada 4 balsas; registro de aptitud y restricciones de salud de "
        "cada participante antes del embarque; prohibición de alcohol 12 horas "
        "antes de la actividad."
    ),
    "management_commitment": (
        "La gerencia general asume el compromiso público de garantizar la "
        "seguridad de participantes y trabajadores como prioridad sobre "
        "cualquier objetivo comercial: asigna presupuesto anual específico para "
        "reposición de equipos y capacitación (8% de los ingresos), preside la "
        "revisión trimestral del sistema de gestión de seguridad, participa en "
        "los simulacros semestrales y garantiza que ninguna salida opere sin "
        "cumplir los controles establecidos, incluida la potestad de cualquier "
        "guía de cancelar la actividad por condiciones inseguras sin "
        "penalización."
    ),
    # --- Granularidad por documento ---
    "safety_objectives": [
        "Reducir los incidentes operativos reportados en 20% frente a la línea base de 2025 (de 10 a 8 o menos) a 31 de diciembre de 2026, medido en el registro de incidentes",
        "Lograr y mantener el 100% de los guías con certificación IRF y WFA vigentes durante todo 2026, verificado en la matriz de competencias cada trimestre",
        "Ejecutar 2 simulacros de emergencia (volcamiento con rescate acuático y evacuación médica) en 2026, uno por semestre, con informe de lecciones aprendidas a los 15 días",
    ],
    "approval_date": "15 de enero de 2026",
    "communication_channels": [
        "Cartelera física en la recepción de la sede",
        "Inducción obligatoria a todo empleado nuevo",
        "Grupo de WhatsApp operativo del equipo",
        "Página web (sección Seguridad)",
        "Briefing de seguridad a clientes antes de cada salida",
    ],
    "activity_step_breakdown": (
        "1) Recepción y registro en sede: peligro = información de salud omitida "
        "por el participante; riesgo = participante con contraindicación médica "
        "en el río. 2) Transporte al embarque (25 min por vía terciaria): "
        "peligro = vía estrecha y húmeda; riesgo = accidente vehicular. 3) "
        "Charla de seguridad y equipamiento: peligro = talla incorrecta de "
        "chaleco o casco; riesgo = pérdida del equipo en el agua y ahogamiento. "
        "4) Embarque y navegación tramo clase II: peligro = corriente y rocas "
        "sumergidas; riesgo = caída al agua, golpe contra roca. 5) Rápido 'La "
        "Lavadora' clase III: peligro = hidráulico recirculante; riesgo = "
        "atrapamiento y ahogamiento; peligro = volcamiento de balsa; riesgo = "
        "golpes múltiples e hipotermia. 6) Zona de nado libre: peligro = "
        "sobrestimación de capacidades del participante; riesgo = agotamiento y "
        "ahogamiento. 7) Desembarque y cierre: peligro = piso rocoso húmedo; "
        "riesgo = caída y esguince."
    ),
    "risk_factors": (
        "Ambientales: crecientes súbitas del Fonce por lluvias aguas arriba, "
        "tormentas eléctricas, troncos y sedimentos tras lluvias, temporada de "
        "lluvias abril-mayo y octubre-noviembre. Humanos: participantes que "
        "ocultan condiciones médicas o consumo de alcohol, pánico en rápidos, "
        "fatiga de guías en temporada alta, terceros (pescadores y bañistas) en "
        "el tramo. De materiales/equipos: desgaste de balsas por abrasión, "
        "pérdida de presión de cámaras, costuras de chalecos vencidas, cascos "
        "fisurados, cuerdas con más de 5 años. Organizativos: rotación de "
        "personal en temporada alta, fallas de comunicación radio-base, presión "
        "comercial por operar con río alto, briefing incompleto por afán."
    ),
    "business_risks": [
        "Cancelaciones masivas por temporada de lluvias prolongada (abril-mayo)",
        "Daño reputacional por un accidente publicado en redes sociales",
        "Dependencia de un único proveedor de balsas y repuestos (importados)",
        "Pérdida del RNT o de permisos de operación por incumplimientos",
        "Concentración de ventas en fines de semana y puentes festivos",
    ],
    "opportunities": [
        "Certificación NTC-ISO 21101 como diferencial comercial frente a operadores informales; plan: certificar en 2026 con organismo acreditado ONAC",
        "Convenio con agencias de Bucaramanga y Bogotá para grupos corporativos; plan: paquete corporativo con charla de seguridad extendida",
        "Formación de 2 guías adicionales como instructores IRF; plan: becas internas 2026",
        "Turismo escolar con protocolo reforzado de menores; plan: producto 'Fonce Educativo' con ratio 1 guía por 4 menores",
    ],
    "equipment_maintenance": (
        "Balsas autovaciables (4 unidades NRS de 14 pies): inspección visual "
        "diaria antes de cada salida (presión, abrasiones, válvulas, líneas "
        "perimetrales) y revisión técnica mensual con prueba de presión por 24 "
        "horas; reparación de parches solo por el coordinador; reposición a los "
        "6 años. Remos (40): inspección visual diaria de pala y mango; baja "
        "inmediata si hay fisura. Chalecos salvavidas (50, tipo V rescate): "
        "inspección visual diaria de costuras, hebillas y flotabilidad; revisión "
        "técnica trimestral con prueba de flotación; baja a los 4 años o tras "
        "impacto fuerte. Cascos (50): inspección visual diaria de carcasa y "
        "correas; baja inmediata tras impacto o fisura; reposición a los 5 "
        "años. Cuerdas de rescate (10 throw bags): inspección visual semanal y "
        "lavado mensual; revisión técnica semestral metro a metro; baja a los 5 "
        "años o tras carga de rescate real. Todo queda en la bitácora de "
        "equipos con firma del inspector."
    ),
    "communication_matrix": (
        "Política y objetivos de seguridad — a todo el personal — inducción y "
        "cartelera — al ingreso y cada actualización. Briefing de seguridad "
        "(posición de nado, comandos, qué hacer al caer) — a clientes — verbal "
        "con demostración — antes de cada salida. Estado del río y decisión de "
        "operar — del coordinador a guías y recepción — grupo de WhatsApp "
        "operativo — diario 6:30 am. Incidentes y lecciones aprendidas — de "
        "guías a coordinador y gerencia — formato de reporte + reunión — dentro "
        "de las 24 horas del evento. Cambios de procedimientos — de gerencia a "
        "todo el personal — reunión mensual de seguridad — mensual. Resultados "
        "de simulacros — de la brigada a todo el personal — informe escrito — "
        "semestral."
    ),
    "participation_consultation": (
        "Reunión mensual de seguridad con todo el equipo operativo (primer "
        "lunes, acta firmada) donde los guías proponen y votan cambios a los "
        "procedimientos; comité de seguridad trimestral (gerente, coordinador y "
        "un guía elegido por sus pares como representante) que revisa "
        "indicadores e incidentes; buzón físico y digital de sugerencias de "
        "seguridad revisado cada semana; evaluación anónima post-simulacro; y "
        "consulta obligatoria a los guías antes de cambiar rutas, ratios o "
        "equipos."
    ),
    "incident_classification": [
        "Incidente (casi accidente): evento sin lesión ni daño, p. ej. caída al agua con recuperación inmediata, roce de balsa con roca",
        "Accidente leve: lesión atendida con primeros auxilios en sitio, sin evacuación (cortaduras, contusiones)",
        "Accidente grave: lesión que requiere evacuación y atención hospitalaria (fracturas, casi ahogamiento)",
        "Accidente crítico/mortal: fatalidad o lesión con riesgo vital; activa el plan de crisis y notificación a autoridades",
    ],
    "incident_report_fields": [
        "Fecha, hora y lugar exacto (tramo/rápido) del evento",
        "Actividad y número de salida",
        "Personas involucradas (nombre, documento, rol o condición de participante)",
        "Descripción cronológica de los hechos",
        "Clasificación (incidente / accidente leve / grave / crítico)",
        "Atención brindada en sitio y por quién",
        "Evacuación y centro médico receptor si aplica",
        "Causa probable y factores contribuyentes",
        "Acciones correctivas propuestas y responsable",
        "Nombre y firma de quien reporta y del coordinador",
    ],
    # --- Parte B: rafting ---
    "activity_fields": {
        "equipo_rafting": (
            "4 balsas autovaciables NRS de 14 pies (8 pasajeros + guía), 40 "
            "remos de polipropileno, 50 chalecos tipo V de rescate, 50 cascos "
            "de agua certificados CE EN 1385, 10 cuerdas de rescate de 20 m, 1 "
            "kayak de seguridad. Inspección diaria con lista de chequeo y "
            "bitácora firmada; revisión técnica mensual."
        ),
        "competencias_rafting": (
            "Guías con certificación IRF Guide clase II-III vigente, WFA, "
            "rescate R3 (4 de 6), mínimo 200 horas de río documentadas en el "
            "Fonce y recertificación anual interna con evaluación práctica."
        ),
        "emergencias_rafting": (
            "Protocolo de volcamiento (recuento inmediato, rescate de nadadores "
            "por cuerda o kayak), protocolo de atrapamiento de pie (parada de "
            "emergencia de todas las balsas), evacuación por los 3 puntos de "
            "salida del tramo hacia la vía, comunicación por radio VHF canal 16 "
            "con la base y teléfono satelital en zona sin señal."
        ),
        "riesgos_rafting": (
            "Volcamiento en 'La Lavadora' (clase III), atrapamiento en "
            "hidráulico, golpe contra roca, atrapamiento de pie en el lecho, "
            "hipotermia en temporada de lluvias, creciente súbita del Fonce, "
            "colisión entre balsas, caída en el embarque/desembarque."
        ),
        "seguimiento_rafting": (
            "Bitácora diaria de inspección de equipos firmada, registro de "
            "nivel del río en cada salida, registro de incidentes con revisión "
            "mensual de tendencias, simulacro semestral evaluado, auditoría "
            "interna anual del procedimiento de rafting."
        ),
        "edades_permitidas_rafting": (
            "Mínimo 12 años (con autorización escrita del acudiente y chaleco "
            "de talla juvenil) y máximo 65 años; mayores de 60 con declaración "
            "médica de aptitud."
        ),
        "restricciones_salud_rafting": (
            "No pueden participar: embarazadas, personas con cirugías en los "
            "últimos 3 meses, afecciones cardiacas no controladas, epilepsia no "
            "controlada, fracturas recientes, o bajo efectos de alcohol o "
            "sustancias psicoactivas. Hipertensión y asma controladas requieren "
            "declararlo y portar su medicamento en bolsa seca."
        ),
        "ruta_descripcion_rafting": (
            "Tramo Puente Viejo → Playa El Gallineral, río Fonce: 11 km, "
            "travesía de ida (retorno terrestre), clase II-III, dificultad "
            "media, 2.5 horas de navegación con parada de descanso en Playa La "
            "Antigua (km 6)."
        ),
        "grupo_participantes_rafting": (
            "Mínimo 4 y máximo 32 participantes por salida (8 por balsa, hasta "
            "4 balsas), siempre con 1 guía certificado por balsa y 1 kayak de "
            "seguridad por salida."
        ),
        "competencias_requeridas_participante_rafting": (
            "Saber flotar (no se exige nadar con técnica), condición física "
            "básica para remar 2.5 horas, y aprobar la charla de seguridad con "
            "demostración de la posición de nado defensivo."
        ),
        "equipos_operacion_rafting": (
            "Balsa, remo, chaleco tipo V, casco EN 1385, cabo de rescate por "
            "balsa, silbato del guía, bolsa seca para medicamentos; traje de "
            "neopreno en temporada de aguas frías (nov-feb)."
        ),
        "equipos_rescate_rafting": (
            "10 throw bags de 20 m, kayak de seguridad con guía R3, camilla "
            "rígida con inmovilizadores en punto intermedio, botiquín tipo B "
            "por balsa, radios VHF, oxígeno portátil en vehículo de apoyo."
        ),
        "indumentaria_rafting": (
            "Participantes: traje de baño o licra, zapatos cerrados que se "
            "sujeten al pie (no chanclas), protector solar. Guías: uniforme "
            "institucional de secado rápido, chaleco de rescate con arnés de "
            "remolque, cuchillo de río y silbato."
        ),
        "seguro_contratado_rafting": (
            "Póliza de responsabilidad civil extracontractual No. RCE-2026-4587 "
            "con Seguros Sura (cobertura $800.000.000 COP) y póliza de "
            "accidentes personales para participantes No. AP-2026-1123 "
            "(cobertura médica hasta $50.000.000 COP por persona), vigentes "
            "hasta 31/12/2026."
        ),
        "politica_cancelacion_rafting": (
            "La operación se cancela sin costo para el cliente cuando: el nivel "
            "del río supera 1.8 m en la escala del Puente Viejo, hay tormenta "
            "eléctrica activa o pronóstico de creciente, o el guía líder lo "
            "determina por cualquier condición insegura. El cliente puede "
            "reprogramar dentro de 90 días o recibir reembolso del 100%."
        ),
    },
    "document_codes": {
        "politica_seguridad": "PO-01",
        "matriz_riesgos": "MT-04",
        "plan_emergencias": "PL-01",
        "gestion_incidentes": "PR-02",
        "manual_perfiles_cargos": "MA-02",
        "comunicacion_participacion_consulta": "PR-07",
        "manual_inspeccion_equipos": "MA-03",
    },
}


def env_local() -> dict[str, str]:
    out = {}
    for line in (ROOT / "frontend" / ".env.local").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def get_token(email: str, password: str) -> str:
    env = env_local()
    url = env["NEXT_PUBLIC_SUPABASE_URL"].rstrip("/")
    key = env["NEXT_PUBLIC_SUPABASE_ANON_KEY"]
    r = httpx.post(
        f"{url}/auth/v1/token?grant_type=password",
        json={"email": email, "password": password},
        headers={"apikey": key},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def phase_load(h: dict) -> None:
    r = httpx.put(f"{API}/onboarding", json=ONBOARDING, headers=h, timeout=60)
    print("PUT /onboarding ->", r.status_code)
    if r.status_code != 200:
        print(r.text[:2000])
        sys.exit(1)
    body = r.json()
    print(f"  completeness onboarding: {body['completeness']}% completed={body['completed']}")


def phase_generate(h: dict, only: list[str] | None = None) -> None:
    doc_types = [dt for dt in DOC_TYPES if not only or dt in only]
    results = []
    for dt in doc_types:
        t0 = time.time()
        try:
            r = httpx.post(
                f"{API}/generation/{dt}",
                json={"regenerate": True},
                headers=h,
                timeout=300,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  {dt}: EXCEPCION {exc}")
            results.append((dt, "EXC", None, None))
            continue
        dt_s = round(time.time() - t0, 1)
        if r.status_code in (200, 201):
            b = r.json()
            results.append((dt, "OK", b["completeness"], b["pending_fields"]))
            print(
                f"  {dt}: v{b['version']} completeness={b['completeness']}% "
                f"pendientes={len(b['pending_fields'])} ({dt_s}s)"
            )
            if b["pending_fields"]:
                print("    PENDIENTES:", b["pending_fields"])
        else:
            results.append((dt, str(r.status_code), None, None))
            print(f"  {dt}: HTTP {r.status_code} ({dt_s}s) {r.text[:300]}")
    ok = [x for x in results if x[1] == "OK"]
    full = [x for x in ok if x[2] == 100.0 and not x[3]]
    n = len(doc_types)
    print(
        f"RESUMEN GENERACION: {len(ok)}/{n} generados, "
        f"{len(full)}/{n} al 100% sin pendientes"
    )


def phase_evaluate(h: dict, only: list[str] | None = None) -> None:
    # IDs de los documentos vigentes: igual que el frontend, se leen de la
    # tabla `documents` vía PostgREST con el token del usuario (RLS activo).
    env = env_local()
    url = env["NEXT_PUBLIC_SUPABASE_URL"].rstrip("/")
    key = env["NEXT_PUBLIC_SUPABASE_ANON_KEY"]
    token = h["Authorization"].split(" ", 1)[1]
    rows = httpx.get(
        f"{url}/rest/v1/documents?select=id,document_type,version&order=version.desc",
        headers={"apikey": key, "Authorization": f"Bearer {token}"},
        timeout=30,
    ).json()
    latest: dict[str, dict] = {}
    for row in rows:
        latest.setdefault(row["document_type"], row)

    doc_types = [dt for dt in DOC_TYPES if not only or dt in only]
    scores = []
    for dt in doc_types:
        row = latest.get(dt)
        if not row:
            print(f"  {dt}: sin documento generado")
            continue
        t0 = time.time()
        r = httpx.post(
            f"{API}/quality/evaluations/{row['id']}", headers=h, timeout=300
        )
        dt_s = round(time.time() - t0, 1)
        if r.status_code == 201:
            b = r.json()
            ev = b["evaluation"]
            missing = ev["completeness"]["missing_required_fields"]
            scores.append((dt, b["score"], missing))
            print(
                f"  {dt} v{row['version']}: score={b['score']} "
                f"faltantes_oblig={len(missing)} coherente={ev['coherence']['coherent']} ({dt_s}s)"
            )
            if missing:
                print("    FALTAN:", missing)
        else:
            print(f"  {dt}: HTTP {r.status_code} ({dt_s}s) {r.text[:300]}")
    if scores:
        avg = sum(s for _, s, _ in scores) / len(scores)
        print(
            f"RESUMEN EVALUACION: {len(scores)}/{len(doc_types)} evaluados, "
            f"score promedio {avg:.1f}"
        )


def main() -> None:
    email, password, phase = sys.argv[1], sys.argv[2], sys.argv[3]
    only = sys.argv[4].split(",") if len(sys.argv) > 4 else None
    token = get_token(email, password)
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if phase in ("load", "all"):
        phase_load(h)
    if phase in ("generate", "all"):
        phase_generate(h, only)
    if phase in ("evaluate", "all"):
        phase_evaluate(h, only)


if __name__ == "__main__":
    main()
