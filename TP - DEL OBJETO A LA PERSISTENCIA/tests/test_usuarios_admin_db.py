"""Administración de usuarios y roles contra la base real (CHG-14, `usuarios-admin`).

Alta de personal, asignación y revocación de roles, historial de seguridad y las rutas que los
exponen. Los servicios se llaman con un `UsuariosUoW` armado sobre `sessionmaker_test` y un
`UsuarioActual` de ADMIN; las rutas, con `entrar_como(client, sessionmaker_test, "ADMIN")`.
"""
import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import SecretStr
from sqlalchemy import text

from tests.auxiliares_auth import contar, filas, insertar_usuario

pytestmark = pytest.mark.db

ADMIN_EMAIL = "admin@example.com"


def _seg(semaforo=None):
    from app.core.dependencies import ParametrosSeguridad

    return ParametrosSeguridad(
        costo=4,
        semaforo=semaforo or asyncio.Semaphore(1),
        hash_ficticio="no-usado",
        secreto=SecretStr("x" * 40),
        minutos_token=15,
        cookie_secure=False,
    )


def _actor(uid: int, email: str = ADMIN_EMAIL):
    from app.core.dependencies import UsuarioActual

    return UsuarioActual(
        id=uid, email=email, nombre="Admin", activo=True, debe_cambiar_password=False, roles_token=["ADMIN"]
    )


async def _admin(sessionmaker, email: str = ADMIN_EMAIL):
    """Inserta un ADMIN vigente y devuelve su `UsuarioActual`."""
    return _actor(await insertar_usuario(sessionmaker, email, roles=("ADMIN",)), email)


def _datos_alta(email="caja@example.com", password="provisoria-1"):
    from app.modules.usuarios.schemas import UsuarioCreate

    return UsuarioCreate(email=email, nombre="Caja", password=password)


async def _alta(sessionmaker, actor, datos=None, seg=None):
    from app.modules.usuarios import service
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    async with sessionmaker() as s:
        return await service.dar_de_alta_personal(UsuariosUoW(s), datos or _datos_alta(), actor, seg or _seg())


# ---- 4.1 Alta de personal ----

async def test_alta_crea_el_usuario_con_cambio_pendiente_hash_valido_sin_roles_y_su_evento(sessionmaker_test):
    from app.core.security import verificar_password

    admin = await _admin(sessionmaker_test)
    respuesta = await _alta(sessionmaker_test, admin)

    assert respuesta.email == "caja@example.com"
    assert (respuesta.activo, respuesta.debe_cambiar_password) == (True, True)
    assert "password_hash" not in respuesta.model_dump()
    [fila] = await filas(sessionmaker_test, "SELECT * FROM usuario WHERE id = :id", id=respuesta.id)
    assert fila["activo"] is True and fila["debe_cambiar_password"] is True
    assert fila["password_hash"] != "provisoria-1"
    assert await verificar_password("provisoria-1", fila["password_hash"], semaforo=asyncio.Semaphore(1))
    assert await contar(sessionmaker_test, "asignacion_rol", "usuario_id = :u", u=respuesta.id) == 0  # D1: sin rol
    [evento] = await filas(sessionmaker_test, "SELECT actor, accion FROM evento_seguridad")
    assert evento["actor"] == ADMIN_EMAIL
    assert evento["accion"] == f"Alta de personal: usuario {respuesta.id}"


async def test_alta_con_otro_actor_y_otro_usuario_deja_sus_propios_datos(sessionmaker_test):
    admin = await _admin(sessionmaker_test, "otro-admin@example.com")
    respuesta = await _alta(sessionmaker_test, admin, _datos_alta("deposito@example.com", "otra-clave-2"))

    [evento] = await filas(sessionmaker_test, "SELECT actor, accion FROM evento_seguridad")
    assert (evento["actor"], evento["accion"]) == ("otro-admin@example.com", f"Alta de personal: usuario {respuesta.id}")


async def test_alta_con_correo_repetido_es_conflicto_y_no_deja_filas_nuevas(sessionmaker_test):
    from app.core.errors import Conflicto

    admin = await _admin(sessionmaker_test)
    await insertar_usuario(sessionmaker_test, "caja@example.com")
    usuarios_antes = await contar(sessionmaker_test, "usuario")
    eventos_antes = await contar(sessionmaker_test, "evento_seguridad")

    with pytest.raises(Conflicto) as excinfo:
        await _alta(sessionmaker_test, admin)

    assert excinfo.value.mensaje == "Ya existe un usuario con ese correo."
    assert await contar(sessionmaker_test, "usuario") == usuarios_antes
    assert await contar(sessionmaker_test, "evento_seguridad") == eventos_antes


async def test_alta_con_el_correo_de_un_cliente_sin_cuenta_crea_el_usuario_y_no_vincula_la_ficha(sessionmaker_test):
    from app.modules.clientes.models import Cliente

    admin = await _admin(sessionmaker_test)
    async with sessionmaker_test() as s:
        s.add(Cliente(nombre="Caja Cliente", email="caja@example.com"))
        await s.commit()

    respuesta = await _alta(sessionmaker_test, admin)

    assert respuesta.id is not None
    [ficha] = await filas(sessionmaker_test, "SELECT usuario_id FROM cliente WHERE email = 'caja@example.com'")
    assert ficha["usuario_id"] is None


async def test_si_falla_el_evento_no_queda_el_usuario(sessionmaker_test, monkeypatch):
    from app.modules.usuarios.repository import EventoSeguridadRepository

    admin = await _admin(sessionmaker_test)

    async def falla(self, evento):
        raise RuntimeError("falla el evento")

    monkeypatch.setattr(EventoSeguridadRepository, "add", falla)
    usuarios_antes = await contar(sessionmaker_test, "usuario")

    with pytest.raises(RuntimeError):
        await _alta(sessionmaker_test, admin)

    assert await contar(sessionmaker_test, "usuario") == usuarios_antes
    assert await contar(sessionmaker_test, "evento_seguridad") == 0


