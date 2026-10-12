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
