"""Repositorios del módulo `usuarios`: un repositorio por entidad.

Heredan `add`, `update` y `get_by_id` de `BaseRepository`; los métodos propios se nombran
por lo que traen. Ninguno confirma: confirmar es del UnitOfWork.
"""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, or_, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import UsuarioNoEncontrado, constraint_violada
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


# FK del usuario de la asignación (naming convention `fk_<tabla>_<columna>_<tabla_ref>`).
FK_ASIGNACION_USUARIO = "fk_asignacion_rol_usuario_id_usuario"


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

    @staticmethod
    def _vigente():
        """Condición de «vigente» (RN-04): no revocada y sin vencer, con el reloj de la base."""
        return (
            AsignacionRol.revocada_en.is_(None),
            or_(AsignacionRol.vence_en.is_(None), AsignacionRol.vence_en > func.now()),
        )

    async def historial(self, usuario_id: int) -> list[AsignacionRol]:
        """Todas las asignaciones del usuario (vigentes, vencidas y revocadas), por `id`."""
        consulta = self._consulta_base().where(AsignacionRol.usuario_id == usuario_id)
        return await self._listar(consulta)

    async def asignar(self, asignacion: AsignacionRol) -> AsignacionRol:
        """Agrega la asignación sin consultar antes si el usuario existe: la base decide.

        EXCEPCIÓN EXPLÍCITA a AGENTS §8 («FK -> 409»): la consigna da 404 a
        `POST /usuarios/{id}/roles` porque el usuario es el recurso de la ruta, así que la FK
        `fk_asignacion_rol_usuario_id_usuario` violada se traduce a `UsuarioNoEncontrado` (gana la
        consigna). Se sigue escribiendo sin consulta previa. Cualquier otra constraint (el índice
        único parcial del rol vigente) se re-lanza tal cual y el UoW la traduce a 409. El `try`
        envuelve sólo el flush y vive DENTRO del bloque del UoW, como `PerfilClienteRepository.add`.

        `desde` (default del servidor) vuelve en el `RETURNING` del INSERT (`eager_defaults`):
        leerlo después del flush no dispara ninguna consulta.
        """
        try:
            return await self.add(asignacion)
        except IntegrityError as e:
            if constraint_violada(e) == FK_ASIGNACION_USUARIO:
                raise UsuarioNoEncontrado(asignacion.usuario_id) from None
            raise

    async def cerrar_vencida(self, usuario_id: int, rol: str) -> int:
        """Cierra la asignación abierta pero vencida de ese rol y devuelve cuántas cerró (0 o 1).

        Una sola sentencia, sin leer antes: `UPDATE ... SET revocada_en = vence_en WHERE ...
        AND vence_en <= now()`. Escribe `vence_en` y no `now()` porque nadie revocó la fila: dejó
        de valer cuando venció, y así el historial no inventa una revocación posterior. El filtro
        `vence_en <= now()` (reloj de la base, el mismo de `roles_vigentes`) deja intacta una
        asignación todavía vigente: el INSERT siguiente choca con el índice único parcial y da 409.
        """
        consulta = (
            update(AsignacionRol)
            .where(
                AsignacionRol.usuario_id == usuario_id,
                AsignacionRol.rol == rol,
                AsignacionRol.revocada_en.is_(None),
                AsignacionRol.vence_en.is_not(None),
                AsignacionRol.vence_en <= func.now(),
            )
            .values(revocada_en=AsignacionRol.vence_en)
            .execution_options(synchronize_session="fetch")
        )
        return (await self.session.execute(consulta)).rowcount

    async def revocar_vigente(self, usuario_id: int, rol: str) -> AsignacionRol | None:
        """Revoca la asignación vigente de ese rol y la devuelve; `None` si no había ninguna.

        Una sola sentencia atómica, `UPDATE ... RETURNING`, sin leer antes: la base bloquea la
        fila y, si otra transacción la cambió, reevalúa el `WHERE`. Acá sí es `now()`: es una
        revocación real. «Vigente» excluye la fila abierta pero vencida (no hay nada que revocar).
        La fila no se borra: sólo se escribe `revocada_en`.
        """
        consulta = (
            update(AsignacionRol)
            .where(AsignacionRol.usuario_id == usuario_id, AsignacionRol.rol == rol, *self._vigente())
            .values(revocada_en=func.now())
            .returning(AsignacionRol)
            .execution_options(populate_existing=True)
        )
        return (await self.session.execute(consulta)).scalars().one_or_none()

    async def bloquear_admins_vigentes(self) -> list[int]:
        """Bloquea las filas `ADMIN` vigentes (`FOR UPDATE`) y devuelve sus `usuario_id`, por `id`.

        Es el primer paso de RN-05: dos ADMIN que se revocan a la vez verían cada uno su propia
        revocación y no la del otro (*write skew*) y el sistema quedaría con cero. Bloquear estas
        filas serializa las revocaciones de `ADMIN`: la segunda espera, y cuando la primera
        confirma, la base reevalúa el `WHERE` y ve el resultado.

        Los `usuario_id` devueltos son los de las filas que TODAVÍA son ADMIN vigentes después de la
        espera: quien llama comprueba que su actor esté entre ellos (si otra transacción le revocó el
        `ADMIN` mientras esperaba, ya no está), porque su `SOLO_ADMIN` se leyó antes del bloqueo.

        Trae las filas en vez de contarlas porque PostgreSQL no admite `FOR UPDATE` con funciones
        de agregado: el conteo va aparte (`contar_admins_vigentes`), después de revocar.
        `ORDER BY id` hace que toda transacción tome los bloqueos en el mismo orden; sin él, una
        podría bloquear A y esperar B mientras otra bloquea B y espera A (*deadlock* que
        PostgreSQL corta con un error: 500 en vez del 409 esperado).
        """
        consulta = (
            select(AsignacionRol.usuario_id)
            .where(AsignacionRol.rol == "ADMIN", *self._vigente())
            .order_by(AsignacionRol.id)
            .with_for_update()
        )
        return list((await self.session.execute(consulta)).scalars().all())

    async def contar_admins_vigentes(self) -> int:
        """Cuenta las asignaciones `ADMIN` vigentes, sin bloqueo (segundo paso de RN-05).

        Va DESPUÉS de revocar y en la misma transacción: ve la propia revocación y, como en
        READ COMMITTED cada sentencia toma una foto nueva, también lo que confirmó quien tenía
        el bloqueo.
        """
        consulta = (
            select(func.count()).select_from(AsignacionRol).where(AsignacionRol.rol == "ADMIN", *self._vigente())
        )
        return (await self.session.execute(consulta)).scalar_one()


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
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, EventoSeguridad)

    async def listar_recientes(self, offset: int, limit: int) -> list[EventoSeguridad]:
        """Una página del historial, del más reciente al más viejo (`cuando DESC, id DESC`).

        Dentro de una transacción `cuando` es igual para todas sus líneas: el `id` desempata. El
        `ORDER BY id` que agrega `_listar` queda como desempate redundante al final.
        """
        consulta = self._consulta_base().order_by(EventoSeguridad.cuando.desc(), EventoSeguridad.id.desc())
        return await self._listar(consulta, offset=offset, limit=limit)
