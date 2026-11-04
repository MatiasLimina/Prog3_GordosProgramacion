"""Motor, fábrica de sesiones y dependencia de sesión.

El motor y la fábrica de sesiones se crean en el lifespan (app/main.py) y viven en
`app.state`; `get_session` entrega una sesión por petición.
"""
from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

import app.core.base  # noqa: F401  (fija la naming convention)
from app.core.config import Settings


def crear_motor(settings: Settings) -> AsyncEngine:
    """Motor asincrónico con el pool y el eco de SQL de la configuración."""
    # timeout de conexión (s): si la base no responde, /health/ready falla rápido
    # en vez de colgarse ~60 s.
    return create_async_engine(
        settings.database_url,
        echo=settings.sql_echo,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        connect_args={"timeout": 5},
    )


def crear_fabrica_sesiones(motor: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    # expire_on_commit=False: los objetos siguen usables tras el commit
    # (en async un refresh implícito sería carga perezosa y fallaría).
    return async_sessionmaker(motor, expire_on_commit=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Una sesión por petición, tomada del sessionmaker de app.state."""
    async with request.app.state.sessionmaker() as session:
        yield session
