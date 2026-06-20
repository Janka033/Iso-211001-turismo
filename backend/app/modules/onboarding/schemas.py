"""Modelos Pydantic del módulo onboarding.

``onboarding_data`` guarda los datos CRUDOS del cliente (lo que dijo), separados
de ``ai_outputs`` (lo que interpreta la IA). La generación los lee como contexto.
Todos los campos son opcionales: el onboarding es incremental y NUNCA inventa;
lo que falte queda vacío y el motor lo marca como ``[PENDIENTE]``.

Los campos llevan límites de tamaño (``max_length``) para acotar el payload:
defensa básica contra entradas abusivas.
"""

from pydantic import BaseModel, Field


class OnboardingPayload(BaseModel):
    """Datos operativos crudos capturados en el onboarding conversacional."""

    activities: list[str] = Field(
        default_factory=list,
        max_length=40,
        description="Actividades de turismo de aventura que ofrece la empresa.",
    )
    main_region: str | None = Field(
        default=None, max_length=120, description="Departamento o zona principal."
    )
    locations: list[str] = Field(
        default_factory=list,
        max_length=60,
        description="Ubicaciones específicas de operación (ríos, cañones, sedes).",
    )
    scope: str | None = Field(
        default=None, max_length=2000, description="Alcance operativo del cliente."
    )
    certified_guides: str | None = Field(
        default=None, max_length=120, description="Número o rango de guías certificados."
    )
    legal_representative: str | None = Field(
        default=None, max_length=200, description="Representante legal de la empresa."
    )
    nit: str | None = Field(default=None, max_length=40, description="NIT de la empresa.")
    rnt_status: str | None = Field(
        default=None,
        max_length=120,
        description="Estado del RNT (vigente / por renovar / no lo tiene).",
    )
    rnt_number: str | None = Field(
        default=None, max_length=60, description="Número de Registro Nacional de Turismo."
    )
    emergency_contacts: list[str] = Field(
        default_factory=list,
        max_length=40,
        description="Contactos de emergencia (bomberos, ambulancia, rescate, ARL).",
    )
    existing_controls: str | None = Field(
        default=None,
        max_length=2000,
        description="Medidas o controles de seguridad que ya aplica la empresa.",
    )
    management_commitment: str | None = Field(
        default=None,
        max_length=2000,
        description="Compromiso de la dirección con la seguridad.",
    )


class OnboardingState(BaseModel):
    """Estado del onboarding: datos + avance calculado."""

    data: OnboardingPayload
    completeness: float = Field(
        description="% de campos clave del onboarding con dato (0-100)."
    )
    completed: bool = Field(
        description="True si todos los campos clave tienen dato."
    )
