"""
Punto de entrada de la aplicación.

Uvicorn (el servidor) busca el objeto `app` de este archivo:
    fastapi dev app/main.py           -> desarrollo (se recarga al guardar)
    uvicorn app.main:app --port 8000  -> producción (lo que usaremos en EC2)

Rutas:
    /tareas...  -> API REST (JSON)
    /health     -> estado del servicio
    /docs       -> Swagger (generado automáticamente)
    /           -> frontend (archivos de la carpeta frontend/)
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from app.config import settings
from app.database import crear_tablas, engine
from app.routers import tareas
from app.seed import sembrar_datos


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Lo que va ANTES del yield se ejecuta al arrancar el servidor.
    crear_tablas()
    if settings.seed_data:
        with Session(engine) as session:
            sembrar_datos(session)
    yield
    # Lo que va DESPUÉS del yield se ejecutaría al apagarlo.


app = FastAPI(
    title="To-Do List API",
    description="CRUD de tareas hecho con FastAPI + SQLModel",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS: solo hace falta si el frontend se sirve desde OTRO origen (p. ej. Vite en :5173).
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(tareas.router)


@app.get("/health", tags=["Sistema"])
def health() -> dict[str, str]:
    """Permite comprobar que la API está viva (lo usaremos tras cada deploy)."""
    return {"status": "ok"}


# El frontend se monta AL FINAL: las rutas de arriba tienen prioridad y todo lo
# demás (/, /css/..., /js/...) se busca como archivo dentro de frontend/.
if settings.frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")
