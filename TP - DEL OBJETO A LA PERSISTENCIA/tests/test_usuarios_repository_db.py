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


async def _contar_fallos(sessionmaker, email="ana@example.com", ip="127.0.0.1", ventana_segundos=60):
    from app.modules.usuarios.repository import IntentoAccesoRepository

    async with sessionmaker() as s:
        return await IntentoAccesoRepository(s).contar_fallos_recientes(email, ip, ventana_segundos)


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


@pytest.mark.parametrize(
    "ventana, esperado",
    [(30, 2), (60, 3), (120, 4)],
    ids=["ventana_30", "ventana_60", "ventana_120"],
)
async def test_la_ventana_es_un_parametro_y_se_respeta(sessionmaker_test, ventana, esperado):
    # fallos de hace 10, 20, 45 y 90 s: cada ventana deja entrar sólo a los más recientes
    await _insertar_intentos(sessionmaker_test, "ana@example.com", "127.0.0.1", False, [10, 20, 45, 90])
    conteo = await _contar_fallos(sessionmaker_test, ventana_segundos=ventana)
    assert conteo.fallos == esperado


# ---- CHG-14: repositorios de asignaciones y eventos (design D3, D4, D5, D7) ----

async def _insertar_asignacion(sessionmaker, usuario_id, rol, *, vence_en=None, revocada_en=None) -> int:
    from app.modules.usuarios.models import AsignacionRol

    async with sessionmaker() as s:
        fila = AsignacionRol(usuario_id=usuario_id, rol=rol, vence_en=vence_en, revocada_en=revocada_en)
        s.add(fila)
        await s.commit()
        return fila.id


async def _fila(sessionmaker, asignacion_id):
    from app.modules.usuarios.models import AsignacionRol

    async with sessionmaker() as s:
        return await s.get(AsignacionRol, asignacion_id)


# ---- historial y asignar ----

async def test_historial_trae_todas_las_filas_del_usuario_por_id(sessionmaker_test):
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    uid = await _crear_usuario(sessionmaker_test)
    otro = await _crear_usuario(sessionmaker_test, "otro@example.com")
    ahora = datetime.now(UTC)
    vigente = await _insertar_asignacion(sessionmaker_test, uid, "VENDEDOR")
    vencida = await _insertar_asignacion(sessionmaker_test, uid, "ADMIN", vence_en=ahora - timedelta(hours=1))
    revocada = await _insertar_asignacion(sessionmaker_test, uid, "CLIENTE", revocada_en=ahora - timedelta(days=1))
    await _insertar_asignacion(sessionmaker_test, otro, "VENDEDOR")  # de otro usuario: no cuenta
    async with sessionmaker_test() as s, UsuariosUoW(s) as uow:
        filas = await uow.asignaciones.historial(uid)
        sin_filas = await uow.asignaciones.historial(otro + 100)
    assert [f.id for f in filas] == [vigente, vencida, revocada]
    assert sin_filas == []


async def test_asignar_asigna_id_y_deja_desde_cargado_sin_consultas(sessionmaker_test):
    from sqlalchemy import event

    from app.modules.usuarios.models import AsignacionRol
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    uid = await _crear_usuario(sessionmaker_test)
    sentencias: list[str] = []

    def _anotar(conn, cursor, statement, *args):
        sentencias.append(statement)

    async with sessionmaker_test() as s, UsuariosUoW(s) as uow:
        fila = await uow.asignaciones.asignar(AsignacionRol(usuario_id=uid, rol="VENDEDOR"))
        motor = s.bind.sync_engine
        event.listen(motor, "before_cursor_execute", _anotar)
        try:
            desde = fila.desde
            id_asignado = fila.id
        finally:
            event.remove(motor, "before_cursor_execute", _anotar)
    assert id_asignado is not None
    assert desde.tzinfo is not None
    assert sentencias == []  # eager_defaults: `desde` volvió por RETURNING del INSERT


async def test_asignar_a_un_usuario_inexistente_lanza_usuario_no_encontrado(sessionmaker_test):
    from app.core.errors import UsuarioNoEncontrado
    from app.modules.usuarios.models import AsignacionRol
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    async with sessionmaker_test() as s:
        with pytest.raises(UsuarioNoEncontrado) as excinfo:
            async with UsuariosUoW(s) as uow:
                await uow.asignaciones.asignar(AsignacionRol(usuario_id=9999, rol="VENDEDOR"))
    assert excinfo.value.usuario_id == 9999
    assert excinfo.value.mensaje == "El usuario no existe."


async def test_asignar_un_rol_vigente_repetido_termina_en_conflicto_del_uow(sessionmaker_test):
    from app.core.errors import Conflicto
    from app.modules.usuarios.models import AsignacionRol
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    uid = await _crear_usuario(sessionmaker_test)
    await _insertar_asignacion(sessionmaker_test, uid, "VENDEDOR")
    async with sessionmaker_test() as s:
        with pytest.raises(Conflicto) as excinfo:
            async with UsuariosUoW(s) as uow:
                await uow.asignaciones.asignar(AsignacionRol(usuario_id=uid, rol="VENDEDOR"))
    assert excinfo.value.mensaje == "El usuario ya tiene ese rol vigente."


