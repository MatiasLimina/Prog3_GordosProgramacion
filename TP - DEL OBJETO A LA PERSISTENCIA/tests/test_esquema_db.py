"""Esquema migrado (libreria_test en `head`): coincide con los modelos y aplica sus restricciones.

Cubre los escenarios de base real que CHG-06/07 dejaron para CHG-08 (spec `migraciones-esquema`):
inventario de tablas, `alembic check`, unicidad de ISBN, restricciones con nombre, `server_default`
de los modelos de acceso y acciones referenciales compatibles con el sólo agregado.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.errors import _buscar_atributo

pytestmark = pytest.mark.db

PROYECTO = Path(__file__).resolve().parent.parent

TABLAS = {
    "editorial", "genero", "autor", "libro", "libro_autor", "cliente", "perfil_cliente",
    "venta", "renglon_venta", "usuario", "asignacion_rol", "intento_acceso",
    "evento_seguridad", "movimiento_stock",
}


# --- helpers de inserción por SQL directo (sin pasar por el ORM) ---

async def _escalar(sm, sql, **params):
    async with sm() as s:
        resultado = (await s.execute(text(sql), params)).scalar()
        await s.commit()
        return resultado


async def _editorial(sm):
    return await _escalar(sm, "INSERT INTO editorial (nombre, pais) VALUES ('E', 'AR') RETURNING id")


async def _libro(sm, isbn="ISBN-1", borrado=False):
    editorial_id = await _escalar(sm, "SELECT min(id) FROM editorial") or await _editorial(sm)
    return await _escalar(
        sm,
        "INSERT INTO libro (isbn, titulo, precio, stock, editorial_id, borrado_en) "
        "VALUES (:isbn, 'T', 10.00, 0, :e, CASE WHEN :borrado THEN now() END) RETURNING id",
        isbn=isbn, e=editorial_id, borrado=borrado,
    )


async def _usuario(sm, email="u@example.com"):
    # Sin activo ni debe_cambiar_password: los completa el server_default.
    return await _escalar(
        sm,
        "INSERT INTO usuario (email, nombre, password_hash) VALUES (:e, 'U', 'x') RETURNING id",
        e=email,
    )


async def _cliente(sm, email, usuario_id=None):
    return await _escalar(
        sm,
        "INSERT INTO cliente (nombre, email, usuario_id) VALUES ('C', :e, :u) RETURNING id",
        e=email, u=usuario_id,
    )


async def _venta(sm):
    cliente_id = await _cliente(sm, "c@example.com")
    return await _escalar(
        sm,
        "INSERT INTO venta (cliente_id, fecha, total) VALUES (:c, now(), 0) RETURNING id",
        c=cliente_id,
    )


async def _movimiento(sm, libro_id, usuario_id, venta_id=None, cantidad=5):
    return await _escalar(
        sm,
        "INSERT INTO movimiento_stock (libro_id, venta_id, usuario_id, cantidad, motivo) "
        "VALUES (:l, :v, :u, :c, 'm') RETURNING id",
        l=libro_id, v=venta_id, u=usuario_id, c=cantidad,
    )


async def _rechazo(sm, sql, **params) -> IntegrityError:
    """Ejecuta una escritura que la base debe rechazar y devuelve el IntegrityError."""
    async with sm() as s:
        with pytest.raises(IntegrityError) as info:
            await s.execute(text(sql), params)
            await s.commit()
    return info.value


def _constraint(error: IntegrityError) -> str | None:
    return _buscar_atributo(error, "constraint_name")


def _sqlstate(error: IntegrityError) -> str | None:
    return _buscar_atributo(error, "sqlstate")


# --- esquema y metadata ---

def test_alembic_check_sin_diferencias_con_los_modelos(esquema_test):
    # Ojo: migrations/env.py no activa compare_server_default, así que `alembic check`
    # NO detecta diferencias de server_default entre modelos y migración. Eso lo cubren
    # los tests de inserción (`test_usuario_completa_sus_booleanos_con_el_default_del_servidor` y
    # `test_asignacion_rol_completa_desde_con_el_default_del_servidor`, que insertan sin dar esas columnas).
    assert esquema_test.database == "libreria_test"
    env = {**os.environ, "POSTGRES_DB": esquema_test.database}
    r = subprocess.run(
        [sys.executable, "-m", "alembic", "check"],
        cwd=PROYECTO, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    assert r.returncode == 0, f"alembic check encontró diferencias:\n{r.stdout}\n{r.stderr}"
    assert "No new upgrade operations detected" in (r.stdout + r.stderr)


async def test_la_base_tiene_las_catorce_tablas(sessionmaker_test):
    async with sessionmaker_test() as s:
        filas = await s.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name <> 'alembic_version'"
        ))
        assert {f[0] for f in filas} == TABLAS


async def test_isbn_unico_solo_entre_vigentes_a_nivel_de_esquema(sessionmaker_test):
    async with sessionmaker_test() as s:
        constraints = {f[0] for f in await s.execute(text(
            "SELECT conname FROM pg_constraint WHERE conrelid = 'libro'::regclass"))}
        indices = dict((await s.execute(text(
            "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'libro'"))).all())
    assert "uq_libro_isbn" not in constraints
    assert "uq_libro_isbn" not in indices
    assert "WHERE (borrado_en IS NULL)" in indices["uq_libro_isbn_vigente"]
    assert "UNIQUE" in indices["uq_libro_isbn_vigente"]


async def test_indices_parciales_de_asignacion_rol(sessionmaker_test):
    async with sessionmaker_test() as s:
        indices = dict((await s.execute(text(
            "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'asignacion_rol'"))).all())
    definicion = indices["uq_asignacion_rol_usuario_rol_vigente"]
    assert "UNIQUE" in definicion
    assert "WHERE (revocada_en IS NULL)" in definicion


# --- Unicidad de ISBN ---

async def test_isbn_repetido_entre_vigentes_se_rechaza(sessionmaker_test):
    await _libro(sessionmaker_test, "ISBN-X")
    e = await _rechazo(
        sessionmaker_test,
        "INSERT INTO libro (isbn, titulo, precio, stock, editorial_id) "
        "VALUES ('ISBN-X', 'otro', 5.00, 0, (SELECT min(id) FROM editorial))",
    )
    assert _constraint(e) == "uq_libro_isbn_vigente"
    assert _sqlstate(e) == "23505"


async def test_isbn_de_un_libro_dado_de_baja_se_puede_reutilizar(sessionmaker_test):
    await _libro(sessionmaker_test, "ISBN-X", borrado=True)
    nuevo = await _libro(sessionmaker_test, "ISBN-X")
    assert nuevo is not None
    # Y los vigentes siguen sin poder repetirse.
    e = await _rechazo(
        sessionmaker_test,
        "INSERT INTO libro (isbn, titulo, precio, stock, editorial_id) "
        "VALUES ('ISBN-X', 'otro', 5.00, 0, (SELECT min(id) FROM editorial))",
    )
    assert _constraint(e) == "uq_libro_isbn_vigente"


# --- Restricciones de la base migrada ---

async def test_rol_fuera_de_la_lista_se_rechaza(sessionmaker_test):
    usuario_id = await _usuario(sessionmaker_test)
    e = await _rechazo(
        sessionmaker_test,
        "INSERT INTO asignacion_rol (usuario_id, rol) VALUES (:u, 'SUPERUSUARIO')",
        u=usuario_id,
    )
    assert _constraint(e) == "ck_asignacion_rol_rol_valido"
    assert _sqlstate(e) == "23514"


async def test_roles_validos_se_aceptan(sessionmaker_test):
    usuario_id = await _usuario(sessionmaker_test)
    for rol in ("ADMIN", "VENDEDOR", "CLIENTE"):
        await _escalar(
            sessionmaker_test,
            "INSERT INTO asignacion_rol (usuario_id, rol) VALUES (:u, :r) RETURNING id",
            u=usuario_id, r=rol,
        )


async def test_dos_asignaciones_vigentes_del_mismo_rol_se_rechazan(sessionmaker_test):
    usuario_id = await _usuario(sessionmaker_test)
    sql = "INSERT INTO asignacion_rol (usuario_id, rol) VALUES (:u, 'ADMIN') RETURNING id"
    await _escalar(sessionmaker_test, sql, u=usuario_id)
    e = await _rechazo(sessionmaker_test, sql, u=usuario_id)
    assert _constraint(e) == "uq_asignacion_rol_usuario_rol_vigente"


async def test_con_la_primera_revocada_se_acepta_otra_del_mismo_rol(sessionmaker_test):
    usuario_id = await _usuario(sessionmaker_test)
    await _escalar(
        sessionmaker_test,
        "INSERT INTO asignacion_rol (usuario_id, rol, revocada_en) VALUES (:u, 'ADMIN', now()) RETURNING id",
        u=usuario_id,
    )
    await _escalar(
        sessionmaker_test,
        "INSERT INTO asignacion_rol (usuario_id, rol) VALUES (:u, 'ADMIN') RETURNING id",
        u=usuario_id,
    )


async def test_dos_clientes_con_el_mismo_usuario_se_rechazan(sessionmaker_test):
    usuario_id = await _usuario(sessionmaker_test)
    await _cliente(sessionmaker_test, "a@example.com", usuario_id)
    e = await _rechazo(
        sessionmaker_test,
        "INSERT INTO cliente (nombre, email, usuario_id) VALUES ('C', 'b@example.com', :u)",
        u=usuario_id,
    )
    assert _constraint(e) == "uq_cliente_usuario_id"


async def test_varios_clientes_sin_usuario_se_aceptan(sessionmaker_test):
    await _cliente(sessionmaker_test, "a@example.com")
    await _cliente(sessionmaker_test, "b@example.com")


async def test_cliente_con_usuario_inexistente_se_rechaza_por_fk(sessionmaker_test):
    e = await _rechazo(
        sessionmaker_test,
        "INSERT INTO cliente (nombre, email, usuario_id) VALUES ('C', 'a@example.com', 9999)",
    )
    assert _constraint(e) == "fk_cliente_usuario_id_usuario"
    assert _sqlstate(e) == "23503"


async def test_movimiento_de_cantidad_cero_se_rechaza(sessionmaker_test):
    libro_id = await _libro(sessionmaker_test)
    usuario_id = await _usuario(sessionmaker_test)
    e = await _rechazo(
        sessionmaker_test,
        "INSERT INTO movimiento_stock (libro_id, usuario_id, cantidad, motivo) VALUES (:l, :u, 0, 'm')",
        l=libro_id, u=usuario_id,
    )
    assert _constraint(e) == "ck_movimiento_stock_cantidad_no_cero"


@pytest.mark.parametrize(
    "padre,fk",
    [
        ("libro", "fk_movimiento_stock_libro_id_libro"),
        ("venta", "fk_movimiento_stock_venta_id_venta"),
        ("usuario", "fk_movimiento_stock_usuario_id_usuario"),
    ],
)
async def test_borrar_un_padre_con_movimientos_se_rechaza_por_fk(sessionmaker_test, padre, fk):
    libro_id = await _libro(sessionmaker_test)
    usuario_id = await _usuario(sessionmaker_test)
    venta_id = await _venta(sessionmaker_test)
    movimiento_id = await _movimiento(sessionmaker_test, libro_id, usuario_id, venta_id)
    ids = {"libro": libro_id, "venta": venta_id, "usuario": usuario_id}

    e = await _rechazo(sessionmaker_test, f"DELETE FROM {padre} WHERE id = :id", id=ids[padre])

    assert _constraint(e) == fk
    assert _sqlstate(e) == "23503"
    cuenta = await _escalar(
        sessionmaker_test, "SELECT count(*) FROM movimiento_stock WHERE id = :i", i=movimiento_id
    )
    assert cuenta == 1


async def test_cuando_del_movimiento_por_defecto_no_nulo_y_con_zona(sessionmaker_test):
    libro_id = await _libro(sessionmaker_test)
    usuario_id = await _usuario(sessionmaker_test)
    movimiento_id = await _movimiento(sessionmaker_test, libro_id, usuario_id)
    async with sessionmaker_test() as s:
        fila = (await s.execute(
            text("SELECT cuando, pg_typeof(cuando)::text FROM movimiento_stock WHERE id = :i"),
            {"i": movimiento_id},
        )).one()
    assert fila[0] is not None
    assert fila[0].tzinfo is not None
    assert fila[1] == "timestamp with time zone"


# --- server_default de los modelos de acceso (autorizados por Lauti, 2026-11-05) ---

async def test_usuario_completa_sus_booleanos_con_el_default_del_servidor(sessionmaker_test):
    usuario_id = await _usuario(sessionmaker_test)
    async with sessionmaker_test() as s:
        fila = (await s.execute(
            text("SELECT activo, debe_cambiar_password FROM usuario WHERE id = :i"), {"i": usuario_id}
        )).one()
    assert tuple(fila) == (True, False)


@pytest.mark.parametrize(
    "insert,tabla,columna",
    [
        ("INSERT INTO intento_acceso (email, ip, exito) VALUES ('a@b.c', '1.2.3.4', false) RETURNING id",
         "intento_acceso", "cuando"),
        ("INSERT INTO evento_seguridad (actor, accion) VALUES ('SISTEMA', 'x') RETURNING id",
         "evento_seguridad", "cuando"),
    ],
)
async def test_fechas_de_registro_por_defecto_no_nulas_y_con_zona(sessionmaker_test, insert, tabla, columna):
    fila_id = await _escalar(sessionmaker_test, insert)
    async with sessionmaker_test() as s:
        valor = (await s.execute(
            text(f"SELECT {columna} FROM {tabla} WHERE id = :i"), {"i": fila_id}
        )).scalar()
    assert valor is not None and valor.tzinfo is not None


async def test_asignacion_rol_completa_desde_con_el_default_del_servidor(sessionmaker_test):
    usuario_id = await _usuario(sessionmaker_test)
    fila_id = await _escalar(
        sessionmaker_test,
        "INSERT INTO asignacion_rol (usuario_id, rol) VALUES (:u, 'ADMIN') RETURNING id",
        u=usuario_id,
    )
    desde = await _escalar(sessionmaker_test, "SELECT desde FROM asignacion_rol WHERE id = :i", i=fila_id)
    assert desde is not None and desde.tzinfo is not None


# --- acciones referenciales compatibles con el sólo agregado (design D9) ---

async def test_ninguna_fk_de_o_hacia_movimiento_stock_tiene_accion_en_delete(sessionmaker_test):
    async with sessionmaker_test() as s:
        filas = (await s.execute(text(
            "SELECT conname, confdeltype::text FROM pg_constraint "
            "WHERE contype = 'f' "
            "AND (conrelid = 'movimiento_stock'::regclass OR confrelid = 'movimiento_stock'::regclass)"
        ))).all()
    assert {f[0] for f in filas} == {
        "fk_movimiento_stock_libro_id_libro",
        "fk_movimiento_stock_venta_id_venta",
        "fk_movimiento_stock_usuario_id_usuario",
    }
    assert {f[1] for f in filas} == {"a"}  # 'a' = NO ACTION