# ---- 4.2 El hash se calcula antes de abrir el UoW ----

async def test_el_hash_termina_antes_de_abrir_el_uow_y_con_el_semaforo_de_los_parametros(
    sessionmaker_test, monkeypatch
):
    from app.modules.usuarios import service
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    admin = await _admin(sessionmaker_test)
    orden: list[tuple] = []
    real_hash = service.hashear_password
    real_aenter = UsuariosUoW.__aenter__
    semaforo = asyncio.Semaphore(1)

    async def hash_espia(password, **kwargs):
        orden.append(("hash-inicio", uow_abierto[0]))
        resultado = await real_hash(password, **kwargs)
        orden.append(("hash-fin", uow_abierto[0], kwargs["semaforo"]))
        return resultado

    async def aenter_espia(self):
        orden.append(("aenter",))
        uow_abierto[0] = True
        return await real_aenter(self)

    uow_abierto = [False]
    monkeypatch.setattr(service, "hashear_password", hash_espia)
    monkeypatch.setattr(UsuariosUoW, "__aenter__", aenter_espia)

    await _alta(sessionmaker_test, admin, seg=_seg(semaforo))

    assert [paso[0] for paso in orden] == ["hash-inicio", "hash-fin", "aenter"]
    assert orden[0][1] is False and orden[1][1] is False  # ningún UoW abierto durante el hash
    assert orden[1][2] is semaforo


# ---- 5. Gestión de roles ----

async def _insertar_asignacion(sessionmaker, usuario_id, rol, *, vence_en=None, revocada_en=None) -> int:
    from app.modules.usuarios.models import AsignacionRol

    async with sessionmaker() as s:
        fila = AsignacionRol(usuario_id=usuario_id, rol=rol, vence_en=vence_en, revocada_en=revocada_en)
        s.add(fila)
        await s.commit()
        return fila.id


async def _asignaciones(sessionmaker, usuario_id):
    return await filas(
        sessionmaker, "SELECT * FROM asignacion_rol WHERE usuario_id = :u ORDER BY id", u=usuario_id
    )


async def _eventos(sessionmaker):
    return await filas(sessionmaker, "SELECT actor, accion FROM evento_seguridad ORDER BY id")


async def _asignar(sessionmaker, actor, usuario_id, rol, vence_en=None):
    from app.modules.usuarios import service
    from app.modules.usuarios.schemas import AsignacionRolCreate
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    async with sessionmaker() as s:
        return await service.asignar_rol(
            UsuariosUoW(s), usuario_id, AsignacionRolCreate(rol=rol, vence_en=vence_en), actor
        )


async def _revocar(sessionmaker, actor, usuario_id, rol):
    from app.modules.usuarios import service
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    async with sessionmaker() as s:
        return await service.revocar_rol(UsuariosUoW(s), usuario_id, rol, actor)


async def _asignar_con(session, actor, usuario_id, rol):
    """`asignar_rol` sobre una sesión que ya tiene el llamador (para conocer su backend)."""
    from app.modules.usuarios import service
    from app.modules.usuarios.schemas import AsignacionRolCreate
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    return await service.asignar_rol(UsuariosUoW(session), usuario_id, AsignacionRolCreate(rol=rol), actor)


async def _revocar_con(session, actor, usuario_id, rol):
    """`revocar_rol` sobre una sesión que ya tiene el llamador (para conocer su backend)."""
    from app.modules.usuarios import service
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    return await service.revocar_rol(UsuariosUoW(session), usuario_id, rol, actor)


def _en(**delta):
    return datetime.now(UTC) + timedelta(**delta)


async def test_listar_roles_devuelve_el_historial_completo_como_contratos(sessionmaker_test):
    from app.modules.usuarios import service
    from app.modules.usuarios.schemas import AsignacionRolRead
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    uid = await insertar_usuario(sessionmaker_test, "v@example.com")
    vigente = await _insertar_asignacion(sessionmaker_test, uid, "VENDEDOR")
    revocada = await _insertar_asignacion(sessionmaker_test, uid, "CLIENTE", revocada_en=_en(days=-1))

    async with sessionmaker_test() as s:
        roles = await service.listar_roles(UsuariosUoW(s), uid)

    assert all(isinstance(r, AsignacionRolRead) for r in roles)
    assert [(r.id, r.rol) for r in roles] == [(vigente, "VENDEDOR"), (revocada, "CLIENTE")]
    assert roles[1].revocada_en is not None


async def test_listar_roles_de_un_usuario_sin_asignaciones_es_lista_vacia(sessionmaker_test):
    from app.modules.usuarios import service
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    uid = await insertar_usuario(sessionmaker_test, "v@example.com")
    async with sessionmaker_test() as s:
        assert await service.listar_roles(UsuariosUoW(s), uid) == []


async def test_listar_roles_de_un_usuario_inexistente_es_usuario_no_encontrado(sessionmaker_test):
    from app.core.errors import UsuarioNoEncontrado
    from app.modules.usuarios import service
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    async with sessionmaker_test() as s:
        with pytest.raises(UsuarioNoEncontrado) as excinfo:
            await service.listar_roles(UsuariosUoW(s), 9999)
    assert excinfo.value.mensaje == "El usuario no existe."


@pytest.mark.parametrize("vence_en", [None, "futuro"])
async def test_asignar_crea_la_asignacion_con_otorgada_por_y_deja_su_evento(sessionmaker_test, vence_en):
    admin = await _admin(sessionmaker_test)
    uid = await insertar_usuario(sessionmaker_test, "v@example.com")
    vence = _en(days=1) if vence_en else None

    respuesta = await _asignar(sessionmaker_test, admin, uid, "VENDEDOR", vence)

    assert (respuesta.usuario_id, respuesta.rol, respuesta.vence_en) == (uid, "VENDEDOR", vence)
    assert respuesta.revocada_en is None and respuesta.otorgada_por == admin.id
    assert respuesta.desde is not None
    [fila] = await _asignaciones(sessionmaker_test, uid)
    assert (fila["otorgada_por"], fila["revocada_en"]) == (admin.id, None)
    assert await _eventos(sessionmaker_test) == [
        {"actor": ADMIN_EMAIL, "accion": f"Asignación del rol VENDEDOR al usuario {uid}"}
    ]


