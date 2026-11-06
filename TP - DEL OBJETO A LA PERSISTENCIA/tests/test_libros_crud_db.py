import pytest

from tests.auxiliares_auth import entrar_como, filas

pytestmark = pytest.mark.db

@pytest.fixture
async def client(client, sessionmaker_test):
    """Sesión de ADMIN: las escrituras del catálogo, clientes y ventas son del grupo protegido (CHG-12)."""
    await entrar_como(client, sessionmaker_test, "ADMIN")
    return client


async def editorial(client, nombre="Eterna Cadencia"):
    r = await client.post("/editoriales/", json={"nombre": nombre, "pais": "Argentina"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def autor(client, nombre="Jorge Luis Borges"):
    r = await client.post("/autores/", json={"nombre": nombre, "nacionalidad": "Argentina"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def cuerpo_libro(isbn, editorial_id, autor_id, **extra):
    body = {
        "isbn": isbn,
        "titulo": f"Titulo {isbn}",
        "precio": "25000.00",
        "stock_inicial": 4,
        "editorial_id": editorial_id,
        "autores": [{"autor_id": autor_id, "rol": "autor", "orden": 1}],
    }
    body.update(extra)
    return body


# --- alta con relaciones (Ejercicio 5) ---

async def test_alta_libro_con_autor_devuelve_detalle_completo(client):
    e = await editorial(client)
    a = await autor(client)
    r = await client.post("/libros/", json=cuerpo_libro("ISBN-1", e, a))
    assert r.status_code == 201, r.text
    datos = r.json()
    assert datos["isbn"] == "ISBN-1"
    assert datos["precio"] == "25000.00"
    assert datos["editorial"]["id"] == e
    assert datos["editorial"]["nombre"] == "Eterna Cadencia"
    assert datos["genero"] is None
    assert len(datos["autores"]) == 1
    autoria = datos["autores"][0]
    assert autoria["autor_id"] == a
    assert autoria["nombre"] == "Jorge Luis Borges"
    assert autoria["rol"] == "autor"
    assert autoria["orden"] == 1


async def test_alta_isbn_repetido_da_409_con_mensaje_propio(client):
    e = await editorial(client)
    a = await autor(client)
    r = await client.post("/libros/", json=cuerpo_libro("ISBN-DUP", e, a))
    assert r.status_code == 201, r.text
    r = await client.post("/libros/", json=cuerpo_libro("ISBN-DUP", e, a))
    assert r.status_code == 409
    assert r.json() == {"detail": "Ya existe un libro con ese ISBN."}


async def test_alta_con_editorial_inexistente_da_409(client):
    a = await autor(client)
    r = await client.post("/libros/", json=cuerpo_libro("ISBN-FK-E", 999999999, a))
    assert r.status_code == 409
    assert r.json() == {"detail": "La editorial indicada no existe."}


async def test_alta_con_autor_inexistente_da_409(client):
    e = await editorial(client)
    r = await client.post("/libros/", json=cuerpo_libro("ISBN-FK-A", e, 999999999))
    assert r.status_code == 409
    assert r.json() == {"detail": "Uno de los autores indicados no existe."}


# --- PATCH parcial ---

async def test_patch_parcial_solo_cambia_lo_enviado(client):
    e = await editorial(client)
    a = await autor(client)
    libro_id = (await client.post("/libros/", json=cuerpo_libro("ISBN-P", e, a))).json()["id"]
    r = await client.patch(f"/libros/{libro_id}", json={"precio": "26000.00"})
    assert r.status_code == 200, r.text
    datos = r.json()
    assert datos["precio"] == "26000.00"
    assert datos["titulo"] == "Titulo ISBN-P"
    assert datos["isbn"] == "ISBN-P"


async def test_patch_precio_invalido_da_422(client):
    e = await editorial(client)
    a = await autor(client)
    libro_id = (await client.post("/libros/", json=cuerpo_libro("ISBN-P2", e, a))).json()["id"]
    r = await client.patch(f"/libros/{libro_id}", json={"precio": "0"})
    assert r.status_code == 422


async def test_patch_libro_inexistente_da_404(client):
    r = await client.patch("/libros/999999999", json={"titulo": "Nuevo titulo"})
    assert r.status_code == 404


async def test_patch_solo_precio_no_cambia_titulo_ni_stock(client):
    e = await editorial(client)
    a = await autor(client)
    creado = (await client.post("/libros/", json=cuerpo_libro("ISBN-PS", e, a, stock_inicial=4))).json()
    r = await client.patch(f"/libros/{creado['id']}", json={"precio": "26000.00"})
    assert r.status_code == 200, r.text
    assert (r.json()["titulo"], r.json()["stock"], r.json()["precio"]) == (creado["titulo"], 4, "26000.00")


async def test_patch_con_stock_da_422_y_el_stock_no_cambia(client):
    e = await editorial(client)
    a = await autor(client)
    libro_id = (await client.post("/libros/", json=cuerpo_libro("ISBN-PK", e, a, stock_inicial=4))).json()["id"]
    assert (await client.patch(f"/libros/{libro_id}", json={"stock": 99})).status_code == 422
    assert (await client.get(f"/libros/{libro_id}")).json()["stock"] == 4


async def test_patch_de_un_libro_dado_de_baja_da_404_y_no_lo_modifica(client, sessionmaker_test):
    from sqlalchemy import text

    e = await editorial(client)
    a = await autor(client)
    libro_id = (await client.post("/libros/", json=cuerpo_libro("ISBN-PB", e, a))).json()["id"]
    async with sessionmaker_test() as s:
        await s.execute(text("UPDATE libro SET borrado_en = now() WHERE id = :i"), {"i": libro_id})
        await s.commit()
    r = await client.patch(f"/libros/{libro_id}", json={"titulo": "Nuevo titulo"})
    assert r.status_code == 404
    assert r.json() == {"detail": "El libro no existe."}
    async with sessionmaker_test() as s:
        titulo = (await s.execute(text("SELECT titulo FROM libro WHERE id = :i"), {"i": libro_id})).scalar_one()
    assert titulo == "Titulo ISBN-PB"


# --- libros de un autor, paginados (RN-10) ---

async def test_libros_de_autor_paginados(client):
    e = await editorial(client)
    a = await autor(client)
    ids = []
    for i in range(3):
        body = cuerpo_libro(f"ISBN-A{i}", e, a)
        body["autores"][0]["orden"] = i + 1
        r = await client.post("/libros/", json=body)
        assert r.status_code == 201, r.text
        ids.append(r.json()["id"])
    r = await client.get(f"/autores/{a}/libros", params={"limit": 2, "offset": 1})
    assert r.status_code == 200
    datos = r.json()
    assert [l["id"] for l in datos] == ids[1:3]
    assert datos[0]["rol"] == "autor"
    assert (await client.get(f"/autores/{a}/libros", params={"limit": 200})).status_code == 422
    r = await client.get("/autores/999999999/libros")
    assert r.status_code == 404
    assert r.json() == {"detail": "El autor no existe."}


# --- listado con envoltorio y búsqueda por titulo con parametro ligado (RN-11, C-16) ---

async def genero(client, nombre="Ficción"):
    r = await client.post("/generos/", json={"nombre": nombre})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def libro(client, isbn, e, a, titulo, **extra):
    r = await client.post("/libros/", json=cuerpo_libro(isbn, e, a, titulo=titulo, **extra))
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def test_listado_de_libros_responde_con_el_envoltorio(client):
    e = await editorial(client)
    a = await autor(client)
    for i in range(3):
        await libro(client, f"ISBN-L{i}", e, a, f"Libro {i}")
    r = await client.get("/libros/", params={"size": 2})
    assert r.status_code == 200
    datos = r.json()
    assert set(datos) == {"items", "total", "page", "size", "pages"}
    assert (datos["total"], datos["page"], datos["size"], datos["pages"]) == (3, 1, 2, 2)
    assert [l["titulo"] for l in datos["items"]] == ["Libro 0", "Libro 1"]
    assert datos["items"][0]["editorial"]["nombre"] == "Eterna Cadencia"
    r = await client.get("/libros/", params={"size": 2, "page": 2})
    assert [l["titulo"] for l in r.json()["items"]] == ["Libro 2"]


async def test_busqueda_titulo_con_inyeccion_da_200_con_el_envoltorio_vacio(client):
    e = await editorial(client)
    a = await autor(client)
    await libro(client, "ISBN-B", e, a, "Ficciones")
    r = await client.get("/libros/", params={"titulo": "' OR '1'='1"})
    assert r.status_code == 200
    datos = r.json()
    assert datos["items"] == [] and datos["total"] == 0 and datos["pages"] == 1
    r = await client.get("/libros/", params={"titulo": "ficc"})
    assert r.status_code == 200
    assert r.json()["total"] == 1


async def test_busqueda_por_titulo_pagina_con_el_total_del_filtro_y_rechaza_la_pagina_inexistente(client):
    e = await editorial(client)
    a = await autor(client)
    await libro(client, "ISBN-1", e, a, "Ficciones")
    await libro(client, "ISBN-2", e, a, "Otro")
    r = await client.get("/libros/", params={"titulo": "ficc", "size": 1})
    assert (r.json()["total"], r.json()["pages"]) == (1, 1)
    r = await client.get("/libros/", params={"titulo": "ficc", "size": 1, "page": 2})
    assert r.status_code == 422
    assert r.json() == {"detail": "La página 2 no existe: hay 1"}
    assert (await client.get("/libros/", params={"size": 500})).status_code == 422


async def test_busqueda_trata_los_comodines_como_texto(client):
    e = await editorial(client)
    a = await autor(client)
    await libro(client, "ISBN-1", e, a, "100% ficción")
    await libro(client, "ISBN-2", e, a, "1000 años")
    r = await client.get("/libros/", params={"titulo": "100%"})
    assert [l["titulo"] for l in r.json()["items"]] == ["100% ficción"]
    r = await client.get("/libros/", params={"titulo": "_000"})
    assert r.json()["total"] == 0  # el _ no es «cualquier carácter»


async def test_listado_filtra_por_genero(client):
    e = await editorial(client)
    a = await autor(client)
    g = await genero(client)
    await libro(client, "ISBN-1", e, a, "Con género", genero_id=g)
    await libro(client, "ISBN-2", e, a, "Sin género")
    r = await client.get("/libros/", params={"genero_id": g})
    assert [l["titulo"] for l in r.json()["items"]] == ["Con género"]
    assert r.json()["total"] == 1


async def test_un_libro_dado_de_baja_no_aparece_en_el_listado_ni_en_el_detalle(client, sessionmaker_test):
    from sqlalchemy import text

    e = await editorial(client)
    a = await autor(client)
    visible = await libro(client, "ISBN-1", e, a, "Visible")
    baja = await libro(client, "ISBN-2", e, a, "De baja")
    async with sessionmaker_test() as s:
        await s.execute(text("UPDATE libro SET borrado_en = now() WHERE id = :i"), {"i": baja})
        await s.commit()
    r = await client.get("/libros/")
    assert [l["id"] for l in r.json()["items"]] == [visible]
    assert r.json()["total"] == 1
    r = await client.get(f"/libros/{baja}")
    assert r.status_code == 404
    assert r.json() == {"detail": "El libro no existe."}


# --- PATCH de libro: sólo título y precio (RN-11); el resto es 422 ---

@pytest.mark.parametrize("campo", ["stock", "isbn", "editorial_id", "genero_id"])
async def test_patch_libro_con_campos_no_editables_da_422(client, campo):
    e = await editorial(client)
    a = await autor(client)
    libro_id = (await client.post("/libros/", json=cuerpo_libro("ISBN-PE", e, a))).json()["id"]
    r = await client.patch(f"/libros/{libro_id}", json={campo: 1})
    assert r.status_code == 422


# --- detalle de libro: cantidad de consultas fija (Ejercicio 6 / C-07) ---

async def test_detalle_de_libro_emite_las_mismas_consultas_con_1_o_3_autores(client, sessionmaker_test):
    from sqlalchemy import event

    e = await editorial(client)
    a1 = await autor(client, "Autor 1")
    a2 = await autor(client, "Autor 2")
    a3 = await autor(client, "Autor 3")
    l1 = (await client.post("/libros/", json=cuerpo_libro("ISBN-Q1", e, a1))).json()["id"]
    cuerpo3 = cuerpo_libro("ISBN-Q3", e, a1)
    cuerpo3["autores"] = [
        {"autor_id": a1, "rol": "autor", "orden": 1},
        {"autor_id": a2, "rol": "coautor", "orden": 2},
        {"autor_id": a3, "rol": "traductor", "orden": 3},
    ]
    r = await client.post("/libros/", json=cuerpo3)
    assert r.status_code == 201, r.text
    l3 = r.json()["id"]

    async def contar(ruta):
        sentencias = []

        def hook(conn, cursor, statement, *a):
            sentencias.append(statement)

        engine = sessionmaker_test.kw["bind"].sync_engine
        event.listen(engine, "before_cursor_execute", hook)
        try:
            r = await client.get(ruta)
        finally:
            event.remove(engine, "before_cursor_execute", hook)
        assert r.status_code == 200, r.text
        return len(sentencias), r.json()

    n1, d1 = await contar(f"/libros/{l1}")
    n3, d3 = await contar(f"/libros/{l3}")
    assert len(d1["autores"]) == 1 and len(d3["autores"]) == 3
    assert n1 == n3


# --- servicio en una misma sesión (identity map con instancias ya cargadas) ---
# Por HTTP cada petición usa una sesión nueva y el resultado depende de cuándo
# el recolector libera las instancias; en una sola sesión el defecto es determinista.

async def test_servicio_actualizar_en_misma_sesion_refleja_titulo_y_precio_nuevos(client, sessionmaker_test):
    from app.modules.libros import service
    from app.modules.libros.schemas import LibroCreate, LibroUpdate
    from app.modules.libros.unit_of_work import LibrosUoW

    e1 = await editorial(client, "Editorial Uno")
    a = await autor(client)
    uid = (await filas(sessionmaker_test, "SELECT id FROM usuario"))[0]["id"]  # el ADMIN de la fixture `client`
    async with sessionmaker_test() as session:
        uow = LibrosUoW(session)
        creado = await service.crear(
            uow,
            LibroCreate(
                isbn="ISBN-S", titulo="T", precio="10.00", stock_inicial=1, editorial_id=e1,
                autores=[{"autor_id": a, "rol": "autor", "orden": 1}],
            ),
            uid,
        )
        assert creado.autores[0].nombre == "Jorge Luis Borges"
        assert creado.editorial.nombre == "Editorial Uno"
        assert creado.stock == 1
        cambiado = await service.actualizar(uow, creado.id, LibroUpdate(titulo="T2", precio="12.00"))
    assert cambiado.titulo == "T2" and str(cambiado.precio) == "12.00"
    assert cambiado.editorial.id == e1
    assert cambiado.stock == 1
