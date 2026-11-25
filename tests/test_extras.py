"""Pruebas de prioridad, búsqueda, datos de ejemplo y frontend."""

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import Tarea
from app.seed import TAREAS_DE_EJEMPLO, sembrar_datos


def crear(client: TestClient, **campos) -> dict:
    respuesta = client.post("/tareas", json={"titulo": "Tarea", **campos})
    assert respuesta.status_code == 201
    return respuesta.json()


# Prioridad ------------------------------------------------------------------
def test_prioridad_por_defecto_es_media(client: TestClient):
    assert crear(client)["prioridad"] == "media"


def test_prioridad_invalida_da_422(client: TestClient):
    respuesta = client.post("/tareas", json={"titulo": "x", "prioridad": "urgente"})
    assert respuesta.status_code == 422


def test_filtrar_por_prioridad(client: TestClient):
    crear(client, titulo="A", prioridad="alta")
    crear(client, titulo="B", prioridad="baja")

    respuesta = client.get("/tareas", params={"prioridad": "alta"})

    assert [t["titulo"] for t in respuesta.json()] == ["A"]


# Búsqueda y validación de texto -----------------------------------------------
def test_buscar_por_titulo_sin_distinguir_mayusculas(client: TestClient):
    crear(client, titulo="Estudiar FastAPI")
    crear(client, titulo="Comprar pan")

    respuesta = client.get("/tareas", params={"q": "fastapi"})

    assert [t["titulo"] for t in respuesta.json()] == ["Estudiar FastAPI"]


def test_titulo_solo_espacios_da_422(client: TestClient):
    respuesta = client.post("/tareas", json={"titulo": "    "})
    assert respuesta.status_code == 422


def test_titulo_se_guarda_sin_espacios_extremos(client: TestClient):
    assert crear(client, titulo="  Limpio  ")["titulo"] == "Limpio"


def test_fecha_creacion_incluye_zona_horaria(client: TestClient):
    fecha = crear(client)["fecha_creacion"]
    assert fecha.endswith("Z") or fecha.endswith("+00:00")


# Datos de ejemplo -------------------------------------------------------------
def test_sembrar_datos_inserta_ejemplos_en_bd_vacia(session: Session):
    insertadas = sembrar_datos(session)

    assert insertadas == len(TAREAS_DE_EJEMPLO)
    assert len(session.exec(select(Tarea)).all()) == len(TAREAS_DE_EJEMPLO)


def test_sembrar_datos_no_duplica(session: Session):
    sembrar_datos(session)
    assert sembrar_datos(session) == 0
    assert len(session.exec(select(Tarea)).all()) == len(TAREAS_DE_EJEMPLO)


# Frontend ---------------------------------------------------------------------
def test_raiz_sirve_el_frontend(client: TestClient):
    respuesta = client.get("/")
    assert respuesta.status_code == 200
    assert "text/html" in respuesta.headers["content-type"]


def test_archivos_estaticos_disponibles(client: TestClient):
    assert client.get("/css/styles.css").status_code == 200
    assert client.get("/js/app.js").status_code == 200