@pytest.mark.parametrize("vence_en", [None, "futuro"], ids=["sin_vencimiento", "vence_en_futuro"])
async def test_asignar_un_rol_vigente_es_conflicto_sin_evento_y_deja_la_fila_intacta(sessionmaker_test, vence_en):
    from app.core.errors import Conflicto

    admin = await _admin(sessionmaker_test)
    uid = await insertar_usuario(sessionmaker_test, "v@example.com")
    vence = _en(days=1) if vence_en else None
    await _insertar_asignacion(sessionmaker_test, uid, "VENDEDOR", vence_en=vence)
    eventos_antes = await contar(sessionmaker_test, "evento_seguridad")

    with pytest.raises(Conflicto) as excinfo:
        await _asignar(sessionmaker_test, admin, uid, "VENDEDOR")

    assert excinfo.value.mensaje == "El usuario ya tiene ese rol vigente."
    [fila] = await _asignaciones(sessionmaker_test, uid)
    assert fila["revocada_en"] is None and fila["vence_en"] == vence
    assert await contar(sessionmaker_test, "evento_seguridad") == eventos_antes


async def test_asignar_a_un_usuario_inexistente_es_usuario_no_encontrado_sin_evento(sessionmaker_test):
    from app.core.errors import UsuarioNoEncontrado

    admin = await _admin(sessionmaker_test)
    eventos_antes = await contar(sessionmaker_test, "evento_seguridad")

    with pytest.raises(UsuarioNoEncontrado):
        await _asignar(sessionmaker_test, admin, 9999, "VENDEDOR")

    assert await contar(sessionmaker_test, "asignacion_rol", "usuario_id = 9999") == 0
    assert await contar(sessionmaker_test, "evento_seguridad") == eventos_antes


async def test_reasignar_un_rol_vencido_lo_cierra_con_su_vence_en_y_abre_una_nueva_con_un_evento(sessionmaker_test):
    admin = await _admin(sessionmaker_test)
    uid = await insertar_usuario(sessionmaker_test, "v@example.com")
    vence = _en(hours=-3)
    vencida = await _insertar_asignacion(sessionmaker_test, uid, "VENDEDOR", vence_en=vence)

    respuesta = await _asignar(sessionmaker_test, admin, uid, "VENDEDOR")

    vieja, nueva = await _asignaciones(sessionmaker_test, uid)
    assert vieja["id"] == vencida
    assert vieja["revocada_en"] == vieja["vence_en"] == vence  # se cerró con su propio vencimiento, no now()
    assert (nueva["id"], nueva["revocada_en"], nueva["vence_en"]) == (respuesta.id, None, None)
    assert await _eventos(sessionmaker_test) == [
        {"actor": ADMIN_EMAIL, "accion": f"Asignación del rol VENDEDOR al usuario {uid}"}
    ]


async def test_si_falla_el_insert_nuevo_la_vencida_sigue_abierta(sessionmaker_test, monkeypatch):
    from app.modules.usuarios.repository import AsignacionRolRepository

    admin = await _admin(sessionmaker_test)
    uid = await insertar_usuario(sessionmaker_test, "v@example.com")
    await _insertar_asignacion(sessionmaker_test, uid, "VENDEDOR", vence_en=_en(hours=-3))

    async def falla(self, asignacion):
        raise RuntimeError("falla el insert")

    monkeypatch.setattr(AsignacionRolRepository, "asignar", falla)

    with pytest.raises(RuntimeError):
        await _asignar(sessionmaker_test, admin, uid, "VENDEDOR")

    [fila] = await _asignaciones(sessionmaker_test, uid)
    assert fila["revocada_en"] is None
    assert await contar(sessionmaker_test, "evento_seguridad") == 0


# ---- 5.3 ADMIN no lleva vencimiento (design D3b) ----

async def test_asignar_admin_con_vencimiento_es_admin_con_vencimiento_sin_abrir_el_uow(sessionmaker_test, monkeypatch):
    from app.core.errors import AdminConVencimiento
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    admin = await _admin(sessionmaker_test)
    uid = await insertar_usuario(sessionmaker_test, "v@example.com")
    aperturas: list[int] = []
    real_aenter = UsuariosUoW.__aenter__

    async def aenter_espia(self):
        aperturas.append(1)
        return await real_aenter(self)

    monkeypatch.setattr(UsuariosUoW, "__aenter__", aenter_espia)
    eventos_antes = await contar(sessionmaker_test, "evento_seguridad")

    with pytest.raises(AdminConVencimiento) as excinfo:
        await _asignar(sessionmaker_test, admin, uid, "ADMIN", _en(days=1))

    assert excinfo.value.mensaje == "El rol ADMIN no puede tener vencimiento."
    assert aperturas == []  # se rechaza antes de abrir el UoW
    assert await contar(sessionmaker_test, "asignacion_rol", "usuario_id = :u", u=uid) == 0
    assert await contar(sessionmaker_test, "evento_seguridad") == eventos_antes


async def test_asignar_vendedor_con_el_mismo_vencimiento_si_se_asigna(sessionmaker_test):
    admin = await _admin(sessionmaker_test)
    uid = await insertar_usuario(sessionmaker_test, "v@example.com")
    vence = _en(days=1)

    respuesta = await _asignar(sessionmaker_test, admin, uid, "VENDEDOR", vence)

    assert respuesta.vence_en == vence


async def test_asignar_admin_sin_vencimiento_si_se_asigna(sessionmaker_test):
    admin = await _admin(sessionmaker_test)
    uid = await insertar_usuario(sessionmaker_test, "v@example.com")

    respuesta = await _asignar(sessionmaker_test, admin, uid, "ADMIN")

    assert (respuesta.rol, respuesta.vence_en) == ("ADMIN", None)


