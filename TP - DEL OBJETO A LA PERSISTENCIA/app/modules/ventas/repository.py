"""Repositorio del módulo `ventas` (CHG-15, mínimo). No confirma: confirmar es del UoW.

Nace con lo que necesita `GET /clientes/{id}/ventas`: la precarga del detalle de una venta y el
listado de las ventas de un cliente. CHG-16 (Matias) lo extiende (detalle por id, listado general,
`/mis-ventas`) y lo compone en su `VentasUoW`.
"""
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.repository import BaseRepository
from app.modules.ventas.models import RenglonVenta, Venta


class VentaRepository(BaseRepository[Venta]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Venta)

    def _con_detalle(self, consulta: Select[tuple[Venta]]) -> Select[tuple[Venta]]:
        """Agrega la precarga de lo que muestra un `VentaRead`: cliente, renglones y libro de cada renglón.

        El cliente y el libro son relaciones a uno (`joinedload`); los renglones, una colección
        (`selectinload`): la cantidad de consultas no depende de cuántas ventas ni renglones haya.
        No filtra por borrado lógico: una venta vieja muestra el libro aunque esté dado de baja.
        """
        return consulta.options(
            joinedload(Venta.cliente),
            selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
        )

    def _de_cliente(self, cliente_id: int) -> Select[tuple[Venta]]:
        """Las ventas de un cliente, SIN precarga: `contar_de_cliente` usa los mismos filtros que la página."""
        return self._consulta_base().where(Venta.cliente_id == cliente_id)

    async def listar_de_cliente(self, cliente_id: int, *, offset: int, limit: int) -> list[Venta]:
        """Una página de las ventas del cliente, en orden de `id`, con el detalle precargado."""
        return await self._listar(self._con_detalle(self._de_cliente(cliente_id)), offset=offset, limit=limit)

    async def contar_de_cliente(self, cliente_id: int) -> int:
        """Cuántas ventas tiene el cliente (sin precarga, así la subconsulta del total no arrastra `JOIN`)."""
        return await self._contar(self._de_cliente(cliente_id))
