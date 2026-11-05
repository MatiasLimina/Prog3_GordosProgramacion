"""PeticionInvalida: excepción de dominio que la app responde como 422."""
import httpx
from fastapi import FastAPI

from app.core.errors import PeticionInvalida
from app.main import app as app_real
from app.main import registrar_handlers


def _app_de_prueba(mensaje: str) -> FastAPI:
    app = FastAPI()
    registrar_handlers(app)

    @app.get("/invalida")
    async def invalida():
        raise PeticionInvalida(mensaje)

    return app


async def _get(app: FastAPI, ruta: str) -> httpx.Response:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        return await c.get(ruta)


def test_peticion_invalida_es_excepcion_y_guarda_el_mensaje():
    error = PeticionInvalida("La página 4 no existe: hay 3")
    assert isinstance(error, Exception)
    assert error.mensaje == "La página 4 no existe: hay 3"
    assert str(error) == "La página 4 no existe: hay 3"


async def test_peticion_invalida_se_responde_como_422_con_detail():
    r = await _get(_app_de_prueba("La página 4 no existe: hay 3"), "/invalida")
    assert r.status_code == 422
    assert r.json() == {"detail": "La página 4 no existe: hay 3"}


def test_la_app_real_tiene_registrado_el_handler():
    assert PeticionInvalida in app_real.exception_handlers