# ---- 5.5 Revocar ----

async def test_revocar_escribe_revocada_en_conserva_la_fila_y_deja_su_evento(sessionmaker_test):
    admin = await _admin(sessionmaker_test)
    uid = await insertar_usuario(sessionmaker_test, "v@example.com", roles=("VENDEDOR",))

    respuesta = await _revocar(sessionmaker_test, admin, uid, "VENDEDOR")

    assert (respuesta.usuario_id, respuesta.rol) == (uid, "VENDEDOR")
    assert respuesta.revocada_en is not None
    [fila] = await _asignaciones(sessionmaker_test, uid)  # la fila se conserva
    assert fila["revocada_en"] is not None
    assert await _eventos(sessionmaker_test) == [
        {"actor": ADMIN_EMAIL, "accion": f"Revocación del rol VENDEDOR al usuario {uid}"}
    ]


async def test_revocar_dos_veces_la_segunda_es_rol_no_vigente(sessionmaker_test):
    from app.core.errors import RolNoVigente

    admin = await _admin(sessionmaker_test)
    uid = await insertar_usuario(sessionmaker_test, "v@example.com", roles=("VENDEDOR",))
    await _revocar(sessionmaker_test, admin, uid, "VENDEDOR")

    with pytest.raises(RolNoVigente) as excinfo:
        await _revocar(sessionmaker_test, admin, uid, "VENDEDOR")

    assert excinfo.value.mensaje == "El usuario no tiene ese rol vigente."
    assert await contar(sessionmaker_test, "evento_seguridad") == 1  # el rechazo no deja evento


async def test_revocar_un_rol_vencido_es_rol_no_vigente_y_no_escribe(sessionmaker_test):
    from app.core.errors import RolNoVigente

    admin = await _admin(sessionmaker_test)
    uid = await insertar_usuario(sessionmaker_test, "v@example.com")
    await _insertar_asignacion(sessionmaker_test, uid, "VENDEDOR", vence_en=_en(hours=-1))

    with pytest.raises(RolNoVigente):
        await _revocar(sessionmaker_test, admin, uid, "VENDEDOR")

    [fila] = await _asignaciones(sessionmaker_test, uid)
    assert fila["revocada_en"] is None


async def test_revocar_a_un_usuario_inexistente_es_usuario_no_encontrado(sessionmaker_test):
    from app.core.errors import UsuarioNoEncontrado

    admin = await _admin(sessionmaker_test)

    with pytest.raises(UsuarioNoEncontrado) as excinfo:
        await _revocar(sessionmaker_test, admin, 9999, "VENDEDOR")

    assert excinfo.value.mensaje == "El usuario no existe."


async def test_un_admin_no_puede_revocarse_su_propio_admin_y_se_rechaza_antes_de_abrir_el_uow(
    sessionmaker_test, monkeypatch
):
    from app.core.errors import AutoRevocacionAdmin, SinPermiso
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    admin = await _admin(sessionmaker_test)
    otro = await insertar_usuario(sessionmaker_test, "otro-admin@example.com", roles=("ADMIN",))  # hay otro: no es RN-05 "cero"
    aperturas: list[int] = []
    real_aenter = UsuariosUoW.__aenter__

    async def aenter_espia(self):
        aperturas.append(1)
        return await real_aenter(self)

    monkeypatch.setattr(UsuariosUoW, "__aenter__", aenter_espia)

    with pytest.raises(AutoRevocacionAdmin) as excinfo:
        await _revocar(sessionmaker_test, admin, admin.id, "ADMIN")

    assert not isinstance(excinfo.value, SinPermiso)
    assert aperturas == []
    [fila] = await _asignaciones(sessionmaker_test, admin.id)
    assert fila["revocada_en"] is None
    assert otro  # el otro ADMIN tampoco se tocó
    assert await contar(sessionmaker_test, "evento_seguridad") == 0


async def test_un_admin_si_puede_revocarse_otro_rol_propio(sessionmaker_test):
    admin = await _admin(sessionmaker_test)
    await _insertar_asignacion(sessionmaker_test, admin.id, "VENDEDOR")

    respuesta = await _revocar(sessionmaker_test, admin, admin.id, "VENDEDOR")

    assert respuesta.revocada_en is not None


async def test_un_actor_que_no_es_admin_vigente_no_puede_revocar_un_admin_y_no_escribe_nada(sessionmaker_test):
    from app.core.errors import SinPermiso

    unico = await insertar_usuario(sessionmaker_test, "unico@example.com", roles=("ADMIN",))
    actor = _actor(await insertar_usuario(sessionmaker_test, "sin-rol@example.com"), "sin-rol@example.com")

    with pytest.raises(SinPermiso) as excinfo:
        await _revocar(sessionmaker_test, actor, unico, "ADMIN")

    assert excinfo.value.mensaje == "No tenés permiso para esta operación."
    [fila] = await _asignaciones(sessionmaker_test, unico)
    assert fila["revocada_en"] is None
    assert await contar(sessionmaker_test, "evento_seguridad") == 0


async def test_el_conteo_final_sigue_protegiendo_si_el_bloqueo_dice_que_el_actor_es_admin(
    sessionmaker_test, monkeypatch
):
    """Defensa en profundidad: con el actor ya comprobado el conteo no puede dar 0, pero la regla RN-05 sigue en pie.

    Se simula que el bloqueo devuelve al actor entre los ADMIN (aunque no lo sea) para ejercitar el conteo.
    """
    from app.core.errors import SinAdministradores
    from app.modules.usuarios.repository import AsignacionRolRepository

    unico = await insertar_usuario(sessionmaker_test, "unico@example.com", roles=("ADMIN",))
    actor = _actor(await insertar_usuario(sessionmaker_test, "sin-rol@example.com"), "sin-rol@example.com")

    async def bloquea_y_dice_que_el_actor_esta(self):
        return [actor.id, unico]

    monkeypatch.setattr(AsignacionRolRepository, "bloquear_admins_vigentes", bloquea_y_dice_que_el_actor_esta)

    with pytest.raises(SinAdministradores) as excinfo:
        await _revocar(sessionmaker_test, actor, unico, "ADMIN")

    assert excinfo.value.mensaje == "No se puede revocar: el sistema quedaría sin administradores vigentes."
    [fila] = await _asignaciones(sessionmaker_test, unico)
    assert fila["revocada_en"] is None  # el UoW revirtió el UPDATE
    assert await contar(sessionmaker_test, "evento_seguridad") == 0


