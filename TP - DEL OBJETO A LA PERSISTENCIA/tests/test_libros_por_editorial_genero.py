import pytest

from tests.auxiliares_auth import entrar_como

pytestmark = pytest.mark.db

@pytest.fixture
async def client(client, sessionmaker_test):
    """Sesión de ADMIN: las escrituras del catálogo, clientes y ventas son del grupo protegido (CHG-12)."""
    await entrar_como(client, sessionmaker_test, "ADMIN")
    return client


async def editorial(client, nombre):
    return (await client.post("/editoriales/", json={"nombre": nombre, "pais": "AR"})).json()["id"]


async def genero(client, nombre):
    return (await client.post("/generos/", json={"nombre": nombre})).json()["id"]


async def libro(client, isbn, editorial_id, genero_id=None):
    body = {"isbn": isbn, "titulo": f"Titulo {isbn}", "precio": "10.50", "stock_inicial": 1, "editorial_id": editorial_id}
    if genero_id is not None:
        body["genero_id"] = genero_id
    r = await client.post("/libros/", json=body)
    assert r.status_code == 201, r.text
    return r.json()["id"]


# --- editoriales ---

async def dar_de_baja_por_sql(sessionmaker_test, libro_id):
    from sqlalchemy import text

    async with sessionmaker_test() as s:
        await s.execute(text("UPDATE libro SET borrado_en = now() WHERE id = :i"), {"i": libro_id})
        await s.commit()


async def test_libros_de_una_editorial_no_incluye_los_de_otra(client):
    e1, e2 = await editorial(client, "E1"), await editorial(client, "E2")
    g = await genero(client, "Novela")
    a = await libro(client, "A", e1, g)
    b = await libro(client, "B", e1)
    await libro(client, "C", e2)
    r = await client.get(f"/editoriales/{e1}/libros")
    assert r.status_code == 200
    pagina = r.json()
    assert set(pagina) == {"items", "total", "page", "size", "pages"}
    assert pagina["total"] == 2
    datos = pagina["items"]
    assert [l["id"] for l in datos] == [a, b]
    assert datos[0]["editorial"]["nombre"] == "E1"
    assert datos[0]["genero"]["nombre"] == "Novela"
    assert datos[1]["genero"] is None


async def test_editorial_sin_libros_da_pagina_vacia(client):
    e = await editorial(client, "Vacia")
    r = await client.get(f"/editoriales/{e}/libros")
    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0, "page": 1, "size": 20, "pages": 1}


async def test_editorial_inexistente_da_404_propio(client):
    r = await client.get("/editoriales/999/libros")
    assert r.status_code == 404
    assert r.json() == {"detail": "La editorial no existe."}


async def test_editorial_id_no_entero_da_422(client):
    assert (await client.get("/editoriales/abc/libros")).status_code == 422


async def test_libros_de_editorial_paginados_con_total_y_pagina_inexistente(client):
    e = await editorial(client, "E")
    ids = [await libro(client, f"L{i}", e) for i in range(4)]
    r = await client.get(f"/editoriales/{e}/libros", params={"size": 2, "page": 2})
    pagina = r.json()
    assert [l["id"] for l in pagina["items"]] == ids[2:]
    assert (pagina["total"], pagina["page"], pagina["size"], pagina["pages"]) == (4, 2, 2, 2)
    r = await client.get(f"/editoriales/{e}/libros", params={"size": 2, "page": 3})
    assert r.status_code == 422
    assert "La página 3 no existe: hay 2" in r.text
    assert (await client.get(f"/editoriales/{e}/libros", params={"size": 0})).status_code == 422


async def test_libros_de_editorial_excluye_los_dados_de_baja_y_el_total_los_excluye(client, sessionmaker_test):
    e = await editorial(client, "E")
    visible = await libro(client, "V", e)
    baja = await libro(client, "B", e)
    await dar_de_baja_por_sql(sessionmaker_test, baja)
    r = await client.get(f"/editoriales/{e}/libros", params={"size": 1})
    assert [l["id"] for l in r.json()["items"]] == [visible]
    assert (r.json()["total"], r.json()["pages"]) == (1, 1)


