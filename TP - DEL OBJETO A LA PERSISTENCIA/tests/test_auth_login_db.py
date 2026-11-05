"""POST /auth/login (RN-07, RN-08, Ej7; C-03, C-04, C-05)."""
import pytest

from app.main import app as fastapi_app
from tests.auxiliares_auth import PASSWORD, login, registrar

pytestmark = pytest.mark.db


def _cookie_de_sesion(r):
    """La cabecera Set-Cookie del login, en minúsculas, para comparar atributos."""
    return r.headers["set-cookie"].lower()


async def test_login_correcto_responde_200_sin_token_en_el_cuerpo(client):
    await registrar(client)

    r = await login(client)

    minutos = fastapi_app.state.settings.jwt_expire_minutes
    assert r.status_code == 200
    assert r.json() == {
        "mensaje": "Sesión iniciada", "debe_cambiar_password": False, "expira_en_segundos": minutos * 60,
    }
    token = client.cookies["access_token"]
    assert token not in r.text


async def test_la_cookie_trae_los_atributos_de_seguridad(client):
    await registrar(client)

    r = await login(client)

    minutos = fastapi_app.state.settings.jwt_expire_minutes
    cabecera = _cookie_de_sesion(r)
    assert cabecera.startswith("access_token=")
    assert "httponly" in cabecera
    assert "samesite=lax" in cabecera
    assert "path=/" in cabecera
    assert f"max-age={minutos * 60}" in cabecera
    assert "secure" not in cabecera


async def test_con_cookie_secure_configurada_la_cookie_trae_secure(client):
    fastapi_app.state.settings = fastapi_app.state.settings.model_copy(update={"cookie_secure": True})
    await registrar(client)

    r = await login(client)

    assert "secure" in _cookie_de_sesion(r)


async def test_el_token_de_la_cookie_verifica_y_lleva_id_y_roles(client, sessionmaker_test):
    from app.core.security import verificar_token
    from tests.auxiliares_auth import filas

    uid = (await registrar(client)).json()["id"]
    await login(client)

    datos = verificar_token(client.cookies["access_token"], secreto=fastapi_app.state.settings.jwt_secret)
    assert datos.usuario_id == uid
    assert datos.roles == ["CLIENTE"]
    assert (await filas(sessionmaker_test, "SELECT count(*) AS n FROM usuario"))[0]["n"] == 1


# ---- RN-08 / C-04: credenciales incorrectas indistinguibles ----

_DETALLE_401 = {"detail": "Correo o contraseña incorrectos."}


async def test_contrasena_incorrecta_y_correo_inexistente_dan_el_mismo_401_sin_cookie(client, monkeypatch):
    from tests.auxiliares_auth import espiar_verificacion

    await registrar(client)
    llamadas = espiar_verificacion(monkeypatch)

    mala = await login(client, password="clave-equivocada")
    assert len(llamadas) == 1
    sin_correo = await login(client, email="fantasma@example.com")
    assert len(llamadas) == 2  # exactamente una verificación en cada caso

    assert mala.status_code == sin_correo.status_code == 401
    assert mala.json() == sin_correo.json() == _DETALLE_401
    assert "set-cookie" not in mala.headers and "set-cookie" not in sin_correo.headers
    assert llamadas[1][1] == fastapi_app.state.hash_ficticio  # correo inexistente: hash ficticio
    assert llamadas[0][1] != fastapi_app.state.hash_ficticio  # correo real: su propio hash


async def test_usuario_inactivo_con_la_contrasena_correcta_da_el_mismo_401(client, sessionmaker_test):
    from tests.auxiliares_auth import insertar_usuario

    await insertar_usuario(sessionmaker_test, "baja@example.com", activo=False)

    r = await login(client, email="baja@example.com")

    assert r.status_code == 401
    assert r.json() == _DETALLE_401
    assert "set-cookie" not in r.headers


async def test_password_hash_corrupto_es_un_fallo_401_y_deja_aviso_sin_el_hash(client, sessionmaker_test, caplog):
    from sqlalchemy import text

    uid = (await registrar(client)).json()["id"]
    async with sessionmaker_test() as s:
        await s.execute(text("UPDATE usuario SET password_hash = 'esto-no-es-bcrypt' WHERE id = :i"), {"i": uid})
        await s.commit()

    with caplog.at_level("WARNING"):
        r = await login(client)

    assert r.status_code == 401
    assert r.json() == _DETALLE_401
    assert str(uid) in caplog.text
    assert "esto-no-es-bcrypt" not in caplog.text


