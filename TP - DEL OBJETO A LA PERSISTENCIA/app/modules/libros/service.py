from app.core.errors import LibroNoEncontrado
from app.core.paginacion import Page, ParametrosPagina, envolver
from app.modules.libros.models import Libro, LibroAutor
from app.modules.libros.schemas import (
    AutorEnLibroRead,
    EditorialSimpleRead,
    GeneroSimpleRead,
    LibroCreate,
    LibroDetalleRead,
    LibroRead,
    LibroUpdate,
    MovimientoStockRead,
    ReponerIn,
    ReposicionRead,
)
from app.modules.libros.unit_of_work import LibrosUoW


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


async def crear(uow: LibrosUoW, datos: LibroCreate, usuario_id: int) -> LibroDetalleRead:
    """Alta de libro con relaciones y, si hay `stock_inicial`, su movimiento «Stock inicial».

    Todo en un solo bloque `async with uow`: el libro, sus autorías y el movimiento se confirman
    juntos o ninguno. Ningún if verifica si los IDs existen: se escribe y la base responde (el UoW
    traduce la FK o el UNIQUE a 409). El stock nunca se escribe en el constructor: entra por
    `registrar_movimiento`, el único punto de escritura (RN-11).
    """
    datos_libro = datos.model_dump(exclude={"autores", "stock_inicial"})
    libro = Libro(**datos_libro)  # stock = 0 por defecto: sólo cambia con registrar_movimiento
    for a in datos.autores:
        libro.autorias.append(LibroAutor(autor_id=a.autor_id, rol=a.rol, orden=a.orden))

    async with uow:
        await uow.libros.add(libro)
        if datos.stock_inicial > 0:
            await uow.libros.registrar_movimiento(libro.id, datos.stock_inicial, "Stock inicial", usuario_id)
        detalle = await uow.libros.get_detalle(libro.id)
        return _armar_detalle(detalle)


async def obtener(uow: LibrosUoW, libro_id: int) -> LibroDetalleRead:
    """Detalle de un libro vigente sin N+1: editorial, género y autores se precargan en el repositorio."""
    async with uow:
        libro = await uow.libros.get_detalle(libro_id)
        if libro is None:
            raise LibroNoEncontrado(libro_id)
        return _armar_detalle(libro)


async def listar(
    uow: LibrosUoW, p: ParametrosPagina, titulo: str | None = None, genero_id: int | None = None
) -> Page[LibroRead]:
    """Página de libros vigentes (Ej3), con el total calculado con los mismos filtros."""
    async with uow:
        total = await uow.libros.contar(titulo=titulo, genero_id=genero_id)
        libros = await uow.libros.buscar(
            titulo=titulo, genero_id=genero_id, offset=(p.page - 1) * p.size, limit=p.size
        )
        return envolver([LibroRead.model_validate(l) for l in libros], total=total, page=p.page, size=p.size)


async def actualizar(uow: LibrosUoW, libro_id: int, datos: LibroUpdate) -> LibroDetalleRead:
    """Actualización parcial de un libro vigente (PATCH con `exclude_unset`): sólo título y precio."""
    async with uow:
        libro = await uow.libros.get_by_id(libro_id)  # vigente: uno dado de baja es 404
        if libro is None:
            raise LibroNoEncontrado(libro_id)
        await uow.libros.update(libro, datos.model_dump(exclude_unset=True))
        detalle = await uow.libros.get_detalle(libro_id)
        return _armar_detalle(detalle)


async def dar_de_baja(uow: LibrosUoW, libro_id: int) -> None:
    """Baja lógica (`borrado_en`): el libro sale del catálogo pero sus datos, autorías y movimientos se conservan.

    Una segunda baja es 404: el libro ya no es vigente.
    """
    async with uow:
        libro = await uow.libros.get_by_id(libro_id)
        if libro is None:
            raise LibroNoEncontrado(libro_id)
        await uow.libros.soft_delete(libro)


async def reponer(uow: LibrosUoW, libro_id: int, datos: ReponerIn, usuario_id: int) -> ReposicionRead:
    """Reposición de stock: una entrada por el punto único, con el ADMIN de la petición como actor.

    El resultado del punto único trae el stock resultante y el movimiento creado, así que no hace
    falta otra lectura. Libro inexistente: 404 (`LibroNoEncontrado`); dado de baja o stock que
    pasaría el máximo: 409, ya traducidos por el repositorio y el handler de la app.
    """
    async with uow:
        resultado = await uow.libros.registrar_movimiento(
            libro_id, datos.cantidad, datos.motivo or "Reposición", usuario_id
        )
        return ReposicionRead(
            libro_id=libro_id,
            stock=resultado.stock,
            movimiento=MovimientoStockRead.model_validate(resultado.movimiento),
        )


async def listar_movimientos(uow: LibrosUoW, libro_id: int, p: ParametrosPagina) -> Page[MovimientoStockRead]:
    """Historial de stock de un libro, en el orden en que ocurrió.

    También de un libro dado de baja: sus datos se conservan y el historial es de ADMIN. El libro
    es el recurso de la ruta, por eso se lee primero para dar el 404.
    """
    async with uow:
        if await uow.libros.get_by_id_including_deleted(libro_id) is None:
            raise LibroNoEncontrado(libro_id)
        total = await uow.movimientos.contar_de_libro(libro_id)
        movimientos = await uow.movimientos.listar_de_libro(libro_id, offset=(p.page - 1) * p.size, limit=p.size)
        return envolver(
            [MovimientoStockRead.model_validate(m) for m in movimientos], total=total, page=p.page, size=p.size
        )
