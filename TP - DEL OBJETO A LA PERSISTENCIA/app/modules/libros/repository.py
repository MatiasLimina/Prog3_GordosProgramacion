"""Repositorios del módulo `libros` (CHG-13).

`LibroRepository` es el dueño del PUNTO ÚNICO de escritura del stock (`registrar_movimiento`, RN-11):
el alta del libro (`stock_inicial`), la reposición y las ventas pasan por ahí, y nadie más escribe
`libro.stock`. Ningún repositorio confirma: confirmar es del UnitOfWork de quien llama.
"""
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes, contains_eager, joinedload, selectinload
from sqlalchemy.orm.util import identity_key  # API documentada de SQLAlchemy; no se reexporta en sqlalchemy.orm

from app.core.errors import (
    LibroDadoDeBaja,
    LibroNoEncontrado,
    StockExcedido,
    StockInsuficiente,
)
from app.core.repository import BaseRepository, SoftDeleteRepository
from app.core.tipos import INT32_MAX
from app.modules.libros.models import Libro, LibroAutor, MovimientoStock


@dataclass(frozen=True)
class ResultadoMovimiento:
    """Lo que deja una escritura de stock: el stock resultante, el precio vigente y el movimiento creado.

    `precio` es el del libro en la misma sentencia que bloquea la fila (una venta lo copia al renglón).
    """

    stock: int
    precio: Decimal
    movimiento: MovimientoStock


