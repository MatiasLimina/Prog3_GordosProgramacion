"""Servicios de autenticación (CHG-11).

Reciben el UoW (y los parámetros de seguridad) ya construidos por el router y abren el
bloque `async with`; nunca construyen un UoW ni lanzan `HTTPException`.
"""
import logging
import math
from dataclasses import dataclass
from datetime import datetime

from app.core.dependencies import MENSAJE_SIN_PERMISO, ParametrosSeguridad, UsuarioActual
from app.core.errors import (
    AdminConVencimiento,
    AutoRevocacionAdmin,
    DemasiadosIntentos,
    NoAutenticado,
    PeticionInvalida,
    RolNoVigente,
    SinAdministradores,
    SinPermiso,
    UsuarioNoEncontrado,
)
from app.core.paginacion import Page, ParametrosPagina, envolver
from app.core.security import emitir_token, hashear_password, verificar_password
from app.modules.clientes.models import Cliente
from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, IntentoAcceso, Usuario
from app.modules.usuarios.schemas import (
    AsignacionRolCreate,
    AsignacionRolRead,
    AuthYoRead,
    CambioPasswordCreate,
    EventoSeguridadRead,
    LoginCreate,
    RegistroCreate,
    UsuarioCreate,
    UsuarioRead,
)
from app.modules.usuarios.unit_of_work import IntentosUoW, UsuariosUoW

logger = logging.getLogger(__name__)

MENSAJE_CREDENCIALES = "Correo o contraseña incorrectos."

# Las fija la consigna (RN-07), no son configuración.
LIMITE_FALLOS = 5
VENTANA_SEGUNDOS = 60


def calcular_retry_after(ahora: datetime, mas_viejo: datetime) -> int:
    """Segundos hasta que el fallo más viejo que cuenta salga de la ventana, entre 1 y 60.

    Se redondea hacia arriba (un cliente que reintenta antes vuelve a recibir 429) y se
    acota: nunca 0, aunque falten milésimas, ni más de la ventana si el reloj se desfasa.
    """
    faltan = VENTANA_SEGUNDOS - (ahora - mas_viejo).total_seconds()
    return min(VENTANA_SEGUNDOS, max(1, math.ceil(faltan)))


async def registrar(uow: UsuariosUoW, datos: RegistroCreate, seg: ParametrosSeguridad) -> UsuarioRead:
    """Auto-registro (RN-02): usuario, rol CLIENTE y ficha de cliente, las tres filas o ninguna.

    - El hash se calcula ANTES de abrir el bloque: bcrypt tarda ~300 ms y no debe correr con
      una conexión tomada.
    - No se consulta antes si el correo existe: se escribe y la base decide. El UNIQUE de
      `usuario.email` o de `cliente.email` revienta en el `flush`, el UoW revierte las tres
      filas y lo traduce a `Conflicto` (409). Así nunca se vincula una ficha de cliente
      que ya existía.
    - No inicia sesión (no hay cookie) y no deja evento de seguridad: RN-16 nombra el alta
      de personal, el cambio de rol y el cambio de contraseña, no el auto-registro.
    - La respuesta no lee `AsignacionRol.desde`: su default lo pone el servidor y queda
      expirado tras el flush (leerlo sería carga perezosa).
    """
    password_hash = await hashear_password(datos.password, costo=seg.costo, semaforo=seg.semaforo)
    async with uow:
        usuario = await uow.usuarios.add(
            Usuario(email=datos.email, nombre=datos.nombre, password_hash=password_hash)
        )
        await uow.asignaciones.add(AsignacionRol(usuario_id=usuario.id, rol="CLIENTE"))
        await uow.clientes.add(Cliente(nombre=datos.nombre, email=datos.email, usuario_id=usuario.id))
        return UsuarioRead.model_validate(usuario)


@dataclass(frozen=True)
class SesionIniciada:
    """Lo que el servicio de login entrega al router: el token sólo sale de acá hacia la cookie."""

    token: str
    debe_cambiar_password: bool
    expira_en_segundos: int


async def _anotar_intento(intentos: IntentosUoW, email: str, ip: str, exito: bool) -> None:
    # DISTINTO: única escritura del sistema con sesión y transacción propias (IntentosUoW),
    #   que se confirma siempre, falle o no la petición.
    # POR QUÉ: el fallo que se quiere contar es el mismo que revierte la transacción de la
    #   petición; si compartiera el UoW, el 401 borraría la fila y RN-07 nunca bloquearía.
    # COSTO: deja filas aunque la petición falle, y usa una segunda sesión (una conexión
    #   más del pool, aunque nunca al mismo tiempo que la de la petición).
    async with intentos:
        await intentos.intentos.add(IntentoAcceso(email=email, ip=ip, exito=exito))


