"""Conflicto: excepción de dominio que la app responde como 409 (D6)."""
import httpx
from fastapi import FastAPI

from app.core.errors import Conflicto
from app.main import app as app_real
from app.main import registrar_handlers


def _app_de_prueba(mensaje: str) -> FastAPI:
    app = FastAPI()
    registrar_handlers(app)

    @app.get("/choque")
    async def choque():
        raise Conflicto(mensaje)

    return app


async def _get(app: FastAPI, ruta: str) -> httpx.Response:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        return await c.get(ruta)


def test_conflicto_es_excepcion_y_guarda_el_mensaje():
    error = Conflicto("Ya existe.")
    assert isinstance(error, Exception)
    assert error.mensaje == "Ya existe."
    assert str(error) == "Ya existe."


async def test_conflicto_se_responde_como_409_con_detail():
    r = await _get(_app_de_prueba("Ya existe."), "/choque")
    assert r.status_code == 409
    assert r.json() == {"detail": "Ya existe."}


async def test_el_cuerpo_lleva_el_mensaje_que_se_le_dio():
    r = await _get(_app_de_prueba("La editorial indicada no existe."), "/choque")
    assert r.json() == {"detail": "La editorial indicada no existe."}


def test_la_app_real_tiene_registrado_el_handler():
    assert Conflicto in app_real.exception_handlers
