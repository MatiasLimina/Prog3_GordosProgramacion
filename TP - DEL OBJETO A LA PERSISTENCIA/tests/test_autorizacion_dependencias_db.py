"""requiere_rol (RN-04) y el control del cambio obligatorio (RN-06), con base real (CHG-12).

Cada test arma una app mínima con rutas de prueba y la misma infraestructura que `client`
(`estado_de_app` + override de `get_session` a la base de test); así se prueba la dependencia
sola, sin depender de cómo se montan las rutas reales.
"""
from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import get_session
from app.core.dependencies import (
    PERSONAL,
    SOLO_ADMIN,
    UsuarioAdmin,
    UsuarioPersonal,
    control_cambio_obligatorio,
    requiere_rol,
)
from app.core.security import emitir_token
from app.main import registrar_handlers
from tests.auxiliares_auth import cabecera_cookie, filas, insertar_usuario
from tests.conftest import estado_de_app

pytestmark = pytest.mark.db

_SIN_PERMISO = {"detail": "No tenés permiso para esta operación."}
_CAMBIO_PENDIENTE = {"detail": "Tenés que cambiar la contraseña antes de continuar."}
_SIN_SESION = {"detail": "No hay una sesión válida."}


def token_de_prueba(usuario_id, roles=(), *, ahora=None):
    """Token firmado con la clave de la configuración (la misma que usa la app mínima)."""
    settings = get_settings()
    return emitir_token(
        usuario_id, roles, secreto=settings.jwt_secret, minutos=settings.jwt_expire_minutes, ahora=ahora
    )


@asynccontextmanager
async def _cliente(sessionmaker, montar, get_session_test=None):
    """Cliente HTTP sobre una app mínima; `montar(app)` agrega las rutas de prueba."""
    app = FastAPI()
    registrar_handlers(app)
    montar(app)

    async def get_session_base():
        async with sessionmaker() as session:
            yield session

    app.dependency_overrides[get_session] = get_session_test or get_session_base
    with estado_de_app(app, sessionmaker):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
            yield c


def _montar_rutas_de_rol(app: FastAPI) -> None:
    @app.get("/solo-admin")
    async def solo_admin(usuario: UsuarioAdmin):
        return {"id": usuario.id}

    @app.get("/personal")
    async def personal(usuario: UsuarioPersonal):
        return {"id": usuario.id}


async def _pedir(sessionmaker, ruta, uid=None, roles_token=(), *, token=None):
    cabeceras = {}
    if token is not None or uid is not None:
        cabeceras = cabecera_cookie(token or token_de_prueba(uid, roles_token))
    async with _cliente(sessionmaker, _montar_rutas_de_rol) as c:
        return await c.get(ruta, headers=cabeceras)


# ---- requiere_rol: lo básico (3.1) ----

async def test_admin_entra_a_la_ruta_de_admin_y_recibe_su_usuario(sessionmaker_test):
    uid = await insertar_usuario(sessionmaker_test, roles=["ADMIN"])

    r = await _pedir(sessionmaker_test, "/solo-admin", uid, ["ADMIN"])

    assert r.status_code == 200
    assert r.json() == {"id": uid}


async def test_vendedor_en_ruta_de_admin_da_403_con_el_mensaje_exacto(sessionmaker_test):
    uid = await insertar_usuario(sessionmaker_test, roles=["VENDEDOR"])

    r = await _pedir(sessionmaker_test, "/solo-admin", uid, ["VENDEDOR"])

    assert r.status_code == 403
    assert r.json() == _SIN_PERMISO


@pytest.mark.parametrize("rol", ["VENDEDOR", "ADMIN"])
async def test_el_personal_entra_a_la_ruta_del_personal(sessionmaker_test, rol):
    uid = await insertar_usuario(sessionmaker_test, roles=[rol])

    r = await _pedir(sessionmaker_test, "/personal", uid, [rol])

    assert r.status_code == 200
    assert r.json() == {"id": uid}


@pytest.mark.parametrize("ruta", ["/solo-admin", "/personal"])
async def test_un_usuario_sin_roles_da_403(sessionmaker_test, ruta):
    uid = await insertar_usuario(sessionmaker_test)

    r = await _pedir(sessionmaker_test, ruta, uid)

    assert r.status_code == 403
    assert r.json() == _SIN_PERMISO


async def test_un_cliente_en_la_ruta_del_personal_da_403(sessionmaker_test):
    uid = await insertar_usuario(sessionmaker_test, roles=["CLIENTE"])

    r = await _pedir(sessionmaker_test, "/personal", uid, ["CLIENTE"])

    assert r.status_code == 403
    assert r.json() == _SIN_PERMISO


