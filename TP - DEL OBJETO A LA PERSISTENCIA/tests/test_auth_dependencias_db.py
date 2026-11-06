"""Infraestructura de auth (CHG-11): estado de la app en los tests y dependencias de seguridad.

El fixture `client` usa `ASGITransport`, que no corre el lifespan: sin estas pruebas,
`app.state` no tendría `settings`, `hash_ficticio`, `semaforo_bcrypt` ni `sessionmaker`.
"""
import asyncio
from types import SimpleNamespace

import pytest

from app.main import app as fastapi_app

pytestmark = pytest.mark.db

_CLAVES = ("settings", "hash_ficticio", "semaforo_bcrypt", "sessionmaker")


async def test_client_deja_el_estado_de_la_app_listo_para_auth(client, sessionmaker_test):
    state = fastapi_app.state
    assert state.settings.bcrypt_cost == 4
    assert state.hash_ficticio.startswith("$2b$04$")
    assert isinstance(state.semaforo_bcrypt, asyncio.Semaphore)
    assert state.sessionmaker is sessionmaker_test


async def test_estado_de_app_restaura_lo_que_habia_y_borra_lo_que_no(sessionmaker_test):
    from tests.conftest import estado_de_app

    state = fastapi_app.state
    previo = {c: state._state[c] for c in _CLAVES if c in state._state}
    centinela = object()
    state._state["hash_ficticio"] = centinela  # algo que ya había (p. ej. tras un lifespan)
    state._state.pop("semaforo_bcrypt", None)  # algo que no había
    try:
        with estado_de_app(fastapi_app, sessionmaker_test):
            assert state.hash_ficticio is not centinela
            assert "semaforo_bcrypt" in state._state
        assert state.hash_ficticio is centinela
        assert "semaforo_bcrypt" not in state._state
    finally:
        for c in _CLAVES:
            state._state.pop(c, None)
        state._state.update(previo)


# ---- ParametrosSeguridad y sesión propia (design D3, D8) ----

def _app_con_estado(**estado):
    """App mínima con `app.state` armado a mano (sin lifespan)."""
    from fastapi import FastAPI

    app = FastAPI()
    for clave, valor in estado.items():
        setattr(app.state, clave, valor)
    return app


async def _get(app, ruta="/prueba"):
    import httpx

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        return await c.get(ruta)


@pytest.mark.parametrize("cookie_secure, minutos, costo", [(False, 60, 4), (True, 15, 5)])
async def test_get_parametros_seguridad_arma_los_parametros_desde_app_state(cookie_secure, minutos, costo):
    from typing import Annotated

    from fastapi import Depends
    from pydantic import SecretStr

    from app.core.config import get_settings
    from app.core.dependencies import ParametrosSeguridad, get_parametros_seguridad

    settings = get_settings().model_copy(
        update={"cookie_secure": cookie_secure, "jwt_expire_minutes": minutos, "bcrypt_cost": costo}
    )
    semaforo = asyncio.Semaphore(2)
    app = _app_con_estado(settings=settings, semaforo_bcrypt=semaforo, hash_ficticio="$2b$04$ficticio")
    visto = []

    @app.get("/prueba")
    async def prueba(seg: Annotated[ParametrosSeguridad, Depends(get_parametros_seguridad)]):
        visto.append(seg)
        return {}

    assert (await _get(app)).status_code == 200
    seg = visto[0]
    assert seg.costo == costo
    assert seg.semaforo is semaforo
    assert seg.hash_ficticio == "$2b$04$ficticio"
    assert isinstance(seg.secreto, SecretStr)
    assert seg.secreto.get_secret_value() == settings.jwt_secret.get_secret_value()
    assert seg.minutos_token == minutos
    assert seg.cookie_secure is cookie_secure


async def test_parametros_seguridad_es_inmutable():
    import dataclasses

    from app.core.dependencies import ParametrosSeguridad

    seg = ParametrosSeguridad(
        costo=4, semaforo=asyncio.Semaphore(1), hash_ficticio="h", secreto=None, minutos_token=1, cookie_secure=False
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        seg.costo = 5


async def test_uow_con_sesion_propia_usa_otra_sesion_y_llega_sin_abrir(sessionmaker_test):
    from typing import Annotated

    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.database import get_session
    from app.core.dependencies import proveedor_uow_sesion_propia
    from app.modules.usuarios.unit_of_work import IntentosUoW

    app = _app_con_estado(sessionmaker=sessionmaker_test)
    visto = []

    @app.get("/prueba")
    async def prueba(
        session: Annotated[AsyncSession, Depends(get_session)],
        intentos: Annotated[IntentosUoW, Depends(proveedor_uow_sesion_propia(IntentosUoW))],
    ):
        visto.append((session, intentos, intentos.session.info.get("uow_activo")))
        return {}

    assert (await _get(app)).status_code == 200
    session, intentos, activo = visto[0]
    assert type(intentos) is IntentosUoW
    assert intentos.session is not session  # sesión nueva, no la de la petición
    assert isinstance(intentos.session, AsyncSession)
    assert not activo  # el router lo construye; abrirlo es del servicio


async def test_uow_con_sesion_propia_entrega_una_sesion_distinta_por_peticion(sessionmaker_test):
    from typing import Annotated

    from fastapi import Depends

    from app.core.dependencies import proveedor_uow_sesion_propia
    from app.modules.usuarios.unit_of_work import IntentosUoW

    app = _app_con_estado(sessionmaker=sessionmaker_test)
    sesiones = []

    @app.get("/prueba")
    async def prueba(intentos: Annotated[IntentosUoW, Depends(proveedor_uow_sesion_propia(IntentosUoW))]):
        sesiones.append(intentos.session)
        return {}

    await _get(app)
    await _get(app)
    assert sesiones[0] is not sesiones[1]


# ---- entrar_como: sesión de prueba sin pasar por /auth/login (CHG-12, design D10) ----

async def test_entrar_como_deja_al_client_con_una_cookie_que_vale_en_auth_yo(client, sessionmaker_test):
    from tests.auxiliares_auth import entrar_como

    uid = await entrar_como(client, sessionmaker_test, "ADMIN")

    r = await client.get("/auth/yo")
    assert r.status_code == 200
    assert r.json()["usuario"]["id"] == uid
    assert r.json()["roles_vigentes"] == ["ADMIN"]


@pytest.mark.parametrize("roles", [("VENDEDOR",), ("VENDEDOR", "ADMIN"), ()])
async def test_entrar_como_asigna_exactamente_los_roles_pedidos(client, sessionmaker_test, roles):
    from tests.auxiliares_auth import entrar_como

    await entrar_como(client, sessionmaker_test, *roles)

    assert (await client.get("/auth/yo")).json()["roles_vigentes"] == sorted(roles)


async def test_entrar_como_con_debe_cambiar_deja_el_flag_en_el_usuario(client, sessionmaker_test):
    from tests.auxiliares_auth import contar, entrar_como

    uid = await entrar_como(client, sessionmaker_test, "VENDEDOR", email="otra@example.com", debe_cambiar=True)

    assert await contar(sessionmaker_test, "usuario", "id = :u AND debe_cambiar_password", u=uid) == 1
    assert (await client.get("/auth/yo")).json()["usuario"]["debe_cambiar_password"] is True


async def test_entrar_como_no_deja_filas_de_intento_de_acceso(client, sessionmaker_test):
    from tests.auxiliares_auth import contar, entrar_como

    await entrar_como(client, sessionmaker_test, "ADMIN")

    assert await contar(sessionmaker_test, "intento_acceso") == 0
