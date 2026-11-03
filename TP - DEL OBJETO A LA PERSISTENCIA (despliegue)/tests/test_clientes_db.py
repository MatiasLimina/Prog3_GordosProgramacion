"""Endpoints de clientes con base real."""
import pytest

pytestmark = pytest.mark.db


async def crear_cliente(client, nombre="Ana Pérez", email="ana@example.com"):
    r = await client.post("/clientes/", json={"nombre": nombre, "email": email})
    assert r.status_code == 201, r.text
    return r.json()


async def crear_libro(client, isbn="ISBN-1", precio="1000.00", stock=10):
    e = (await client.post("/editoriales/", json={"nombre": "E", "pais": "AR"})).json()["id"]
    r = await client.post(
        "/libros/",
        json={"isbn": isbn, "titulo": f"T {isbn}", "precio": precio, "stock": stock, "editorial_id": e},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


# --- alta ---

async def test_alta_cliente_201(client):
    r = await client.post("/clientes/", json={"nombre": "Ana Pérez", "email": "ana@example.com"})
    assert r.status_code == 201
    assert r.json() == {"id": 1, "nombre": "Ana Pérez", "email": "ana@example.com"}


async def test_alta_cliente_email_repetido_409(client):
    await crear_cliente(client)
    r = await client.post("/clientes/", json={"nombre": "Otra", "email": "ana@example.com"})
    assert r.status_code == 409
    assert r.json() == {"detail": "Ya existe un cliente con ese email."}


@pytest.mark.parametrize(
    "body",
    [
        {"nombre": "Ana", "email": "no-es-email"},
        {"nombre": "", "email": "a@example.com"},
        {"email": "a@example.com"},
        {"nombre": "Ana", "email": "a@example.com", "id": 7},
    ],
)
async def test_alta_cliente_contrato_invalido_422(client, body):
    r = await client.post("/clientes/", json=body)
    assert r.status_code == 422


# --- detalle ---

async def test_get_cliente_sin_perfil_devuelve_perfil_null(client):
    c = await crear_cliente(client)
    r = await client.get(f"/clientes/{c['id']}")
    assert r.status_code == 200
    assert r.json() == {"id": 1, "nombre": "Ana Pérez", "email": "ana@example.com", "perfil": None}


async def test_get_cliente_con_perfil(client):
    c = await crear_cliente(client)
    await client.post(f"/clientes/{c['id']}/perfil", json={"telefono": "11 2233", "direccion": "Calle 1"})
    r = await client.get(f"/clientes/{c['id']}")
    assert r.status_code == 200
    assert r.json()["perfil"] == {
        "id": 1, "cliente_id": 1, "telefono": "11 2233", "direccion": "Calle 1"
    }


async def test_get_cliente_inexistente_404(client):
    r = await client.get("/clientes/999")
    assert r.status_code == 404
    assert r.json() == {"detail": "El cliente no existe."}


async def test_get_cliente_id_invalido_422(client):
    assert (await client.get("/clientes/0")).status_code == 422


# --- listado ---

async def test_listado_clientes_paginado(client):
    for i in range(3):
        await crear_cliente(client, nombre=f"C{i}", email=f"c{i}@example.com")
    r = await client.get("/clientes/", params={"limit": 2})
    assert [c["id"] for c in r.json()] == [1, 2]
    r = await client.get("/clientes/", params={"limit": 2, "offset": 2})
    assert [c["id"] for c in r.json()] == [3]


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
async def test_listado_clientes_limites_422(client, params):
    assert (await client.get("/clientes/", params=params)).status_code == 422


# --- PATCH ---

async def test_patch_parcial_solo_cambia_lo_enviado(client):
    await crear_cliente(client)
    r = await client.patch("/clientes/1", json={"nombre": "Ana María"})
    assert r.status_code == 200
    assert r.json() == {"id": 1, "nombre": "Ana María", "email": "ana@example.com", "perfil": None}
    r = await client.patch("/clientes/1", json={"email": "nuevo@example.com"})
    assert r.json()["email"] == "nuevo@example.com"
    assert r.json()["nombre"] == "Ana María"


async def test_patch_email_de_otro_cliente_409(client):
    await crear_cliente(client)
    await crear_cliente(client, nombre="Beto", email="beto@example.com")
    r = await client.patch("/clientes/2", json={"email": "ana@example.com"})
    assert r.status_code == 409
    assert r.json() == {"detail": "Ya existe un cliente con ese email."}


async def test_patch_inexistente_404(client):
    r = await client.patch("/clientes/999", json={"nombre": "X"})
    assert r.status_code == 404


@pytest.mark.parametrize("body", [{"nombre": None}, {"email": None}, {"email": "mal"}])
async def test_patch_contrato_invalido_422(client, body):
    await crear_cliente(client)
    assert (await client.patch("/clientes/1", json=body)).status_code == 422


async def test_patch_vacio_no_cambia_nada(client):
    await crear_cliente(client)
    r = await client.patch("/clientes/1", json={})
    assert r.status_code == 200
    assert r.json()["nombre"] == "Ana Pérez"


# --- perfil ---

async def test_crear_perfil_201(client):
    await crear_cliente(client)
    r = await client.post("/clientes/1/perfil", json={"telefono": "11 2233", "direccion": "Calle 1"})
    assert r.status_code == 201
    assert r.json() == {"id": 1, "cliente_id": 1, "telefono": "11 2233", "direccion": "Calle 1"}


async def test_segundo_perfil_409(client):
    await crear_cliente(client)
    body = {"telefono": "11 2233", "direccion": "Calle 1"}
    assert (await client.post("/clientes/1/perfil", json=body)).status_code == 201
    r = await client.post("/clientes/1/perfil", json={"telefono": "99", "direccion": "Otra"})
    assert r.status_code == 409
    assert r.json() == {"detail": "El cliente ya tiene un perfil."}


async def test_perfil_de_cliente_inexistente_404(client):
    r = await client.post("/clientes/999/perfil", json={"telefono": "1", "direccion": "d"})
    assert r.status_code == 404
    assert r.json() == {"detail": "El cliente no existe."}


@pytest.mark.parametrize("body", [{"telefono": "1"}, {"direccion": "d"}, {"telefono": "", "direccion": "d"}])
async def test_perfil_contrato_invalido_422(client, body):
    await crear_cliente(client)
    assert (await client.post("/clientes/1/perfil", json=body)).status_code == 422


# --- ventas de cliente ---

async def test_ventas_de_cliente_inexistente_404(client):
    r = await client.get("/clientes/999/ventas")
    assert r.status_code == 404
    assert r.json() == {"detail": "El cliente no existe."}


async def test_ventas_de_cliente_sin_ventas_lista_vacia(client):
    await crear_cliente(client)
    r = await client.get("/clientes/1/ventas")
    assert r.status_code == 200
    assert r.json() == []


async def test_ventas_de_cliente_solo_las_suyas_y_paginadas(client):
    await crear_cliente(client)
    await crear_cliente(client, nombre="Beto", email="beto@example.com")
    libro = await crear_libro(client)
    for cliente_id in (1, 1, 2, 1):
        r = await client.post(
            "/ventas/", json={"cliente_id": cliente_id, "renglones": [{"libro_id": libro, "cantidad": 1}]}
        )
        assert r.status_code == 201, r.text
    r = await client.get("/clientes/1/ventas")
    assert [v["id"] for v in r.json()] == [1, 2, 4]
    assert all(v["cliente"]["id"] == 1 for v in r.json())
    assert r.json()[0]["renglones"][0]["titulo"] == "T ISBN-1"
    r = await client.get("/clientes/1/ventas", params={"limit": 2, "offset": 1})
    assert [v["id"] for v in r.json()] == [2, 4]
    assert (await client.get("/clientes/1/ventas", params={"limit": 0})).status_code == 422
    assert (await client.get("/clientes/1/ventas", params={"limit": 101})).status_code == 422