async def contar_consultas(client, sessionmaker_test, ruta):
    from sqlalchemy import event

    consultas = []

    def hook(conn, cursor, statement, *a):
        consultas.append(statement)

    engine = sessionmaker_test.kw["bind"].sync_engine
    event.listen(engine, "before_cursor_execute", hook)
    try:
        r = await client.get(ruta)
    finally:
        event.remove(engine, "before_cursor_execute", hook)
    assert r.status_code == 200, r.text
    return len(consultas), r.json()


async def test_libros_de_editorial_emiten_las_mismas_consultas_con_1_o_5_libros(client, sessionmaker_test):
    e1, e5 = await editorial(client, "E1"), await editorial(client, "E5")
    g = await genero(client, "G")
    await libro(client, "Q0", e1, g)
    for i in range(5):
        await libro(client, f"Q{i + 1}", e5, g)
    n1, d1 = await contar_consultas(client, sessionmaker_test, f"/editoriales/{e1}/libros")
    n5, d5 = await contar_consultas(client, sessionmaker_test, f"/editoriales/{e5}/libros")
    assert (d1["total"], d5["total"]) == (1, 5)
    assert n1 == n5


# --- géneros ---

async def test_libros_de_un_genero_excluye_otros_y_los_sin_genero(client):
    e = await editorial(client, "E")
    g1, g2 = await genero(client, "G1"), await genero(client, "G2")
    a = await libro(client, "A", e, g1)
    b = await libro(client, "B", e, g1)
    await libro(client, "C", e, g2)
    await libro(client, "D", e)  # genero_id nulo: no debe aparecer
    r = await client.get(f"/generos/{g1}/libros")
    assert r.status_code == 200
    pagina = r.json()
    assert set(pagina) == {"items", "total", "page", "size", "pages"}
    assert pagina["total"] == 2
    datos = pagina["items"]
    assert [l["id"] for l in datos] == [a, b]
    assert all(l["genero"]["nombre"] == "G1" and l["editorial"]["nombre"] == "E" for l in datos)


async def test_genero_sin_libros_da_pagina_vacia(client):
    g = await genero(client, "Vacio")
    r = await client.get(f"/generos/{g}/libros")
    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0, "page": 1, "size": 20, "pages": 1}


async def test_genero_inexistente_da_404_propio(client):
    r = await client.get("/generos/999/libros")
    assert r.status_code == 404
    assert r.json() == {"detail": "El género no existe."}


async def test_genero_id_no_entero_da_422(client):
    assert (await client.get("/generos/abc/libros")).status_code == 422


async def test_libros_de_genero_paginados_con_total_y_pagina_inexistente(client):
    e = await editorial(client, "E")
    g = await genero(client, "G")
    ids = [await libro(client, f"L{i}", e, g) for i in range(4)]
    r = await client.get(f"/generos/{g}/libros", params={"size": 2, "page": 2})
    pagina = r.json()
    assert [l["id"] for l in pagina["items"]] == ids[2:]
    assert (pagina["total"], pagina["page"], pagina["size"], pagina["pages"]) == (4, 2, 2, 2)
    r = await client.get(f"/generos/{g}/libros", params={"size": 2, "page": 3})
    assert r.status_code == 422
    assert "La página 3 no existe: hay 2" in r.text


async def test_libros_de_genero_excluye_los_dados_de_baja_y_el_total_los_excluye(client, sessionmaker_test):
    e = await editorial(client, "E")
    g = await genero(client, "G")
    visible = await libro(client, "V", e, g)
    baja = await libro(client, "B", e, g)
    await dar_de_baja_por_sql(sessionmaker_test, baja)
    r = await client.get(f"/generos/{g}/libros", params={"size": 1})
    assert [l["id"] for l in r.json()["items"]] == [visible]
    assert (r.json()["total"], r.json()["pages"]) == (1, 1)


async def test_libros_de_genero_emiten_las_mismas_consultas_con_1_o_5_libros(client, sessionmaker_test):
    e = await editorial(client, "E")
    g1, g5 = await genero(client, "G1"), await genero(client, "G5")
    await libro(client, "Q0", e, g1)
    for i in range(5):
        await libro(client, f"Q{i + 1}", e, g5)
    n1, d1 = await contar_consultas(client, sessionmaker_test, f"/generos/{g1}/libros")
    n5, d5 = await contar_consultas(client, sessionmaker_test, f"/generos/{g5}/libros")
    assert (d1["total"], d5["total"]) == (1, 5)
    assert n1 == n5