# ---- contenido del token y flags ----

async def test_el_token_lleva_solo_los_roles_vigentes(client, sessionmaker_test):
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import text

    from app.core.security import verificar_token
    from tests.auxiliares_auth import insertar_usuario

    uid = await insertar_usuario(sessionmaker_test, roles=["VENDEDOR", "ADMIN", "CLIENTE"])
    async with sessionmaker_test() as s:
        await s.execute(
            text("UPDATE asignacion_rol SET revocada_en = now() WHERE usuario_id = :u AND rol = 'ADMIN'"), {"u": uid}
        )
        await s.execute(
            text("UPDATE asignacion_rol SET vence_en = :v WHERE usuario_id = :u AND rol = 'CLIENTE'"),
            {"u": uid, "v": datetime.now(UTC) - timedelta(hours=1)},
        )
        await s.commit()

    r = await login(client)

    assert r.status_code == 200
    datos = verificar_token(client.cookies["access_token"], secreto=fastapi_app.state.settings.jwt_secret)
    assert datos.roles == ["VENDEDOR"]


async def test_usuario_sin_asignaciones_inicia_sesion_con_roles_vacios(client, sessionmaker_test):
    from app.core.security import verificar_token
    from tests.auxiliares_auth import insertar_usuario

    await insertar_usuario(sessionmaker_test)

    r = await login(client)

    assert r.status_code == 200
    assert verificar_token(client.cookies["access_token"], secreto=fastapi_app.state.settings.jwt_secret).roles == []


async def test_usuario_con_cambio_pendiente_recibe_el_flag_verdadero_y_cookie(client, sessionmaker_test):
    from tests.auxiliares_auth import insertar_usuario

    await insertar_usuario(sessionmaker_test, "nuevo@example.com", debe_cambiar=True)

    r = await login(client, email="nuevo@example.com")

    assert r.status_code == 200
    assert r.json()["debe_cambiar_password"] is True
    assert "access_token=" in r.headers["set-cookie"]


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"email": "ana@example.com", "password": "ñ" * 37},  # 74 bytes
        {"email": "ana@example.com", "password": PASSWORD, "rol": "ADMIN"},
        {"email": "no-es-correo", "password": PASSWORD},
    ],
    ids=["password_74_bytes", "campo_de_mas", "correo_invalido"],
)
async def test_cuerpo_invalido_da_422_sin_verificar(client, monkeypatch, cuerpo):
    from tests.auxiliares_auth import espiar_verificacion

    llamadas = espiar_verificacion(monkeypatch)
    r = await client.post("/auth/login", json=cuerpo)
    assert r.status_code == 422
    assert llamadas == []


# ---- Ej7: intento_acceso con sesión y transacción propias ----

async def test_un_login_fallido_deja_una_fila_con_exito_falso(client, sessionmaker_test):
    from tests.auxiliares_auth import filas

    await registrar(client)

    r = await login(client, password="clave-equivocada")

    assert r.status_code == 401
    intentos = await filas(sessionmaker_test, "SELECT * FROM intento_acceso")
    assert len(intentos) == 1
    assert (intentos[0]["email"], intentos[0]["ip"], intentos[0]["exito"]) == ("ana@example.com", "127.0.0.1", False)


async def test_un_login_correcto_deja_una_fila_con_exito_verdadero(client, sessionmaker_test):
    from tests.auxiliares_auth import filas

    await registrar(client)

    assert (await login(client)).status_code == 200

    intentos = await filas(sessionmaker_test, "SELECT * FROM intento_acceso")
    assert [(i["email"], i["exito"]) for i in intentos] == [("ana@example.com", True)]


async def test_un_correo_inexistente_tambien_deja_su_fila(client, sessionmaker_test):
    from tests.auxiliares_auth import filas

    r = await login(client, email="fantasma@example.com")

    assert r.status_code == 401
    intentos = await filas(sessionmaker_test, "SELECT email, exito FROM intento_acceso")
    assert [(i["email"], i["exito"]) for i in intentos] == [("fantasma@example.com", False)]


