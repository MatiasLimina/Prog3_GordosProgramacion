"""Repositorios del módulo `usuarios`: un repositorio por entidad.

Heredan `add`, `update` y `get_by_id` de `BaseRepository`; los métodos propios se nombran
por lo que traen. Ninguno confirma: confirmar es del UnitOfWork.
"""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, IntentoAcceso, Usuario


@dataclass(frozen=True)
class ConteoFallos:
    """Resultado de `contar_fallos_recientes`: `mas_viejo` es `None` si no hay fallos.

    `ahora` es el reloj de la base, el mismo que escribe `intento_acceso.cuando`.
    """

    fallos: int
    mas_viejo: datetime | None
    ahora: datetime


# Una sola sentencia, parámetros ligados. Los fallos cuentan si son del mismo correo e IP,
# de los últimos `:ventana` segundos (la fija el servicio, RN-07) y POSTERIORES al último éxito del mismo correo e IP (RN-07: un login
# correcto reinicia la cuenta sin borrar filas). Usa ix_intento_acceso_email_ip_cuando.
_CONTAR_FALLOS = text(
    """
    SELECT count(*) AS fallos, min(cuando) AS mas_viejo, now() AS ahora
    FROM intento_acceso
    WHERE email = :email AND ip = :ip AND NOT exito
      AND cuando > now() - make_interval(secs => :ventana)
      AND cuando > COALESCE(
            (SELECT max(cuando) FROM intento_acceso
             WHERE email = :email AND ip = :ip AND exito),
            '-infinity')
    """
)


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

    async def contar_fallos_recientes(self, email: str, ip: str, ventana_segundos: int) -> ConteoFallos:
        """Fallos vigentes del correo desde esa IP (dentro de la ventana, posteriores al último éxito).

        La ventana la pasa quien llama (el servicio, con `VENTANA_SEGUNDOS`): el repositorio no
        importa del servicio y así el valor vive en un solo lugar.
        """
        parametros = {"email": email, "ip": ip, "ventana": ventana_segundos}
        fila = (await self.session.execute(_CONTAR_FALLOS, parametros)).one()
        return ConteoFallos(fallos=fila.fallos, mas_viejo=fila.mas_viejo, ahora=fila.ahora)


class EventoSeguridadRepository(BaseRepository[EventoSeguridad]):
    """Sólo lo heredado: CHG-14 agrega el listado de `GET /eventos`."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, EventoSeguridad)
