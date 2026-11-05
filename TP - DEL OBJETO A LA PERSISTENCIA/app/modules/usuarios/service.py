"""Servicios de autenticación (CHG-11).

Reciben el UoW (y los parámetros de seguridad) ya construidos por el router y abren el
bloque `async with`; nunca construyen un UoW ni lanzan `HTTPException`.
"""
import logging
import math
from dataclasses import dataclass
from datetime import datetime

from app.core.dependencies import ParametrosSeguridad, UsuarioActual
from app.core.errors import DemasiadosIntentos, NoAutenticado, PeticionInvalida
from app.core.security import emitir_token, hashear_password, verificar_password
from app.modules.clientes.models import Cliente
from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, IntentoAcceso, Usuario
from app.modules.usuarios.schemas import AuthYoRead, CambioPasswordCreate, LoginCreate, RegistroCreate, UsuarioRead
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
    try:
        coincide = await verificar_password(datos.password, cred.password_hash, semaforo=seg.semaforo)
    except ValueError:
        # Hash corrupto en la base (bcrypt: «Invalid salt»): se trata como fallo, sin el hash.
        logger.warning("password_hash inválido para el usuario id=%s", cred.usuario_id)
        coincide = False
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
    if not await verificar_password(datos.password_actual, hash_actual, semaforo=seg.semaforo):
        raise PeticionInvalida("La contraseña actual no es correcta.")
    hash_nuevo = await hashear_password(datos.password_nueva, costo=seg.costo, semaforo=seg.semaforo)
    async with uow:
        await uow.usuarios.update(usuario, {"password_hash": hash_nuevo, "debe_cambiar_password": False})
        await uow.eventos.add(EventoSeguridad(actor=actual.email, accion="Cambio de contraseña"))
