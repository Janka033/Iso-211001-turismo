"""Modelos Pydantic del módulo inventory (inventario operativo).

Los ítems tienen ``attributes`` flexibles por categoría (un equipo no tiene los
mismos campos que una salida de emergencia). Para no usar ``dict``/``Any`` sin
tipar, los valores se acotan a escalares JSON o listas de strings.
"""

from typing import Literal

from pydantic import BaseModel, Field

# Valor de un atributo flexible: escalar JSON o lista de strings.
AttrValue = str | int | float | bool | list[str] | None

ItemCategory = Literal[
    "equipo",
    "vehiculo",
    "salida_emergencia",
    "guia",
    "actividad",
    "riesgo",
    "contacto_emergencia",
    "otro",
]


class ItemCreate(BaseModel):
    category: ItemCategory
    name: str = Field(min_length=1, max_length=200)
    attributes: dict[str, AttrValue] = Field(default_factory=dict)


class ItemUpdate(BaseModel):
    category: ItemCategory | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    attributes: dict[str, AttrValue] | None = None


class ItemOut(BaseModel):
    id: str
    category: str
    name: str
    attributes: dict[str, AttrValue] = Field(default_factory=dict)
    evidence_count: int = 0
    created_at: str
    updated_at: str


class EvidenceOut(BaseModel):
    id: str
    caption: str | None = None
    url: str | None = None  # URL firmada temporal para ver la foto
    uploaded_at: str
