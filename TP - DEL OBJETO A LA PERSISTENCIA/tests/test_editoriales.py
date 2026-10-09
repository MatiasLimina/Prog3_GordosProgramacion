import pytest

pytestmark = pytest.mark.db


async def crear(client, nombre="Planeta", pais="España"):
    return await client.post("/editoriales/", json={"nombre": nombre, "pais": pais})


async def test_post_crea_con_201_y_devuelve_id(client):
    r = await crear(client)
    assert r.status_code == 201
    assert r.json() == {"id": 1, "nombre": "Planeta", "pais": "España"}


async def test_post_ignora_id_enviado_por_el_cliente(client):
    r = await client.post("/editoriales/", json={"id": 99, "nombre": "A", "pais": "B"})
    assert r.status_code == 201
    assert r.json()["id"] == 1


async def test_post_nombre_repetido_da_409_con_mensaje_propio(client):
    await crear(client)
    r = await crear(client, pais="Otro")
    assert r.status_code == 409
    assert r.json() == {"detail": "Ya existe una editorial con ese nombre."}
    for interno in ("duplicate", "uq_editorial", "violates", "INSERT"):
        assert interno not in r.text


@pytest.mark.parametrize(
    "body",
    [
        {"pais": "AR"},
        {"nombre": "A"},
        {"nombre": "", "pais": "AR"},
        {"nombre": "A", "pais": ""},
        {"nombre": "x" * 151, "pais": "AR"},
    ],
)
async def test_post_body_invalido_da_422(client, body):
    r = await client.post("/editoriales/", json=body)
    assert r.status_code == 422


async def test_get_por_id(client):
    await crear(client, "Sudamericana", "Argentina")
    r = await client.get("/editoriales/1")
    assert r.status_code == 200
    assert r.json() == {"id": 1, "nombre": "Sudamericana", "pais": "Argentina"}


async def test_get_inexistente_da_404_con_mensaje_propio(client):
    r = await client.get("/editoriales/999")
    assert r.status_code == 404
    assert r.json() == {"detail": "La editorial no existe."}


async def test_c01_id_no_numerico_da_422(client):
    r = await client.get("/editoriales/abc")
    assert r.status_code == 422


async def test_listado_paginado_ordenado_por_id(client):
    for n in "ABCDE":
        await crear(client, n)
    r = await client.get("/editoriales/", params={"limit": 2, "offset": 1})
    assert [e["nombre"] for e in r.json()] == ["B", "C"]
    r = await client.get("/editoriales/")
    assert len(r.json()) == 5


async def test_listado_vacio_y_limit_invalido(client):
    assert (await client.get("/editoriales/")).json() == []
    assert (await client.get("/editoriales/", params={"limit": 101})).status_code == 422
