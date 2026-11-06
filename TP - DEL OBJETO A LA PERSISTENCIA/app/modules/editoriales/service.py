from app.core.errors import NoEncontrado
from app.core.paginacion import Page, ParametrosPagina, envolver
from app.modules.editoriales.models import Editorial
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate
from app.modules.editoriales.unit_of_work import EditorialesUoW
from app.modules.libros.schemas import LibroRead

_NO_EXISTE = "La editorial no existe."


async def _obtener(uow: EditorialesUoW, editorial_id: int) -> Editorial:
    """La editorial de la ruta (404 si no existe). Se llama dentro de un bloque `async with uow`."""
    editorial = await uow.editoriales.get_by_id(editorial_id)
    if editorial is None:
        raise NoEncontrado(_NO_EXISTE)
    return editorial


async def crear(uow: EditorialesUoW, datos: EditorialCreate) -> EditorialRead:
    """Alta: se escribe y la base decide (UNIQUE de `nombre` -> 409 con mensaje propio, sin consulta previa)."""
    async with uow:
        editorial = await uow.editoriales.add(Editorial(**datos.model_dump()))
        return EditorialRead.model_validate(editorial)


async def listar(uow: EditorialesUoW, p: ParametrosPagina) -> Page[EditorialRead]:
    async with uow:
        total = await uow.editoriales.count()
        editoriales = await uow.editoriales.get_all(offset=(p.page - 1) * p.size, limit=p.size)
        return envolver(
            [EditorialRead.model_validate(e) for e in editoriales], total=total, page=p.page, size=p.size
        )


async def obtener(uow: EditorialesUoW, editorial_id: int) -> EditorialRead:
    async with uow:
        return EditorialRead.model_validate(await _obtener(uow, editorial_id))


async def actualizar(uow: EditorialesUoW, editorial_id: int, datos: EditorialUpdate) -> EditorialRead:
    """PATCH: sólo lo enviado (`exclude_unset`); un nombre ocupado es 409 al escribir."""
    async with uow:
        editorial = await _obtener(uow, editorial_id)
        await uow.editoriales.update(editorial, datos.model_dump(exclude_unset=True))
        return EditorialRead.model_validate(editorial)


async def listar_libros(uow: EditorialesUoW, editorial_id: int, p: ParametrosPagina) -> Page[LibroRead]:
    """Libros vigentes de una editorial (404 si la editorial no existe).

    La editorial es el recurso de la ruta, por eso se lee primero para dar el 404.
    """
    async with uow:
        await _obtener(uow, editorial_id)
        total = await uow.libros.contar_por_editorial(editorial_id)
        libros = await uow.libros.listar_por_editorial(editorial_id, offset=(p.page - 1) * p.size, limit=p.size)
        return envolver([LibroRead.model_validate(l) for l in libros], total=total, page=p.page, size=p.size)
