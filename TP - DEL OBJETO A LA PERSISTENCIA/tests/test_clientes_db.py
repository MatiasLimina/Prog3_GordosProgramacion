"""Endpoints de clientes con base real."""
from contextlib import contextmanager

import pytest
from sqlalchemy import event

from tests.auxiliares_auth import entrar_como, filas, registrar

pytestmark = pytest.mark.db

@pytest.fixture
async def client(client, sessionmaker_test):
    """Sesión de ADMIN: las escrituras del catálogo, clientes y ventas son del grupo protegido (CHG-12)."""
    await entrar_como(client, sessionmaker_test, "ADMIN")
    return client


@contextmanager
def contar_sentencias(sessionmaker):
    """Lista que se llena con cada sentencia que llega a la base mientras dura el bloque."""
    sentencias: list[str] = []

    def hook(conn, cursor, statement, *args):
        sentencias.append(statement)

    engine = sessionmaker.kw["bind"].sync_engine
    event.listen(engine, "before_cursor_execute", hook)
    try:
        yield sentencias
    finally:
        event.remove(engine, "before_cursor_execute", hook)


async def registrar_cliente_con_cuenta(client, email="bea@example.com", nombre="Bea"):
    """Cliente con usuario vinculado, creado por el auto-registro (RN-02); devuelve el id del cliente."""
    r = await registrar(client, email=email, nombre=nombre)
    assert r.status_code == 201, r.text
    return (await client.get("/clientes/", params={"size": 100})).json()["items"][-1]["id"]


async def crear_cliente(client, nombre="Ana Pérez", email="ana@example.com"):
    r = await client.post("/clientes/", json={"nombre": nombre, "email": email})
    assert r.status_code == 201, r.text
    return r.json()


async def crear_libro(client, isbn="ISBN-1", precio="1000.00", stock=10):
    e = (await client.post("/editoriales/", json={"nombre": f"E {isbn}", "pais": "AR"})).json()["id"]
    r = await client.post(
        "/libros/",
        json={"isbn": isbn, "titulo": f"T {isbn}", "precio": precio, "stock_inicial": stock, "editorial_id": e},
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
    assert r.json() == {"detail": "Ya existe un cliente con ese correo."}


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
    for i in range(5):
        await crear_cliente(client, nombre=f"C{i}", email=f"c{i}@example.com")
    r = await client.get("/clientes/", params={"size": 2, "page": 2})
    assert r.status_code == 200
    cuerpo = r.json()
    assert [c["id"] for c in cuerpo["items"]] == [3, 4]
    assert (cuerpo["total"], cuerpo["page"], cuerpo["size"], cuerpo["pages"]) == (5, 2, 2, 3)
    r = await client.get("/clientes/", params={"size": 2, "page": 3})
    assert [c["id"] for c in r.json()["items"]] == [5]
    assert set(r.json()["items"][0]) == {"id", "nombre", "email"}


async def test_listado_clientes_por_defecto_trae_la_primera_pagina_de_20(client):
    await crear_cliente(client)
    cuerpo = (await client.get("/clientes/")).json()
    assert (cuerpo["total"], cuerpo["page"], cuerpo["size"], cuerpo["pages"]) == (1, 1, 20, 1)


async def test_listado_clientes_sin_clientes_es_una_pagina_vacia(client):
    r = await client.get("/clientes/")
    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0, "page": 1, "size": 20, "pages": 1}


async def test_listado_clientes_pagina_fuera_de_rango_422(client):
    for i in range(5):
        await crear_cliente(client, nombre=f"C{i}", email=f"c{i}@example.com")
    r = await client.get("/clientes/", params={"size": 2, "page": 4})
    assert r.status_code == 422
    assert r.json() == {"detail": "La página 4 no existe: hay 3"}


async def test_listado_clientes_limit_ya_no_pagina(client):
    for i in range(3):
        await crear_cliente(client, nombre=f"C{i}", email=f"c{i}@example.com")
    cuerpo = (await client.get("/clientes/", params={"limit": 1, "offset": 2})).json()
    assert [c["id"] for c in cuerpo["items"]] == [1, 2, 3]
    assert cuerpo["size"] == 20