@pytest.mark.parametrize("ruta", ["/solo-admin", "/personal"])
async def test_sin_cookie_da_401_antes_que_el_rol(sessionmaker_test, ruta):
    async with _cliente(sessionmaker_test, _montar_rutas_de_rol) as c:
        r = await c.get(ruta)

    assert r.status_code == 401
    assert r.json() == _SIN_SESION


async def test_un_admin_inactivo_da_401(sessionmaker_test):
    uid = await insertar_usuario(sessionmaker_test, roles=["ADMIN"], activo=False)

    r = await _pedir(sessionmaker_test, "/solo-admin", uid, ["ADMIN"])

    assert r.status_code == 401
    assert r.json() == _SIN_SESION


# ---- requiere_rol: bordes de RN-04 (3.3) ----

async def test_un_rol_revocado_despues_de_emitir_el_token_da_403_y_la_fila_se_conserva(sessionmaker_test):
    uid = await insertar_usuario(sessionmaker_test, roles=["ADMIN"])
    token = token_de_prueba(uid, ["ADMIN"])
    async with _cliente(sessionmaker_test, _montar_rutas_de_rol) as c:
        antes = await c.get("/solo-admin", headers=cabecera_cookie(token))
        async with sessionmaker_test() as s:
            await s.execute(text("UPDATE asignacion_rol SET revocada_en = now() WHERE usuario_id = :u"), {"u": uid})
            await s.commit()
        despues = await c.get("/solo-admin", headers=cabecera_cookie(token))

    assert antes.status_code == 200
    assert despues.status_code == 403
    assert despues.json() == _SIN_PERMISO
    assert len(await filas(sessionmaker_test, "SELECT 1 FROM asignacion_rol WHERE usuario_id = :u", u=uid)) == 1


async def test_un_rol_vencido_despues_de_emitir_el_token_da_403(sessionmaker_test):
    uid = await insertar_usuario(sessionmaker_test, roles=["ADMIN"])
    token = token_de_prueba(uid, ["ADMIN"])
    async with _cliente(sessionmaker_test, _montar_rutas_de_rol) as c:
        async with sessionmaker_test() as s:
            await s.execute(
                text("UPDATE asignacion_rol SET vence_en = now() - interval '1 minute' WHERE usuario_id = :u"),
                {"u": uid},
            )
            await s.commit()
        r = await c.get("/solo-admin", headers=cabecera_cookie(token))

    assert r.status_code == 403
    assert r.json() == _SIN_PERMISO


async def test_un_rol_con_vencimiento_futuro_sigue_vigente(sessionmaker_test):
    uid = await insertar_usuario(sessionmaker_test, roles=["ADMIN"])
    async with sessionmaker_test() as s:
        await s.execute(
            text("UPDATE asignacion_rol SET vence_en = now() + interval '1 day' WHERE usuario_id = :u"), {"u": uid}
        )
        await s.commit()

    r = await _pedir(sessionmaker_test, "/solo-admin", uid, ["ADMIN"])

    assert r.status_code == 200


async def test_un_token_que_dice_admin_no_alcanza_si_la_base_no_lo_tiene(sessionmaker_test):
    uid = await insertar_usuario(sessionmaker_test)

    r = await _pedir(sessionmaker_test, "/solo-admin", uid, ["ADMIN"])

    assert r.status_code == 403


async def test_un_rol_obtenido_despues_de_emitir_el_token_sirve_sin_iniciar_sesion_de_nuevo(sessionmaker_test):
    uid = await insertar_usuario(sessionmaker_test)
    token = token_de_prueba(uid, [])
    async with _cliente(sessionmaker_test, _montar_rutas_de_rol) as c:
        antes = await c.get("/solo-admin", headers=cabecera_cookie(token))
        async with sessionmaker_test() as s:
            await s.execute(
                text("INSERT INTO asignacion_rol (usuario_id, rol) VALUES (:u, 'ADMIN')"), {"u": uid}
            )
            await s.commit()
        despues = await c.get("/solo-admin", headers=cabecera_cookie(token))

    assert antes.status_code == 403
    assert despues.status_code == 200


@pytest.mark.parametrize("roles", [("ADMNI",), ("ADMIN", "root"), ()])
def test_requiere_rol_rechaza_al_construirse_un_rol_que_no_existe_o_ninguno(roles):
    with pytest.raises(ValueError):
        requiere_rol(*roles)


def test_las_constantes_de_rol_exigen_lo_que_dice_la_consigna():
    assert SOLO_ADMIN.roles == frozenset({"ADMIN"})
    assert PERSONAL.roles == frozenset({"VENDEDOR", "ADMIN"})


# ---- una sola conexión y una sola consulta de roles por petición (3.5) ----