@dataclass(frozen=True)
class _Credenciales:
    """Lo que el login lee de la base, en valores simples (sin objetos ORM)."""

    existe: bool
    usuario_id: int | None
    password_hash: str
    activo: bool
    debe_cambiar_password: bool
    roles: list[str]


async def _verificar_o_fallar(password: str, password_hash: str, usuario_id: int | None, seg: ParametrosSeguridad) -> bool:
    """`verificar_password` que trata un hash corrupto como contraseña incorrecta (nunca 500).

    bcrypt lanza `ValueError` («Invalid salt») si el hash guardado está dañado: se avisa en el
    log con el id del usuario (jamás con el hash) y se devuelve `False`, igual que un fallo normal.
    """
    try:
        return await verificar_password(password, password_hash, semaforo=seg.semaforo)
    except ValueError:
        logger.warning("password_hash inválido para el usuario id=%s", usuario_id)
        return False


async def iniciar_sesion(
    uow: UsuariosUoW, intentos: IntentosUoW, datos: LoginCreate, ip: str, seg: ParametrosSeguridad
) -> SesionIniciada:
    """Login en orden fijo (RN-07, RN-08, Ej7); devuelve el token sólo para que el router lo ponga en la cookie.

    1. Límite de intentos: con 5 fallos del mismo correo e IP en 60 s se lanza
       `DemasiadosIntentos` ANTES de buscar al usuario y sin calcular ningún hash. El 429 no
       se anota: no es un intento verificado, y anotarlo extendería el bloqueo mientras el
       atacante insista.
    2. Verificación: contra el hash del usuario o, si el correo no existe, contra el hash
       ficticio del arranque (RN-08: misma respuesta y el mismo trabajo bcrypt).
    3. Anotación del intento (sesión propia, ver `_anotar_intento`) y recién después el 401.

    La lectura (conteo, usuario y roles) va en un bloque corto que termina ANTES de
    verificar: bcrypt tarda ~300 ms y no debe correr con una conexión tomada. Los roles se
    leen en ese mismo bloque para no abrir un segundo; son «vigentes al emitir» con
    milisegundos de diferencia. Costo asumido: esa lectura sólo ocurre si el correo existe
    (~1 ms de diferencia frente a ~250 ms de bcrypt).

    Un usuario inactivo con la contraseña correcta da el mismo 401 y se anota como fallo (no
    revela que la cuenta existe). Un `password_hash` corrupto también es un fallo.
    """
    async with uow:
        conteo = await uow.intentos.contar_fallos_recientes(datos.email, ip, VENTANA_SEGUNDOS)
        if conteo.fallos >= LIMITE_FALLOS:
            raise DemasiadosIntentos(calcular_retry_after(conteo.ahora, conteo.mas_viejo))
        usuario = await uow.usuarios.get_by_email(datos.email)
        if usuario is None:
            cred = _Credenciales(False, None, seg.hash_ficticio, False, False, [])
        else:
            cred = _Credenciales(
                existe=True,
                usuario_id=usuario.id,
                password_hash=usuario.password_hash,
                activo=usuario.activo,
                debe_cambiar_password=usuario.debe_cambiar_password,
                roles=await uow.asignaciones.roles_vigentes(usuario.id),
            )
    coincide = await _verificar_o_fallar(datos.password, cred.password_hash, cred.usuario_id, seg)
    exito = coincide and cred.existe and cred.activo
    await _anotar_intento(intentos, datos.email, ip, exito)
    if not exito:
        raise NoAutenticado(MENSAJE_CREDENCIALES)
    token = emitir_token(cred.usuario_id, cred.roles, secreto=seg.secreto, minutos=seg.minutos_token)
    return SesionIniciada(token, cred.debe_cambiar_password, seg.minutos_token * 60)


async def yo(uow: UsuariosUoW, actual: UsuarioActual) -> AuthYoRead:
    """La sesión propia: el usuario, sus roles vigentes (leídos de la base ahora) y los del token.

    Se responde también con el cambio de contraseña pendiente: `/auth/yo` es de las rutas
    que ese estado no bloquea (RN-06).
    """
    async with uow:
        roles_vigentes = await uow.asignaciones.roles_vigentes(actual.id)
    return AuthYoRead(
        usuario=UsuarioRead.model_validate(actual, from_attributes=True),
        roles_vigentes=roles_vigentes,
        roles_token=actual.roles_token,
    )


