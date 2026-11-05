"""Dependencias de FastAPI compartidas.

Hoy:
- `proveedor_uow`: la fábrica que CONSTRUYE el UnitOfWork de una petición sin abrirlo.
- `proveedor_uow_sesion_propia`: lo mismo sobre una sesión NUEVA (sólo `intento_acceso`).
- `ParametrosSeguridad` / `get_parametros_seguridad`: costo y semáforo de bcrypt, hash ficticio,
  clave y duración del token y `cookie_secure`, leídos de `app.state`.
- `get_usuario_actual` (CHG-11): cookie -> token -> usuario, con las cinco causas de 401.

CHG-12 reutiliza `get_usuario_actual` y suma `requiere_rol` y el control del cambio
obligatorio (RN-06). Todas reciben la misma sesión (`Depends(get_session)`, que FastAPI
cachea por petición), así una petición autenticada usa una sola conexión del pool.
"""
import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_session
from app.core.errors import NoAutenticado
from app.core.security import TokenInvalido, verificar_token
from app.core.unit_of_work import UnitOfWork
from app.modules.usuarios.repository import UsuarioRepository


def proveedor_uow[U: UnitOfWork](clase: type[U]) -> Callable[..., Awaitable[U]]:
    """Dependencia que construye `clase(session)` con la sesión de la petición.

    Condición: todo UoW de módulo se construye sólo con `(session)`; lo que necesite más
    se arma adentro. Un solo UoW abierto por sesión a la vez: un handler puede recibir
    varios UoW (comparten la sesión de la petición), pero nunca anidar sus `async with`,
    ni con UoW distintos (lanza `RuntimeError`). Ejemplo de un módulo:

        # app/modules/editoriales/unit_of_work.py
        class EditorialesUoW(UnitOfWork):
            MENSAJES = {"uq_editorial_nombre": "Ya existe una editorial con ese nombre."}

            def __init__(self, session: AsyncSession) -> None:
                super().__init__(session)
                self.editoriales = EditorialRepository(session)

        EditorialesUoWDep = Annotated[EditorialesUoW, Depends(proveedor_uow(EditorialesUoW))]

        # router.py: construye el UoW y se lo pasa al servicio sin abrirlo
        @router.post("/", status_code=201)
        async def crear(datos: EditorialCreate, uow: EditorialesUoWDep):
            return await service.crear(uow, datos)

        # service.py: abre el bloque (confirma o revierte al salir)
        async def crear(uow: EditorialesUoW, datos: EditorialCreate) -> Editorial:
            async with uow:
                return await uow.editoriales.add(Editorial(**datos.model_dump()))
    """

    # `async def`: una dependencia `def` correría en el threadpool sin necesidad.
    async def _proveer(session: Annotated[AsyncSession, Depends(get_session)]) -> U:
        return clase(session)

    return _proveer


@dataclass(frozen=True)
class ParametrosSeguridad:
    """Lo que el servicio de auth necesita de la configuración y del arranque.

    Lo arma `get_parametros_seguridad` desde `app.state`; el servicio nunca lee `app.state`
    (es FastAPI). Envuelve costo y semáforo de bcrypt sin tocar `security.py`.
    """

    costo: int
    semaforo: asyncio.Semaphore
    hash_ficticio: str
    secreto: SecretStr
    minutos_token: int
    cookie_secure: bool


async def get_parametros_seguridad(request: Request) -> ParametrosSeguridad:
    estado = request.app.state
    return ParametrosSeguridad(
        costo=estado.settings.bcrypt_cost,
        semaforo=estado.semaforo_bcrypt,
        hash_ficticio=estado.hash_ficticio,
        secreto=estado.settings.jwt_secret,
        minutos_token=estado.settings.jwt_expire_minutes,
        cookie_secure=estado.settings.cookie_secure,
    )


async def get_fabrica_sesiones(request: Request) -> async_sessionmaker[AsyncSession]:
    return request.app.state.sessionmaker


def proveedor_uow_sesion_propia[U: UnitOfWork](clase: type[U]) -> Callable[..., AsyncIterator[U]]:
    """Como `proveedor_uow`, pero sobre una sesión NUEVA y no la de la petición.

    Es para la única escritura que debe confirmarse aunque la petición falle
    (`intento_acceso`). La sesión se cierra al terminar la petición; no toma una conexión
    del pool hasta su primera consulta, así que un 422 o un 429 nunca la usan.
    """

    async def _proveer(
        fabrica: Annotated[async_sessionmaker[AsyncSession], Depends(get_fabrica_sesiones)],
    ) -> AsyncIterator[U]:
        async with fabrica() as session:
            yield clase(session)

    return _proveer


NOMBRE_COOKIE = "access_token"
_MENSAJE_SIN_SESION = "No hay una sesión válida."


@dataclass(frozen=True)
class UsuarioActual:
    """El usuario de la petición, en valores simples y SIN `password_hash`.

    `roles_token` son los roles con los que se emitió el token: informativos (RN-04). Los
    vigentes se leen de la base en cada petición que los necesite.
    """

    id: int
    email: str
    nombre: str
    activo: bool
    debe_cambiar_password: bool
    roles_token: list[str]


async def get_usuario_actual(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    seg: Annotated[ParametrosSeguridad, Depends(get_parametros_seguridad)],
) -> UsuarioActual:
    """Identifica al usuario SÓLO con la cookie `access_token` (nunca con `Authorization`).

    Lanza `NoAutenticado` (401) con un mismo mensaje fijo por cualquiera de las cinco causas:
    sin cookie, token inválido, token vencido, usuario inexistente o usuario inactivo. Nunca
    dice cuál ocurrió ni incluye el token o la clave.

    Usa la MISMA sesión que el UoW de la petición (`Depends(get_session)` la cachea): una
    petición autenticada toma una sola conexión del pool. La lectura va en un bloque corto
    del UoW base que termina acá, ANTES del bloque del servicio (son sucesivos, no
    anidados): confirma una transacción vacía y devuelve la conexión al pool, así bcrypt no
    corre con una conexión tomada. Devuelve valores simples y no el objeto ORM porque un
    rollback posterior lo expiraría y leerlo dispararía carga perezosa (`MissingGreenlet`).

    CHG-12 la reutiliza para `requiere_rol` y para el control del cambio obligatorio (RN-06).
    """
    token = request.cookies.get(NOMBRE_COOKIE)
    if not token:
        raise NoAutenticado(_MENSAJE_SIN_SESION)
    try:
        datos = verificar_token(token, secreto=seg.secreto)
    except TokenInvalido:  # incluye TokenVencido
        raise NoAutenticado(_MENSAJE_SIN_SESION) from None
    async with UnitOfWork(session):
        usuario = await UsuarioRepository(session).get_by_id(datos.usuario_id)
        actual = None
        if usuario is not None and usuario.activo:
            actual = UsuarioActual(
                id=usuario.id,
                email=usuario.email,
                nombre=usuario.nombre,
                activo=usuario.activo,
                debe_cambiar_password=usuario.debe_cambiar_password,
                roles_token=datos.roles,
            )
    if actual is None:
        raise NoAutenticado(_MENSAJE_SIN_SESION)
    return actual