async def test_con_dos_admin_uno_puede_revocar_al_otro_y_queda_uno(sessionmaker_test):
    admin = await _admin(sessionmaker_test)
    otro = await insertar_usuario(sessionmaker_test, "otro-admin@example.com", roles=("ADMIN",))

    respuesta = await _revocar(sessionmaker_test, admin, otro, "ADMIN")

    assert respuesta.revocada_en is not None
    assert await contar(sessionmaker_test, "asignacion_rol", "rol = 'ADMIN' AND revocada_en IS NULL") == 1
    assert await _eventos(sessionmaker_test) == [
        {"actor": ADMIN_EMAIL, "accion": f"Revocación del rol ADMIN al usuario {otro}"}
    ]


async def test_si_falla_el_evento_la_asignacion_sigue_vigente(sessionmaker_test, monkeypatch):
    from app.modules.usuarios.repository import EventoSeguridadRepository

    admin = await _admin(sessionmaker_test)
    uid = await insertar_usuario(sessionmaker_test, "v@example.com", roles=("VENDEDOR",))

    async def falla(self, evento):
        raise RuntimeError("falla el evento")

    monkeypatch.setattr(EventoSeguridadRepository, "add", falla)

    with pytest.raises(RuntimeError):
        await _revocar(sessionmaker_test, admin, uid, "VENDEDOR")

    [fila] = await _asignaciones(sessionmaker_test, uid)
    assert fila["revocada_en"] is None


# ---- 5.7 Concurrencia determinista (design D5, D12): dos sesiones reales ----
#
# Ninguna usa `sleep` para «dar tiempo» a una carrera: la sesión 1 toma el bloqueo y NO
# confirma; la operación de la sesión 2 se lanza en una tarea sobre una sesión cuyo backend
# (`pg_backend_pid()`) ya conocemos, y se espera a que `pg_stat_activity` la muestre en
# `wait_event_type = 'Lock'`: recién ahí se sabe que está esperando el bloqueo de la 1. Si la
# tarea termina sin haber esperado nunca, la espera falla enseguida (no hay carrera que probar).

TOPE_ESPERA = 5.0  # segundos: tope de seguridad, no un tiempo que se espere siempre


async def _pid_del_backend(session) -> int:
    """El pid del backend de PostgreSQL que atiende a `session` (abre su transacción: la confirma el UoW)."""
    return (await session.execute(text("SELECT pg_backend_pid()"))).scalar_one()


async def _esperando_un_bloqueo(sessionmaker, pid: int, tarea: "asyncio.Task") -> bool:
    """`True` cuando el backend `pid` figura esperando un bloqueo; `False` si la tarea termina antes o vence el tope."""
    consulta = text("SELECT 1 FROM pg_stat_activity WHERE pid = :pid AND wait_event_type = 'Lock'")
    reloj = asyncio.get_running_loop().time
    limite = reloj() + TOPE_ESPERA
    while not tarea.done() and reloj() < limite:
        async with sessionmaker() as s:
            if (await s.execute(consulta, {"pid": pid})).first() is not None:
                return True
        await asyncio.sleep(0.02)
    return False


async def _carrera(sessionmaker, tomar_bloqueo, operacion):
    """Sesión 1 toma un bloqueo sin confirmar; `operacion(sesion_2)` debe quedar ESPERÁNDOLO; luego se confirma la 1.

    `tomar_bloqueo(uow1)` corre dentro de un `UsuariosUoW` abierto sobre la sesión 1. `operacion(s2)` corre en
    una tarea sobre la sesión 2, cuyo backend se conoce de antemano. Falla si la operación termina sin haber
    esperado nunca (no hubo carrera que probar). Al salir del bloque de la sesión 1 se confirma y la tarea
    puede seguir. Devuelve `(resultado, excepcion)` de la operación; uno de los dos es `None`.
    """
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    tarea = None
    async with sessionmaker() as s2:
        pid2 = await _pid_del_backend(s2)
        try:
            async with sessionmaker() as s1, UsuariosUoW(s1) as uow1:
                await tomar_bloqueo(uow1)
                tarea = asyncio.create_task(operacion(s2))
                assert await _esperando_un_bloqueo(sessionmaker, pid2, tarea), (
                    "la operación de la sesión 2 no esperó el bloqueo de la sesión 1"
                )
            terminadas, _ = await asyncio.wait({tarea}, timeout=TOPE_ESPERA)
            assert terminadas, "la operación de la sesión 2 no terminó tras confirmar la sesión 1"
            error = tarea.exception()
            return (None if error else tarea.result()), error
        finally:
            if tarea is not None and not tarea.done():
                tarea.cancel()
                await asyncio.gather(tarea, return_exceptions=True)


async def _admin_vigentes(sessionmaker) -> list[int]:
    resultado = await filas(
        sessionmaker,
        "SELECT usuario_id FROM asignacion_rol WHERE rol = 'ADMIN' AND revocada_en IS NULL ORDER BY usuario_id",
    )
    return [f["usuario_id"] for f in resultado]


