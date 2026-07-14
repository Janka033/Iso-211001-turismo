"""Modelos Pydantic del módulo salidas (operación de terreno + registro público).

El registro del turista llega por el endpoint público (link/QR): los datos de
salud son SENSIBLES (Ley 1581/2012) y viajan a ``participante_salud``, nunca
mezclados con la identidad. Las declaraciones del formulario son obligatorias:
sin ellas el registro no es válido.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator

SalidaStatus = Literal["programada", "en_curso", "finalizada", "cancelada"]
EventType = Literal[
    "check_in",
    "inicio_recorrido",
    "punto_control",
    "novedad",
    "induccion",
    "emergencia_activada",
    "pon_paso",
    "emergencia_cerrada",
    "fin_recorrido",
]
CheckPhase = Literal["pre", "post"]
# Clasificación del molde MinCIT: B = buen estado, C = cambio de equipo,
# MC = mantenimiento correctivo.
CheckStatus = Literal["B", "C", "MC"]
IncidentStatus = Literal["borrador", "en_investigacion", "cerrado"]
DocumentType = Literal["CC", "TI", "CE", "PA"]
BloodType = Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

# Respuesta a un campo condicional de la ficha técnica (sabe_nadar, peso_kg…).
ActivityAnswer = str | int | float | bool


# ---------------------------------------------------------------------------
# Salidas (staff autenticado)
# ---------------------------------------------------------------------------


class SalidaCreate(BaseModel):
    activity_profile_id: str
    route_name: str | None = Field(default=None, max_length=200)
    scheduled_start: datetime
    capacity: int = Field(gt=0, le=200)


class SalidaOut(BaseModel):
    id: str
    activity_profile_id: str
    route_name: str | None = None
    scheduled_start: str
    capacity: int
    status: str
    qr_token_expires_at: str
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str


class SalidaCreatedOut(SalidaOut):
    """Respuesta de creación: la ÚNICA vez que el token viaja en claro.

    En DB solo queda su sha256 (``qr_token_hash``); si se pierde el token se
    regenera la salida, no se recupera.
    """

    public_token: str
    public_registration_path: str


class SalidaStatusUpdate(BaseModel):
    status: Literal["en_curso", "finalizada", "cancelada"]


class GuiaAssignIn(BaseModel):
    guia_user_id: str
    is_lead: bool = False


class GuiaOut(BaseModel):
    guia_user_id: str
    is_lead: bool


class ActivityProfileOut(BaseModel):
    """Ficha técnica resumida para que recepción elija actividad al crear
    una salida. Solo se listan las activas."""

    id: str
    name: str
    activity_type: str
    min_age: int | None = None
    max_age: int | None = None
    difficulty: str | None = None
    duration_minutes: int | None = None
    location: str | None = None


# ---------------------------------------------------------------------------
# Registro público del turista (link/QR, sin auth)
# ---------------------------------------------------------------------------


class EmergencyContact(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    parentesco: str = Field(min_length=1, max_length=60)
    telefono: str = Field(min_length=7, max_length=20)


class GuardianIn(BaseModel):
    """Acudiente de un menor de edad: es quien firma el consentimiento."""

    nombre: str = Field(min_length=1, max_length=120)
    documento: str = Field(min_length=3, max_length=30)
    parentesco: str = Field(min_length=1, max_length=60)
    telefono: str = Field(min_length=7, max_length=20)


class MedicalConditions(BaseModel):
    cardiaca: bool = False
    respiratoria: bool = False
    diabetes: bool = False
    epilepsia: bool = False
    embarazo: bool = False
    cirugia_reciente: bool = False
    otras: str | None = Field(default=None, max_length=500)

    def any_condition(self) -> bool:
        return bool(
            self.cardiaca
            or self.respiratoria
            or self.diabetes
            or self.epilepsia
            or self.embarazo
            or self.cirugia_reciente
            or (self.otras or "").strip()
        )


class RegistroTuristaIn(BaseModel):
    # Sección A — identificación
    document_type: DocumentType
    document_number: str = Field(min_length=3, max_length=30)
    full_name: str = Field(min_length=3, max_length=160)
    birth_date: date
    nationality: str | None = Field(default=None, max_length=60)
    phone: str = Field(min_length=7, max_length=20)
    email: EmailStr
    guardian: GuardianIn | None = None
    emergency_contacts: list[EmergencyContact] = Field(min_length=1, max_length=2)

    # Sección B — salud (datos sensibles → participante_salud)
    eps: str = Field(min_length=2, max_length=120)
    arl: str | None = Field(default=None, max_length=120)
    blood_type: BloodType
    allergies: str = Field(min_length=2, max_length=500)  # "Ninguna" explícito
    medical_conditions: MedicalConditions
    current_medications: str | None = Field(default=None, max_length=500)
    activity_specific: dict[str, ActivityAnswer] = Field(default_factory=dict)

    # Sección D — declaraciones (los checks del formulario; la firma del
    # consentimiento llega en la fase siguiente)
    declares_truthful: bool
    accepts_data_processing: bool
    received_risk_info: bool
    declares_sober: bool

    @model_validator(mode="after")
    def _declaraciones_obligatorias(self) -> "RegistroTuristaIn":
        if not (
            self.declares_truthful
            and self.accepts_data_processing
            and self.received_risk_info
            and self.declares_sober
        ):
            raise ValueError(
                "Todas las declaraciones son obligatorias para registrarse."
            )
        return self


class RegistroTuristaOut(BaseModel):
    participante_id: str
    salida_id: str
    status: str


# ---------------------------------------------------------------------------
# Consentimiento informado (texto versionado + firma digital del turista)
# ---------------------------------------------------------------------------


class ConsentTemplateOut(BaseModel):
    id: str
    version: int
    body_md: str
    effective_from: str


class ConsentTemplateCreate(BaseModel):
    """Nueva versión del texto (solo gerente). Nunca se edita una versión
    publicada: cada cambio es una fila nueva."""

    body_md: str = Field(min_length=200, max_length=50_000)


class PublicConsentOut(BaseModel):
    """Lo que el turista lee antes de firmar."""

    activity_name: str | None = None
    template_version: int
    body_md: str


class FirmaConsentimientoIn(BaseModel):
    participante_id: str
    accepted_privacy: bool
    accepted_risk_info: bool
    # Trazo de la firma como PNG en base64 (con o sin prefijo data-URL).
    signature_png_base64: str = Field(min_length=100, max_length=500_000)

    @model_validator(mode="after")
    def _aceptaciones_obligatorias(self) -> "FirmaConsentimientoIn":
        if not (self.accepted_privacy and self.accepted_risk_info):
            raise ValueError(
                "Debe aceptar el tratamiento de datos y la información de "
                "riesgos para firmar."
            )
        return self


class FirmaConsentimientoOut(BaseModel):
    consentimiento_id: str
    participante_id: str
    template_version: int
    signed_by_guardian: bool
    signed_at: str
    participante_status: str


class EvidenciaOut(BaseModel):
    """Ruta en el bucket privado, para referenciar en evidence_paths de
    checks e incidentes."""

    storage_path: str


# ---------------------------------------------------------------------------
# Manifiesto de ruta
# ---------------------------------------------------------------------------


class SaludOut(BaseModel):
    eps: str
    arl: str | None = None
    blood_type: str
    allergies: str
    medical_conditions: MedicalConditions
    current_medications: str | None = None
    activity_specific: dict[str, ActivityAnswer] = Field(default_factory=dict)


class ParticipanteOut(BaseModel):
    id: str
    full_name: str
    document_type: str
    document_number: str
    phone: str
    status: str
    has_medical_alert: bool
    guardian: GuardianIn | None = None
    emergency_contacts: list[EmergencyContact]
    # None cuando el rol no puede ver salud (recepcionista) — lo decide RLS.
    salud: SaludOut | None = None


class ManifiestoOut(BaseModel):
    salida: SalidaOut
    participantes: list[ParticipanteOut]


# ---------------------------------------------------------------------------
# Sync de eventos de terreno (app de guías, offline-first)
# ---------------------------------------------------------------------------


class EventoIn(BaseModel):
    # El id lo genera el DISPOSITIVO: reintentos de sync = inserts idempotentes.
    id: str = Field(min_length=32, max_length=40)
    event_type: EventType
    participante_id: str | None = None
    note: str | None = Field(default=None, max_length=2000)
    occurred_at: datetime


class EventosSyncIn(BaseModel):
    eventos: list[EventoIn] = Field(min_length=1, max_length=500)


class EventosSyncOut(BaseModel):
    received: int
    inserted: int


# ---------------------------------------------------------------------------
# Revisión pre/post operacional de equipos (molde MinCIT 8.1, offline-first)
# ---------------------------------------------------------------------------


class EquipmentCheckIn(BaseModel):
    # El id lo genera el DISPOSITIVO: reintentos de sync = inserts idempotentes.
    id: str = Field(min_length=32, max_length=40)
    item_id: str
    phase: CheckPhase
    status: CheckStatus
    quantity: int | None = Field(default=None, gt=0, le=10_000)
    note: str | None = Field(default=None, max_length=2000)
    evidence_paths: list[str] = Field(default_factory=list, max_length=20)
    checked_at: datetime


class EquipmentChecksSyncIn(BaseModel):
    checks: list[EquipmentCheckIn] = Field(min_length=1, max_length=500)


class EquipmentChecksSyncOut(BaseModel):
    received: int
    inserted: int


class EquipmentCheckOut(BaseModel):
    id: str
    item_id: str
    phase: str
    status: str
    quantity: int | None = None
    note: str | None = None
    evidence_paths: list[str] = Field(default_factory=list)
    checked_by: str
    checked_at: str


# ---------------------------------------------------------------------------
# Registro e investigación de incidentes (molde MinCIT 8.3)
# ---------------------------------------------------------------------------


class PersonRef(BaseModel):
    nombre: str = Field(min_length=1, max_length=160)
    telefono: str | None = Field(default=None, max_length=20)


class InvolvedParticipant(PersonRef):
    participante_id: str | None = None


class WitnessRef(PersonRef):
    version: str | None = Field(default=None, max_length=4000)


class InvestigatorRef(BaseModel):
    nombre: str = Field(min_length=1, max_length=160)
    cargo: str = Field(min_length=1, max_length=120)


class IncidentCreate(BaseModel):
    """Reporte inicial en terreno: lo mínimo que el guía sabe en caliente.

    El servidor pre-llena actividad y guía líder desde la salida; la
    investigación (causas, plan de acción…) llega después vía PATCH.
    """

    occurred_at: datetime
    location: str = Field(min_length=2, max_length=300)
    circumstances: str = Field(min_length=10, max_length=8000)
    involved_participants: list[InvolvedParticipant] = Field(
        default_factory=list, max_length=50
    )
    emergency_response: str | None = Field(default=None, max_length=8000)
    evidence_paths: list[str] = Field(default_factory=list, max_length=30)


class IncidentUpdate(BaseModel):
    """Campos de la investigación (molde 8.3); todos opcionales, se
    completan por etapas. El cambio de estado viaja aparte para que las
    transiciones sean explícitas."""

    status: IncidentStatus | None = None
    location: str | None = Field(default=None, min_length=2, max_length=300)
    lead_guide_name: str | None = Field(default=None, max_length=160)
    lead_guide_phone: str | None = Field(default=None, max_length=20)
    other_staff: list[PersonRef] | None = None
    involved_participants: list[InvolvedParticipant] | None = None
    witnesses: list[WitnessRef] | None = None
    environmental_conditions: str | None = Field(default=None, max_length=4000)
    equipment_state: str | None = Field(default=None, max_length=4000)
    circumstances: str | None = Field(default=None, min_length=10, max_length=8000)
    probable_causes: str | None = Field(default=None, max_length=8000)
    emergency_response: str | None = Field(default=None, max_length=8000)
    consequences: str | None = Field(default=None, max_length=8000)
    action_plan: str | None = Field(default=None, max_length=8000)
    info_source: str | None = Field(default=None, max_length=500)
    risk_was_identified: bool | None = None
    investigators: list[InvestigatorRef] | None = None
    observations: str | None = Field(default=None, max_length=4000)
    evidence_paths: list[str] | None = Field(default=None, max_length=30)


class IncidentOut(BaseModel):
    id: str
    salida_id: str | None = None
    activity_type: str
    occurred_at: str
    location: str
    status: str
    lead_guide_name: str | None = None
    lead_guide_phone: str | None = None
    other_staff: list[PersonRef] = Field(default_factory=list)
    involved_participants: list[InvolvedParticipant] = Field(default_factory=list)
    witnesses: list[WitnessRef] = Field(default_factory=list)
    environmental_conditions: str | None = None
    equipment_state: str | None = None
    circumstances: str | None = None
    probable_causes: str | None = None
    emergency_response: str | None = None
    consequences: str | None = None
    action_plan: str | None = None
    info_source: str | None = None
    risk_was_identified: bool | None = None
    investigators: list[InvestigatorRef] = Field(default_factory=list)
    observations: str | None = None
    evidence_paths: list[str] = Field(default_factory=list)
    reported_by: str
    created_at: str
    updated_at: str
