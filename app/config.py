"""
Configuración central, leída de variables de entorno.

Buena práctica ("12-factor app"): el MISMO código corre en tu PC, en el
pipeline y en EC2; lo único que cambia son estas variables.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

# Carpeta raíz del proyecto (la que contiene app/ y frontend/)
BASE_DIR = Path(__file__).resolve().parent.parent


def _leer_bool(nombre: str, por_defecto: bool) -> bool:
    valor = os.getenv(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in {"1", "true", "yes", "si", "sí"}


def _leer_lista(nombre: str) -> list[str]:
    valor = os.getenv(nombre, "")
    return [item.strip() for item in valor.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", f"sqlite:///{(BASE_DIR / 'tareas.db').as_posix()}"
        )
    )
    # Carga tareas de ejemplo al arrancar si la tabla está vacía.
    seed_data: bool = field(default_factory=lambda: _leer_bool("SEED_DATA", True))
    # Orígenes permitidos para CORS (solo si el frontend vive en OTRO dominio/puerto).
    cors_origins: list[str] = field(default_factory=lambda: _leer_lista("CORS_ORIGINS"))
    frontend_dir: Path = BASE_DIR / "frontend"


settings = Settings()
