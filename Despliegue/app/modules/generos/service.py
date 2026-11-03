from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

from app.core.errors import commit_or_409
from app.core.pagination import Pagination
from app.modules.generos.models import Genero
from app.modules.generos.schemas import GeneroCreate
from app.modules.libros.models import Libro
from app.modules.libros.schemas import LibroRead

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


async def obtener(session: AsyncSession, genero_id: int) -> Genero:
    genero = await session.get(Genero, genero_id)
    if genero is None:
        raise HTTPException(status_code=404, detail="El género no existe.")
    return genero


async def listar_libros(session: AsyncSession, genero_id: int, p: Pagination) -> list[LibroRead]:
    """Libros de un género (404 si el género no existe), paginados.

    Precarga editorial y género en la misma consulta (joinedload): sin lazy loading.
    """
    await obtener(session, genero_id)
    consulta = (
        select(Libro)
        .where(Libro.genero_id == genero_id)
        .options(joinedload(Libro.editorial), joinedload(Libro.genero))
        .order_by(Libro.id)
        .limit(p.limit)
        .offset(p.offset)
    )
    libros = (await session.execute(consulta)).scalars().all()
    return [LibroRead.model_validate(libro) for libro in libros]
