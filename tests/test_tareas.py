"""Pruebas del CRUD de tareas. Patrón de cada test: Preparar -> Ejecutar -> Verificar."""

from fastapi.testclient import TestClient


def crear(client: TestClient, **campos) -> dict:
    datos = {"titulo": "Estudiar FastAPI", **campos}
    respuesta = client.post("/tareas", json=datos)
    assert respuesta.status_code == 201
    return respuesta.json()


def test_health(client: TestClient):
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


# CREATE ---------------------------------------------------------------------
def test_crear_tarea(client: TestClient):
    tarea = crear(client, descripcion="Ver la documentación")

    assert tarea["id"] is not None
    assert tarea["titulo"] == "Estudiar FastAPI"
    assert tarea["descripcion"] == "Ver la documentación"
    assert tarea["completada"] is False
    assert "fecha_creacion" in tarea


def test_crear_tarea_sin_titulo_da_422(client: TestClient):
    respuesta = client.post("/tareas", json={"descripcion": "sin título"})
    assert respuesta.status_code == 422


def test_crear_tarea_con_titulo_vacio_da_422(client: TestClient):
    respuesta = client.post("/tareas", json={"titulo": ""})
    assert respuesta.status_code == 422


def test_crear_tarea_ignora_id_enviado_por_cliente(client: TestClient):
    tarea = crear(client, id=999)
    assert tarea["id"] != 999


# READ -----------------------------------------------------------------------
def test_listar_tareas(client: TestClient):
    crear(client, titulo="Tarea 1")
    crear(client, titulo="Tarea 2")

    respuesta = client.get("/tareas")

    assert respuesta.status_code == 200
    assert [t["titulo"] for t in respuesta.json()] == ["Tarea 1", "Tarea 2"]


def test_listar_tareas_filtrando_por_completada(client: TestClient):
    crear(client, titulo="Pendiente")
    crear(client, titulo="Hecha", completada=True)

    respuesta = client.get("/tareas", params={"completada": True})

    assert [t["titulo"] for t in respuesta.json()] == ["Hecha"]


def test_obtener_tarea(client: TestClient):
    creada = crear(client)

    respuesta = client.get(f"/tareas/{creada['id']}")

    assert respuesta.status_code == 200
    assert respuesta.json() == creada


def test_obtener_tarea_inexistente_da_404(client: TestClient):
    respuesta = client.get("/tareas/12345")
    assert respuesta.status_code == 404
    assert respuesta.json() == {"detail": "Tarea no encontrada"}


# UPDATE ---------------------------------------------------------------------
def test_reemplazar_tarea_con_put(client: TestClient):
    creada = crear(client, descripcion="vieja")

    respuesta = client.put(
        f"/tareas/{creada['id']}", json={"titulo": "Nuevo título", "completada": True}
    )

    assert respuesta.status_code == 200
    tarea = respuesta.json()
    assert tarea["titulo"] == "Nuevo título"
    assert tarea["completada"] is True
    assert tarea["descripcion"] is None  # PUT reemplaza todo: lo no enviado vuelve al default


def test_actualizar_parcial_con_patch(client: TestClient):
    creada = crear(client, descripcion="se mantiene")

    respuesta = client.patch(f"/tareas/{creada['id']}", json={"completada": True})

    assert respuesta.status_code == 200
    tarea = respuesta.json()
    assert tarea["completada"] is True
    assert tarea["titulo"] == "Estudiar FastAPI"
    assert tarea["descripcion"] == "se mantiene"  # PATCH no toca lo que no se envía


def test_actualizar_tarea_inexistente_da_404(client: TestClient):
    respuesta = client.patch("/tareas/12345", json={"completada": True})
    assert respuesta.status_code == 404


# DELETE ---------------------------------------------------------------------
def test_eliminar_tarea(client: TestClient):
    creada = crear(client)

    respuesta = client.delete(f"/tareas/{creada['id']}")

    assert respuesta.status_code == 204
    assert client.get(f"/tareas/{creada['id']}").status_code == 404


def test_eliminar_tarea_inexistente_da_404(client: TestClient):
    respuesta = client.delete("/tareas/12345")
    assert respuesta.status_code == 404