async def test_dos_admin_que_se_revocan_a_la_vez_dejan_exactamente_uno(sessionmaker_test):
    from app.core.errors import SinPermiso

    actor_a = await _admin(sessionmaker_test, "a@example.com")
    actor_b = await _admin(sessionmaker_test, "b@example.com")

    async def a_revoca_a_b(uow1):  # Sesión 1: A revoca a B, sin confirmar (toma el bloqueo de las filas ADMIN).
        await uow1.asignaciones.bloquear_admins_vigentes()
        assert await uow1.asignaciones.revocar_vigente(actor_b.id, "ADMIN") is not None

    # Sesión 2: B revoca a A. Debe esperar; al confirmar A, B ya no es ADMIN.
    _, error = await _carrera(
        sessionmaker_test, a_revoca_a_b, lambda s2: _revocar_con(s2, actor_b, actor_a.id, "ADMIN")
    )

    # B ya no es ADMIN cuando por fin obtiene el bloqueo: 403, no un 409 por «quedar en cero».
    assert isinstance(error, SinPermiso)
    assert error.mensaje == "No tenés permiso para esta operación."
    assert await _admin_vigentes(sessionmaker_test) == [actor_a.id]  # queda A: la 2.ª se revirtió
    assert await _eventos(sessionmaker_test) == []  # la 2.ª no dejó evento


async def test_un_admin_revocado_mientras_espera_el_bloqueo_no_puede_revocar_a_otro(sessionmaker_test):
    """Carrera de autorización (hallazgo del advisor): con tres ADMIN, A revoca a B mientras B revoca a C.

    B pasó `SOLO_ADMIN` antes de que A confirmara, espera el bloqueo y, cuando A confirma, ya no es
    ADMIN. Sin la comprobación del actor dentro del bloque, B revocaría a C igual (queda A: el conteo da
    1) y quien ya no es administrador habría administrado.
    """
    from app.core.errors import SinPermiso

    actor_a = await _admin(sessionmaker_test, "a@example.com")
    actor_b = await _admin(sessionmaker_test, "b@example.com")
    actor_c = await _admin(sessionmaker_test, "c@example.com")

    async def a_revoca_a_b(uow1):
        await uow1.asignaciones.bloquear_admins_vigentes()
        assert await uow1.asignaciones.revocar_vigente(actor_b.id, "ADMIN") is not None

    _, error = await _carrera(
        sessionmaker_test, a_revoca_a_b, lambda s2: _revocar_con(s2, actor_b, actor_c.id, "ADMIN")
    )

    assert isinstance(error, SinPermiso)
    assert await _admin_vigentes(sessionmaker_test) == [actor_a.id, actor_c.id]  # C sigue ADMIN vigente
    assert await _eventos(sessionmaker_test) == []  # B no dejó evento: no escribió nada


async def test_dos_asignaciones_iguales_a_la_vez_la_segunda_espera_el_indice_y_es_conflicto(sessionmaker_test):
    from app.core.errors import Conflicto
    from app.modules.usuarios.models import AsignacionRol

    admin = await _admin(sessionmaker_test)
    uid = await insertar_usuario(sessionmaker_test, "v@example.com")

    async def inserta_el_vendedor(uow1):  # Sesión 1: inserta y no confirma (la entrada del índice único queda tomada).
        await uow1.asignaciones.asignar(AsignacionRol(usuario_id=uid, rol="VENDEDOR"))

    _, error = await _carrera(
        sessionmaker_test, inserta_el_vendedor, lambda s2: _asignar_con(s2, admin, uid, "VENDEDOR")
    )

    assert isinstance(error, Conflicto)
    assert error.mensaje == "El usuario ya tiene ese rol vigente."
    abiertas = await filas(
        sessionmaker_test, "SELECT id FROM asignacion_rol WHERE usuario_id = :u AND revocada_en IS NULL", u=uid
    )
    assert len(abiertas) == 1
    assert await contar(sessionmaker_test, "evento_seguridad") == 0  # la perdedora no dejó evento


# ---- 6. Historial de seguridad ----

async def _listar_eventos(sessionmaker, page=1, size=20):
    from app.core.paginacion import ParametrosPagina
    from app.modules.usuarios import service
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    async with sessionmaker() as s:
        return await service.listar_eventos(UsuariosUoW(s), ParametrosPagina(page=page, size=size))


async def _insertar_eventos(sessionmaker, n):
    from app.modules.usuarios.models import EventoSeguridad

    base = datetime(2026, 1, 1, tzinfo=UTC)
    async with sessionmaker() as s:
        s.add_all([
            EventoSeguridad(cuando=base + timedelta(days=i), actor="SISTEMA", accion=f"evento {i}") for i in range(n)
        ])
        await s.commit()


async def test_listar_eventos_devuelve_el_envoltorio_del_mas_reciente_al_mas_viejo(sessionmaker_test):
    from app.modules.usuarios.schemas import EventoSeguridadRead

    await _insertar_eventos(sessionmaker_test, 3)

    pagina = await _listar_eventos(sessionmaker_test, page=1, size=2)

    assert (pagina.total, pagina.page, pagina.size, pagina.pages) == (3, 1, 2, 2)
    assert all(isinstance(e, EventoSeguridadRead) for e in pagina.items)
    assert [e.accion for e in pagina.items] == ["evento 2", "evento 1"]
    segunda = await _listar_eventos(sessionmaker_test, page=2, size=2)
    assert [e.accion for e in segunda.items] == ["evento 0"]


async def test_listar_eventos_sin_lineas_es_una_pagina_vacia(sessionmaker_test):
    pagina = await _listar_eventos(sessionmaker_test)

    assert (pagina.items, pagina.total, pagina.pages) == ([], 0, 1)


async def test_listar_eventos_fuera_de_rango_es_peticion_invalida(sessionmaker_test):
    from app.core.errors import PeticionInvalida

    await _insertar_eventos(sessionmaker_test, 1)

    with pytest.raises(PeticionInvalida) as excinfo:
        await _listar_eventos(sessionmaker_test, page=2)

    assert excinfo.value.mensaje == "La página 2 no existe: hay 1"


