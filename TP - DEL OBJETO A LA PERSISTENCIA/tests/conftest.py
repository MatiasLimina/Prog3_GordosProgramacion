"""Fixtures de tests con base real (PostgreSQL, base `libreria_test`).

La URL se deriva de la configuración (POSTGRES_*) cambiando sólo el nombre de la
base, así no hay credenciales nuevas en ningún archivo. Crear la base una vez con:
    docker compose exec -T postgres sh -c 'createdb -U "$POSTGRES_USER" libreria_test'

Si la base no responde, los tests marcados `db` se SALTEAN. Con REQUIRE_TEST_DB=1
la falta de base es un FALLO (para CI o para no engañarse con skips silenciosos).
Sólo los errores de conexión causan skip; cualquier otro error (esquema, vaciado de tablas)
hace fallar el test.
"""
import asyncio
import os
import secrets
import subprocess
import sys
from contextlib import contextmanager
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
from app.core.security import calcular_hash_ficticio
from app.main import app as fastapi_app

# La suite no depende de la clave real del desarrollador: se genera una en cada corrida
# (si ya hay una en el entorno, se respeta). Es obligatoria para construir Settings.
os.environ.setdefault("JWT_SECRET", secrets.token_urlsafe(48))

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
        _sin_base("falta configuración: POSTGRES_* o JWT_SECRET")
    return url


def _alembic_upgrade_head(url) -> None:
    """Corre `alembic upgrade head` contra la base de test en un subproceso.

    `migrations/env.py` arma la URL con Settings, y el entorno pisa al `.env`:
    alcanza con pasar POSTGRES_DB=libreria_test al subproceso.
    """
    assert url.database == "libreria_test"
    env = {**os.environ, "POSTGRES_DB": url.database}
    proyecto = Path(__file__).resolve().parent.parent
    resultado = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=proyecto, env=env, capture_output=True, text=True, timeout=120,
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


# Todas las secuencias del esquema vuelven a 1 (lo mismo que `RESTART IDENTITY`).
_REINICIAR_SECUENCIAS = text(
    "SELECT setval(c.oid, 1, false) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
    "WHERE c.relkind = 'S' AND n.nspname = 'public'"
)


async def _vaciar_tablas(conn) -> None:
    """Deja todas las tablas vacías y los ids desde 1.

    Con `DELETE` y no con `TRUNCATE`: `TRUNCATE` crea archivos nuevos para cada tabla, índice
    y secuencia, y en el volumen de Docker Desktop (WSL2) eso cuesta ~3,6 s por test; con las
    pocas filas que deja un test, `DELETE` tarda ~70 ms. `session_replication_role = replica`
    apaga los disparadores sólo dentro de esta transacción: el de sólo agregado de
    `movimiento_stock` (RN-12) rechaza el `DELETE`, y sin las FK el orden de borrado no importa.
    Requiere superusuario (el usuario del Postgres de `docker-compose.yml` lo es).
    """
    await conn.execute(text("SET LOCAL session_replication_role = replica"))
    for tabla in reversed(SQLModel.metadata.sorted_tables):
        await conn.execute(text(f'DELETE FROM "{tabla.name}"'))
    await conn.execute(_REINICIAR_SECUENCIAS)


@pytest.fixture
async def sessionmaker_test(esquema_test):
    engine = create_async_engine(esquema_test, poolclass=NullPool, connect_args={"timeout": 3})
    # Aislamiento: cada test arranca con tablas vacías e ids desde 1.
    async with engine.begin() as conn:
        await _vaciar_tablas(conn)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


_COSTO_BCRYPT_TEST = 4  # el mínimo que acepta bcrypt: los tests no esperan ~300 ms por hash
_CLAVES_ESTADO = ("settings", "hash_ficticio", "semaforo_bcrypt", "sessionmaker")


@contextmanager
def estado_de_app(app, sessionmaker):
    """Deja en `app.state` lo que el lifespan crearía y, al salir, restaura lo que había.

    `ASGITransport` no corre el lifespan, así que sin esto `app.state` no tiene los recursos
    que usan los endpoints de auth. Costo de bcrypt bajo; `sessionmaker` es el de la base de
    test (la fábrica de sesiones propias de `intento_acceso` sale de acá). Lo que no existía
    se borra al salir y lo que existía vuelve a su valor: ningún test deja estado a otro.
    """
    state = app.state._state
    previo = {c: state[c] for c in _CLAVES_ESTADO if c in state}
    settings = get_settings().model_copy(update={"bcrypt_cost": _COSTO_BCRYPT_TEST})
    state["settings"] = settings
    state["hash_ficticio"] = calcular_hash_ficticio(_COSTO_BCRYPT_TEST)
    state["semaforo_bcrypt"] = asyncio.Semaphore(settings.bcrypt_max_concurrentes)
    state["sessionmaker"] = sessionmaker
    try:
        yield
    finally:
        for clave in _CLAVES_ESTADO:
            state.pop(clave, None)
        state.update(previo)


@pytest.fixture
async def client(sessionmaker_test):
    async def get_session_test():
        async with sessionmaker_test() as session:
            yield session

    fastapi_app.dependency_overrides[get_session] = get_session_test
    with estado_de_app(fastapi_app, sessionmaker_test):
        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as c:
            yield c
    fastapi_app.dependency_overrides.clear()
