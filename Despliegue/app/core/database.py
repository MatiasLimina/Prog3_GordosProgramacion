"""Motor, sessionmaker y dependencia de sesión.

El motor y el sessionmaker se crean en el lifespan (app/main.py) y viven en
`app.state`; `get_session` entrega una sesión por petición.
"""
from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

import app.core.base  # noqa: F401  (fija la naming convention)


def crear_engine_y_sessionmaker(
    url: str, echo: bool = False
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    # timeout de conexión (s): si la base no responde, /health/ready falla rápido
    # en vez de colgarse ~60 s.
    engine = create_async_engine(url, echo=echo, connect_args={"timeout": 5})
    # expire_on_commit=False: los objetos siguen usables tras el commit
    # (en async un refresh implícito sería carga perezosa y fallaría).
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    return engine, sessionmaker


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Una sesión por petición, tomada del sessionmaker de app.state."""
    async with request.app.state.sessionmaker() as session:
        yield session
