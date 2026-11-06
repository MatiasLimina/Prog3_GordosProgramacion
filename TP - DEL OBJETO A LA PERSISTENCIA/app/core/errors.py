"""Traducción de errores de base de datos a respuestas HTTP (RN-15).

Regla: el cliente nunca ve texto interno de la base (mensajes de PostgreSQL,
nombres de constraints, SQL). Cada módulo pasa sus propios mensajes en
español, indexados por nombre de constraint.
"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# Mensajes por defecto según el SQLSTATE de PostgreSQL.
_MENSAJES_POR_SQLSTATE = {
    "23505": "Ya existe un registro con un valor único repetido.",
    "23503": "El registro referencia o depende de otro que no permite la relación.",
    "23514": "Los datos enviados no cumplen las condiciones requeridas.",
    "23001": "El registro no se puede modificar ni borrar.",
}
_MENSAJE_GENERICO = "La operación no pudo completarse por un conflicto con los datos existentes."


class Conflicto(Exception):
    """Choque con lo guardado; la app lo responde como 409 con `mensaje`.

    Es una excepción de dominio: no conoce HTTP. La lanza el UnitOfWork cuando la
    base rechaza una escritura por integridad, y el handler de `app/main.py` la
    traduce a `409 {"detail": mensaje}`.
    """

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class PeticionInvalida(Exception):
    """La petición no cumple el contrato; la app lo responde como 422 con `mensaje`.

    Es una excepción de dominio: no conoce HTTP. La lanza el código de negocio
    (por ejemplo, una página de listado fuera de rango en `core/paginacion.py`),
    y el handler de `app/main.py` la traduce a `422 {"detail": mensaje}`.
    """

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class NoEncontrado(Exception):
    """El recurso de la ruta no existe; la app lo responde como 404 con `mensaje`.

    Es una excepción de dominio: no conoce HTTP. La lanzan los servicios («La editorial no
    existe.», «El libro no existe.») y el handler de `app/main.py` la traduce a
    `404 {"detail": mensaje}`.
    """

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class LibroNoEncontrado(NoEncontrado):
    """El libro de un movimiento de stock no existe (404 si nadie la traduce).

    Es una excepción de dominio: no conoce HTTP. NO es un `Conflicto`: en la reposición el
    libro es el recurso de la ruta (404). Una operación que lo considere un choque con lo
    guardado (una venta con un libro inexistente) la atrapa y relanza un `Conflicto`.
    """

    def __init__(self, libro_id: int) -> None:
        super().__init__("El libro no existe.")
        self.libro_id = libro_id


class LibroDadoDeBaja(Conflicto):
    """El libro está dado de baja (borrado lógico): no se repone ni se vende (409).

    Es una excepción de dominio: no conoce HTTP.
    """

    def __init__(self, libro_id: int) -> None:
        super().__init__(f"El libro {libro_id} está dado de baja.")
        self.libro_id = libro_id


class StockInsuficiente(Conflicto):
    """Una salida de stock pide más unidades de las que hay (409).

    Es una excepción de dominio: no conoce HTTP.
    """

    def __init__(self, libro_id: int, *, disponible: int, pedido: int) -> None:
        super().__init__(f"Stock insuficiente para el libro {libro_id}: hay {disponible}, se pidieron {pedido}.")
        self.libro_id = libro_id
        self.disponible = disponible
        self.pedido = pedido


class StockExcedido(Conflicto):
    """Una entrada de stock haría pasar el stock del máximo de int32 (409).

    Es una excepción de dominio: no conoce HTTP.
    """

    def __init__(self, libro_id: int) -> None:
        super().__init__(f"El stock del libro {libro_id} superaría el máximo permitido.")
        self.libro_id = libro_id


class ClienteNoEncontrado(NoEncontrado):
    """El cliente de la ruta no existe (404 con «El cliente no existe.»).

    Es una excepción de dominio: no conoce HTTP. La lanzan el servicio de clientes y el
    repositorio de perfiles (cuando la FK del perfil dice que el cliente no existe); CHG-16 la
    puede reutilizar, igual que `LibroNoEncontrado`.
    """

    def __init__(self, cliente_id: int) -> None:
        super().__init__("El cliente no existe.")
        self.cliente_id = cliente_id


class CorreoConCuenta(Conflicto):
    """El correo de un cliente con usuario vinculado no se puede cambiar (409).

    Es una excepción de dominio: no conoce HTTP. El texto vive acá y no en `MENSAJES` del UoW
    porque no es una constraint de la base sino una regla de negocio.
    """

    def __init__(self, cliente_id: int) -> None:
        super().__init__("El correo de un cliente con cuenta no se puede cambiar.")
        self.cliente_id = cliente_id


class NoAutenticado(Exception):
    """No hay una sesión válida o las credenciales no sirven; la app lo responde como 401.

    Es una excepción de dominio: no conoce HTTP. La lanzan el login («Correo o contraseña
    incorrectos.») y la dependencia del usuario actual (mensaje fijo, sin decir cuál de las
    cinco causas ocurrió), y el handler de `app/main.py` la traduce a `401 {"detail": mensaje}`.
    Sin `WWW-Authenticate`: la autenticación por cookie no tiene un esquema estándar que anunciar.
    """

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class SinPermiso(Exception):
    """La sesión es válida pero no alcanza para esta operación; la app lo responde como 403.

    Es una excepción de dominio: no conoce HTTP. La lanzan `requiere_rol` (falta el rol
    vigente), el control del cambio obligatorio de contraseña (RN-06) y, desde CHG-16, el
    servicio de ventas cuando el cliente no es el dueño de la venta. El handler de
    `app/main.py` la traduce a `403 {"detail": mensaje}`. El mensaje nunca nombra roles ni
    detalles internos.
    """

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class DemasiadosIntentos(Exception):
    """Se superó el límite de intentos de login (RN-07); la app lo responde como 429.

    Es una excepción de dominio: no conoce HTTP. `retry_after` son los segundos que faltan
    para que el fallo más viejo que cuenta salga de la ventana; el handler de `app/main.py`
    los pone en la cabecera `Retry-After` y usa un detalle fijo.
    """

    def __init__(self, retry_after: int) -> None:
        super().__init__(f"Demasiados intentos; reintentar en {retry_after} s.")
        self.retry_after = retry_after


def _buscar_atributo(error: IntegrityError, nombre: str) -> str | None:
    """Busca un atributo en `orig` y, si no está, en `orig.__cause__`.

    Con SQLAlchemy + asyncpg, `orig` es un adaptador que copia `sqlstate`
    pero NO `constraint_name`; ese vive en la excepción original de asyncpg,
    accesible como `orig.__cause__`.
    """
    orig = error.orig
    for candidato in (orig, getattr(orig, "__cause__", None)):
        valor = getattr(candidato, nombre, None)
        if valor:
            return valor
    return None


def constraint_violada(error: IntegrityError) -> str | None:
    """Nombre de la constraint que violó el `IntegrityError`, o `None` si la base no lo informa.

    Es la única forma de leerlo: `mensaje_para` la usa adentro y quien necesite distinguir una
    constraint de otra (p. ej. FK -> 404 y UNIQUE -> 409) la usa directamente.
    """
    return _buscar_atributo(error, "constraint_name")


def mensaje_para(error: IntegrityError, mensajes: dict[str, str], default: str | None = None) -> str:
    """Devuelve el mensaje propio para un IntegrityError."""
    constraint = constraint_violada(error)
    if constraint in mensajes:
        return mensajes[constraint]
    if default is not None:
        return default
    sqlstate = _buscar_atributo(error, "sqlstate") or _buscar_atributo(error, "pgcode")
    return _MENSAJES_POR_SQLSTATE.get(sqlstate, _MENSAJE_GENERICO)


@asynccontextmanager
async def traducir_integrity(
    session: AsyncSession, mensajes: dict[str, str], default: str | None = None
) -> AsyncIterator[None]:
    """Envuelve cualquier escritura (flush/commit/execute).

    Si la base rechaza la escritura (IntegrityError): rollback y 409 con
    mensaje propio. `mensajes` mapea nombre de constraint -> mensaje en español.
    """
    try:
        yield
    except IntegrityError as e:
        await session.rollback()
        # `from None`: no encadena la excepción de la base en la respuesta/log de HTTP.
        raise HTTPException(status_code=409, detail=mensaje_para(e, mensajes, default)) from None


async def commit_or_409(
    session: AsyncSession, mensajes: dict[str, str], default: str | None = None
) -> None:
    """Hace commit traduciendo IntegrityError a 409 (ver traducir_integrity)."""
    async with traducir_integrity(session, mensajes, default):
        await session.commit()
