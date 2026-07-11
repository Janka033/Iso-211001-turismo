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
    "check_in", "inicio_recorrido", "punto_control", "novedad", "fin_recorrido"
]
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
# Manifiesto de ruta
# ---------------------------------------------------------------------------


class SaludOut(BaseModel):
    eps: str
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
