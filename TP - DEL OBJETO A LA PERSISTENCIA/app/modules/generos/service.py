from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.errors import commit_or_409
from app.core.pagination import Pagination
from app.modules.generos.models import Genero
from app.modules.generos.schemas import GeneroCreate

MENSAJES = {
    "uq_genero_nombre": "Ya existe un género con ese nombre.",
}


async def crear(session: AsyncSession, datos: GeneroCreate) -> Genero:
    genero = Genero(**datos.model_dump())
    session.add(genero)
    await commit_or_409(session, MENSAJES)
    return genero


async def listar(session: AsyncSession, p: Pagination) -> list[Genero]:
    consulta = select(Genero).order_by(Genero.id).limit(p.limit).offset(p.offset)
    return list((await session.execute(consulta)).scalars().all())