async def test_una_ruta_con_usuario_y_rol_repetido_usa_una_sesion_y_consulta_los_roles_una_vez(
    sessionmaker_test, monkeypatch
):
    from app.core.dependencies import proveedor_uow
    from app.modules.usuarios.repository import AsignacionRolRepository
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    sesiones = []
    consultas = []
    real = AsignacionRolRepository.roles_vigentes

    async def roles_vigentes_espia(self, usuario_id):
        consultas.append(usuario_id)
        return await real(self, usuario_id)

    monkeypatch.setattr(AsignacionRolRepository, "roles_vigentes", roles_vigentes_espia)

    async def get_session_espia():
        async with sessionmaker_test() as session:
            sesiones.append(session)
            yield session

    recibidos = {}

    def montar(app: FastAPI) -> None:
        # El rol repetido (parámetro + dependencies) y el UoW de módulo: todo debe compartir sesión.
        @app.get("/mixta", dependencies=[Depends(PERSONAL)])
        async def mixta(usuario: UsuarioPersonal, uow: UsuariosUoW = Depends(proveedor_uow(UsuariosUoW))):
            recibidos["sesion_del_uow"] = uow.session
            return {"id": usuario.id}

    uid = await insertar_usuario(sessionmaker_test, roles=["VENDEDOR"])
    async with _cliente(sessionmaker_test, montar, get_session_espia) as c:
        r = await c.get("/mixta", headers=cabecera_cookie(token_de_prueba(uid, ["VENDEDOR"])))

    assert r.status_code == 200
    assert len(sesiones) == 1
    assert recibidos["sesion_del_uow"] is sesiones[0]
    assert consultas == [uid]


# ---- control del cambio obligatorio de contraseña, RN-06 (4.1) ----

def _montar_grupo_con_control(app: FastAPI) -> None:
    grupo = APIRouter(dependencies=[Depends(control_cambio_obligatorio)])

    @grupo.get("/sin-rol")
    async def sin_rol():
        return {"ok": True}

    @grupo.get("/con-rol", dependencies=[Depends(SOLO_ADMIN)])
    async def con_rol():
        return {"ok": True}

    app.include_router(grupo)


@pytest.mark.parametrize("ruta", ["/sin-rol", "/con-rol"])
async def test_con_el_cambio_pendiente_el_control_responde_403_aunque_tenga_el_rol(sessionmaker_test, ruta):
    uid = await insertar_usuario(sessionmaker_test, roles=["ADMIN"], debe_cambiar=True)

    async with _cliente(sessionmaker_test, _montar_grupo_con_control) as c:
        r = await c.get(ruta, headers=cabecera_cookie(token_de_prueba(uid, ["ADMIN"])))

    assert r.status_code == 403
    assert r.json() == _CAMBIO_PENDIENTE


async def test_el_cambio_pendiente_gana_sobre_la_falta_de_rol(sessionmaker_test):
    uid = await insertar_usuario(sessionmaker_test, roles=["VENDEDOR"], debe_cambiar=True)

    async with _cliente(sessionmaker_test, _montar_grupo_con_control) as c:
        r = await c.get("/con-rol", headers=cabecera_cookie(token_de_prueba(uid, ["VENDEDOR"])))

    assert r.status_code == 403
    assert r.json() == _CAMBIO_PENDIENTE


async def test_sin_el_cambio_pendiente_el_control_deja_pasar(sessionmaker_test):
    uid = await insertar_usuario(sessionmaker_test)

    async with _cliente(sessionmaker_test, _montar_grupo_con_control) as c:
        r = await c.get("/sin-rol", headers=cabecera_cookie(token_de_prueba(uid)))

    assert r.status_code == 200


async def test_el_control_sin_cookie_da_401_y_no_403(sessionmaker_test):
    async with _cliente(sessionmaker_test, _montar_grupo_con_control) as c:
        r = await c.get("/sin-rol")

    assert r.status_code == 401
    assert r.json() == _SIN_SESION


async def test_al_apagar_el_flag_en_la_base_la_misma_cookie_pasa(sessionmaker_test):
    uid = await insertar_usuario(sessionmaker_test, debe_cambiar=True)
    cabeceras = cabecera_cookie(token_de_prueba(uid))
    async with _cliente(sessionmaker_test, _montar_grupo_con_control) as c:
        antes = await c.get("/sin-rol", headers=cabeceras)
        async with sessionmaker_test() as s:
            await s.execute(text("UPDATE usuario SET debe_cambiar_password = false WHERE id = :u"), {"u": uid})
            await s.commit()
        despues = await c.get("/sin-rol", headers=cabeceras)

    assert antes.status_code == 403
    assert despues.status_code == 200
