import pytest

pytestmark = pytest.mark.db


async def crear(client, nombre="Novela"):
    return await client.post("/generos/", json={"nombre": nombre})


async def test_post_crea_con_201(client):
    r = await crear(client)
    assert r.status_code == 201
    assert r.json() == {"id": 1, "nombre": "Novela"}


async def test_post_ignora_id_del_cliente(client):
    r = await client.post("/generos/", json={"id": 50, "nombre": "Ensayo"})
    assert r.json() == {"id": 1, "nombre": "Ensayo"}


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


async def test_listado_paginado_ordenado_por_id(client):
    for n in ["A", "B", "C", "D"]:
        await crear(client, n)
    r = await client.get("/generos/", params={"limit": 2, "offset": 2})
    assert [g["nombre"] for g in r.json()] == ["C", "D"]
    assert len((await client.get("/generos/")).json()) == 4


async def test_listado_vacio_y_paginacion_invalida(client):
    assert (await client.get("/generos/")).json() == []
    assert (await client.get("/generos/", params={"offset": -1})).status_code == 422


async def test_no_hay_patch_de_generos(client):
    await crear(client)
    assert (await client.patch("/generos/1", json={"nombre": "X"})).status_code in (404, 405)
