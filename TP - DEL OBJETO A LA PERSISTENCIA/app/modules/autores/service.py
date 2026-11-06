from app.core.errors import NoEncontrado
from app.core.paginacion import Page, ParametrosPagina, envolver
from app.modules.autores.models import Autor
from app.modules.autores.schemas import AutorCreate, AutorLibroRead, AutorRead, AutorUpdate
from app.modules.autores.unit_of_work import AutoresUoW

_NO_EXISTE = "El autor no existe."


async def _obtener(uow: AutoresUoW, autor_id: int) -> Autor:
    """El autor de la ruta (404 si no existe). Se llama dentro de un bloque `async with uow`."""
    autor = await uow.autores.get_by_id(autor_id)
    if autor is None:
        raise NoEncontrado(_NO_EXISTE)
    return autor


async def crear(uow: AutoresUoW, datos: AutorCreate) -> AutorRead:
    async with uow:
        autor = await uow.autores.add(Autor(**datos.model_dump()))
        return AutorRead.model_validate(autor)


async def listar(uow: AutoresUoW, p: ParametrosPagina) -> Page[AutorRead]:
    async with uow:
        total = await uow.autores.count()
        autores = await uow.autores.get_all(offset=(p.page - 1) * p.size, limit=p.size)
        return envolver([AutorRead.model_validate(a) for a in autores], total=total, page=p.page, size=p.size)


async def obtener(uow: AutoresUoW, autor_id: int) -> AutorRead:
    async with uow:
        return AutorRead.model_validate(await _obtener(uow, autor_id))


async def actualizar(uow: AutoresUoW, autor_id: int, datos: AutorUpdate) -> AutorRead:
    """PATCH: sólo lo enviado (`exclude_unset`)."""
    async with uow:
        autor = await _obtener(uow, autor_id)
        await uow.autores.update(autor, datos.model_dump(exclude_unset=True))
        return AutorRead.model_validate(autor)


async def listar_libros_de_autor(uow: AutoresUoW, autor_id: int, p: ParametrosPagina) -> Page[AutorLibroRead]:
    """Libros vigentes de un autor, por `orden`, con su `rol` y `orden` (404 si el autor no existe).

    El autor es el recurso de la ruta, por eso se lee primero para dar el 404.
    """
    async with uow:
        await _obtener(uow, autor_id)
        total = await uow.autorias.contar_por_autor(autor_id)
        autorias = await uow.autorias.listar_por_autor(autor_id, offset=(p.page - 1) * p.size, limit=p.size)
        items = [
            AutorLibroRead(
                id=la.libro.id,
                isbn=la.libro.isbn,
                titulo=la.libro.titulo,
                precio=la.libro.precio,
                stock=la.libro.stock,
                rol=la.rol,
                orden=la.orden,
            )
            for la in autorias
        ]
        return envolver(items, total=total, page=p.page, size=p.size)
