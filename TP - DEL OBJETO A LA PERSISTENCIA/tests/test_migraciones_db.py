"""Migraciones de Alembic sobre una base DESCARTABLE (`libreria_migraciones`).

Reversibilidad (`upgrade head` -> `downgrade base` -> `upgrade head`), aplicación de la tercera
migración sobre una base con filas del TP y presencia del disparador de sólo agregado (cuarta migración). No toca `libreria_test`: ese esquema lo deja armado el
fixture de sesión para el resto de la corrida.

La base `libreria_migraciones` la crea y la borra cada test (conexión a la base `postgres`).
Igual que el conftest: sin base responde skip, y con REQUIRE_TEST_DB=1 responde fallo.
"""
import os
import subprocess
import sys
from pathlib import Path

import asyncpg
import pytest
import pytest_asyncio
from sqlalchemy.engine import make_url

from app.core.config import get_settings

pytestmark = pytest.mark.db

BASE_DESCARTABLE = "libreria_migraciones"
PROYECTO = Path(__file__).resolve().parent.parent

SEGUNDA_REVISION = "9df0eb6a1dd6"
TERCERA_REVISION = "0003"
CUARTA_REVISION = "0004"

FUNCION = "movimiento_stock_solo_agregado"
DISPARADOR = "tg_movimiento_stock_solo_agregado"

TABLAS = {
    "editorial", "genero", "autor", "libro", "libro_autor", "cliente", "perfil_cliente",
    "venta", "renglon_venta", "usuario", "asignacion_rol", "intento_acceso",
    "evento_seguridad", "movimiento_stock",
}


def _sin_base(motivo: str):
    if os.environ.get("REQUIRE_TEST_DB") == "1":
        pytest.fail(f"REQUIRE_TEST_DB=1 y no hay base para migraciones: {motivo}")
    pytest.skip(f"No hay base para migraciones ({motivo})")


def _url(base: str):
    try:
        return make_url(get_settings().database_url).set(database=base)
    except RuntimeError:
        _sin_base("falta configuración: POSTGRES_* o JWT_SECRET")


async def _conectar(base: str) -> asyncpg.Connection:
    url = _url(base)
    return await asyncpg.connect(
        host=url.host, port=url.port, user=url.username, password=url.password,
        database=url.database, timeout=5,
    )


async def _administrar(accion: str) -> None:
    """CREATE/DROP DATABASE desde la base `postgres`; sólo sobre la base descartable."""
    assert BASE_DESCARTABLE == "libreria_migraciones"  # nunca borrar otra base
    sentencias = {
        "crear": f'CREATE DATABASE "{BASE_DESCARTABLE}"',
        "borrar": f'DROP DATABASE IF EXISTS "{BASE_DESCARTABLE}" WITH (FORCE)',
    }
    conexion = await _conectar("postgres")
    try:
        await conexion.execute(sentencias[accion])
    finally:
        await conexion.close()


def alembic(*args: str) -> subprocess.CompletedProcess:
    """Corre Alembic en un subproceso contra la base descartable."""
    env = {**os.environ, "POSTGRES_DB": BASE_DESCARTABLE}
    r = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=PROYECTO, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
    )
    assert r.returncode == 0, f"alembic {' '.join(args)} falló:\n{r.stdout}\n{r.stderr}"
    return r


@pytest_asyncio.fixture
async def base_migraciones():
    """Crea `libreria_migraciones` vacía y la borra al terminar."""
    try:
        await _administrar("borrar")
        await _administrar("crear")
    except (OSError, TimeoutError, asyncpg.PostgresError) as e:
        _sin_base(type(e).__name__)
    try:
        yield BASE_DESCARTABLE
    finally:
        await _administrar("borrar")


async def _tablas() -> set[str]:
    conexion = await _conectar(BASE_DESCARTABLE)
    try:
        filas = await conexion.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        )
    finally:
        await conexion.close()
    return {f["table_name"] for f in filas}


