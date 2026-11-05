"""get_usuario_actual (las cinco causas de 401), GET /auth/yo y POST /auth/logout."""
from datetime import UTC, datetime, timedelta

import pytest

from app.main import app as fastapi_app
from tests.auxiliares_auth import cabecera_cookie, insertar_usuario, login, registrar, token_de_prueba

pytestmark = pytest.mark.db

_DETALLE_401 = {"detail": "No hay una sesión válida."}


async def test_sin_cookie_da_401_con_el_mensaje_fijo(client):
    r = await client.get("/auth/yo")
    assert r.status_code == 401
    assert r.json() == _DETALLE_401


async def test_un_token_valido_en_authorization_y_sin_cookie_da_401(client, sessionmaker_test):
    uid = await insertar_usuario(sessionmaker_test)
    token = token_de_prueba(uid)

    r = await client.get("/auth/yo", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 401
    assert r.json() == _DETALLE_401


async def test_la_cookie_valida_si_funciona_como_control(client, sessionmaker_test):
    # Mismo token que el caso anterior, pero en la cookie: distingue «ignora Authorization» de «roto».
    uid = await insertar_usuario(sessionmaker_test)

    r = await client.get("/auth/yo", headers=cabecera_cookie(token_de_prueba(uid)))

    assert r.status_code == 200


@pytest.mark.parametrize("causa", ["vencido", "firma_alterada", "usuario_inexistente", "usuario_inactivo", "basura"])
async def test_las_cinco_causas_de_401_dan_el_mismo_cuerpo_sin_filtrar_nada(client, sessionmaker_test, causa):
    uid = await insertar_usuario(sessionmaker_test, "baja@example.com", activo=(causa != "usuario_inactivo"))
    if causa == "vencido":
        token = token_de_prueba(uid, ahora=datetime.now(UTC) - timedelta(hours=2))
    elif causa == "firma_alterada":
        token = token_de_prueba(uid)[:-4] + "AAAA"
    elif causa == "usuario_inexistente":
        token = token_de_prueba(999)
    elif causa == "basura":
        token = "esto.no.es-un-jwt"
    else:
        token = token_de_prueba(uid)

    r = await client.get("/auth/yo", headers=cabecera_cookie(token))

    assert r.status_code == 401
    assert r.json() == _DETALLE_401
    assert token not in r.text
    assert fastapi_app.state.settings.jwt_secret.get_secret_value() not in r.text


# ---- GET /auth/yo ----

async def test_yo_devuelve_usuario_y_roles_vigentes_y_del_token(client, sessionmaker_test):
    uid = await insertar_usuario(sessionmaker_test, "vende@example.com", roles=["VENDEDOR"])
    await login(client, "vende@example.com")

    r = await client.get("/auth/yo")

    assert r.status_code == 200
    assert r.json() == {
        "usuario": {
            "id": uid, "email": "vende@example.com", "nombre": "Ana", "activo": True, "debe_cambiar_password": False,
        },
        "roles_vigentes": ["VENDEDOR"],
        "roles_token": ["VENDEDOR"],
    }
    assert "password_hash" not in r.text


async def test_yo_lee_los_roles_vigentes_de_la_base_en_cada_peticion(client, sessionmaker_test):
    from sqlalchemy import text

    uid = await insertar_usuario(sessionmaker_test, "vende@example.com", roles=["VENDEDOR"])
    await login(client, "vende@example.com")
    async with sessionmaker_test() as s:
        await s.execute(text("UPDATE asignacion_rol SET revocada_en = now() WHERE usuario_id = :u"), {"u": uid})
        await s.commit()

    r = await client.get("/auth/yo")  # misma cookie

    assert r.status_code == 200
    assert r.json()["roles_vigentes"] == []
    assert r.json()["roles_token"] == ["VENDEDOR"]


async def test_yo_responde_200_aunque_el_cambio_de_contrasena_este_pendiente(client, sessionmaker_test):
    await insertar_usuario(sessionmaker_test, "nuevo@example.com", debe_cambiar=True, roles=["CLIENTE"])
    await login(client, "nuevo@example.com")

    r = await client.get("/auth/yo")

    assert r.status_code == 200
    assert r.json()["usuario"]["debe_cambiar_password"] is True
    assert r.json()["roles_vigentes"] == ["CLIENTE"]


async def test_yo_de_un_usuario_registrado_muestra_el_rol_cliente(client):
    await registrar(client)
    await login(client)

    r = await client.get("/auth/yo")

    assert r.json()["roles_vigentes"] == r.json()["roles_token"] == ["CLIENTE"]


# ---- POST /auth/logout ----

def _borra_la_cookie(r) -> bool:
    cabecera = r.headers["set-cookie"].lower()
    return cabecera.startswith("access_token=") and "max-age=0" in cabecera and "path=/" in cabecera


async def test_logout_borra_la_cookie_y_la_sesion_deja_de_servir(client):
    await registrar(client)
    await login(client)
    assert (await client.get("/auth/yo")).status_code == 200

    r = await client.post("/auth/logout")

    assert r.status_code == 200
    assert r.json() == {"mensaje": "Sesión cerrada"}
    assert _borra_la_cookie(r)
    assert (await client.get("/auth/yo")).status_code == 401


async def test_logout_sin_sesion_tambien_responde_200_con_la_cabecera(client):
    r = await client.post("/auth/logout")

    assert r.status_code == 200
    assert r.json() == {"mensaje": "Sesión cerrada"}
    assert _borra_la_cookie(r)


async def test_logout_con_cookie_secure_borra_con_los_mismos_atributos(client):
    fastapi_app.state.settings = fastapi_app.state.settings.model_copy(update={"cookie_secure": True})

    r = await client.post("/auth/logout")

    cabecera = r.headers["set-cookie"].lower()
    assert "secure" in cabecera and "httponly" in cabecera and "samesite=lax" in cabecera
