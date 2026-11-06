"""Autorización de TODAS las rutas de la app real, parametrizada desde la matriz (CHG-12, con base).

Los parámetros de ruta van con `1` y el cuerpo vacío: las dependencias (sesión, control del
cambio pendiente, rol) se resuelven antes que la validación, así que el 401/403 sale antes
que cualquier 422.
"""
import pytest

from tests.auxiliares_auth import cabecera_cookie, insertar_usuario, token_de_prueba
from tests.matriz_acceso import ABIERTO, CUALQUIERA, MATRIZ, PROTEGIDO, ruta_concreta

pytestmark = pytest.mark.db


def _ids(clave):
    return f"{clave[0]} {clave[1]}"


_PROTEGIDAS = sorted(c for c, (g, _) in MATRIZ.items() if g == PROTEGIDO)
_CON_ROL = sorted(c for c, (g, a) in MATRIZ.items() if g == PROTEGIDO and isinstance(a, frozenset))
_SOLO_ADMIN = sorted(c for c in _CON_ROL if MATRIZ[c][1] == frozenset({"ADMIN"}))
_ABIERTAS_SIN_SESION = sorted(c for c, (g, a) in MATRIZ.items() if g == ABIERTO and a == CUALQUIERA)


async def _pedir(client, clave, cabeceras=None):
    metodo, ruta = clave
    return await client.request(metodo, ruta_concreta(ruta), json={}, headers=cabeceras or {})


@pytest.mark.parametrize("clave", _PROTEGIDAS, ids=_ids)
async def test_cada_ruta_protegida_sin_cookie_da_401(client, clave):
    r = await _pedir(client, clave)

    assert r.status_code == 401
    assert r.json() == {"detail": "No hay una sesión válida."}


@pytest.mark.parametrize("clave", _SOLO_ADMIN, ids=_ids)
async def test_cada_ruta_de_admin_con_un_vendedor_da_403(client, sessionmaker_test, clave):
    uid = await insertar_usuario(sessionmaker_test, roles=["VENDEDOR"])

    r = await _pedir(client, clave, cabecera_cookie(token_de_prueba(uid, ["VENDEDOR"])))

    assert r.status_code == 403
    assert r.json() == {"detail": "No tenés permiso para esta operación."}


@pytest.mark.parametrize("clave", _CON_ROL, ids=_ids)
async def test_cada_ruta_con_rol_con_un_cliente_da_403(client, sessionmaker_test, clave):
    uid = await insertar_usuario(sessionmaker_test, roles=["CLIENTE"])

    r = await _pedir(client, clave, cabecera_cookie(token_de_prueba(uid, ["CLIENTE"])))

    assert r.status_code == 403
    assert r.json() == {"detail": "No tenés permiso para esta operación."}


@pytest.mark.parametrize("clave", _ABIERTAS_SIN_SESION, ids=_ids)
async def test_cada_ruta_abierta_para_cualquiera_no_responde_401_ni_403_sin_cookie(client, clave):
    r = await _pedir(client, clave)

    assert r.status_code not in (401, 403)
