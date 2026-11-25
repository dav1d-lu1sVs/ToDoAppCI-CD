"""
Capa de acceso a datos: conexión a la base de datos.

- engine: el "motor" que sabe cómo conectarse a la BD (se crea UNA vez).
- Session: una "conversación" con la BD; se abre por cada petición HTTP
  y se cierra al terminar. Ahí haces add / commit / query.
"""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

# check_same_thread=False es necesario solo en SQLite, porque FastAPI puede
# atender una misma petición en hilos distintos.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)


def crear_tablas() -> None:
    """Crea las tablas definidas con `table=True` si aún no existen."""
    import app.models  # noqa: F401  (registra los modelos antes de crear tablas)

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    Dependencia de FastAPI: entrega una sesión a cada endpoint que la pida.

    `yield` hace que el código después de él (cerrar la sesión) se ejecute
    automáticamente cuando termina la petición.
    """
    with Session(engine) as session:
        yield session


# Alias reutilizable: en cada endpoint escribes `session: SessionDep`
# y FastAPI llama a get_session() por ti (Inyección de Dependencias).
SessionDep = Annotated[Session, Depends(get_session)]
