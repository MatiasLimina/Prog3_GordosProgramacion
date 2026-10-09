"""Traducción de errores de base de datos a respuestas HTTP (RN-12).

Regla: el cliente nunca ve texto interno de la base (mensajes de PostgreSQL,
nombres de constraints, SQL). Cada módulo pasa sus propios mensajes en
español, indexados por nombre de constraint.
"""
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# Mensajes por defecto según el SQLSTATE de PostgreSQL.
_MENSAJES_POR_SQLSTATE = {
    "23505": "Ya existe un registro con un valor único repetido.",
    "23503": "El registro referencia o depende de otro que no permite la relación.",
    "23514": "Los datos enviados no cumplen las condiciones requeridas.",
}
_MENSAJE_GENERICO = "La operación no pudo completarse por un conflicto con los datos existentes."


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


async def commit_or_409(
    session: AsyncSession, mensajes: dict[str, str], default: str | None = None
) -> None:
    """Hace commit; si la base rechaza la escritura, rollback y 409.

    `mensajes` mapea nombre de constraint -> mensaje en español.
    """
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        # `from None`: no encadena la excepción de la base en la respuesta/log de HTTP.
        raise HTTPException(status_code=409, detail=mensaje_para(e, mensajes, default)) from None
