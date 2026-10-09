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


async def test_patch_parcial_no_pisa_campos_no_enviados(client):
    await crear(client, "Planeta", "España")
    r = await client.patch("/editoriales/1", json={"pais": "México"})
    assert r.status_code == 200
    assert r.json() == {"id": 1, "nombre": "Planeta", "pais": "México"}
    r = await client.patch("/editoriales/1", json={"nombre": "Planeta SA"})
    assert r.json() == {"id": 1, "nombre": "Planeta SA", "pais": "México"}
    # y quedó persistido
    assert (await client.get("/editoriales/1")).json()["nombre"] == "Planeta SA"


async def test_patch_vacio_no_cambia_nada(client):
    await crear(client)
    r = await client.patch("/editoriales/1", json={})
    assert r.status_code == 200
    assert r.json() == {"id": 1, "nombre": "Planeta", "pais": "España"}


async def test_patch_a_nombre_existente_da_409(client):
    await crear(client, "A")
    await crear(client, "B")
    r = await client.patch("/editoriales/2", json={"nombre": "A"})
    assert r.status_code == 409
    assert r.json() == {"detail": "Ya existe una editorial con ese nombre."}
    # el rollback dejó el dato original
    assert (await client.get("/editoriales/2")).json()["nombre"] == "B"


async def test_patch_inexistente_da_404(client):
    r = await client.patch("/editoriales/999", json={"pais": "X"})
    assert r.status_code == 404


async def test_patch_body_invalido_da_422(client):
    await crear(client)
    assert (await client.patch("/editoriales/1", json={"nombre": ""})).status_code == 422