async def test_un_422_no_deja_fila(client, sessionmaker_test):
    from tests.auxiliares_auth import contar

    r = await client.post("/auth/login", json={"email": "ana@example.com", "password": "ñ" * 37})

    assert r.status_code == 422
    assert await contar(sessionmaker_test, "intento_acceso") == 0


async def test_el_intento_se_confirma_con_una_sesion_distinta_antes_de_responder(client, monkeypatch):
    from app.core.database import get_session
    from app.modules.usuarios.unit_of_work import IntentosUoW

    sesiones_de_la_peticion = []
    get_session_test = fastapi_app.dependency_overrides[get_session]

    async def get_session_registrando():
        async for session in get_session_test():
            sesiones_de_la_peticion.append(session)
            yield session

    fastapi_app.dependency_overrides[get_session] = get_session_registrando

    cierres = []
    aexit_real = IntentosUoW.__aexit__

    async def aexit_espia(self, exc_type, exc, tb):
        cierres.append((self.session, exc_type))
        return await aexit_real(self, exc_type, exc, tb)

    monkeypatch.setattr(IntentosUoW, "__aexit__", aexit_espia)

    await registrar(client)
    r = await login(client, password="clave-equivocada")

    assert r.status_code == 401
    assert len(cierres) == 1  # ya se cerró (confirmó) cuando llegó la respuesta
    sesion_del_intento, exc_type = cierres[0]
    assert exc_type is None  # salió sin error: confirmó
    assert all(sesion_del_intento is not s for s in sesiones_de_la_peticion)


# ---- RN-07 / C-05: límite de intentos ----

_DETALLE_429 = {"detail": "Demasiados intentos fallidos. Probá de nuevo más tarde."}


async def _cinco_fallos(client):
    for _ in range(5):
        assert (await login(client, password="clave-equivocada")).status_code == 401


async def test_el_sexto_intento_da_429_sin_verificar_y_sin_anotarse(client, sessionmaker_test, monkeypatch):
    from tests.auxiliares_auth import contar, espiar_verificacion

    await registrar(client)
    await _cinco_fallos(client)
    llamadas = espiar_verificacion(monkeypatch)

    r = await login(client, password="clave-equivocada")

    assert r.status_code == 429
    assert r.json() == _DETALLE_429
    assert 1 <= int(r.headers["retry-after"]) <= 60
    assert llamadas == []  # ningún hash en un intento rechazado por el límite
    assert await contar(sessionmaker_test, "intento_acceso", "email = :e AND NOT exito", e="ana@example.com") == 5


async def test_con_la_contrasena_correcta_tras_cinco_fallos_tambien_da_429_sin_cookie(client):
    await registrar(client)
    await _cinco_fallos(client)

    r = await login(client)

    assert r.status_code == 429
    assert "set-cookie" not in r.headers


async def test_cuatro_fallos_no_bloquean_el_quinto_intento(client):
    await registrar(client)
    for _ in range(4):
        await login(client, password="clave-equivocada")

    assert (await login(client)).status_code == 200


@pytest.mark.parametrize(
    "email, ip, hace_segundos",
    [
        ("ana@example.com", "127.0.0.1", [61, 70, 80, 90, 100]),  # fuera de la ventana
        ("ana@example.com", "10.0.0.9", [5, 10, 15, 20, 25]),  # otra IP
    ],
    ids=["viejos", "otra_ip"],
)
async def test_fallos_viejos_o_de_otra_ip_no_bloquean(client, sessionmaker_test, email, ip, hace_segundos):
    from tests.test_usuarios_repository_db import _insertar_intentos

    await registrar(client)
    await _insertar_intentos(sessionmaker_test, email, ip, False, hace_segundos)

    assert (await login(client)).status_code == 200


async def test_un_exito_reinicia_la_cuenta(client, sessionmaker_test):
    from tests.auxiliares_auth import contar

    await registrar(client)
    for _ in range(4):
        await login(client, password="clave-equivocada")
    assert (await login(client)).status_code == 200
    for _ in range(4):
        assert (await login(client, password="clave-equivocada")).status_code == 401  # ningún 429

    assert await contar(sessionmaker_test, "intento_acceso") == 9