async def _indices_y_constraints() -> tuple[set[str], set[str]]:
    """Nombres de índices (schema public) y de constraints de la base descartable."""
    conexion = await _conectar(BASE_DESCARTABLE)
    try:
        indices = await conexion.fetch("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
        constraints = await conexion.fetch(
            "SELECT c.conname FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace "
            "WHERE n.nspname = 'public'"
        )
    finally:
        await conexion.close()
    return {f["indexname"] for f in indices}, {f["conname"] for f in constraints}


async def _version() -> list[str]:
    conexion = await _conectar(BASE_DESCARTABLE)
    try:
        filas = await conexion.fetch("SELECT version_num FROM alembic_version")
    finally:
        await conexion.close()
    return [f["version_num"] for f in filas]


async def _funcion_y_disparador() -> tuple[bool, bool]:
    """(existe la función, existe el disparador) de sólo agregado."""
    conexion = await _conectar(BASE_DESCARTABLE)
    try:
        funcion = await conexion.fetchval("SELECT count(*) FROM pg_proc WHERE proname = $1", FUNCION)
        disparador = await conexion.fetchval(
            "SELECT count(*) FROM pg_trigger WHERE tgname = $1 AND NOT tgisinternal", DISPARADOR
        )
    finally:
        await conexion.close()
    return funcion == 1, disparador == 1


async def _insertar_movimiento() -> int:
    conexion = await _conectar(BASE_DESCARTABLE)
    try:
        editorial_id = await conexion.fetchval("INSERT INTO editorial (nombre, pais) VALUES ('E', 'AR') RETURNING id")
        libro_id = await conexion.fetchval(
            "INSERT INTO libro (isbn, titulo, precio, stock, editorial_id) VALUES ('I', 'T', 1, 1, $1) RETURNING id",
            editorial_id,
        )
        usuario_id = await conexion.fetchval(
            "INSERT INTO usuario (email, nombre, password_hash) VALUES ('u@example.com', 'U', 'x') RETURNING id"
        )
        return await conexion.fetchval(
            "INSERT INTO movimiento_stock (libro_id, usuario_id, cantidad, motivo) VALUES ($1, $2, 1, 'm') RETURNING id",
            libro_id, usuario_id,
        )
    finally:
        await conexion.close()


async def _actualizar_motivo(movimiento_id: int) -> None:
    conexion = await _conectar(BASE_DESCARTABLE)
    try:
        await conexion.execute("UPDATE movimiento_stock SET motivo = 'cambiado' WHERE id = $1", movimiento_id)
    finally:
        await conexion.close()


async def test_upgrade_head_deja_las_catorce_tablas(base_migraciones):
    alembic("upgrade", "head")

    assert await _tablas() == TABLAS | {"alembic_version"}
    assert await _version() == [CUARTA_REVISION]
    assert await _funcion_y_disparador() == (True, True)


async def test_downgrade_base_deja_solo_alembic_version_vacia(base_migraciones):
    alembic("upgrade", "head")
    alembic("downgrade", "base")

    assert await _tablas() == {"alembic_version"}
    assert await _version() == []
    assert await _funcion_y_disparador() == (False, False)


async def test_ida_vuelta_e_ida_deja_el_mismo_esquema(base_migraciones):
    alembic("upgrade", "head")
    primera = await _tablas()
    primeros_nombres = await _indices_y_constraints()
    assert primeros_nombres[0] and primeros_nombres[1]
    alembic("downgrade", "base")
    alembic("upgrade", "head")

    assert await _tablas() == primera == TABLAS | {"alembic_version"}
    assert await _indices_y_constraints() == primeros_nombres
    assert await _version() == [CUARTA_REVISION]
    assert await _funcion_y_disparador() == (True, True)


async def test_bajar_a_la_tercera_revision_retira_el_disparador_y_volver_a_head_lo_instala(base_migraciones):
    alembic("upgrade", "head")
    movimiento_id = await _insertar_movimiento()

    alembic("downgrade", TERCERA_REVISION)
    assert await _version() == [TERCERA_REVISION]
    assert await _funcion_y_disparador() == (False, False)
    await _actualizar_motivo(movimiento_id)  # sin disparador, el UPDATE se acepta

    alembic("upgrade", "head")
    assert await _version() == [CUARTA_REVISION]
    assert await _funcion_y_disparador() == (True, True)
    with pytest.raises(asyncpg.IntegrityConstraintViolationError):
        await _actualizar_motivo(movimiento_id)  # con disparador, se rechaza otra vez


async def test_la_tercera_migracion_se_aplica_sobre_una_base_con_datos_del_tp(base_migraciones):
    alembic("upgrade", SEGUNDA_REVISION)
    conexion = await _conectar(BASE_DESCARTABLE)
    try:
        editorial_id = await conexion.fetchval(
            "INSERT INTO editorial (nombre, pais) VALUES ('Editorial TP', 'AR') RETURNING id"
        )
        await conexion.execute(
            "INSERT INTO libro (isbn, titulo, precio, stock, editorial_id) "
            "VALUES ('ISBN-TP', 'Libro del TP', 1500.00, 7, $1)",
            editorial_id,
        )
        await conexion.execute(
            "INSERT INTO cliente (nombre, email) VALUES ('Ana TP', 'ana@example.com')"
        )
    finally:
        await conexion.close()

    alembic("upgrade", "head")

    conexion = await _conectar(BASE_DESCARTABLE)
    try:
        libro = await conexion.fetchrow("SELECT isbn, titulo, precio, stock, borrado_en FROM libro")
        cliente = await conexion.fetchrow("SELECT nombre, email, usuario_id FROM cliente")
        usuarios = await conexion.fetchval("SELECT count(*) FROM usuario")
        movimientos = await conexion.fetchval("SELECT count(*) FROM movimiento_stock")
    finally:
        await conexion.close()
    assert (libro["isbn"], libro["titulo"], str(libro["precio"]), libro["stock"]) == (
        "ISBN-TP", "Libro del TP", "1500.00", 7,
    )
    assert libro["borrado_en"] is None
    assert (cliente["nombre"], cliente["email"], cliente["usuario_id"]) == ("Ana TP", "ana@example.com", None)
    assert (usuarios, movimientos) == (0, 0)