async def test_ningun_evento_contiene_la_contrasena_provisoria_ni_un_hash(sessionmaker_test):
    admin = await _admin(sessionmaker_test)
    await _alta(sessionmaker_test, admin, _datos_alta(password="provisoria-1"))

    pagina = await _listar_eventos(sessionmaker_test)

    texto = " ".join(f"{e.actor} {e.accion}" for e in pagina.items)
    assert pagina.total == 1
    assert "provisoria-1" not in texto and "$2" not in texto


# ---- 7. Rutas HTTP (sesión de ADMIN por cookie) ----

async def _entrar_admin(client, sessionmaker, email=ADMIN_EMAIL):
    from tests.auxiliares_auth import entrar_como

    return await entrar_como(client, sessionmaker, "ADMIN", email=email)


def _alta_json(**extra):
    return {"email": "caja@example.com", "nombre": "Caja", "password": "provisoria-1", **extra}


async def test_post_usuarios_responde_201_sin_password_ni_hash(client, sessionmaker_test):
    await _entrar_admin(client, sessionmaker_test)

    r = await client.post("/usuarios/", json=_alta_json())

    assert r.status_code == 201
    cuerpo = r.json()
    assert set(cuerpo) == {"id", "email", "nombre", "activo", "debe_cambiar_password"}
    assert (cuerpo["activo"], cuerpo["debe_cambiar_password"]) == (True, True)
    assert "provisoria-1" not in r.text and "$2" not in r.text


async def test_post_usuarios_con_correo_repetido_es_409_con_mensaje_propio_sin_filas(client, sessionmaker_test):
    await _entrar_admin(client, sessionmaker_test)
    await insertar_usuario(sessionmaker_test, "caja@example.com")
    usuarios, eventos = await contar(sessionmaker_test, "usuario"), await contar(sessionmaker_test, "evento_seguridad")

    r = await client.post("/usuarios/", json=_alta_json())

    assert r.status_code == 409
    assert r.json() == {"detail": "Ya existe un usuario con ese correo."}
    assert await contar(sessionmaker_test, "usuario") == usuarios
    assert await contar(sessionmaker_test, "evento_seguridad") == eventos


@pytest.mark.parametrize(
    "cuerpo",
    [
        _alta_json(debe_cambiar_password=False),
        _alta_json(rol="ADMIN"),
        _alta_json(activo=False),
        _alta_json(email="no-es-un-correo"),
        _alta_json(nombre="   "),
    ],
    ids=["debe_cambiar_password", "rol", "activo", "correo_invalido", "nombre_vacio"],
)
async def test_post_usuarios_con_un_cuerpo_invalido_es_422_sin_filas(client, sessionmaker_test, cuerpo):
    await _entrar_admin(client, sessionmaker_test)
    usuarios = await contar(sessionmaker_test, "usuario")

    r = await client.post("/usuarios/", json=cuerpo)

    assert r.status_code == 422
    assert await contar(sessionmaker_test, "usuario") == usuarios


async def test_post_usuarios_con_73_bytes_es_422_y_no_llama_al_hash(client, sessionmaker_test, monkeypatch):
    from app.modules.usuarios import service

    llamadas: list[str] = []
    real = service.hashear_password

    async def espia(password, **kwargs):
        llamadas.append(password)
        return await real(password, **kwargs)

    monkeypatch.setattr(service, "hashear_password", espia)
    await _entrar_admin(client, sessionmaker_test)
    usuarios = await contar(sessionmaker_test, "usuario")

    r = await client.post("/usuarios/", json=_alta_json(password="x" * 73))

    assert r.status_code == 422
    assert llamadas == []
    assert await contar(sessionmaker_test, "usuario") == usuarios


async def test_un_admin_con_el_cambio_de_contrasena_pendiente_recibe_403_en_el_alta(client, sessionmaker_test):
    from tests.auxiliares_auth import entrar_como

    await entrar_como(client, sessionmaker_test, "ADMIN", debe_cambiar=True)
    usuarios = await contar(sessionmaker_test, "usuario")

    r = await client.post("/usuarios/", json=_alta_json())

    assert r.status_code == 403
    assert await contar(sessionmaker_test, "usuario") == usuarios


async def test_get_roles_responde_200_con_el_historial_y_404_si_no_existe_el_usuario(client, sessionmaker_test):
    await _entrar_admin(client, sessionmaker_test)
    uid = await insertar_usuario(sessionmaker_test, "v@example.com", roles=("VENDEDOR",))

    r = await client.get(f"/usuarios/{uid}/roles")
    inexistente = await client.get("/usuarios/9999/roles")

    assert r.status_code == 200
    assert [(a["rol"], a["revocada_en"]) for a in r.json()] == [("VENDEDOR", None)]
    assert set(r.json()[0]) == {"id", "usuario_id", "rol", "desde", "vence_en", "revocada_en", "otorgada_por"}
    assert (inexistente.status_code, inexistente.json()) == (404, {"detail": "El usuario no existe."})


async def test_post_roles_responde_201_404_y_409(client, sessionmaker_test):
    admin_id = await _entrar_admin(client, sessionmaker_test)
    uid = await insertar_usuario(sessionmaker_test, "v@example.com")

    creada = await client.post(f"/usuarios/{uid}/roles", json={"rol": "VENDEDOR"})
    repetida = await client.post(f"/usuarios/{uid}/roles", json={"rol": "VENDEDOR"})
    inexistente = await client.post("/usuarios/9999/roles", json={"rol": "VENDEDOR"})

    assert creada.status_code == 201
    assert (creada.json()["rol"], creada.json()["otorgada_por"], creada.json()["vence_en"]) == ("VENDEDOR", admin_id, None)
    assert (repetida.status_code, repetida.json()) == (409, {"detail": "El usuario ya tiene ese rol vigente."})
    assert (inexistente.status_code, inexistente.json()) == (404, {"detail": "El usuario no existe."})


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"rol": "VENDEDOR", "vence_en": "2020-01-01T10:00:00+00:00"},  # pasado
        {"rol": "VENDEDOR", "vence_en": "2099-01-01T10:00:00"},  # sin zona
        {"rol": "GERENTE"},
        {"rol": "VENDEDOR", "extra": 1},
    ],
    ids=["pasado", "sin_zona", "rol_desconocido", "campo_extra"],
)
async def test_post_roles_con_un_cuerpo_invalido_es_422_sin_filas_ni_eventos(client, sessionmaker_test, cuerpo):
    await _entrar_admin(client, sessionmaker_test)
    uid = await insertar_usuario(sessionmaker_test, "v@example.com")
    asignaciones = await contar(sessionmaker_test, "asignacion_rol")
    eventos = await contar(sessionmaker_test, "evento_seguridad")

    r = await client.post(f"/usuarios/{uid}/roles", json=cuerpo)

    assert r.status_code == 422
    assert await contar(sessionmaker_test, "asignacion_rol") == asignaciones
    assert await contar(sessionmaker_test, "evento_seguridad") == eventos