async def cambiar_password(
    uow: UsuariosUoW, actual: UsuarioActual, datos: CambioPasswordCreate, seg: ParametrosSeguridad
) -> None:
    """Cambia la contraseña propia (RN-16): `password_hash`, bajar el flag y dejar el evento, o nada.

    1. Lectura del hash actual en un bloque corto (valor simple).
    2. FUERA de todo bloque: verificar la actual y calcular el hash de la nueva (bcrypt no
       corre con una conexión tomada).
    3. UN solo bloque de escritura: `update` del usuario y `add` del evento de seguridad; si
       cualquiera falla, no queda ninguna de las dos.

    La contraseña actual incorrecta es 422 y no 401: en este proyecto 401 significa «no hay
    sesión válida» y un cliente lo leería como sesión vencida. No emite token ni toca la
    cookie y no invalida las sesiones abiertas: la misma cookie sigue sirviendo.
    """
    async with uow:
        usuario = await uow.usuarios.get_by_id(actual.id)
        if usuario is None:  # borrado entre la dependencia y acá: sin sesión válida
            raise NoAutenticado("No hay una sesión válida.")
        hash_actual = usuario.password_hash
    if not await _verificar_o_fallar(datos.password_actual, hash_actual, actual.id, seg):
        raise PeticionInvalida("La contraseña actual no es correcta.")
    hash_nuevo = await hashear_password(datos.password_nueva, costo=seg.costo, semaforo=seg.semaforo)
    async with uow:
        await uow.usuarios.update(usuario, {"password_hash": hash_nuevo, "debe_cambiar_password": False})
        await uow.eventos.add(EventoSeguridad(actor=actual.email, accion="Cambio de contraseña"))


# ---------------------------------------------------------------------------
# Administración de usuarios (CHG-14, Nico). Todas las operaciones son del ADMIN: el router
# las protege con `SOLO_ADMIN` y le pasa el `UsuarioActual` como `actor` (valores simples:
# sobreviven a un rollback). Una operación de escritura = un solo bloque `async with uow`.
# ---------------------------------------------------------------------------


async def dar_de_alta_personal(
    uow: UsuariosUoW, datos: UsuarioCreate, actor: UsuarioActual, seg: ParametrosSeguridad
) -> UsuarioRead:
    """Alta de personal (RN-16): usuario con contraseña provisoria y su evento, o ninguno.

    - El hash va ANTES del bloque: bcrypt tarda ~300 ms y no debe correr con una conexión tomada.
    - No consulta si el correo existe: la base decide (UNIQUE -> `Conflicto` 409 del UoW).
    - `debe_cambiar_password` queda en `True`: la contraseña es provisoria (RN-06).
    - NO asigna rol (design D1): los roles se dan después con `asignar_rol`, así cada rol queda con
      su vencimiento, quién lo otorgó y su propia línea de historial.
    - El evento se agrega dentro del bloque y después del usuario: si falla, el UoW revierte todo.
    """
    password_hash = await hashear_password(datos.password, costo=seg.costo, semaforo=seg.semaforo)
    async with uow:
        usuario = await uow.usuarios.add(
            Usuario(
                email=datos.email,
                nombre=datos.nombre,
                password_hash=password_hash,
                debe_cambiar_password=True,
            )
        )
        await uow.eventos.add(EventoSeguridad(actor=actor.email, accion=f"Alta de personal: usuario {usuario.id}"))
        return UsuarioRead.model_validate(usuario)


async def listar_roles(uow: UsuariosUoW, usuario_id: int) -> list[AsignacionRolRead]:
    """Historial completo de asignaciones del usuario (vigentes, vencidas y revocadas), sin paginar.

    Acá la lectura del usuario ES la operación: si no existe, 404. El historial de un usuario es
    corto y la consigna sólo pagina `/eventos`.
    """
    async with uow:
        if await uow.usuarios.get_by_id(usuario_id) is None:
            raise UsuarioNoEncontrado(usuario_id)
        return [AsignacionRolRead.model_validate(a) for a in await uow.asignaciones.historial(usuario_id)]


async def asignar_rol(
    uow: UsuariosUoW, usuario_id: int, datos: AsignacionRolCreate, actor: UsuarioActual
) -> AsignacionRolRead:
    """Asigna un rol con `vence_en` opcional (RN-03, RN-16): asignación y evento, o nada.

    Sin consulta previa: la base decide. Si hay una fila abierta pero VENCIDA de ese rol se cierra
    con `revocada_en = vence_en` (`cerrar_vencida`) antes del INSERT; si la abierta sigue vigente
    no se toca y el índice único parcial da 409 (`Conflicto` del UoW). Si el usuario no existe,
    la FK del INSERT da `UsuarioNoEncontrado` (404): excepción explícita a AGENTS §8, ver
    `AsignacionRolRepository.asignar`.

    Cerrar la vencida y abrir la nueva es UN cambio de rol: una sola línea de evento, en el mismo
    bloque y después de la escritura que registra.

    `ADMIN` no lleva vencimiento (D3b, RN-05: el sistema no puede quedarse sin administradores
    por vencimiento). La regla vive acá y no en `AsignacionRolCreate`: ese contrato es genérico
    (no distingue roles) y esto es una regla de negocio. Es una comparación pura, antes del bloque.
    """
    if datos.rol == "ADMIN" and datos.vence_en is not None:
        raise AdminConVencimiento()
    async with uow:
        await uow.asignaciones.cerrar_vencida(usuario_id, datos.rol)
        asignacion = await uow.asignaciones.asignar(
            AsignacionRol(usuario_id=usuario_id, rol=datos.rol, vence_en=datos.vence_en, otorgada_por=actor.id)
        )
        await uow.eventos.add(
            EventoSeguridad(actor=actor.email, accion=f"Asignación del rol {datos.rol} al usuario {usuario_id}")
        )
        return AsignacionRolRead.model_validate(asignacion)