@pytest.mark.parametrize("params", [{"size": 0}, {"size": 101}, {"page": 0}])
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
    assert r.json() == {"detail": "Ya existe un cliente con ese correo."}


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
    assert r.json() == {"id": 1, "nombre": "Ana Pérez", "email": "ana@example.com", "perfil": None}


async def test_patch_de_un_cliente_con_perfil_devuelve_el_perfil(client):
    await crear_cliente(client)
    await client.post("/clientes/1/perfil", json={"telefono": "11 2233", "direccion": "Calle 1"})
    r = await client.patch("/clientes/1", json={"nombre": "Ana María"})
    assert r.status_code == 200
    assert r.json()["nombre"] == "Ana María"
    assert r.json()["perfil"] == {"id": 1, "cliente_id": 1, "telefono": "11 2233", "direccion": "Calle 1"}


async def test_patch_con_usuario_id_422_y_no_cambia_nada(client):
    await crear_cliente(client)
    r = await client.patch("/clientes/1", json={"nombre": "Otro", "usuario_id": 1})
    assert r.status_code == 422
    assert (await client.get("/clientes/1")).json()["nombre"] == "Ana Pérez"


async def test_alta_con_usuario_id_422_y_no_crea_nada(client):
    r = await client.post("/clientes/", json={"nombre": "Ana", "email": "a@example.com", "usuario_id": 1})
    assert r.status_code == 422
    assert (await client.get("/clientes/")).json()["total"] == 0


# --- correo de un cliente con cuenta (D10) ---

async def test_patch_del_correo_de_un_cliente_con_cuenta_409_y_no_cambia_nada(client, sessionmaker_test):
    cid = await registrar_cliente_con_cuenta(client)
    r = await client.patch(f"/clientes/{cid}", json={"nombre": "Bea P.", "email": "otra@example.com"})
    assert r.status_code == 409
    assert r.json() == {"detail": "El correo de un cliente con cuenta no se puede cambiar."}
    cliente = (await filas(sessionmaker_test, "SELECT nombre, email FROM cliente WHERE id = :i", i=cid))[0]
    assert (cliente["nombre"], cliente["email"]) == ("Bea", "bea@example.com")
    usuario = await filas(sessionmaker_test, "SELECT email FROM usuario WHERE email IN ('bea@example.com', 'otra@example.com')")
    assert [u["email"] for u in usuario] == ["bea@example.com"]


async def test_patch_con_el_mismo_correo_de_un_cliente_con_cuenta_200_sin_cambios(client):
    cid = await registrar_cliente_con_cuenta(client)
    r = await client.patch(f"/clientes/{cid}", json={"email": "bea@example.com"})
    assert r.status_code == 200
    assert r.json() == {"id": cid, "nombre": "Bea", "email": "bea@example.com", "perfil": None}


async def test_patch_de_solo_el_nombre_de_un_cliente_con_cuenta_200(client):
    cid = await registrar_cliente_con_cuenta(client)
    r = await client.patch(f"/clientes/{cid}", json={"nombre": "Bea P."})
    assert r.status_code == 200
    assert r.json()["nombre"] == "Bea P."
    assert r.json()["email"] == "bea@example.com"


async def test_un_cliente_sin_cuenta_cambia_su_correo_200(client):
    c = await crear_cliente(client, nombre="Beto", email="beto@example.com")
    r = await client.patch(f"/clientes/{c['id']}", json={"nombre": "Beto B.", "email": "beto2@example.com"})
    assert r.status_code == 200
    assert (r.json()["nombre"], r.json()["email"]) == ("Beto B.", "beto2@example.com")


async def test_el_patch_rechazado_no_hace_consultas_de_mas(client, sessionmaker_test):
    """La regla mira el cliente que el PATCH ya leyó para el 404: sin consulta extra."""
    con_cuenta = await registrar_cliente_con_cuenta(client)
    sin_cuenta = (await crear_cliente(client, nombre="Beto", email="beto@example.com"))["id"]
    with contar_sentencias(sessionmaker_test) as rechazado:
        r = await client.patch(f"/clientes/{con_cuenta}", json={"email": "otra@example.com"})
        assert r.status_code == 409
    with contar_sentencias(sessionmaker_test) as aceptado:
        r = await client.patch(f"/clientes/{sin_cuenta}", json={"email": "beto2@example.com"})
        assert r.status_code == 200
    assert len(rechazado) <= len(aceptado)


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

