"""Ciclo de vida de la app: recursos que crea el lifespan y cómo los libera.

No usan la base real: el motor no conecta al crearse. Cada test arma el entorno con
monkeypatch y corre desde una carpeta temporal para no leer el .env del desarrollador.
"""
import asyncio
import os
import secrets
import socket
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

import app.main as principal
from app.core.config import Settings
from app.main import app, lifespan

CONTRASENA_FALSA = "secreto-de-prueba"
RAIZ = Path(__file__).resolve().parent.parent


def _limpiar_estado():
    for clave in list(app.state._state):
        delattr(app.state, clave)


@pytest.fixture
def entorno(monkeypatch, tmp_path):
    """Entorno válido y mínimo; devuelve un helper para cambiar variables."""
    for campo in Settings.model_fields:
        monkeypatch.delenv(campo.upper(), raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir(tmp_path)
    variables = {
        "POSTGRES_USER": "u", "POSTGRES_PASSWORD": CONTRASENA_FALSA, "POSTGRES_DB": "db",
        "JWT_SECRET": secrets.token_urlsafe(48), "BCRYPT_COST": "4",
    }
    for nombre, valor in variables.items():
        monkeypatch.setenv(nombre, valor)
    _limpiar_estado()
    yield monkeypatch
    _limpiar_estado()


class _Motores(list):
    """Motores creados, con la cuenta de cierres de cada uno."""

    def __init__(self):
        super().__init__()
        self._cierres = {}  # id(motor) -> llamadas a dispose()

    def cierres(self, motor) -> int:
        return self._cierres.get(id(motor), 0)


@pytest.fixture
def motores(monkeypatch):
    """Registra los motores que crea el lifespan y las llamadas a dispose() de cada uno.

    AsyncEngine no admite atributos nuevos (usa __slots__): se espía la clase y se
    cuenta por identidad del motor.
    """
    creados = _Motores()
    crear_real = principal.crear_motor
    dispose_real = AsyncEngine.dispose

    def crear_espia(settings):
        motor = crear_real(settings)
        creados.append(motor)
        return motor

    async def dispose_espia(self, *args, **kw):
        creados._cierres[id(self)] = creados.cierres(self) + 1
        return await dispose_real(self, *args, **kw)

    monkeypatch.setattr(principal, "crear_motor", crear_espia)
    monkeypatch.setattr(AsyncEngine, "dispose", dispose_espia)
    return creados


# --- La app no arranca sin JWT_SECRET (DoD de CHG-03) ----------------------------


async def test_la_app_no_arranca_sin_jwt_secret(entorno, motores):
    entorno.delenv("JWT_SECRET")
    with pytest.raises(RuntimeError) as exc:
        async with lifespan(app):
            pytest.fail("el lifespan no debió ceder el control")
    assert "JWT_SECRET" in str(exc.value)
    assert CONTRASENA_FALSA not in str(exc.value)
    assert motores == []  # falla rápido: no se creó ningún recurso
    assert not hasattr(app.state, "engine")


# --- Recursos del arranque -------------------------------------------------------


async def test_el_arranque_deja_los_recursos_en_el_estado(entorno, motores):
    async with lifespan(app):
        assert isinstance(app.state.settings, Settings)
        assert isinstance(app.state.engine, AsyncEngine)
        assert app.state.engine is motores[0]
        assert app.state.sessionmaker.kw["expire_on_commit"] is False
        assert app.state.hash_ficticio.startswith("$2b$04$")


async def test_el_hash_ficticio_usa_el_costo_de_la_configuracion(entorno, motores):
    entorno.setenv("BCRYPT_COST", "5")
    async with lifespan(app):
        assert app.state.settings.bcrypt_cost == 5
        assert app.state.hash_ficticio.startswith("$2b$05$")


async def test_el_hash_ficticio_se_calcula_una_vez_con_el_costo_y_fuera_del_bucle(
    entorno, motores
):
    llamadas = []

    def doble(costo):
        llamadas.append((costo, threading.get_ident()))
        return "$2b$04$hash-doble"

    entorno.setattr(principal, "calcular_hash_ficticio", doble)
    hilo_del_bucle = threading.get_ident()
    async with lifespan(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            assert (await c.get("/health/live")).status_code == 200
            assert (await c.get("/health/live")).status_code == 200
        assert app.state.hash_ficticio == "$2b$04$hash-doble"
    assert len(llamadas) == 1
    costo, hilo = llamadas[0]
    assert costo == 4
    assert hilo != hilo_del_bucle  # asyncio.to_thread: no bloquea el bucle de eventos


async def test_el_apagado_cierra_el_motor_una_sola_vez(entorno, motores):
    async with lifespan(app):
        assert motores.cierres(motores[0]) == 0
    assert len(motores) == 1
    assert motores.cierres(motores[0]) == 1


async def test_el_motor_se_cierra_tambien_si_el_apagado_viene_por_una_excepcion(entorno, motores):
    with pytest.raises(ValueError):
        async with lifespan(app):
            raise ValueError("falla durante la vida de la app")
    assert motores.cierres(motores[0]) == 1


def test_importar_la_app_no_crea_motor_ni_fabrica(tmp_path):
    codigo = (
        "import app.main as m\n"
        "print(any(hasattr(m.app.state, k) for k in "
        "('engine', 'sessionmaker', 'settings', 'hash_ficticio')))"
    )
    # Entorno mínimo (sin variables de configuración); en Windows hace falta SYSTEMROOT.
    entorno = {"PYTHONPATH": str(RAIZ), "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}
    r = subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=tmp_path, env=entorno, capture_output=True, text=True, timeout=120, check=False,
    )
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "False"


# --- /health/ready con la base caída (DoD de CHG-03) -----------------------------


def _puerto_cerrado() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def test_ready_da_503_con_la_app_arrancada_y_la_base_caida(entorno, motores):
    entorno.setenv("POSTGRES_HOST", "127.0.0.1")
    entorno.setenv("POSTGRES_PORT", str(_puerto_cerrado()))
    async with (
        lifespan(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c,
    ):
        inicio = asyncio.get_running_loop().time()
        r = await c.get("/health/ready")
        duracion = asyncio.get_running_loop().time() - inicio
        vivo = await c.get("/health/live")
    assert r.status_code == 503
    assert r.json() == {"detail": "La base de datos no está disponible."}
    assert duracion < 10
    for interno in ("127.0.0.1", CONTRASENA_FALSA, "SELECT"):
        assert interno not in r.text
    assert vivo.status_code == 200  # la sonda de vida no depende de la base
