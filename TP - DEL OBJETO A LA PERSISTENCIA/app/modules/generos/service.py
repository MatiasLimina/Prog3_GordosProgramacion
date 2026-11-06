from app.core.errors import NoEncontrado
from app.core.paginacion import Page, ParametrosPagina, envolver
from app.modules.generos.models import Genero
from app.modules.generos.schemas import GeneroCreate, GeneroRead
from app.modules.generos.unit_of_work import GenerosUoW
from app.modules.libros.schemas import LibroRead

_NO_EXISTE = "El género no existe."


async def _obtener(uow: GenerosUoW, genero_id: int) -> Genero:
    """El género de la ruta (404 si no existe). Se llama dentro de un bloque `async with uow`."""
    genero = await uow.generos.get_by_id(genero_id)
    if genero is None:
        raise NoEncontrado(_NO_EXISTE)
    return genero


async def crear(uow: GenerosUoW, datos: GeneroCreate) -> GeneroRead:
    """Alta: se escribe y la base decide (UNIQUE de `nombre` -> 409 con mensaje propio, sin consulta previa)."""
    async with uow:
        genero = await uow.generos.add(Genero(**datos.model_dump()))
        return GeneroRead.model_validate(genero)


async def listar(uow: GenerosUoW, p: ParametrosPagina) -> Page[GeneroRead]:
    async with uow:
        total = await uow.generos.count()
        generos = await uow.generos.get_all(offset=(p.page - 1) * p.size, limit=p.size)
        return envolver([GeneroRead.model_validate(g) for g in generos], total=total, page=p.page, size=p.size)


async def listar_libros(uow: GenerosUoW, genero_id: int, p: ParametrosPagina) -> Page[LibroRead]:
    """Libros vigentes de un género (404 si el género no existe).

    El género es el recurso de la ruta, por eso se lee primero para dar el 404.
    """
    async with uow:
        await _obtener(uow, genero_id)
        total = await uow.libros.contar_por_genero(genero_id)
        libros = await uow.libros.listar_por_genero(genero_id, offset=(p.page - 1) * p.size, limit=p.size)
        return envolver([LibroRead.model_validate(l) for l in libros], total=total, page=p.page, size=p.size)
