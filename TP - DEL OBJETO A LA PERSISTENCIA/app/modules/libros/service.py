from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select

from app.core.errors import commit_or_409
from app.core.pagination import Pagination
from app.modules.libros.models import Libro, LibroAutor
from app.modules.libros.schemas import (
    AutorEnLibroRead,
    EditorialSimpleRead,
    GeneroSimpleRead,
    LibroCreate,
    LibroDetalleRead,
    LibroRead,
    LibroUpdate,
)

MENSAJES = {
    "uq_libro_isbn": "Ya existe un libro con ese ISBN.",
    "fk_libro_editorial_id_editorial": "La editorial indicada no existe.",
    "fk_libro_genero_id_genero": "El género indicado no existe.",
    "fk_libro_autor_autor_id_autor": "Uno de los autores indicados no existe.",
    "fk_libro_autor_libro_id_libro": "El libro indicado no existe.",
    "pk_libro_autor": "No se puede repetir el mismo autor en un libro.",
    "ck_libro_precio_positivo": "El precio del libro debe ser mayor a cero.",
    "ck_libro_stock_no_negativo": "El stock del libro no puede ser negativo.",
    "ck_libro_autor_orden_positivo": "El orden del autor debe ser mayor o igual a 1.",
    "ck_libro_autor_rol_valido": "El rol del autor no es válido.",
}


def _armar_detalle(libro: Libro) -> LibroDetalleRead:
    autores_dto = [
        AutorEnLibroRead(
            id=la.autor.id,
            autor_id=la.autor.id,
            nombre=la.autor.nombre,
            nacionalidad=la.autor.nacionalidad,
            rol=la.rol,
            orden=la.orden,
        )
        for la in sorted(libro.autorias, key=lambda x: x.orden)
        if la.autor is not None
    ]
    return LibroDetalleRead(
        id=libro.id,
        isbn=libro.isbn,
        titulo=libro.titulo,
        precio=libro.precio,
        stock=libro.stock,
        editorial=EditorialSimpleRead.model_validate(libro.editorial) if libro.editorial else None,  # type: ignore[arg-type]
        genero=GeneroSimpleRead.model_validate(libro.genero) if libro.genero else None,
        autores=autores_dto,
    )


async def crear(session: AsyncSession, datos: LibroCreate) -> LibroDetalleRead:
    """Alta de libro con relaciones.

    Ningún if verifica si los IDs existen: se escribe y la base responde.
    Si la base rechaza una FK o unicidad, commit_or_409 responde 409 (RN-01, Ejercicio 5).
    """
    datos_libro = datos.model_dump(exclude={"autores"})
    libro = Libro(**datos_libro)

    for a in datos.autores:
        autoria = LibroAutor(
            autor_id=a.autor_id,
            rol=a.rol,
            orden=a.orden,
        )
        libro.autorias.append(autoria)

    session.add(libro)
    await commit_or_409(session, MENSAJES)

    return await obtener(session, libro.id)


async def obtener(session: AsyncSession, libro_id: int) -> LibroDetalleRead:
    """Detalle de un libro sin N+1 (Ejercicio 6).

    Usa joinedload para editorial y género (a uno) y selectinload para autorias
    con joinedload de autor (colección). Cantidad fija de consultas en consola.
    """
    consulta = (
        select(Libro)
        .where(Libro.id == libro_id)
        .options(
            joinedload(Libro.editorial),
            joinedload(Libro.genero),
            selectinload(Libro.autorias).joinedload(LibroAutor.autor),
        )
        # populate_existing: si el Libro ya está en el identity map (p. ej. recién
        # creado o modificado en esta sesión), se recargan también sus relaciones;
        # sin esto la precarga se saltea y la respuesta puede salir desactualizada.
        .execution_options(populate_existing=True)
    )
    resultado = await session.execute(consulta)
    libro = resultado.scalars().first()
    if libro is None:
        raise HTTPException(status_code=404, detail="El libro no existe.")

    return _armar_detalle(libro)


async def listar(
    session: AsyncSession,
    p: Pagination,
    titulo: str | None = None,
    genero_id: int | None = None,
) -> list[LibroRead]:
    """Listado paginado con precarga de editorial y género (RN-10, RN-11).

    Filtro de título por parámetro ligado (ilike) sin concatenación SQL.
    """
    consulta = (
        select(Libro)
        .options(
            joinedload(Libro.editorial),
            joinedload(Libro.genero),
        )
    )

    if titulo:
        consulta = consulta.where(Libro.titulo.ilike(f"%{titulo}%"))

    if genero_id is not None:
        consulta = consulta.where(Libro.genero_id == genero_id)

    consulta = consulta.order_by(Libro.id).limit(p.limit).offset(p.offset)
    resultado = await session.execute(consulta)
    libros = resultado.scalars().all()

    return [
        LibroRead(
            id=l.id,
            isbn=l.isbn,
            titulo=l.titulo,
            precio=l.precio,
            stock=l.stock,
            editorial=EditorialSimpleRead.model_validate(l.editorial) if l.editorial else None,  # type: ignore[arg-type]
            genero=GeneroSimpleRead.model_validate(l.genero) if l.genero else None,
        )
        for l in libros
    ]


async def actualizar(
    session: AsyncSession,
    libro_id: int,
    datos: LibroUpdate,
) -> LibroDetalleRead:
    """Actualización parcial de libro (PATCH con exclude_unset)."""
    libro = await session.get(Libro, libro_id)
    if libro is None:
        raise HTTPException(status_code=404, detail="El libro no existe.")

    cambios = datos.model_dump(exclude_unset=True)
    if cambios:
        libro.sqlmodel_update(cambios)
        session.add(libro)
        await commit_or_409(session, MENSAJES)

    return await obtener(session, libro_id)
