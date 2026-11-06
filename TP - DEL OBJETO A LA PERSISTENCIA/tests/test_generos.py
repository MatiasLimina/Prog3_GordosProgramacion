import pytest

from tests.auxiliares_auth import entrar_como

pytestmark = pytest.mark.db

@pytest.fixture
async def client(client, sessionmaker_test):
    """Sesión de ADMIN: las escrituras del catálogo, clientes y ventas son del grupo protegido (CHG-12)."""
    await entrar_como(client, sessionmaker_test, "ADMIN")
    return client


async def crear(client, nombre="Novela"):
    return await client.post("/generos/", json={"nombre": nombre})


async def test_post_crea_con_201(client):
    r = await crear(client)
    assert r.status_code == 201
    assert r.json() == {"id": 1, "nombre": "Novela"}


async def test_post_con_id_del_cliente_da_422_y_no_crea_nada(client):
    # BREAKING (CHG-13): antes se ignoraba el `id`; ahora el contrato de entrada es `extra="forbid"`.
    r = await client.post("/generos/", json={"id": 50, "nombre": "Ensayo"})
    assert r.status_code == 422
    assert (await client.get("/generos/")).json()["total"] == 0


async def test_post_nombre_repetido_da_409_con_mensaje_propio(client):
    await crear(client)
    r = await crear(client)
    assert r.status_code == 409
    assert r.json() == {"detail": "Ya existe un género con ese nombre."}
    for interno in ("duplicate", "uq_genero", "violates", "INSERT"):
        assert interno not in r.text


@pytest.mark.parametrize("body", [{}, {"nombre": ""}, {"nombre": "x" * 101}])
async def test_post_body_invalido_da_422(client, body):
    assert (await client.post("/generos/", json=body)).status_code == 422


async def test_listado_responde_con_el_envoltorio_ordenado_por_id(client):
    for n in ["A", "B", "C"]:
        await crear(client, n)
    r = await client.get("/generos/", params={"size": 2})
    assert r.status_code == 200
    datos = r.json()
    assert set(datos) == {"items", "total", "page", "size", "pages"}
    assert (datos["total"], datos["page"], datos["size"], datos["pages"]) == (3, 1, 2, 2)
    assert [g["nombre"] for g in datos["items"]] == ["A", "B"]
    r = await client.get("/generos/", params={"size": 2, "page": 2})
    assert [g["nombre"] for g in r.json()["items"]] == ["C"]


async def test_listado_pagina_fuera_de_rango_da_422(client):
    for n in ["A", "B", "C"]:
        await crear(client, n)
    r = await client.get("/generos/", params={"size": 2, "page": 3})
    assert r.status_code == 422
    assert "La página 3 no existe: hay 2" in r.text


async def test_listado_vacio_tiene_una_pagina_vacia_y_parametros_invalidos_dan_422(client):
    assert (await client.get("/generos/")).json() == {"items": [], "total": 0, "page": 1, "size": 20, "pages": 1}
    assert (await client.get("/generos/", params={"page": 0})).status_code == 422
    assert (await client.get("/generos/", params={"size": 101})).status_code == 422


async def test_post_con_campo_extra_da_422(client):
    assert (await client.post("/generos/", json={"nombre": "X", "otro": 1})).status_code == 422


async def test_no_hay_patch_de_generos(client):
    await crear(client)
    assert (await client.patch("/generos/1", json={"nombre": "X"})).status_code in (404, 405)
