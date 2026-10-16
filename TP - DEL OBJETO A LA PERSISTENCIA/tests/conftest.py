"""Fixtures de tests con base real (PostgreSQL, base `libreria_test`).

La URL se deriva de DATABASE_URL cambiando sólo el nombre de la base, así no
hay credenciales nuevas en ningún archivo. Crear la base una vez con:
    docker compose exec -T postgres sh -c 'createdb -U "$POSTGRES_USER" libreria_test'

Si la base no responde, los tests marcados `db` se SALTEAN. Con REQUIRE_TEST_DB=1
la falta de base es un FALLO (para CI o para no engañarse con skips silenciosos).
Sólo los errores de conexión causan skip; cualquier otro error (esquema, TRUNCATE)
hace fallar el test.
"""
import os
import subprocess
import sys
from pathlib import Path

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

import app.models  # noqa: F401  (registra todos los modelos en el metadata)
from app.core.config import get_settings
from app.core.database import get_session
from app.main import app as fastapi_app

# Errores que significan "no hay base de test disponible".
_SIN_BASE = (OSError, TimeoutError, asyncpg.InvalidCatalogNameError)


def _es_falta_de_base(exc: BaseException) -> bool:
    """SQLAlchemy envuelve los errores de asyncpg: se revisa la cadena completa."""
    visto = set()
    while exc is not None and id(exc) not in visto:
        if isinstance(exc, _SIN_BASE):
            return True
        visto.add(id(exc))
        exc = getattr(exc, "orig", None) or exc.__cause__
    return False


def _sin_base(motivo: str):
    if os.environ.get("REQUIRE_TEST_DB") == "1":
        pytest.fail(f"REQUIRE_TEST_DB=1 y no hay base de test: {motivo}")
    pytest.skip(f"No hay base de test ({motivo}); ¿existe libreria_test?")


def _url_test():
    try:
        url = make_url(get_settings().database_url).set(database="libreria_test")
    except RuntimeError:
        _sin_base("DATABASE_URL no está definida")
    return url


def _alembic_upgrade_head(url) -> None:
    """Corre `alembic upgrade head` contra la base de test en un subproceso.

    `migrations/env.py` toma DATABASE_URL del entorno (load_dotenv no pisa las
    variables ya definidas), así que alcanza con apuntarla a libreria_test.
    """
    assert url.database == "libreria_test"
    env = {**os.environ, "DATABASE_URL": url.render_as_string(hide_password=False)}
    proyecto = Path(__file__).resolve().parent.parent
    resultado = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=proyecto, env=env, capture_output=True, text=True,
    )
    if resultado.returncode != 0:
        pytest.fail(f"alembic upgrade head falló en libreria_test:\n{resultado.stdout}\n{resultado.stderr}")


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def esquema_test():
    """Deja el esquema de test limpio y actualizado, una vez por corrida.

    Vacía el esquema `public` de `libreria_test` y corre `alembic upgrade head`
    sobre él, así los tests ejercitan las migraciones reales. Nunca se usa
    `create_all`: el esquema sólo se crea con Alembic.
    """
    url = _url_test()
    assert url.database == "libreria_test"  # nunca borrar otra base
    engine = create_async_engine(url, poolclass=NullPool, connect_args={"timeout": 3})
    try:
        try:
            async with engine.connect():
                pass
        except Exception as e:
            if _es_falta_de_base(e):
                _sin_base(type(e).__name__)
            raise
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
    finally:
        await engine.dispose()
    _alembic_upgrade_head(url)
    return url


@pytest.fixture
async def sessionmaker_test(esquema_test):
    engine = create_async_engine(esquema_test, poolclass=NullPool, connect_args={"timeout": 3})
    # Aislamiento: cada test arranca con tablas vacías e ids desde 1.
    tablas = ", ".join(f'"{t.name}"' for t in SQLModel.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tablas} RESTART IDENTITY CASCADE"))
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def client(sessionmaker_test):
    async def get_session_test():
        async with sessionmaker_test() as session:
            yield session

    fastapi_app.dependency_overrides[get_session] = get_session_test
    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as c:
        yield c
    fastapi_app.dependency_overrides.clear()
