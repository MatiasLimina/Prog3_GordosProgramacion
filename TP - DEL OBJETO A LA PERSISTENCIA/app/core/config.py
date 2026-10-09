"""Configuración de la app tomada del entorno (.env).

Decisión: no se lee DATABASE_URL al importar el módulo. `get_settings()` la
lee cuando se la llama (en el lifespan o en Alembic), así los tests pueden
importar `app` sin tener la variable definida y pueden pasar un dict propio.
"""
import os
from collections.abc import Mapping
from dataclasses import dataclass

from dotenv import load_dotenv

# Carga .env (si existe) en os.environ; no pisa variables ya definidas.
load_dotenv()

_VERDADEROS = {"true", "1", "yes"}


@dataclass(frozen=True)
class Settings:
    database_url: str
    db_echo: bool


def get_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Arma la configuración desde `environ` (por defecto, os.environ)."""
    env = os.environ if environ is None else environ
    database_url = env.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "Falta la variable de entorno DATABASE_URL. "
            "Copiá env.example a .env y completalo."
        )
    db_echo = env.get("DB_ECHO", "false").strip().lower() in _VERDADEROS
    return Settings(database_url=database_url, db_echo=db_echo)
