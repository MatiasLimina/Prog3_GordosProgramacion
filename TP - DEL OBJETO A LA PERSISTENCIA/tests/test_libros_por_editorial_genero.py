import pytest

pytestmark = pytest.mark.db


async def editorial(client, nombre):
    return (await client.post("/editoriales/", json={"nombre": nombre, "pais": "AR"})).json()["id"]


async def genero(client, nombre):
    return (await client.post("/generos/", json={"nombre": nombre})).json()["id"]


async def libro(client, isbn, editorial_id, genero_id=None):
    body = {"isbn": isbn, "titulo": f"Titulo {isbn}", "precio": "10.50", "stock": 1, "editorial_id": editorial_id}
    if genero_id is not None:
        body["genero_id"] = genero_id
    r = await client.post("/libros/", json=body)
    assert r.status_code == 201, r.text
    return r.json()["id"]


# --- editoriales ---

async def test_libros_de_una_editorial_no_incluye_los_de_otra(client):
    e1, e2 = await editorial(client, "E1"), await editorial(client, "E2")
    g = await genero(client, "Novela")
    a = await libro(client, "A", e1, g)
    b = await libro(client, "B", e1)
    await libro(client, "C", e2)
    r = await client.get(f"/editoriales/{e1}/libros")
    assert r.status_code == 200
    datos = r.json()
    assert [l["id"] for l in datos] == [a, b]
    assert datos[0]["editorial"]["nombre"] == "E1"
    assert datos[0]["genero"]["nombre"] == "Novela"
    assert datos[1]["genero"] is None


async def test_editorial_sin_libros_da_lista_vacia(client):
    e = await editorial(client, "Vacia")
    r = await client.get(f"/editoriales/{e}/libros")
    assert r.status_code == 200
    assert r.json() == []


async def test_editorial_inexistente_da_404_propio(client):
    r = await client.get("/editoriales/999/libros")
    assert r.status_code == 404
    assert r.json() == {"detail": "La editorial no existe."}


async def test_editorial_id_no_entero_da_422(client):
    assert (await client.get("/editoriales/abc/libros")).status_code == 422


async def test_libros_de_editorial_paginados(client):
    e = await editorial(client, "E")
    ids = [await libro(client, f"L{i}", e) for i in range(4)]
    r = await client.get(f"/editoriales/{e}/libros", params={"limit": 2, "offset": 1})
    assert [l["id"] for l in r.json()] == ids[1:3]
    assert (await client.get(f"/editoriales/{e}/libros", params={"limit": 0})).status_code == 422


async def test_libros_de_editorial_sin_lazy_loading_cantidad_fija_de_consultas(client, sessionmaker_test):
    from sqlalchemy import event

    e = await editorial(client, "E")
    g = await genero(client, "G")
    for i in range(3):
        await libro(client, f"Q{i}", e, g)
    consultas = []

    def contar(conn, cursor, statement, *a):
        consultas.append(statement)

    engine = sessionmaker_test.kw["bind"].sync_engine
    event.listen(engine, "before_cursor_execute", contar)
    try:
        await client.get(f"/editoriales/{e}/libros")
        con_3 = len(consultas)
        for i in range(3, 6):
            await libro(client, f"Q{i}", e, g)
        consultas.clear()
        await client.get(f"/editoriales/{e}/libros")
        con_6 = len(consultas)
    finally:
        event.remove(engine, "before_cursor_execute", contar)
    assert con_3 == con_6


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
    datos = r.json()
    assert [l["id"] for l in datos] == [a, b]
    assert all(l["genero"]["nombre"] == "G1" and l["editorial"]["nombre"] == "E" for l in datos)


async def test_genero_sin_libros_da_lista_vacia(client):
    g = await genero(client, "Vacio")
    r = await client.get(f"/generos/{g}/libros")
    assert r.status_code == 200
    assert r.json() == []


async def test_genero_inexistente_da_404_propio(client):
    r = await client.get("/generos/999/libros")
    assert r.status_code == 404
    assert r.json() == {"detail": "El género no existe."}


async def test_genero_id_no_entero_da_422(client):
    assert (await client.get("/generos/abc/libros")).status_code == 422


async def test_libros_de_genero_paginados(client):
    e = await editorial(client, "E")
    g = await genero(client, "G")
    ids = [await libro(client, f"L{i}", e, g) for i in range(4)]
    r = await client.get(f"/generos/{g}/libros", params={"limit": 2, "offset": 2})
    assert [l["id"] for l in r.json()] == ids[2:]
