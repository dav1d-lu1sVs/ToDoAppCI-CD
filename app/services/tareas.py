"""
Capa de servicios (lógica de negocio): equivale a un @Service de Spring.

Aquí NO se habla de HTTP (nada de códigos 404 ni HTTPException): solo datos.
Así esta lógica se puede reutilizar desde un router, un script o una prueba.
"""

from sqlmodel import Session, col, select

from app.models import Prioridad, Tarea, TareaCrear


def listar(
    session: Session,
    *,
    offset: int = 0,
    limit: int = 100,
    completada: bool | None = None,
    prioridad: Prioridad | None = None,
    q: str | None = None,
) -> list[Tarea]:
    consulta = select(Tarea)
    if completada is not None:
        consulta = consulta.where(Tarea.completada == completada)
    if prioridad is not None:
        consulta = consulta.where(Tarea.prioridad == prioridad)
    if q:
        consulta = consulta.where(col(Tarea.titulo).ilike(f"%{q}%"))
    consulta = consulta.order_by(col(Tarea.id)).offset(offset).limit(limit)
    return list(session.exec(consulta).all())


def obtener(session: Session, tarea_id: int) -> Tarea | None:
    return session.get(Tarea, tarea_id)


def crear(session: Session, datos: TareaCrear) -> Tarea:
    tarea = Tarea.model_validate(datos)
    return _guardar(session, tarea)


def actualizar(session: Session, tarea: Tarea, cambios: dict) -> Tarea:
    tarea.sqlmodel_update(cambios)
    return _guardar(session, tarea)


def eliminar(session: Session, tarea: Tarea) -> None:
    session.delete(tarea)
    session.commit()


def _guardar(session: Session, tarea: Tarea) -> Tarea:
    session.add(tarea)
    session.commit()
    session.refresh(tarea)  # recarga id y fecha generados por la BD
    return tarea
