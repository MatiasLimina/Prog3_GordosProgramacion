from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

from app.core.errors import commit_or_409
from app.core.pagination import Pagination
from app.modules.editoriales.models import Editorial
from app.modules.libros.models import Libro
from app.modules.libros.schemas import LibroRead
from app.modules.editoriales.schemas import EditorialCreate, EditorialUpdate

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


async def actualizar(session: AsyncSession, editorial_id: int, datos: EditorialUpdate) -> Editorial:
    editorial = await obtener(session, editorial_id)
    # Sólo lo enviado: lo que el cliente no mandó no se toca.
    editorial.sqlmodel_update(datos.model_dump(exclude_unset=True))
    session.add(editorial)
    await commit_or_409(session, MENSAJES)
    return editorial


async def listar_libros(session: AsyncSession, editorial_id: int, p: Pagination) -> list[LibroRead]:
    """Libros de una editorial (404 si la editorial no existe), paginados.

    Precarga editorial y género en la misma consulta (joinedload): sin lazy loading.
    """
    await obtener(session, editorial_id)
    consulta = (
        select(Libro)
        .where(Libro.editorial_id == editorial_id)
        .options(joinedload(Libro.editorial), joinedload(Libro.genero))
        .order_by(Libro.id)
        .limit(p.limit)
        .offset(p.offset)
    )
    libros = (await session.execute(consulta)).scalars().all()
    return [LibroRead.model_validate(libro) for libro in libros]