async def test_post_roles_admin_con_vencimiento_es_422_con_el_mensaje_propio(client, sessionmaker_test):
    await _entrar_admin(client, sessionmaker_test)
    uid = await insertar_usuario(sessionmaker_test, "v@example.com")
    vence = _en(days=1).isoformat()
    eventos = await contar(sessionmaker_test, "evento_seguridad")

    admin_vence = await client.post(f"/usuarios/{uid}/roles", json={"rol": "ADMIN", "vence_en": vence})
    vendedor_vence = await client.post(f"/usuarios/{uid}/roles", json={"rol": "VENDEDOR", "vence_en": vence})

    assert (admin_vence.status_code, admin_vence.json()) == (422, {"detail": "El rol ADMIN no puede tener vencimiento."})
    assert vendedor_vence.status_code == 201
    assert await contar(sessionmaker_test, "asignacion_rol", "usuario_id = :u", u=uid) == 1
    assert await contar(sessionmaker_test, "evento_seguridad") == eventos + 1


async def test_delete_rol_responde_200_404_y_422(client, sessionmaker_test):
    await _entrar_admin(client, sessionmaker_test)
    uid = await insertar_usuario(sessionmaker_test, "v@example.com", roles=("VENDEDOR",))

    revocada = await client.delete(f"/usuarios/{uid}/roles/VENDEDOR")
    segunda = await client.delete(f"/usuarios/{uid}/roles/VENDEDOR")
    inexistente = await client.delete("/usuarios/9999/roles/VENDEDOR")
    desconocido = await client.delete(f"/usuarios/{uid}/roles/GERENTE")
    no_entero = await client.get("/usuarios/abc/roles")

    assert revocada.status_code == 200 and revocada.json()["revocada_en"] is not None
    assert (segunda.status_code, segunda.json()) == (404, {"detail": "El usuario no tiene ese rol vigente."})
    assert (inexistente.status_code, inexistente.json()) == (404, {"detail": "El usuario no existe."})
    assert desconocido.status_code == 422
    assert no_entero.status_code == 422


async def test_get_eventos_responde_el_envoltorio_y_422_fuera_de_rango(client, sessionmaker_test):
    await _entrar_admin(client, sessionmaker_test)
    await client.post("/usuarios/", json=_alta_json())

    r = await client.get("/eventos/")
    fuera = await client.get("/eventos/?page=99")

    assert r.status_code == 200
    cuerpo = r.json()
    assert set(cuerpo) == {"items", "total", "page", "size", "pages"}
    assert cuerpo["total"] == 1 and set(cuerpo["items"][0]) == {"id", "cuando", "actor", "accion"}
    assert (fuera.status_code, fuera.json()) == (422, {"detail": "La página 99 no existe: hay 1"})


# ---- 7.4 El personal nuevo: alta, login con la provisoria y todo lo protegido bloqueado ----

async def test_el_usuario_recien_dado_de_alta_no_puede_usar_lo_protegido_ni_antes_ni_despues_de_cambiar_la_contrasena(
    client, sessionmaker_test
):
    from app.core.dependencies import MENSAJE_CAMBIO_PENDIENTE, MENSAJE_SIN_PERMISO
    from tests.auxiliares_auth import login

    await _entrar_admin(client, sessionmaker_test)
    alta = await client.post("/usuarios/", json=_alta_json())
    nuevo = alta.json()["id"]
    roles_del_nuevo = await client.get(f"/usuarios/{nuevo}/roles")
    assert (alta.status_code, roles_del_nuevo.status_code, roles_del_nuevo.json()) == (201, 200, [])

    # El usuario nuevo inicia sesión con la provisoria: el cambio está pendiente (RN-06).
    client.cookies.clear()
    entrada = await login(client, "caja@example.com", "provisoria-1")
    assert (entrada.status_code, entrada.json()["debe_cambiar_password"]) == (200, True)
    pendiente = await client.post("/clientes/", json={"nombre": "X", "email": "x@example.com"})
    assert (pendiente.status_code, pendiente.json()) == (403, {"detail": MENSAJE_CAMBIO_PENDIENTE})

    # Cambia la contraseña: ya no hay cambio pendiente pero tampoco tiene ningún rol (D1).
    cambio = await client.post(
        "/auth/cambiar-password", json={"password_actual": "provisoria-1", "password_nueva": "definitiva-2"}
    )
    assert cambio.status_code == 200
    clientes_antes = await contar(sessionmaker_test, "cliente")
    eventos_antes = await contar(sessionmaker_test, "evento_seguridad")
    sin_rol = await client.post("/clientes/", json={"nombre": "X", "email": "x@example.com"})
    sin_eventos = await client.get("/eventos/")
    assert (sin_rol.status_code, sin_rol.json()) == (403, {"detail": MENSAJE_SIN_PERMISO})
    assert sin_eventos.status_code == 403
    assert await contar(sessionmaker_test, "cliente") == clientes_antes
    assert await contar(sessionmaker_test, "evento_seguridad") == eventos_antes
