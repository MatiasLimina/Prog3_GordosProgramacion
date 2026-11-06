"""Autores por HTTP (CHG-13): alta, detalle, PATCH, listado con envoltorio y libros vigentes del autor."""
import pytest
from sqlalchemy import event, text

from tests.auxiliares_auth import entrar_como

pytestmark = pytest.mark.db


@pytest.fixture
async def client(client, sessionmaker_test):
    """Sesión de ADMIN: las escrituras del catálogo son del grupo protegido (CHG-12)."""
    await entrar_como(client, sessionmaker_test, "ADMIN")
    return client


async def crear_autor(client, nombre="Jorge Luis Borges", nacionalidad="Argentina"):
    r = await client.post("/autores/", json={"nombre": nombre, "nacionalidad": nacionalidad})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def crear_editorial(client):
    r = await client.post("/editoriales/", json={"nombre": "Eterna Cadencia", "pais": "Argentina"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def crear_libro(client, isbn, editorial_id, autores):
    body = {
        "isbn": isbn,
        "titulo": f"Titulo {isbn}",
        "precio": "100.00",
        "stock_inicial": 1,
        "editorial_id": editorial_id,
        "autores": [{"autor_id": a, "rol": rol, "orden": orden} for a, rol, orden in autores],
    }
    r = await client.post("/libros/", json=body)
    assert r.status_code == 201, r.text
    return r.json()["id"]


# --- alta y detalle ---

async def test_post_crea_con_201_y_devuelve_id(client):
    r = await client.post("/autores/", json={"nombre": "Borges", "nacionalidad": "Argentina"})
    assert r.status_code == 201
    assert r.json() == {"id": 1, "nombre": "Borges", "nacionalidad": "Argentina"}


async def test_post_con_campo_extra_da_422_y_no_crea_nada(client):
    # BREAKING (CHG-13): antes se ignoraba el campo; ahora el contrato de entrada es `extra="forbid"`.
    r = await client.post("/autores/", json={"id": 9, "nombre": "A", "nacionalidad": "B"})
    assert r.status_code == 422
    assert (await client.get("/autores/")).json()["total"] == 0


async def test_get_por_id_200_y_404(client):
    a = await crear_autor(client)
    r = await client.get(f"/autores/{a}")
    assert r.status_code == 200
    assert r.json() == {"id": a, "nombre": "Jorge Luis Borges", "nacionalidad": "Argentina"}
    r = await client.get("/autores/999")
    assert r.status_code == 404
    assert r.json() == {"detail": "El autor no existe."}


# --- PATCH ---

async def test_patch_parcial_solo_cambia_lo_enviado(client):
    a = await crear_autor(client)
    r = await client.patch(f"/autores/{a}", json={"nacionalidad": "Uruguaya"})
    assert r.status_code == 200
    assert r.json() == {"id": a, "nombre": "Jorge Luis Borges", "nacionalidad": "Uruguaya"}
    assert (await client.get(f"/autores/{a}")).json()["nacionalidad"] == "Uruguaya"


async def test_patch_vacio_no_cambia_nada(client):
    a = await crear_autor(client)
    r = await client.patch(f"/autores/{a}", json={})
    assert r.status_code == 200
    assert r.json() == {"id": a, "nombre": "Jorge Luis Borges", "nacionalidad": "Argentina"}


async def test_patch_inexistente_da_404(client):
    r = await client.patch("/autores/999", json={"nombre": "X"})
    assert r.status_code == 404
    assert r.json() == {"detail": "El autor no existe."}


@pytest.mark.parametrize("body", [{"id": 5}, {"nombre": "X", "otro": 1}])
async def test_patch_con_campo_extra_da_422_y_no_modifica(client, body):
    a = await crear_autor(client)
    assert (await client.patch(f"/autores/{a}", json=body)).status_code == 422
    assert (await client.get(f"/autores/{a}")).json()["nombre"] == "Jorge Luis Borges"


async def test_patch_con_null_explicito_da_422(client):
    a = await crear_autor(client)
    assert (await client.patch(f"/autores/{a}", json={"nombre": None})).status_code == 422


# --- listado con envoltorio ---

async def test_listado_responde_con_el_envoltorio_ordenado_por_id(client):
    for n in "ABC":
        await crear_autor(client, n)
    r = await client.get("/autores/", params={"size": 2})
    assert r.status_code == 200
    datos = r.json()
    assert set(datos) == {"items", "total", "page", "size", "pages"}
    assert (datos["total"], datos["page"], datos["size"], datos["pages"]) == (3, 1, 2, 2)
    assert [a["nombre"] for a in datos["items"]] == ["A", "B"]


async def test_listado_pagina_fuera_de_rango_da_422_y_vacio_tiene_una_pagina(client):
    assert (await client.get("/autores/")).json() == {"items": [], "total": 0, "page": 1, "size": 20, "pages": 1}
    await crear_autor(client)
    r = await client.get("/autores/", params={"page": 2})
    assert r.status_code == 422
    assert "La página 2 no existe: hay 1" in r.text
    assert (await client.get("/autores/", params={"size": 101})).status_code == 422


# --- libros vigentes de un autor ---

async def test_libros_de_autor_con_envoltorio_orden_rol_y_solo_vigentes(client, sessionmaker_test):
    e = await crear_editorial(client)
    a = await crear_autor(client)
    otro = await crear_autor(client, "Otro")
    segundo = await crear_libro(client, "L2", e, [(a, "coautor", 2), (otro, "autor", 1)])
    primero = await crear_libro(client, "L1", e, [(a, "autor", 1)])
    baja = await crear_libro(client, "LB", e, [(a, "autor", 1)])
    await crear_libro(client, "LO", e, [(otro, "autor", 2)])  # de otro autor: no aparece
    async with sessionmaker_test() as s:
        await s.execute(text("UPDATE libro SET borrado_en = now() WHERE id = :i"), {"i": baja})
        await s.commit()
    r = await client.get(f"/autores/{a}/libros")
    assert r.status_code == 200
    pagina = r.json()
    assert set(pagina) == {"items", "total", "page", "size", "pages"}
    assert (pagina["total"], pagina["pages"]) == (2, 1)  # el dado de baja no cuenta
    assert [(l["id"], l["rol"], l["orden"]) for l in pagina["items"]] == [
        (primero, "autor", 1),
        (segundo, "coautor", 2),
    ]


async def test_libros_de_autor_total_con_el_filtro_aunque_la_pagina_sea_chica(client, sessionmaker_test):
    e = await crear_editorial(client)
    a = await crear_autor(client)
    for i in range(3):
        await crear_libro(client, f"L{i}", e, [(a, "autor", i + 1)])
    async with sessionmaker_test() as s:
        await s.execute(text("UPDATE libro SET borrado_en = now() WHERE isbn = 'L2'"))
        await s.commit()
    r = await client.get(f"/autores/{a}/libros", params={"size": 1, "page": 2})
    assert r.status_code == 200
    assert (r.json()["total"], r.json()["pages"]) == (2, 2)
    r = await client.get(f"/autores/{a}/libros", params={"size": 1, "page": 3})
    assert r.status_code == 422


async def test_autor_sin_libros_da_pagina_vacia_y_autor_inexistente_404(client):
    a = await crear_autor(client)
    r = await client.get(f"/autores/{a}/libros")
    assert r.json() == {"items": [], "total": 0, "page": 1, "size": 20, "pages": 1}
    r = await client.get("/autores/999/libros")
    assert r.status_code == 404
    assert r.json() == {"detail": "El autor no existe."}


async def test_libros_de_autor_emiten_las_mismas_consultas_con_1_o_5_libros(client, sessionmaker_test):
    e = await crear_editorial(client)
    a1, a5 = await crear_autor(client, "Uno"), await crear_autor(client, "Cinco")
    await crear_libro(client, "Q0", e, [(a1, "autor", 1)])
    for i in range(5):
        await crear_libro(client, f"Q{i + 1}", e, [(a5, "autor", 1)])

    async def contar(ruta):
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
        return len(consultas), r.json(), consultas

    n1, d1, _ = await contar(f"/autores/{a1}/libros")
    n5, d5, sql5 = await contar(f"/autores/{a5}/libros")
    assert (d1["total"], d5["total"]) == (1, 5)
    assert n1 == n5
    # Un solo JOIN a `libro` por consulta de listado: el mismo sirve para filtrar y para precargar.
    listados = [q for q in sql5 if "FROM libro_autor" in q]
    assert listados and all(q.count("JOIN libro ") == 1 for q in listados), listados


async def test_libros_de_autor_con_el_mismo_orden_se_desempatan_por_id(client):
    e = await crear_editorial(client)
    a = await crear_autor(client)
    primero = await crear_libro(client, "T1", e, [(a, "autor", 1)])
    segundo = await crear_libro(client, "T2", e, [(a, "autor", 1)])
    # Caracterizacion: el orden total ya lo da `_listar` (clave primaria al final).
    r = await client.get(f"/autores/{a}/libros")
    assert [l["id"] for l in r.json()["items"]] == [primero, segundo]
