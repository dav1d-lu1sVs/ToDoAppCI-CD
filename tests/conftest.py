"""
Fixtures de pytest: preparan el entorno para cada prueba.

Cada test recibe una base de datos SQLite EN MEMORIA, nueva y vacía,
así las pruebas no tocan tareas.db ni dependen unas de otras.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",  # sin archivo = en memoria
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # misma conexión siempre, si no la BD en memoria "desaparece"
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()  # cierra la conexión al terminar el test


@pytest.fixture(name="client")
def client_fixture(session: Session):
    # dependency_overrides: reemplaza la dependencia real por la de pruebas.
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()
