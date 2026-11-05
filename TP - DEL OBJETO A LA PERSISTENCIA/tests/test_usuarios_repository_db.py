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
