"""Repositorios del módulo `clientes` (CHG-15). Ninguno confirma: confirmar es del UoW."""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.errors import ClienteNoEncontrado, constraint_violada
from app.core.repository import BaseRepository
from app.modules.clientes.models import Cliente, PerfilCliente

FK_PERFIL_CLIENTE = "fk_perfil_cliente_cliente_id_cliente"


class ClienteRepository(BaseRepository[Cliente]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Cliente)

    async def get_detalle(self, cliente_id: int) -> Cliente | None:
        """El cliente con su perfil precargado (sin consultas al leerlo), o `None` si no existe."""
        consulta = (
            self._consulta_base()
            .where(Cliente.id == cliente_id)
            .options(joinedload(Cliente.perfil))
            # populate_existing: si el Cliente ya está en el mapa de identidad (recién creado o
            # modificado en esta sesión) se recargan también sus relaciones; sin esto la precarga
            # se saltea y el perfil puede salir desactualizado.
            .execution_options(populate_existing=True)
        )
        return (await self.session.execute(consulta)).scalar_one_or_none()


class PerfilClienteRepository(BaseRepository[PerfilCliente]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, PerfilCliente)

    async def add(self, perfil: PerfilCliente) -> PerfilCliente:
        """Agrega el perfil sin consultar antes si el cliente existe: la base decide.

        FK del cliente violada -> `ClienteNoEncontrado` (404: el recurso de la ruta no existe).
        Cualquier otro `IntegrityError` (el UNIQUE del segundo perfil) se re-lanza tal cual y el
        UoW lo traduce a 409. El `try` envuelve sólo el flush del perfil y vive DENTRO del bloque
        del UoW: si el error llegara sin atrapar, el UoW lo volvería 409 y la FK nunca daría 404.
        La excepción de dominio sale enseguida, así la transacción abortada no se sigue usando.
        """
        try:
            return await super().add(perfil)
        except IntegrityError as e:
            if constraint_violada(e) == FK_PERFIL_CLIENTE:
                raise ClienteNoEncontrado(perfil.cliente_id) from None
            raise
