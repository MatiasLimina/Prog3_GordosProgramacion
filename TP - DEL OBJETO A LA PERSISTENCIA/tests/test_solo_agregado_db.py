"""Sólo agregado de `movimiento_stock` (RN-12, C-14): lo garantiza la base con un disparador.

Los casos de rechazo dependen de la cuarta migración (disparador BEFORE UPDATE OR DELETE FOR EACH ROW,
SQLSTATE 23001 y CONSTRAINT `movimiento_stock_solo_agregado`). INSERT y TRUNCATE siguen permitidos:
el seed vacía con TRUNCATE. El conftest vacía con DELETE y apaga los disparadores sólo en esa
transacción (`session_replication_role = replica`).
"""
from collections.abc import Mapping
from typing import ClassVar

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel

from app.core.errors import Conflicto, _buscar_atributo, mensaje_para
from app.core.unit_of_work import UnitOfWork
from app.modules.libros.models import MovimientoStock

pytestmark = pytest.mark.db

CONSTRAINT = "movimiento_stock_solo_agregado"


# --- helpers de inserción por SQL directo ---

async def _escalar(sm, sql, **params):
    async with sm() as s:
        resultado = (await s.execute(text(sql), params)).scalar()
        await s.commit()
        return resultado


async def _movimiento(sm, cantidad=5, motivo="Stock inicial") -> int:
    """Inserta editorial, libro, usuario y un movimiento; devuelve el id del movimiento."""
    editorial_id = await _escalar(sm, "INSERT INTO editorial (nombre, pais) VALUES ('E', 'AR') RETURNING id")
    libro_id = await _escalar(
        sm,
        "INSERT INTO libro (isbn, titulo, precio, stock, editorial_id) "
        "VALUES ('ISBN-1', 'T', 10.00, :c, :e) RETURNING id",
        c=cantidad, e=editorial_id,
    )
    usuario_id = await _escalar(
        sm, "INSERT INTO usuario (email, nombre, password_hash) VALUES ('u@example.com', 'U', 'x') RETURNING id"
    )
    return await _escalar(
        sm,
        "INSERT INTO movimiento_stock (libro_id, usuario_id, cantidad, motivo) "
        "VALUES (:l, :u, :c, :m) RETURNING id",
        l=libro_id, u=usuario_id, c=cantidad, m=motivo,
    )


async def _fila(sm, movimiento_id: int):
    """Lee la fila desde una sesión nueva: sólo ve lo confirmado."""
    async with sm() as s:
        return (
            await s.execute(
                text("SELECT cantidad, motivo, cuando FROM movimiento_stock WHERE id = :i"), {"i": movimiento_id}
            )
        ).one_or_none()


async def _rechazo(sm, sql, **params) -> IntegrityError:
    async with sm() as s:
        with pytest.raises(IntegrityError) as info:
            await s.execute(text(sql), params)
            await s.commit()
    return info.value


def _mensaje_de_la_base(error: IntegrityError) -> str:
    return str(getattr(error.orig, "__cause__", None) or error.orig)


# --- el alta sigue permitida ---

async def test_insert_de_un_movimiento_se_acepta(sessionmaker_test):
    movimiento_id = await _movimiento(sessionmaker_test)

    fila = await _fila(sessionmaker_test, movimiento_id)
    assert (fila.cantidad, fila.motivo) == (5, "Stock inicial")


async def test_varios_inserts_se_aceptan(sessionmaker_test):
    primero = await _movimiento(sessionmaker_test)
    libro_id = await _escalar(sessionmaker_test, "SELECT min(id) FROM libro")
    usuario_id = await _escalar(sessionmaker_test, "SELECT min(id) FROM usuario")
    segundo = await _escalar(
        sessionmaker_test,
        "INSERT INTO movimiento_stock (libro_id, usuario_id, cantidad, motivo) "
        "VALUES (:l, :u, -2, 'Venta') RETURNING id",
        l=libro_id, u=usuario_id,
    )

    assert segundo != primero
    assert await _escalar(sessionmaker_test, "SELECT count(*) FROM movimiento_stock") == 2


# --- UPDATE y DELETE rechazados por SQL ---

async def test_update_se_rechaza_con_23001_y_nombre_de_constraint(sessionmaker_test):
    movimiento_id = await _movimiento(sessionmaker_test, cantidad=5)
    antes = await _fila(sessionmaker_test, movimiento_id)

    error = await _rechazo(
        sessionmaker_test, "UPDATE movimiento_stock SET cantidad = 99, motivo = 'otro' WHERE id = :i", i=movimiento_id
    )

    assert _buscar_atributo(error, "sqlstate") == "23001"
    assert _buscar_atributo(error, "constraint_name") == CONSTRAINT
    assert await _fila(sessionmaker_test, movimiento_id) == antes


async def test_delete_se_rechaza_con_23001_y_nombre_de_constraint(sessionmaker_test):
    movimiento_id = await _movimiento(sessionmaker_test)
    antes = await _fila(sessionmaker_test, movimiento_id)

    error = await _rechazo(sessionmaker_test, "DELETE FROM movimiento_stock WHERE id = :i", i=movimiento_id)

    assert _buscar_atributo(error, "sqlstate") == "23001"
    assert _buscar_atributo(error, "constraint_name") == CONSTRAINT
    assert await _fila(sessionmaker_test, movimiento_id) == antes


@pytest.mark.parametrize(
    "operacion, sql",
    [
        ("UPDATE", "UPDATE movimiento_stock SET motivo = 'x' WHERE id = :i"),
        ("DELETE", "DELETE FROM movimiento_stock WHERE id = :i"),
    ],
)
async def test_el_mensaje_dice_solo_agregado_la_operacion_el_id_y_como_corregir(sessionmaker_test, operacion, sql):
    movimiento_id = await _movimiento(sessionmaker_test)

    error = await _rechazo(sessionmaker_test, sql, i=movimiento_id)

    mensaje = _mensaje_de_la_base(error)
    assert "sólo agregado" in mensaje
    assert operacion in mensaje
    assert f"movimiento {movimiento_id}" in mensaje
    assert "compense" in mensaje