class LibroRepository(SoftDeleteRepository[Libro]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Libro)

    def _filtrada(self, *, titulo: str | None, genero_id: int | None) -> Select[tuple[Libro]]:
        """Los libros vigentes que cumplen los filtros, SIN precarga.

        `buscar` le agrega las `options(...)` y `contar` no: así el total usa exactamente los mismos
        filtros que la página y su subconsulta no arrastra los `JOIN` de la precarga.
        """
        consulta = self._consulta_base()
        if titulo:
            # `icontains(autoescape=True)`: ILIKE con parámetro ligado y `%` / `_` / `\` escapados,
            # así el texto del usuario nunca es un comodín.
            consulta = consulta.where(Libro.titulo.icontains(titulo, autoescape=True))
        if genero_id is not None:
            consulta = consulta.where(Libro.genero_id == genero_id)
        return consulta

    async def get_detalle(self, libro_id: int) -> Libro | None:
        """El libro vigente con editorial, género y autores precargados (sin consultas al leerlos), o `None`."""
        consulta = (
            self._consulta_base()
            .where(Libro.id == libro_id)
            .options(
                joinedload(Libro.editorial),
                joinedload(Libro.genero),
                selectinload(Libro.autorias).joinedload(LibroAutor.autor),
            )
            # populate_existing: si el Libro ya está en el mapa de identidad (recién creado o
            # modificado en esta sesión) se recargan también sus relaciones; sin esto la precarga
            # se saltea y la respuesta puede salir desactualizada.
            .execution_options(populate_existing=True)
        )
        return (await self.session.execute(consulta)).scalar_one_or_none()

    async def buscar(self, *, titulo: str | None, genero_id: int | None, offset: int, limit: int) -> list[Libro]:
        """Una página de libros vigentes, por título (sin distinguir mayúsculas) y género, con editorial y género."""
        consulta = self._con_editorial_y_genero(self._filtrada(titulo=titulo, genero_id=genero_id))
        return await self._listar(consulta, offset=offset, limit=limit)

    async def contar(self, *, titulo: str | None, genero_id: int | None) -> int:
        """Cuántos libros vigentes cumplen los mismos filtros que `buscar`."""
        return await self._contar(self._filtrada(titulo=titulo, genero_id=genero_id))

    def _con_editorial_y_genero(self, consulta: Select[tuple[Libro]]) -> Select[tuple[Libro]]:
        """Agrega la precarga de lo que muestra un `LibroRead`: editorial y género (relaciones a uno)."""
        return consulta.options(joinedload(Libro.editorial), joinedload(Libro.genero))

    async def listar_por_editorial(self, editorial_id: int, *, offset: int, limit: int) -> list[Libro]:
        """Una página de los libros vigentes de una editorial, con editorial y género."""
        consulta = self._consulta_base().where(Libro.editorial_id == editorial_id)
        return await self._listar(self._con_editorial_y_genero(consulta), offset=offset, limit=limit)

    async def contar_por_editorial(self, editorial_id: int) -> int:
        """Cuántos libros vigentes tiene la editorial (mismo filtro que `listar_por_editorial`)."""
        return await self._contar(self._consulta_base().where(Libro.editorial_id == editorial_id))

    async def listar_por_genero(self, genero_id: int, *, offset: int, limit: int) -> list[Libro]:
        """Una página de los libros vigentes de un género, con editorial y género."""
        consulta = self._consulta_base().where(Libro.genero_id == genero_id)
        return await self._listar(self._con_editorial_y_genero(consulta), offset=offset, limit=limit)

    async def contar_por_genero(self, genero_id: int) -> int:
        """Cuántos libros vigentes tiene el género (mismo filtro que `listar_por_genero`)."""
        return await self._contar(self._consulta_base().where(Libro.genero_id == genero_id))

    async def registrar_movimiento(
        self, libro_id: int, cantidad: int, motivo: str, usuario_id: int, venta_id: int | None = None
    ) -> ResultadoMovimiento:
        """Cambia el stock de un libro vigente y deja el movimiento que lo explica.

        `cantidad` > 0 es una entrada y < 0 una salida; 0 o un valor fuera del rango int32
        (|cantidad| > INT32_MAX) son errores de programación (`ValueError`, sin tocar la base).
        Hace `flush()` y NUNCA `commit()`: confirma el UoW de quien llama.

        Devuelve el stock resultante, el precio vigente y el movimiento (con `id` y `cuando` ya cargados). Rechaza con
        excepciones de dominio, sin escribir nada: `LibroNoEncontrado` (404 si nadie la traduce),
        `LibroDadoDeBaja`, `StockInsuficiente` y `StockExcedido` (409).

        Quien registre varias líneas en una transacción (ventas) MUST llamar en orden ascendente de
        `libro_id`: así dos transacciones toman los bloqueos de fila en el mismo orden y no se traban
        entre sí (deadlock). Quien necesite el stock o un id DESPUÉS de un posible rollback los guarda
        como `int` antes del bloque (ver la advertencia de `core/unit_of_work.py`); el `movimiento` se
        serializa dentro del bloque.
        """
        if cantidad == 0:
            raise ValueError("La cantidad de un movimiento de stock no puede ser cero.")
        if not -INT32_MAX <= cantidad <= INT32_MAX:
            raise ValueError(f"La cantidad de un movimiento de stock debe estar entre -{INT32_MAX} y {INT32_MAX}.")
        # Una sola sentencia: la base bloquea la fila y reevalúa el WHERE si otra transacción la
        # cambió (READ COMMITTED), así que no hay actualizaciones perdidas ni stock negativo.
        # Las entradas se acotan con `INT32_MAX - cantidad` (calculado acá y ligado como parámetro):
        # la base nunca hace una suma que desborde int32 (daría `DataError`, no un 409).
        limite = Libro.stock + cantidad >= 0 if cantidad < 0 else Libro.stock <= INT32_MAX - cantidad
        resultado = await self.session.execute(
            update(Libro)
            .where(Libro.id == libro_id, Libro.borrado_en.is_(None), limite)
            .values(stock=Libro.stock + cantidad)
            .returning(Libro.stock, Libro.precio)
            .execution_options(synchronize_session=False)
        )
        fila = resultado.one_or_none()
        if fila is None:
            await self._rechazar(libro_id, cantidad)
        stock, precio = fila.stock, fila.precio
        self._sincronizar_libro_cargado(libro_id, stock)
        movimiento = MovimientoStock(
            libro_id=libro_id, cantidad=cantidad, motivo=motivo, usuario_id=usuario_id, venta_id=venta_id
        )
        self.session.add(movimiento)
        await self.session.flush()
        return ResultadoMovimiento(stock=stock, precio=precio, movimiento=movimiento)

    def _sincronizar_libro_cargado(self, libro_id: int, stock: int) -> None:
        """Deja el `Libro` ya cargado en la sesión (si lo hay) con el stock que devolvió la base.

        No se usa `synchronize_session`: con "evaluate" o "fetch" SQLAlchemy calcula `stock + cantidad`
        en Python sobre el valor en memoria, y si otra sesión cambió el stock antes el objeto queda
        con un valor que la base nunca tuvo. `set_committed_value` pone el valor real sin marcar el
        objeto como modificado ni emitir sentencias.
        """
        cargado = self.session.sync_session.identity_map.get(identity_key(Libro, libro_id))
        if cargado is not None:
            attributes.set_committed_value(cargado, "stock", stock)

    async def _rechazar(self, libro_id: int, cantidad: int) -> None:
        """Elige la excepción que explica por qué el `UPDATE` no tocó ninguna fila (siempre lanza).

        La lectura es por COLUMNAS y no con `get_by_id_including_deleted`: `session.get` devolvería
        del mapa de identidad un `Libro` ya cargado, con un stock o un `borrado_en` viejos, y el
        mensaje mentiría. Corre sólo en el camino de rechazo, después de la escritura fallida: no es
        «consultar antes para validar».
        """
        fila = (
            await self.session.execute(select(Libro.stock, Libro.borrado_en).where(Libro.id == libro_id))
        ).one_or_none()
        if fila is None:
            raise LibroNoEncontrado(libro_id)
        stock, borrado_en = fila
        if borrado_en is not None:
            raise LibroDadoDeBaja(libro_id)
        if cantidad < 0:
            raise StockInsuficiente(libro_id, disponible=stock, pedido=-cantidad)
        raise StockExcedido(libro_id)