async def vender(client, cliente_id, *libro_ids, cantidad=1):
    r = await client.post(
        "/ventas/",
        json={"cliente_id": cliente_id, "renglones": [{"libro_id": l, "cantidad": cantidad} for l in libro_ids]},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def test_ventas_de_cliente_inexistente_404(client):
    r = await client.get("/clientes/999/ventas")
    assert r.status_code == 404
    assert r.json() == {"detail": "El cliente no existe."}


async def test_ventas_de_cliente_inexistente_con_pagina_fuera_de_rango_es_404_y_no_422(client):
    r = await client.get("/clientes/999/ventas", params={"page": 5})
    assert r.status_code == 404
    assert r.json() == {"detail": "El cliente no existe."}


async def test_ventas_de_cliente_sin_ventas_es_una_pagina_vacia(client):
    await crear_cliente(client)
    r = await client.get("/clientes/1/ventas")
    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0, "page": 1, "size": 20, "pages": 1}


async def test_ventas_de_cliente_solo_las_suyas_en_orden_de_id(client):
    await crear_cliente(client)
    await crear_cliente(client, nombre="Beto", email="beto@example.com")
    libro = await crear_libro(client)
    for cliente_id in (1, 1, 2, 1):
        await vender(client, cliente_id, libro)
    r = await client.get("/clientes/1/ventas")
    assert r.status_code == 200
    cuerpo = r.json()
    assert [v["id"] for v in cuerpo["items"]] == [1, 2, 4]
    assert all(v["cliente"]["id"] == 1 for v in cuerpo["items"])
    assert cuerpo["items"][0]["renglones"][0]["titulo"] == "T ISBN-1"
    assert (cuerpo["total"], cuerpo["page"], cuerpo["size"], cuerpo["pages"]) == (3, 1, 20, 1)


async def test_ventas_de_cliente_paginadas(client):
    await crear_cliente(client)
    await crear_cliente(client, nombre="Beto", email="beto@example.com")
    libro = await crear_libro(client)
    for cliente_id in (1, 1, 2, 1):
        await vender(client, cliente_id, libro)
    r = await client.get("/clientes/1/ventas", params={"size": 2, "page": 2})
    assert [v["id"] for v in r.json()["items"]] == [4]
    assert (r.json()["total"], r.json()["pages"]) == (3, 2)
    r = await client.get("/clientes/1/ventas", params={"size": 2, "page": 3})
    assert r.status_code == 422
    assert r.json() == {"detail": "La página 3 no existe: hay 2"}
    assert (await client.get("/clientes/1/ventas", params={"size": 0})).status_code == 422
    assert (await client.get("/clientes/1/ventas", params={"size": 101})).status_code == 422


async def test_ventas_de_cliente_con_un_libro_dado_de_baja_siguen_mostrando_su_titulo(client):
    await crear_cliente(client)
    libro = await crear_libro(client)
    await vender(client, 1, libro)
    assert (await client.delete(f"/libros/{libro}")).status_code == 204
    r = await client.get("/clientes/1/ventas")
    assert r.status_code == 200
    assert r.json()["items"][0]["renglones"][0]["titulo"] == "T ISBN-1"


async def test_ventas_de_cliente_hacen_las_mismas_consultas_con_1x1_que_con_3x2(client, sessionmaker_test):
    await crear_cliente(client)
    await crear_cliente(client, nombre="Beto", email="beto@example.com")
    l1 = await crear_libro(client, isbn="ISBN-1")
    l2 = await crear_libro(client, isbn="ISBN-2")
    await vender(client, 1, l1)
    for _ in range(3):
        await vender(client, 2, l1, l2)

    async def consultas(cliente_id):
        with contar_sentencias(sessionmaker_test) as sentencias:
            r = await client.get(f"/clientes/{cliente_id}/ventas")
        assert r.status_code == 200, r.text
        return len(sentencias), r.json()

    n_chico, chico = await consultas(1)
    n_grande, grande = await consultas(2)
    assert (len(chico["items"]), len(chico["items"][0]["renglones"])) == (1, 1)
    assert (len(grande["items"]), len(grande["items"][0]["renglones"])) == (3, 2)
    assert n_chico == n_grande
