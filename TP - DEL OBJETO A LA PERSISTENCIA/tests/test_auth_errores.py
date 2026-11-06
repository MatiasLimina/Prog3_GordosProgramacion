"""NoAutenticado (401), DemasiadosIntentos (429) y SinPermiso (403): excepciones de dominio de auth (D6, CHG-12 D7)."""
import httpx
import pytest
from fastapi import FastAPI

from app.core.errors import DemasiadosIntentos, NoAutenticado, SinPermiso
from app.main import registrar_handlers

_DETALLE_429 = "Demasiados intentos fallidos. Probá de nuevo más tarde."


def _app(excepcion: Exception) -> FastAPI:
    app = FastAPI()
    registrar_handlers(app)

    @app.get("/prueba")
    async def prueba():
        raise excepcion

    return app


async def _get(app: FastAPI) -> httpx.Response:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        return await c.get("/prueba")


@pytest.mark.parametrize("mensaje", ["x", "No hay una sesión válida."])
async def test_no_autenticado_responde_401_con_su_mensaje_y_sin_www_authenticate(mensaje):
    r = await _get(_app(NoAutenticado(mensaje)))
    assert r.status_code == 401
    assert r.json() == {"detail": mensaje}
    assert "www-authenticate" not in r.headers


@pytest.mark.parametrize("segundos", [17, 1, 60])
async def test_demasiados_intentos_responde_429_con_retry_after_y_detalle_fijo(segundos):
    r = await _get(_app(DemasiadosIntentos(segundos)))
    assert r.status_code == 429
    assert r.headers["retry-after"] == str(segundos)
    assert r.json() == {"detail": _DETALLE_429}


def test_las_excepciones_guardan_sus_datos():
    assert NoAutenticado("x").mensaje == "x"
    assert DemasiadosIntentos(17).retry_after == 17


@pytest.mark.parametrize("mensaje", ["x", "No tenés permiso para esta operación."])
async def test_sin_permiso_responde_403_con_su_mensaje(mensaje):
    r = await _get(_app(SinPermiso(mensaje)))
    assert r.status_code == 403
    assert r.json() == {"detail": mensaje}


def test_sin_permiso_es_de_dominio_y_guarda_su_mensaje():
    from fastapi import HTTPException

    error = SinPermiso("x")
    assert error.mensaje == "x"
    assert not isinstance(error, HTTPException)
