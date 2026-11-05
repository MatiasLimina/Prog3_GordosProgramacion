"""Repositorios del módulo `usuarios`: un repositorio por entidad.

Heredan `add`, `update` y `get_by_id` de `BaseRepository`; los métodos propios se nombran
por lo que traen. Ninguno confirma: confirmar es del UnitOfWork.
"""
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, IntentoAcceso, Usuario


class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Usuario)

    async def get_by_email(self, email: str) -> Usuario | None:
        """El usuario con ese correo exacto, o `None` (el login decide qué responder)."""
        resultado = await self.session.execute(self._consulta_base().where(Usuario.email == email))
        return resultado.scalar_one_or_none()


class AsignacionRolRepository(BaseRepository[AsignacionRol]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AsignacionRol)

    async def roles_vigentes(self, usuario_id: int) -> list[str]:
        """Roles vigentes del usuario, ordenados: no revocados y sin vencer (RN-04).

        «Sin vencer» se mide con `now()` de la base, el mismo reloj que escribe `desde`.
        """
        consulta = (
            select(AsignacionRol.rol)
            .where(
                AsignacionRol.usuario_id == usuario_id,
                AsignacionRol.revocada_en.is_(None),
                or_(AsignacionRol.vence_en.is_(None), AsignacionRol.vence_en > func.now()),
            )
            .order_by(AsignacionRol.rol)
        )
        return list((await self.session.execute(consulta)).scalars().all())


class IntentoAccesoRepository(BaseRepository[IntentoAcceso]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, IntentoAcceso)


class EventoSeguridadRepository(BaseRepository[EventoSeguridad]):
    """Sólo lo heredado: CHG-14 agrega el listado de `GET /eventos`."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, EventoSeguridad)
