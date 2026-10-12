import pytest

pytestmark = pytest.mark.db


async def base(client):
    e = (await client.post("/editoriales/", json={"nombre": "E", "pais": "AR"})).json()["id"]
    return e


def cuerpo(editorial_id, **extra):
    d = {"isbn": "X1", "titulo": "T", "precio": "10.50", "stock": 1, "editorial_id": editorial_id}
    d.update(extra)
    return d


# --- precio contra Numeric(10,2) ---

@pytest.mark.parametrize("precio", ["123456789012.00", "10.999", "100000000.00"])
async def test_post_precio_fuera_de_numeric_10_2_da_422(client, precio):
    e = await base(client)
    r = await client.post("/libros/", json=cuerpo(e, precio=precio))
    assert r.status_code == 422


@pytest.mark.parametrize("precio", ["123456789012.00", "10.999"])
async def test_patch_precio_fuera_de_numeric_10_2_da_422(client, precio):
    e = await base(client)
    await client.post("/libros/", json=cuerpo(e))
    r = await client.patch("/libros/1", json={"precio": precio})
    assert r.status_code == 422


@pytest.mark.parametrize("precio", ["10.50", "99999999.99", "0.01"])
async def test_precio_valido_sigue_dando_201(client, precio):
    e = await base(client)
    r = await client.post("/libros/", json=cuerpo(e, precio=precio))
    assert r.status_code == 201
    assert r.json()["precio"] == precio
