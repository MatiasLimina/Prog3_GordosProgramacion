import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import OperationalError

from app.core.database import get_session
from app.main import app


class SesionOk:
    def __init__(self):
        self.consultas = []

    async def execute(self, stmt):
        self.consultas.append(str(stmt))


class SesionRota:
    async def execute(self, stmt):
        raise OperationalError("SELECT 1", {}, Exception('connection refused to host "10.0.0.5" password=secreto'))


@pytest.fixture
async def client():
    # ASGITransport no ejecuta el lifespan: no hace falta base ni .env.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


async def test_live_responde_vivo_sin_tocar_la_base(client):
    # Sin override de get_session ni app.state.sessionmaker: si tocara la base, fallaría.
    r = await client.get("/health/live")
    assert r.status_code == 200
    assert r.json() == {"estado": "vivo"}


async def test_ready_ok_ejecuta_select_1(client):
    sesion = SesionOk()
    app.dependency_overrides[get_session] = lambda: sesion
    r = await client.get("/health/ready")
    assert r.status_code == 200
    assert r.json() == {"estado": "listo", "base_de_datos": "disponible"}
    assert sesion.consultas == ["SELECT 1"]


async def test_ready_con_base_caida_da_503_sin_texto_interno(client):
    app.dependency_overrides[get_session] = lambda: SesionRota()
    r = await client.get("/health/ready")
    assert r.status_code == 503
    assert r.json() == {"detail": "La base de datos no está disponible."}
    cuerpo = r.text
    for interno in ("connection refused", "10.0.0.5", "secreto", "SELECT"):
        assert interno not in cuerpo


async def test_ready_ante_cualquier_error_da_503(client):
    class SesionExplota:
        async def execute(self, stmt):
            raise RuntimeError("falla inesperada interna")

    app.dependency_overrides[get_session] = lambda: SesionExplota()
    r = await client.get("/health/ready")
    assert r.status_code == 503
    assert "inesperada" not in r.text
