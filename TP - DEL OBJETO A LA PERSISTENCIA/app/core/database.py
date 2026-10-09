"""Motor, sessionmaker y dependencia de sesión.

El motor y el sessionmaker se crean en el lifespan (app/main.py) y viven en
`app.state`; `get_session` entrega una sesión por petición.
"""
from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

# Nombres predecibles para constraints: los mensajes 409 se eligen por nombre
# y Alembic puede crearlos/borrarlos sin depender de nombres autogenerados.
# Se fija al importar este módulo, antes de que se definan las tablas.
SQLModel.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def crear_engine_y_sessionmaker(
    url: str, echo: bool = False
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(url, echo=echo)
    # expire_on_commit=False: los objetos siguen usables tras el commit
    # (en async un refresh implícito sería carga perezosa y fallaría).
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    return engine, sessionmaker


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Una sesión por petición, tomada del sessionmaker de app.state."""
    async with request.app.state.sessionmaker() as session:
        yield session
