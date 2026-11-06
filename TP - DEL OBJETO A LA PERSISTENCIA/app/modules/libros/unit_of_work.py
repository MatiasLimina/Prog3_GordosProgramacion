"""UoW del módulo `libros`: compone los repositorios con la misma sesión.

`libros` es el dueño del punto único de escritura del stock (`registrar_movimiento`) y
`movimientos` lee el historial. Los `MENSAJES` son los del 409 por nombre de constraint: el UoW
base atrapa el `IntegrityError` (en el flush o en el commit), revierte y lanza `Conflicto`.
"""
from collections.abc import Mapping
from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.unit_of_work import UnitOfWork
from app.modules.libros.repository import LibroRepository, MovimientoStockRepository


class LibrosUoW(UnitOfWork):
    MENSAJES: ClassVar[Mapping[str, str]] = {
        "uq_libro_isbn_vigente": "Ya existe un libro con ese ISBN.",
        "fk_libro_editorial_id_editorial": "La editorial indicada no existe.",
        "fk_libro_genero_id_genero": "El género indicado no existe.",
        "fk_libro_autor_autor_id_autor": "Uno de los autores indicados no existe.",
        "fk_libro_autor_libro_id_libro": "El libro indicado no existe.",
        "pk_libro_autor": "No se puede repetir el mismo autor en un libro.",
        "ck_libro_precio_positivo": "El precio del libro debe ser mayor a cero.",
        "ck_libro_stock_no_negativo": "El stock del libro no puede ser negativo.",
        "ck_libro_autor_orden_positivo": "El orden del autor debe ser mayor o igual a 1.",
        "ck_libro_autor_rol_valido": "El rol del autor no es válido.",
        "movimiento_stock_solo_agregado": (
            "Los movimientos de stock no se modifican ni se borran: un error se corrige con otro movimiento."
        ),
        "fk_movimiento_stock_usuario_id_usuario": "El usuario indicado no existe.",
    }

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.libros = LibroRepository(session)
        self.movimientos = MovimientoStockRepository(session)
