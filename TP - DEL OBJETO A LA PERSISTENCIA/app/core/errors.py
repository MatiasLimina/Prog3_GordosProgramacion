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


def mensaje_para(error: IntegrityError, mensajes: dict[str, str], default: str | None = None) -> str:
    """Devuelve el mensaje propio para un IntegrityError."""
    constraint = _buscar_atributo(error, "constraint_name")
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
