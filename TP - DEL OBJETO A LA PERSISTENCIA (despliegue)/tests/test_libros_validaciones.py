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


# --- enteros fuera de int32 (ids y stock) ---

GIGANTE = 99_999_999_999


@pytest.mark.parametrize(
    "ruta",
    [
        f"/editoriales/{GIGANTE}",
        f"/editoriales/{GIGANTE}/libros",
        f"/generos/{GIGANTE}/libros",
        f"/autores/{GIGANTE}",
        f"/autores/{GIGANTE}/libros",
        f"/libros/{GIGANTE}",
        "/editoriales/0",
        "/libros/0",
        "/libros/-1",
        "/editoriales/abc",  # C-01 sigue igual
        "/libros/abc",
    ],
)
async def test_path_param_invalido_da_422(client, ruta):
    assert (await client.get(ruta)).status_code == 422


async def test_patch_con_id_gigante_da_422(client):
    for ruta in (f"/editoriales/{GIGANTE}", f"/libros/{GIGANTE}", f"/autores/{GIGANTE}"):
        assert (await client.patch(ruta, json={})).status_code == 422


async def test_id_maximo_int32_pasa_la_validacion_y_da_404(client):
    assert (await client.get("/editoriales/2147483647")).status_code == 404
    assert (await client.get("/libros/2147483647")).status_code == 404


@pytest.mark.parametrize(
    "extra",
    [{"editorial_id": GIGANTE}, {"genero_id": GIGANTE}, {"stock": GIGANTE}, {"stock": -1},
     {"autores": [{"autor_id": GIGANTE, "rol": "autor", "orden": 1}]},
     {"autores": [{"autor_id": 1, "rol": "autor", "orden": 0}]}],
)
async def test_post_libro_con_enteros_invalidos_da_422(client, extra):
    e = await base(client)
    body = cuerpo(e)
    body.update(extra)
    assert (await client.post("/libros/", json=body)).status_code == 422


async def test_patch_libro_con_enteros_invalidos_da_422(client):
    e = await base(client)
    await client.post("/libros/", json=cuerpo(e))
    for body in ({"editorial_id": GIGANTE}, {"genero_id": GIGANTE}, {"stock": GIGANTE}, {"stock": -1}):
        assert (await client.patch("/libros/1", json=body)).status_code == 422


async def test_filtro_genero_id_gigante_en_listado_da_422(client):
    assert (await client.get("/libros/", params={"genero_id": GIGANTE})).status_code == 422
