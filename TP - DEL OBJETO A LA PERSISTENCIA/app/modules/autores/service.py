from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.errors import commit_or_409
from app.core.pagination import Pagination
from app.modules.autores.models import Autor
from app.modules.autores.schemas import AutorCreate, AutorLibroRead, AutorRead, AutorUpdate
from app.modules.libros.models import Libro, LibroAutor

MENSAJES: dict[str, str] = {}


async def crear(session: AsyncSession, datos: AutorCreate) -> AutorRead:
    autor = Autor(**datos.model_dump())
    session.add(autor)
    await commit_or_409(session, MENSAJES)
    return AutorRead.model_validate(autor)


async def listar(session: AsyncSession, p: Pagination) -> list[AutorRead]:
    consulta = select(Autor).order_by(Autor.id).limit(p.limit).offset(p.offset)
    resultado = await session.execute(consulta)
    autores = resultado.scalars().all()
    return [AutorRead.model_validate(a) for a in autores]


async def obtener(session: AsyncSession, autor_id: int) -> AutorRead:
    autor = await session.get(Autor, autor_id)
    if autor is None:
        raise HTTPException(status_code=404, detail="El autor no existe.")
    return AutorRead.model_validate(autor)


async def actualizar(session: AsyncSession, autor_id: int, datos: AutorUpdate) -> AutorRead:
    autor = await session.get(Autor, autor_id)
    if autor is None:
        raise HTTPException(status_code=404, detail="El autor no existe.")

    cambios = datos.model_dump(exclude_unset=True)
    if cambios:
        autor.sqlmodel_update(cambios)
        session.add(autor)
        await commit_or_409(session, MENSAJES)

    return AutorRead.model_validate(autor)


async def listar_libros_de_autor(session: AsyncSession, autor_id: int) -> list[AutorLibroRead]:
    # Verificar existencia del autor
    await obtener(session, autor_id)

    consulta = (
        select(LibroAutor, Libro)
        .join(Libro, LibroAutor.libro_id == Libro.id)
        .where(LibroAutor.autor_id == autor_id)
        .order_by(LibroAutor.orden, Libro.id)
    )
    resultado = await session.execute(consulta)
    filas = resultado.all()

    return [
        AutorLibroRead(
            id=libro.id,
            isbn=libro.isbn,
            titulo=libro.titulo,
            precio=libro.precio,
            stock=libro.stock,
            rol=la.rol,
            orden=la.orden,
        )
        for la, libro in filas
    ]
