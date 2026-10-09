from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.errors import commit_or_409
from app.core.pagination import Pagination
from app.modules.editoriales.models import Editorial
from app.modules.editoriales.schemas import EditorialCreate

MENSAJES = {
    "uq_editorial_nombre": "Ya existe una editorial con ese nombre.",
}


async def crear(session: AsyncSession, datos: EditorialCreate) -> Editorial:
    editorial = Editorial(**datos.model_dump())
    session.add(editorial)
    await commit_or_409(session, MENSAJES)
    return editorial


async def listar(session: AsyncSession, p: Pagination) -> list[Editorial]:
    consulta = select(Editorial).order_by(Editorial.id).limit(p.limit).offset(p.offset)
    return list((await session.execute(consulta)).scalars().all())


async def obtener(session: AsyncSession, editorial_id: int) -> Editorial:
    editorial = await session.get(Editorial, editorial_id)
    if editorial is None:
        raise HTTPException(status_code=404, detail="La editorial no existe.")
    return editorial
