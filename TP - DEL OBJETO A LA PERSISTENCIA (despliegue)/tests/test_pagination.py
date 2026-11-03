import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.pagination import Pagination, pagination_params

app = FastAPI()


@app.get("/items")
async def items(p: Pagination = Depends(pagination_params)):
    return {"limit": p.limit, "offset": p.offset}


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_valores_por_defecto(client):
    r = await client.get("/items")
    assert r.status_code == 200
    assert r.json() == {"limit": 20, "offset": 0}


@pytest.mark.parametrize("limit,offset", [(1, 0), (100, 5), (50, 200)])
async def test_valores_validos(client, limit, offset):
    r = await client.get("/items", params={"limit": limit, "offset": offset})
    assert r.status_code == 200
    assert r.json() == {"limit": limit, "offset": offset}


@pytest.mark.parametrize("limit", [0, 101, -3])
async def test_limit_fuera_de_rango_da_422(client, limit):
    r = await client.get("/items", params={"limit": limit})
    assert r.status_code == 422


async def test_offset_negativo_da_422(client):
    r = await client.get("/items", params={"offset": -1})
    assert r.status_code == 422
