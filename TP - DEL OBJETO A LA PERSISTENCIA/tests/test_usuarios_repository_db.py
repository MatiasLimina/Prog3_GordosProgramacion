"""Repositorios del módulo `usuarios` contra la base real (CHG-11)."""
from datetime import UTC, datetime, timedelta

import pytest

pytestmark = pytest.mark.db


async def _crear_usuario(sessionmaker, email="ana@example.com") -> int:
    from app.modules.usuarios.models import Usuario

    async with sessionmaker() as s:
        usuario = Usuario(email=email, nombre="Ana", password_hash="hash-no-real")
        s.add(usuario)
        await s.commit()
        return usuario.id


# ---- UsuarioRepository.get_by_email ----

async def test_get_by_email_devuelve_el_usuario(sessionmaker_test):
    from app.modules.usuarios.repository import UsuarioRepository

    uid = await _crear_usuario(sessionmaker_test)
    async with sessionmaker_test() as s:
        usuario = await UsuarioRepository(s).get_by_email("ana@example.com")
    assert usuario is not None
    assert usuario.id == uid
    assert usuario.nombre == "Ana"


async def test_get_by_email_devuelve_none_si_no_existe_y_distingue_correos(sessionmaker_test):
    from app.modules.usuarios.repository import UsuarioRepository

    await _crear_usuario(sessionmaker_test)
    async with sessionmaker_test() as s:
        repo = UsuarioRepository(s)
        assert await repo.get_by_email("otra@example.com") is None
        assert await repo.get_by_email("ana@example.com' OR '1'='1") is None  # parámetro ligado


# ---- AsignacionRolRepository.roles_vigentes ----

async def test_roles_vigentes_devuelve_solo_los_no_revocados_y_sin_vencer(sessionmaker_test):
    from app.modules.usuarios.models import AsignacionRol
    from app.modules.usuarios.repository import AsignacionRolRepository

    uid = await _crear_usuario(sessionmaker_test)
    ahora = datetime.now(UTC)
    async with sessionmaker_test() as s:
        s.add_all([
            AsignacionRol(usuario_id=uid, rol="VENDEDOR"),
            AsignacionRol(usuario_id=uid, rol="ADMIN", revocada_en=ahora - timedelta(days=1)),
            AsignacionRol(usuario_id=uid, rol="CLIENTE", vence_en=ahora - timedelta(hours=1)),
        ])
        await s.commit()
    async with sessionmaker_test() as s:
        assert await AsignacionRolRepository(s).roles_vigentes(uid) == ["VENDEDOR"]


async def test_roles_vigentes_sin_filas_es_lista_vacia_y_ordena_por_rol(sessionmaker_test):
    from app.modules.usuarios.models import AsignacionRol
    from app.modules.usuarios.repository import AsignacionRolRepository

    uid = await _crear_usuario(sessionmaker_test)
    otro = await _crear_usuario(sessionmaker_test, "otro@example.com")
    futuro = datetime.now(UTC) + timedelta(days=1)
    async with sessionmaker_test() as s:
        assert await AsignacionRolRepository(s).roles_vigentes(uid) == []
        s.add_all([
            AsignacionRol(usuario_id=uid, rol="VENDEDOR", vence_en=futuro),
            AsignacionRol(usuario_id=uid, rol="ADMIN"),
            AsignacionRol(usuario_id=otro, rol="CLIENTE"),  # de otro usuario: no cuenta
        ])
        await s.commit()
    async with sessionmaker_test() as s:
        assert await AsignacionRolRepository(s).roles_vigentes(uid) == ["ADMIN", "VENDEDOR"]


# ---- IntentoAccesoRepository.contar_fallos_recientes (D4) ----

async def _insertar_intentos(sessionmaker, email, ip, exito, hace_segundos):
    """Una fila por cada antigüedad; `cuando` se calcula con el reloj de la base."""
    from sqlalchemy import text

    async with sessionmaker() as s:
        for seg in hace_segundos:
            await s.execute(
                text(
                    "INSERT INTO intento_acceso (cuando, email, ip, exito) "
                    "VALUES (now() - make_interval(secs => :seg), :email, :ip, :exito)"
                ),
                {"seg": seg, "email": email, "ip": ip, "exito": exito},
            )
        await s.commit()


async def _contar_fallos(sessionmaker, email="ana@example.com", ip="127.0.0.1"):
    from app.modules.usuarios.repository import IntentoAccesoRepository

    async with sessionmaker() as s:
        return await IntentoAccesoRepository(s).contar_fallos_recientes(email, ip)


async def test_cuenta_los_fallos_recientes_del_mismo_correo_e_ip(sessionmaker_test):
    await _insertar_intentos(sessionmaker_test, "ana@example.com", "127.0.0.1", False, [50, 40, 30, 20, 10])
    conteo = await _contar_fallos(sessionmaker_test)
    assert conteo.fallos == 5
    # el más viejo es el de hace ~50 s, medido con el mismo reloj que `ahora`
    assert 49 < (conteo.ahora - conteo.mas_viejo).total_seconds() < 55
    assert conteo.ahora.tzinfo is not None


@pytest.mark.parametrize(
    "fallos_de, esperado",
    [
        (("ana@example.com", "127.0.0.1", [61, 90, 120, 300, 600]), 0),  # fuera de la ventana
        (("ana@example.com", "10.0.0.9", [5, 10, 15, 20, 25]), 0),  # otra IP
        (("otra@example.com", "127.0.0.1", [5, 10, 15, 20, 25]), 0),  # otro correo
        (("ana@example.com", "127.0.0.1", [70, 5, 10]), 2),  # mezcla: sólo cuentan los de la ventana
    ],
    ids=["viejos", "otra_ip", "otro_correo", "mezcla"],
)
async def test_no_cuenta_fallos_fuera_de_alcance(sessionmaker_test, fallos_de, esperado):
    email, ip, antiguedades = fallos_de
    await _insertar_intentos(sessionmaker_test, email, ip, False, antiguedades)
    conteo = await _contar_fallos(sessionmaker_test)
    assert conteo.fallos == esperado
    if esperado == 0:
        assert conteo.mas_viejo is None


async def test_un_exito_reinicia_la_cuenta_sin_borrar_filas(sessionmaker_test):
    await _insertar_intentos(sessionmaker_test, "ana@example.com", "127.0.0.1", False, [50, 45, 40, 35])
    await _insertar_intentos(sessionmaker_test, "ana@example.com", "127.0.0.1", True, [30])
    await _insertar_intentos(sessionmaker_test, "ana@example.com", "127.0.0.1", False, [25, 20, 15, 10])
    conteo = await _contar_fallos(sessionmaker_test)
    assert conteo.fallos == 4
    assert 24 < (conteo.ahora - conteo.mas_viejo).total_seconds() < 30  # el más viejo POSTERIOR al éxito
    from tests.auxiliares_auth import contar

    assert await contar(sessionmaker_test, "intento_acceso") == 9


async def test_el_exito_de_otra_ip_o_de_otro_correo_no_reinicia(sessionmaker_test):
    await _insertar_intentos(sessionmaker_test, "ana@example.com", "127.0.0.1", False, [50, 40, 30])
    await _insertar_intentos(sessionmaker_test, "ana@example.com", "10.0.0.9", True, [20])
    await _insertar_intentos(sessionmaker_test, "otra@example.com", "127.0.0.1", True, [20])
    assert (await _contar_fallos(sessionmaker_test)).fallos == 3
