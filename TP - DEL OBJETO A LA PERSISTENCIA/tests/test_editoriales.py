import pytest

from tests.auxiliares_auth import entrar_como

pytestmark = pytest.mark.db

@pytest.fixture
async def client(client, sessionmaker_test):
    """Sesión de ADMIN: las escrituras del catálogo, clientes y ventas son del grupo protegido (CHG-12)."""
    await entrar_como(client, sessionmaker_test, "ADMIN")
    return client


async def crear(client, nombre="Planeta", pais="España"):
    return await client.post("/editoriales/", json={"nombre": nombre, "pais": pais})


async def test_post_crea_con_201_y_devuelve_id(client):
    r = await crear(client)
    assert r.status_code == 201
    assert r.json() == {"id": 1, "nombre": "Planeta", "pais": "España"}


async def test_post_con_id_enviado_por_el_cliente_da_422_y_no_crea_nada(client):
    # BREAKING (CHG-13): antes se ignoraba el `id`; ahora el contrato de entrada es `extra="forbid"`.
    r = await client.post("/editoriales/", json={"id": 99, "nombre": "A", "pais": "B"})
    assert r.status_code == 422
    assert (await client.get("/editoriales/")).json()["total"] == 0


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


async def test_listado_responde_con_el_envoltorio_ordenado_por_id(client):
    for n in "ABCDE":
        await crear(client, n)
    r = await client.get("/editoriales/", params={"size": 2})
    assert r.status_code == 200
    datos = r.json()
    assert set(datos) == {"items", "total", "page", "size", "pages"}
    assert (datos["total"], datos["page"], datos["size"], datos["pages"]) == (5, 1, 2, 3)
    assert [e["nombre"] for e in datos["items"]] == ["A", "B"]
    r = await client.get("/editoriales/", params={"size": 2, "page": 3})
    assert [e["nombre"] for e in r.json()["items"]] == ["E"]


async def test_listado_pagina_mas_alla_de_la_ultima_da_422(client):
    for n in "ABCDE":
        await crear(client, n)
    r = await client.get("/editoriales/", params={"size": 2, "page": 4})
    assert r.status_code == 422
    assert "La página 4 no existe: hay 3" in r.text


async def test_listado_vacio_tiene_una_pagina_vacia(client):
    assert (await client.get("/editoriales/")).json() == {"items": [], "total": 0, "page": 1, "size": 20, "pages": 1}


async def test_limit_y_offset_ya_no_paginan_y_size_fuera_de_rango_da_422(client):
    for n in "ABCDE":
        await crear(client, n)
    r = await client.get("/editoriales/", params={"limit": 1})
    assert r.status_code == 200
    assert len(r.json()["items"]) == 5  # `limit` se ignora: no pagina
    assert (await client.get("/editoriales/", params={"size": 101})).status_code == 422
    assert (await client.get("/editoriales/", params={"page": 0})).status_code == 422


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


@pytest.mark.parametrize("body", [{"nombre": None}, {"pais": None}, {"nombre": "X", "pais": None}])
async def test_patch_con_null_explicito_da_422(client, body):
    await crear(client)
    r = await client.patch("/editoriales/1", json=body)
    assert r.status_code == 422
    # no se modificó nada
    assert (await client.get("/editoriales/1")).json() == {"id": 1, "nombre": "Planeta", "pais": "España"}


async def test_patch_omitir_campos_sigue_permitido_tras_el_validador(client):
    await crear(client)
    r = await client.patch("/editoriales/1", json={"nombre": "Nueva"})
    assert r.status_code == 200
    assert r.json() == {"id": 1, "nombre": "Nueva", "pais": "España"}


@pytest.mark.parametrize("body", [{"id": 5}, {"pais": "X", "otro": 1}])
async def test_patch_con_campo_extra_da_422_y_no_modifica(client, body):
    await crear(client)
    r = await client.patch("/editoriales/1", json=body)
    assert r.status_code == 422
    assert (await client.get("/editoriales/1")).json() == {"id": 1, "nombre": "Planeta", "pais": "España"}


async def test_post_con_campo_extra_da_422(client):
    r = await client.post("/editoriales/", json={"nombre": "A", "pais": "B", "otro": 1})
    assert r.status_code == 422
