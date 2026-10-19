import pytest

pytestmark = pytest.mark.db


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
        "stock": 4,
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
    r = await client.patch("/libros/999999999", json={"stock": 10})
    assert r.status_code == 404


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


# --- busqueda por titulo con parametro ligado (RN-11) ---

async def test_busqueda_titulo_con_inyeccion_da_200_vacia(client):
    e = await editorial(client)
    a = await autor(client)
    r = await client.post("/libros/", json=cuerpo_libro("ISBN-B", e, a))
    assert r.status_code == 201, r.text
    r = await client.get("/libros/", params={"titulo": "' OR '1'='1"})
    assert r.status_code == 200
    assert r.json() == []
    r = await client.get("/libros/", params={"titulo": "isbn-b"})
    assert r.status_code == 200
    assert len(r.json()) == 1


# --- PATCH de editorial y género: la respuesta refleja el valor nuevo ---

async def test_patch_editorial_id_devuelve_la_editorial_nueva(client):
    e1 = await editorial(client, "Editorial Uno")
    e2 = await editorial(client, "Editorial Dos")
    a = await autor(client)
    libro_id = (await client.post("/libros/", json=cuerpo_libro("ISBN-PE", e1, a))).json()["id"]
    r = await client.patch(f"/libros/{libro_id}", json={"editorial_id": e2})
    assert r.status_code == 200, r.text
    assert r.json()["editorial"]["id"] == e2
    assert r.json()["editorial"]["nombre"] == "Editorial Dos"
    r = await client.get(f"/libros/{libro_id}")
    assert r.json()["editorial"]["id"] == e2


async def test_patch_genero_id_devuelve_el_genero_nuevo(client):
    e = await editorial(client)
    a = await autor(client)
    g1 = (await client.post("/generos/", json={"nombre": "Novela"})).json()["id"]
    g2 = (await client.post("/generos/", json={"nombre": "Cuento"})).json()["id"]
    libro_id = (await client.post("/libros/", json=cuerpo_libro("ISBN-PG", e, a, genero_id=g1))).json()["id"]
    r = await client.patch(f"/libros/{libro_id}", json={"genero_id": g2})
    assert r.status_code == 200, r.text
    assert r.json()["genero"]["id"] == g2
    assert r.json()["genero"]["nombre"] == "Cuento"


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

async def test_servicio_actualizar_en_misma_sesion_refleja_editorial_y_genero_nuevos(client, sessionmaker_test):
    from app.modules.libros import service
    from app.modules.libros.schemas import LibroCreate, LibroUpdate

    e1 = await editorial(client, "Editorial Uno")
    e2 = await editorial(client, "Editorial Dos")
    a = await autor(client)
    g1 = (await client.post("/generos/", json={"nombre": "Novela"})).json()["id"]
    g2 = (await client.post("/generos/", json={"nombre": "Cuento"})).json()["id"]
    async with sessionmaker_test() as session:
        creado = await service.crear(
            session,
            LibroCreate(
                isbn="ISBN-S", titulo="T", precio="10.00", stock=1, editorial_id=e1, genero_id=g1,
                autores=[{"autor_id": a, "rol": "autor", "orden": 1}],
            ),
        )
        assert creado.autores[0].nombre == "Jorge Luis Borges"
        assert creado.editorial.nombre == "Editorial Uno"
        cambiado = await service.actualizar(session, creado.id, LibroUpdate(editorial_id=e2, genero_id=g2))
    assert cambiado.editorial.id == e2 and cambiado.editorial.nombre == "Editorial Dos"
    assert cambiado.genero.id == g2 and cambiado.genero.nombre == "Cuento"
