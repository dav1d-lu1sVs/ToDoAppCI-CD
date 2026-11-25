"""
Capa de rutas (la "API" propiamente dicha): equivale a un @RestController.

Responsabilidad: recibir la petición HTTP, delegar en el servicio y traducir
el resultado a una respuesta HTTP (códigos 201, 404, 204...).
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.database import SessionDep
from app.models import Prioridad, Tarea, TareaActualizar, TareaCrear, TareaPublica
from app.services import tareas as servicio

router = APIRouter(prefix="/tareas", tags=["Tareas"])


def obtener_tarea_o_404(session: SessionDep, tarea_id: int) -> Tarea:
    tarea = servicio.obtener(session, tarea_id)
    if tarea is None:
        # HTTPException corta la ejecución y FastAPI responde con ese código.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    return tarea


# CREATE ---------------------------------------------------------------------
@router.post("", response_model=TareaPublica, status_code=status.HTTP_201_CREATED)
def crear_tarea(datos: TareaCrear, session: SessionDep) -> Tarea:
    # `datos` llega YA validado: si el JSON es inválido FastAPI responde 422 solo.
    return servicio.crear(session, datos)


# READ (lista) ---------------------------------------------------------------
@router.get("", response_model=list[TareaPublica])
def listar_tareas(
    session: SessionDep,
    # Parámetros de query: /tareas?completada=true&prioridad=alta&q=estudiar
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    completada: bool | None = None,
    prioridad: Prioridad | None = None,
    q: Annotated[str | None, Query(max_length=100, description="Buscar en el título")] = None,
) -> list[Tarea]:
    return servicio.listar(
        session, offset=offset, limit=limit, completada=completada, prioridad=prioridad, q=q
    )


# READ (una) -----------------------------------------------------------------
@router.get("/{tarea_id}", response_model=TareaPublica)
def obtener_tarea(tarea_id: int, session: SessionDep) -> Tarea:
    # `tarea_id` es un parámetro de ruta; FastAPI lo convierte a int (o da 422).
    return obtener_tarea_o_404(session, tarea_id)


# UPDATE completo (PUT: se reemplazan TODOS los campos) ----------------------
@router.put("/{tarea_id}", response_model=TareaPublica)
def reemplazar_tarea(tarea_id: int, datos: TareaCrear, session: SessionDep) -> Tarea:
    tarea = obtener_tarea_o_404(session, tarea_id)
    return servicio.actualizar(session, tarea, datos.model_dump())


# UPDATE parcial (PATCH: solo los campos enviados) ---------------------------
@router.patch("/{tarea_id}", response_model=TareaPublica)
def actualizar_tarea(tarea_id: int, datos: TareaActualizar, session: SessionDep) -> Tarea:
    tarea = obtener_tarea_o_404(session, tarea_id)
    # exclude_unset=True -> ignora los campos que el cliente NO mandó
    return servicio.actualizar(session, tarea, datos.model_dump(exclude_unset=True))


# DELETE ---------------------------------------------------------------------
@router.delete("/{tarea_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tarea(tarea_id: int, session: SessionDep) -> None:
    tarea = obtener_tarea_o_404(session, tarea_id)
    servicio.eliminar(session, tarea)
