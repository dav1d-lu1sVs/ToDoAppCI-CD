"""
Datos de ejemplo para la base de datos.

Se ejecuta solo al arrancar la API (si SEED_DATA=true y la tabla está vacía)
o a mano con:
    python -m app.seed
"""

from sqlmodel import Session, select

from app.models import Prioridad, Tarea

TAREAS_DE_EJEMPLO: list[dict] = [
    {
        "titulo": "Configurar el pipeline de GitLab CI/CD",
        "descripcion": "Crear las 5 etapas: lint, build, test, packing y deploy.",
        "prioridad": Prioridad.alta,
    },
    {
        "titulo": "Lanzar instancia EC2 en AWS",
        "descripcion": "Ubuntu, abrir puertos 22 y 8000 en el Security Group.",
        "prioridad": Prioridad.alta,
    },
    {
        "titulo": "Estudiar el tutorial de FastAPI",
        "descripcion": "Path params, query params, request body y dependencias.",
        "prioridad": Prioridad.media,
        "completada": True,
    },
    {
        "titulo": "Escribir pruebas unitarias del CRUD",
        "descripcion": "Cubrir casos felices y errores 404 / 422.",
        "prioridad": Prioridad.media,
        "completada": True,
    },
    {
        "titulo": "Preparar la presentación del proyecto",
        "descripcion": "Explicar arquitectura, pipeline y demo en vivo.",
        "prioridad": Prioridad.media,
    },
    {
        "titulo": "Agregar autenticación con JWT",
        "descripcion": "Mejora opcional para una siguiente versión.",
        "prioridad": Prioridad.baja,
    },
]


def sembrar_datos(session: Session) -> int:
    """Inserta las tareas de ejemplo si no hay ninguna. Devuelve cuántas insertó."""
    if session.exec(select(Tarea).limit(1)).first() is not None:
        return 0
    session.add_all(Tarea(**datos) for datos in TAREAS_DE_EJEMPLO)
    session.commit()
    return len(TAREAS_DE_EJEMPLO)


if __name__ == "__main__":
    from app.database import crear_tablas, engine

    crear_tablas()
    with Session(engine) as session:
        insertadas = sembrar_datos(session)
    print(f"Tareas insertadas: {insertadas}" if insertadas else "La BD ya tenía datos.")
