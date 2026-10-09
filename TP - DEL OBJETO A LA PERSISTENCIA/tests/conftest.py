"""Fixtures de tests con base real (PostgreSQL, base `libreria_test`).

La URL se deriva de DATABASE_URL cambiando sólo el nombre de la base, así no
hay credenciales nuevas en ningún archivo. Crear la base una vez con:
    docker compose exec -T postgres sh -c 'createdb -U "$POSTGRES_USER" libreria_test'
"""
import pytest
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


@pytest.fixture
async def sessionmaker_test():
    try:
        url = make_url(get_settings().database_url).set(database="libreria_test")
    except RuntimeError:
        pytest.skip("DATABASE_URL no está definida: no hay base de test.")
    engine = create_async_engine(url, poolclass=NullPool, connect_args={"timeout": 3})
    try:
        async with engine.begin() as conn:
            # TEMPORAL: create_all SÓLO acá, para los tests. En la Fase 3 se
            # reemplaza por `alembic upgrade head`. La app NUNCA usa create_all.
            await conn.run_sync(SQLModel.metadata.create_all)
            # Aislamiento: cada test arranca con tablas vacías e ids desde 1.
            tablas = ", ".join(f'"{t.name}"' for t in SQLModel.metadata.sorted_tables)
            await conn.execute(text(f"TRUNCATE {tablas} RESTART IDENTITY CASCADE"))
    except Exception as e:
        await engine.dispose()
        pytest.skip(f"La base de test no responde ({type(e).__name__}); ¿existe libreria_test?")
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