async def revocar_rol(uow: UsuariosUoW, usuario_id: int, rol: str, actor: UsuarioActual) -> AsignacionRolRead:
    """Revoca el rol vigente del usuario sin borrar la fila (RN-05, RN-16): revocación y evento, o nada.

    RN-05, autoprotección: nadie se revoca su propio `ADMIN` (409, nunca 403). Es una comparación
    pura y se rechaza antes de abrir el UoW.

    RN-05, nunca cero administradores, también con revocaciones simultáneas. Sin protección, dos
    ADMIN que se revocan a la vez (A revoca a B y B revoca a A) cuentan cada uno 1 porque no ven la
    revocación sin confirmar del otro y confirman los dos: cero ADMIN (*write skew*). Por eso, para
    revocar un `ADMIN`: (1) `bloquear_admins_vigentes` toma `FOR UPDATE` las filas `ADMIN` vigentes
    (`ORDER BY id`, para que nadie tome los bloqueos en otro orden y se produzca un *deadlock*);
    (2) se comprueba que el propio actor sigue entre ellas; (3) se revoca; (4) recién ahí se cuenta,
    porque `FOR UPDATE` no se puede combinar con `count()` en la misma consulta.

    El paso (2) cierra una carrera de AUTORIZACIÓN, no de conteo. `SOLO_ADMIN` verificó el `ADMIN` del
    actor en su propia transacción, ya confirmada, ANTES de este bloque; la espera del bloqueo en (1)
    puede durar lo que tarde otra transacción. Con tres ADMIN, si A revoca a B y B revoca a C a la vez,
    B ya pasó `SOLO_ADMIN`, espera en (1) y, cuando A confirma, la base reevalúa el `WHERE` y devuelve las
    filas de A y C pero no la de B. Sin (2), B revocaría a C (quedaría A: el conteo da 1) siendo ya un
    no-administrador. Con (2) el actor que no figura entre las filas bloqueadas recibe `SinPermiso`
    (403) y no se escribe nada; también cubre el cruce de dos ADMIN que se revocan entre sí (la
    perdedora recibe 403 y no «409 sin administradores»). Es gratis: el bloqueo ya trajo esos
    `usuario_id`. El conteo del paso (4) queda como defensa en profundidad: con el actor comprobado y
    la autorrevocación prohibida, el actor sigue siendo ADMIN y el conteo no puede dar 0.

    No lee antes de escribir: `revocar_vigente` es un `UPDATE ... RETURNING`. Sólo si no tocó nada se
    lee el usuario, para elegir entre 404 «el usuario no existe» y 404 «no tiene ese rol vigente»
    (un rol vencido tampoco es revocable: no está vigente).
    """
    if rol == "ADMIN" and usuario_id == actor.id:
        raise AutoRevocacionAdmin()
    async with uow:
        if rol == "ADMIN" and actor.id not in await uow.asignaciones.bloquear_admins_vigentes():
            raise SinPermiso(MENSAJE_SIN_PERMISO)  # el actor dejó de ser ADMIN mientras esperaba el bloqueo
        revocada = await uow.asignaciones.revocar_vigente(usuario_id, rol)
        if revocada is None:
            if await uow.usuarios.get_by_id(usuario_id) is None:
                raise UsuarioNoEncontrado(usuario_id)
            raise RolNoVigente(usuario_id, rol)
        if rol == "ADMIN" and await uow.asignaciones.contar_admins_vigentes() == 0:
            raise SinAdministradores()
        await uow.eventos.add(
            EventoSeguridad(actor=actor.email, accion=f"Revocación del rol {rol} al usuario {usuario_id}")
        )
        return AsignacionRolRead.model_validate(revocada)


async def listar_eventos(uow: UsuariosUoW, p: ParametrosPagina) -> Page[EventoSeguridadRead]:
    """Historial de seguridad paginado, del más reciente al más viejo (`envolver` da el 422 fuera de rango)."""
    async with uow:
        total = await uow.eventos.count()
        eventos = await uow.eventos.listar_recientes((p.page - 1) * p.size, p.size)
        return envolver(
            [EventoSeguridadRead.model_validate(e) for e in eventos], total=total, page=p.page, size=p.size
        )