# ---- cerrar_vencida ----

async def test_cerrar_vencida_escribe_vence_en_y_solo_en_la_fila_abierta_y_vencida(sessionmaker_test):
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    uid = await _crear_usuario(sessionmaker_test)
    otro = await _crear_usuario(sessionmaker_test, "otro@example.com")
    ahora = datetime.now(UTC)
    vence = ahora - timedelta(hours=2)
    vencida = await _insertar_asignacion(sessionmaker_test, uid, "VENDEDOR", vence_en=vence)
    futura = await _insertar_asignacion(sessionmaker_test, uid, "ADMIN", vence_en=ahora + timedelta(days=1))
    sin_vencimiento = await _insertar_asignacion(sessionmaker_test, uid, "CLIENTE")
    revocada_antes = ahora - timedelta(days=3)
    revocada = await _insertar_asignacion(
        sessionmaker_test, uid, "VENDEDOR", vence_en=ahora - timedelta(days=5), revocada_en=revocada_antes
    )
    de_otro = await _insertar_asignacion(sessionmaker_test, otro, "VENDEDOR", vence_en=vence)
    async with sessionmaker_test() as s, UsuariosUoW(s) as uow:
        cerradas = await uow.asignaciones.cerrar_vencida(uid, "VENDEDOR")
        otra_vez = await uow.asignaciones.cerrar_vencida(uid, "VENDEDOR")
    assert (cerradas, otra_vez) == (1, 0)
    cerrada = await _fila(sessionmaker_test, vencida)
    assert cerrada.revocada_en == cerrada.vence_en == vence  # su propio vencimiento, no now()
    assert (await _fila(sessionmaker_test, futura)).revocada_en is None
    assert (await _fila(sessionmaker_test, sin_vencimiento)).revocada_en is None
    assert (await _fila(sessionmaker_test, revocada)).revocada_en == revocada_antes
    assert (await _fila(sessionmaker_test, de_otro)).revocada_en is None  # otro usuario


async def test_cerrar_vencida_no_toca_otro_rol_del_mismo_usuario(sessionmaker_test):
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    uid = await _crear_usuario(sessionmaker_test)
    vence = datetime.now(UTC) - timedelta(hours=1)
    vendedor = await _insertar_asignacion(sessionmaker_test, uid, "VENDEDOR", vence_en=vence)
    async with sessionmaker_test() as s, UsuariosUoW(s) as uow:
        assert await uow.asignaciones.cerrar_vencida(uid, "CLIENTE") == 0
    assert (await _fila(sessionmaker_test, vendedor)).revocada_en is None


# ---- revocar_vigente ----

async def test_revocar_vigente_devuelve_la_fila_revocada_y_la_deja_en_la_base(sessionmaker_test):
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    uid = await _crear_usuario(sessionmaker_test)
    futura = datetime.now(UTC) + timedelta(days=1)
    sin_venc = await _insertar_asignacion(sessionmaker_test, uid, "VENDEDOR")
    con_futuro = await _insertar_asignacion(sessionmaker_test, uid, "CLIENTE", vence_en=futura)
    async with sessionmaker_test() as s, UsuariosUoW(s) as uow:
        a = await uow.asignaciones.revocar_vigente(uid, "VENDEDOR")
        b = await uow.asignaciones.revocar_vigente(uid, "CLIENTE")
        assert (a.id, a.rol, a.usuario_id) == (sin_venc, "VENDEDOR", uid)
        assert a.revocada_en is not None and a.desde is not None
        assert b.vence_en == futura
    assert (await _fila(sessionmaker_test, sin_venc)).revocada_en is not None
    assert (await _fila(sessionmaker_test, con_futuro)).revocada_en is not None


@pytest.mark.parametrize("caso", ["vencida", "ya_revocada", "no_existe", "otro_rol"])
async def test_revocar_vigente_devuelve_none_y_no_escribe_si_no_hay_vigente(sessionmaker_test, caso):
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    uid = await _crear_usuario(sessionmaker_test)
    ahora = datetime.now(UTC)
    antes = ahora - timedelta(days=1)
    fila = None
    if caso == "vencida":
        fila = await _insertar_asignacion(sessionmaker_test, uid, "VENDEDOR", vence_en=ahora - timedelta(hours=1))
    elif caso == "ya_revocada":
        fila = await _insertar_asignacion(sessionmaker_test, uid, "VENDEDOR", revocada_en=antes)
    elif caso == "otro_rol":
        fila = await _insertar_asignacion(sessionmaker_test, uid, "CLIENTE")
    async with sessionmaker_test() as s, UsuariosUoW(s) as uow:
        assert await uow.asignaciones.revocar_vigente(uid, "VENDEDOR") is None
    if fila is not None:
        asignacion = await _fila(sessionmaker_test, fila)
        assert asignacion.revocada_en == (antes if caso == "ya_revocada" else None)