class LibroAutorRepository(BaseRepository[LibroAutor]):
    """Lecturas de las autorías (la relación libro-autor con `rol` y `orden`)."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, LibroAutor)

    def _de_autor(self, autor_id: int) -> Select[tuple[LibroAutor]]:
        """Las autorías del autor sobre libros vigentes, SIN precarga (la comparten `listar` y `contar`)."""
        return (
            self._consulta_base()
            .join(Libro, LibroAutor.libro_id == Libro.id)
            .where(LibroAutor.autor_id == autor_id, Libro.borrado_en.is_(None))
        )

    async def listar_por_autor(self, autor_id: int, *, offset: int, limit: int) -> list[LibroAutor]:
        """Una página de las autorías del autor sobre libros vigentes, por `orden` (con el libro precargado)."""
        consulta = (
            self._de_autor(autor_id)
            .options(contains_eager(LibroAutor.libro))  # reusa el JOIN de `_de_autor`
            # `_listar` agrega la clave primaria al final: el orden es total.
            .order_by(LibroAutor.orden)
        )
        return await self._listar(consulta, offset=offset, limit=limit)

    async def contar_por_autor(self, autor_id: int) -> int:
        """Cuántos libros vigentes tiene el autor (mismo filtro que `listar_por_autor`)."""
        return await self._contar(self._de_autor(autor_id))


class MovimientoStockRepository(BaseRepository[MovimientoStock]):
    """Lecturas del historial de stock. Sólo lectura: los movimientos los crea `registrar_movimiento`."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MovimientoStock)

    def _de_libro(self, libro_id: int) -> Select[tuple[MovimientoStock]]:
        return self._consulta_base().where(MovimientoStock.libro_id == libro_id)

    async def listar_de_libro(self, libro_id: int, *, offset: int, limit: int) -> list[MovimientoStock]:
        """Una página de los movimientos del libro, en orden de `id` (el orden en que ocurrieron)."""
        return await self._listar(self._de_libro(libro_id), offset=offset, limit=limit)

    async def contar_de_libro(self, libro_id: int) -> int:
        return await self._contar(self._de_libro(libro_id))
