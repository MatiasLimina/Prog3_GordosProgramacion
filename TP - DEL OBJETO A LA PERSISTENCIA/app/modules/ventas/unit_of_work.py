"""UoW del módulo `ventas`: compone los repositorios que sus operaciones necesitan, con la misma sesión.

`ventas` es el propio; `libros` aporta el punto único de escritura del stock (RN-11); `clientes`
resuelve «mi cliente» en `/mis-ventas`; `asignaciones` da los roles vigentes del detalle. `MENSAJES`
elige el 409 por nombre de constraint.
"""
from collections.abc import Mapping
from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.unit_of_work import UnitOfWork
from app.modules.clientes.repository import ClienteRepository
from app.modules.libros.repository import LibroRepository
from app.modules.usuarios.repository import AsignacionRolRepository
from app.modules.ventas.repository import VentaRepository


class VentasUoW(UnitOfWork):
    MENSAJES: ClassVar[Mapping[str, str]] = {
        "fk_venta_cliente_id_cliente": "El cliente indicado no existe.",
        # Defensa: el punto único de stock ya rechazó el libro antes de insertar el renglón.
        "fk_renglon_venta_libro_id_libro": "El libro indicado no existe.",
    }

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.ventas = VentaRepository(session)
        self.libros = LibroRepository(session)
        self.clientes = ClienteRepository(session)
        self.asignaciones = AsignacionRolRepository(session)
