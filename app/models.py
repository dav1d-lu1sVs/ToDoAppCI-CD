"""
Modelos de datos.

SQLModel = Pydantic (validación de JSON) + SQLAlchemy (tablas de BD) en una sola clase.

Usamos VARIOS modelos para la misma entidad, cada uno con un propósito:
    TareaBase        -> campos comunes (no es tabla)
    Tarea            -> la TABLA en la base de datos
    TareaCrear       -> lo que el cliente ENVÍA para crear / reemplazar (POST, PUT)
    TareaActualizar  -> lo que el cliente envía para actualizar parcialmente (PATCH)
    TareaPublica     -> lo que la API DEVUELVE

Así el cliente nunca puede mandar `id` ni `fecha_creacion` (los genera el servidor).
"""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class Prioridad(StrEnum):
    """Valores permitidos: cualquier otro texto da 422 automáticamente."""

    baja = "baja"
    media = "media"
    alta = "alta"


class TareaBase(SQLModel):
    titulo: str = Field(min_length=1, max_length=100)
    descripcion: str | None = Field(default=None, max_length=500)
    completada: bool = False
    prioridad: Prioridad = Prioridad.media


class Tarea(TareaBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    fecha_creacion: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TareaCrear(TareaBase):
    # Quita espacios al inicio/fin: "   " se vuelve "" y no pasa min_length=1.
    model_config = {"str_strip_whitespace": True}


class TareaActualizar(SQLModel):
    model_config = {"str_strip_whitespace": True}

    # Todo opcional: el cliente manda solo lo que quiere cambiar.
    titulo: str | None = Field(default=None, min_length=1, max_length=100)
    descripcion: str | None = Field(default=None, max_length=500)
    completada: bool | None = None
    prioridad: Prioridad | None = None


class TareaPublica(TareaBase):
    id: int
    fecha_creacion: datetime

    @field_validator("fecha_creacion")
    @classmethod
    def asegurar_utc(cls, valor: datetime) -> datetime:
        # SQLite no guarda la zona horaria; la marcamos como UTC para que el
        # navegador la convierta bien a la hora local.
        return valor if valor.tzinfo else valor.replace(tzinfo=UTC)
