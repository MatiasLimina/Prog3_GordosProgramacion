"""Tests del envoltorio de paginación page/size (CHG-05, consigna sección 2.9)."""
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import PeticionInvalida
from app.core.paginacion import Page, ParametrosPagina, envolver, paginacion_params
from app.main import registrar_handlers

app = FastAPI()
registrar_handlers(app)


@app.get("/items")
async def items(p: ParametrosPagina = Depends(paginacion_params)):
    datos = [{"id": i} for i in range(1, 6)]
    desde = (p.page - 1) * p.size
    return envolver(datos[desde:desde + p.size], total=len(datos), page=p.page, size=p.size)


@pytest.fixture
def client():
    return TestClient(app)


# --- Parámetros page/size (vía HTTP) ---

def test_parametros_por_defecto(client):
    r = client.get("/items")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["page"] == 1
    assert cuerpo["size"] == 20
    assert cuerpo["pages"] == 1
    assert len(cuerpo["items"]) == 5
    assert cuerpo["total"] == 5


@pytest.mark.parametrize("params", [{"page": 0}, {"page": -1}, {"size": 0}, {"size": 101}, {"size": -5}, {"page": "x"}])
def test_parametros_fuera_de_rango_dan_422(client, params):
    r = client.get("/items", params=params)
    assert r.status_code == 422


@pytest.mark.parametrize("size", [1, 100])
def test_size_en_los_limites(client, size):
    r = client.get("/items", params={"size": size})
    assert r.status_code == 200
    assert r.json()["size"] == size


def test_page_mas_alla_de_la_ultima_da_422_con_mensaje(client):
    r = client.get("/items", params={"size": 2, "page": 4})
    assert r.status_code == 422
    assert "La página 4 no existe: hay 3" in r.json()["detail"]


# --- envoltorio directo ---

def test_envoltorio_cero_resultados():
    page = envolver([], total=0, page=1, size=20)
    assert page.items == []
    assert page.total == 0
    assert page.page == 1
    assert page.size == 20
    assert page.pages == 1


def test_envoltorio_un_resultado():
    page = envolver([{"id": 1}], total=1, page=1, size=20)
    assert page.pages == 1
    assert page.items == [{"id": 1}]


def test_envoltorio_multiplio_exacto():
    datos = [{"id": i} for i in range(1, 5)]
    page = envolver(datos[2:4], total=4, page=2, size=2)
    assert page.pages == 2
    assert page.items == [{"id": 3}, {"id": 4}]


def test_envoltorio_sobrante():
    items = [{"id": 5}]
    page = envolver(items, total=5, page=3, size=2)
    assert page.pages == 3
    assert page.items == [{"id": 5}]


def test_page_fuera_de_rango_lanza_excepcion_de_dominio():
    with pytest.raises(PeticionInvalida) as exc:
        envolver([], total=5, page=4, size=2)
    assert exc.value.mensaje == "La página 4 no existe: hay 3"


def test_page_fuera_de_rango_lista_vacia():
    with pytest.raises(PeticionInvalida) as exc:
        envolver([], total=0, page=2, size=20)
    assert exc.value.mensaje == "La página 2 no existe: hay 1"


def test_page_es_generico_y_serializa():
    class Item(BaseModel):
        id: int

    page = envolver([Item(id=1), Item(id=2)], total=2, page=1, size=2)
    assert isinstance(page, Page)
    datos = page.model_dump()
    assert datos == {"items": [{"id": 1}, {"id": 2}], "total": 2, "page": 1, "size": 2, "pages": 1}
    assert '"pages":1' in page.model_dump_json().replace(" ", "")