# ---- bloquear_admins_vigentes y contar_admins_vigentes ----

async def test_bloquear_admins_vigentes_devuelve_los_usuarios_ordenados_por_id_de_asignacion(sessionmaker_test):
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    u1 = await _crear_usuario(sessionmaker_test, "u1@example.com")
    u2 = await _crear_usuario(sessionmaker_test, "u2@example.com")
    u3 = await _crear_usuario(sessionmaker_test, "u3@example.com")
    u4 = await _crear_usuario(sessionmaker_test, "u4@example.com")
    u5 = await _crear_usuario(sessionmaker_test, "u5@example.com")
    ahora = datetime.now(UTC)
    await _insertar_asignacion(sessionmaker_test, u2, "ADMIN")  # primero, aunque su usuario_id es mayor
    await _insertar_asignacion(sessionmaker_test, u1, "ADMIN")
    await _insertar_asignacion(sessionmaker_test, u3, "ADMIN", vence_en=ahora - timedelta(hours=1))  # vencido
    await _insertar_asignacion(sessionmaker_test, u4, "ADMIN", revocada_en=ahora - timedelta(hours=1))  # revocado
    await _insertar_asignacion(sessionmaker_test, u5, "VENDEDOR")  # otro rol
    async with sessionmaker_test() as s, UsuariosUoW(s) as uow:
        assert await uow.asignaciones.bloquear_admins_vigentes() == [u2, u1]


async def test_contar_admins_vigentes_cuenta_vigentes_y_ve_la_revocacion_de_la_misma_transaccion(sessionmaker_test):
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    u1 = await _crear_usuario(sessionmaker_test, "u1@example.com")
    u2 = await _crear_usuario(sessionmaker_test, "u2@example.com")
    u3 = await _crear_usuario(sessionmaker_test, "u3@example.com")
    await _insertar_asignacion(sessionmaker_test, u1, "ADMIN")
    await _insertar_asignacion(sessionmaker_test, u2, "ADMIN", vence_en=datetime.now(UTC) + timedelta(days=1))
    await _insertar_asignacion(sessionmaker_test, u3, "ADMIN", revocada_en=datetime.now(UTC))
    async with sessionmaker_test() as s, UsuariosUoW(s) as uow:
        assert await uow.asignaciones.contar_admins_vigentes() == 2
        assert await uow.asignaciones.revocar_vigente(u1, "ADMIN") is not None
        assert await uow.asignaciones.contar_admins_vigentes() == 1  # ya no cuenta la recién revocada


async def test_bloquear_admins_vigentes_usa_for_update_y_order_by_id_y_ningun_agregado(sessionmaker_test):
    from sqlalchemy import event

    from app.modules.usuarios.unit_of_work import UsuariosUoW

    sentencias: list[str] = []

    def _anotar(conn, cursor, statement, *args):
        sentencias.append(statement)

    async with sessionmaker_test() as s:
        motor = s.bind.sync_engine
        event.listen(motor, "before_cursor_execute", _anotar)
        try:
            async with UsuariosUoW(s) as uow:
                await uow.asignaciones.bloquear_admins_vigentes()
        finally:
            event.remove(motor, "before_cursor_execute", _anotar)
    [sql] = [x for x in sentencias if "asignacion_rol" in x]
    assert "FOR UPDATE" in sql
    assert "ORDER BY asignacion_rol.id" in sql
    assert "count(" not in sql.lower()


# ---- EventoSeguridadRepository.listar_recientes ----

async def test_listar_recientes_ordena_por_cuando_e_id_descendentes_y_count_cuenta_todas(sessionmaker_test):
    from app.modules.usuarios.models import EventoSeguridad
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    base = datetime(2026, 1, 1, tzinfo=UTC)
    async with sessionmaker_test() as s:
        s.add_all([
            EventoSeguridad(cuando=base, actor="a", accion="viejo"),
            EventoSeguridad(cuando=base + timedelta(days=2), actor="a", accion="nuevo-1"),
            EventoSeguridad(cuando=base + timedelta(days=2), actor="a", accion="nuevo-2"),  # mismo `cuando`: gana el id mayor
            EventoSeguridad(cuando=base + timedelta(days=1), actor="a", accion="medio"),
        ])
        await s.commit()
    async with sessionmaker_test() as s, UsuariosUoW(s) as uow:
        todos = await uow.eventos.listar_recientes(0, 10)
        pagina = await uow.eventos.listar_recientes(1, 2)
        total = await uow.eventos.count()
    assert [e.accion for e in todos] == ["nuevo-2", "nuevo-1", "medio", "viejo"]
    assert [e.accion for e in pagina] == ["nuevo-1", "medio"]
    assert total == 4