async def test_el_mensaje_nombra_el_id_de_la_fila_afectada_y_no_otro(sessionmaker_test):
    primero = await _movimiento(sessionmaker_test)
    libro_id = await _escalar(sessionmaker_test, "SELECT min(id) FROM libro")
    usuario_id = await _escalar(sessionmaker_test, "SELECT min(id) FROM usuario")
    segundo = await _escalar(
        sessionmaker_test,
        "INSERT INTO movimiento_stock (libro_id, usuario_id, cantidad, motivo) "
        "VALUES (:l, :u, 1, 'otro') RETURNING id",
        l=libro_id, u=usuario_id,
    )

    error = await _rechazo(sessionmaker_test, "DELETE FROM movimiento_stock WHERE id = :i", i=segundo)

    assert f"movimiento {segundo}" in _mensaje_de_la_base(error)
    assert f"movimiento {primero}." not in _mensaje_de_la_base(error)


async def test_update_que_no_toca_filas_no_se_rechaza(sessionmaker_test):
    # El disparador es por fila: un UPDATE sin filas afectadas no tiene nada que proteger.
    await _movimiento(sessionmaker_test)

    await _escalar(sessionmaker_test, "UPDATE movimiento_stock SET motivo = 'x' WHERE id = -1 RETURNING id")

    assert await _escalar(sessionmaker_test, "SELECT count(*) FROM movimiento_stock") == 1


# --- desde el ORM ---

async def test_borrar_desde_el_orm_falla_y_no_deja_escrituras(sessionmaker_test):
    movimiento_id = await _movimiento(sessionmaker_test)
    antes = await _fila(sessionmaker_test, movimiento_id)

    async with sessionmaker_test() as session:
        movimiento = await session.get(MovimientoStock, movimiento_id)
        await session.delete(movimiento)
        with pytest.raises(IntegrityError) as info:
            await session.commit()
    assert _buscar_atributo(info.value, "constraint_name") == CONSTRAINT

    assert await _fila(sessionmaker_test, movimiento_id) == antes


async def test_cambiar_un_campo_desde_el_orm_falla_y_no_deja_escrituras(sessionmaker_test):
    movimiento_id = await _movimiento(sessionmaker_test)
    antes = await _fila(sessionmaker_test, movimiento_id)

    async with sessionmaker_test() as session:
        movimiento = await session.get(MovimientoStock, movimiento_id)
        movimiento.motivo = "Corregido a mano"
        with pytest.raises(IntegrityError) as info:
            await session.commit()
    assert _buscar_atributo(info.value, "sqlstate") == "23001"

    assert await _fila(sessionmaker_test, movimiento_id) == antes


# --- dentro de una unidad de trabajo ---

class UoWMovimientos(UnitOfWork):
    MENSAJES: ClassVar[Mapping[str, str]] = {CONSTRAINT: "Los movimientos de stock no se modifican."}


async def test_cambio_dentro_del_uow_lanza_conflicto_y_la_fila_queda_igual(sessionmaker_test):
    movimiento_id = await _movimiento(sessionmaker_test)
    antes = await _fila(sessionmaker_test, movimiento_id)

    async with sessionmaker_test() as session:
        with pytest.raises(Conflicto) as exc:
            async with UoWMovimientos(session):
                movimiento = await session.get(MovimientoStock, movimiento_id)
                movimiento.cantidad = 100

    assert exc.value.mensaje == "Los movimientos de stock no se modifican."
    assert await _fila(sessionmaker_test, movimiento_id) == antes


async def test_uow_sin_la_clave_en_sus_mensajes_igual_lanza_conflicto(sessionmaker_test):
    # Nunca otra excepción (RN-15): sin la clave propia el mensaje es el de respaldo, pero sigue siendo 409.
    movimiento_id = await _movimiento(sessionmaker_test)

    async with sessionmaker_test() as session:
        with pytest.raises(Conflicto) as exc:
            async with UnitOfWork(session):
                await session.delete(await session.get(MovimientoStock, movimiento_id))

    # Mensaje de respaldo de 23001 en app/core/errors.py (commit 2, anterior a este).
    assert exc.value.mensaje == "El registro no se puede modificar ni borrar."

    assert await _fila(sessionmaker_test, movimiento_id) is not None


async def test_mensaje_para_elige_el_mensaje_por_el_nombre_de_constraint_del_commit(sessionmaker_test):
    movimiento_id = await _movimiento(sessionmaker_test)

    async with sessionmaker_test() as session:
        movimiento = await session.get(MovimientoStock, movimiento_id)
        movimiento.motivo = "x"
        with pytest.raises(IntegrityError) as info:
            await session.commit()

    assert mensaje_para(info.value, {CONSTRAINT: "X"}) == "X"
    assert mensaje_para(info.value, {"otra": "Y"}, default="D") == "D"


# --- TRUNCATE sigue permitido ---

async def test_truncate_de_todas_las_tablas_con_movimientos_termina_sin_error(sessionmaker_test):
    await _movimiento(sessionmaker_test)
    tablas = ", ".join(f'"{t.name}"' for t in SQLModel.metadata.sorted_tables)

    async with sessionmaker_test() as s:
        await s.execute(text(f"TRUNCATE {tablas} RESTART IDENTITY CASCADE"))
        await s.commit()

    assert await _escalar(sessionmaker_test, "SELECT count(*) FROM movimiento_stock") == 0
