"""Detalle con dueño, listado del personal y `/mis-ventas` (CHG-16, RN-14).

Las sesiones se arman con `insertar_usuario` + cookie firmada (sin bcrypt). Cada cliente con cuenta
se vincula a su usuario por `cliente.usuario_id`. La cantidad de sentencias de cada lectura no
depende de cuántos renglones ni ventas haya (C-15).
"""
import re

import pytest
from sqlalchemy import text

from tests.auxiliares_auth import contar, entrar_como, insertar_usuario, token_de_prueba
from tests.test_ventas_db import ContadorSQL, cuerpo, crear_libro

pytestmark = pytest.mark.db

MENSAJE_SIN_PERMISO = "No tenés permiso para esta operación."


def _como(client, uid, *roles):
    client.cookies.set("access_token", token_de_prueba(uid, roles))


async def _cliente_con_cuenta(sm, email, nombre):
    """Usuario CLIENTE + ficha de cliente vinculada. Devuelve `(usuario_id, cliente_id)`."""
    uid = await insertar_usuario(sm, email, roles=("CLIENTE",))
    async with sm() as s:
        cid = (
            await s.execute(
                text("INSERT INTO cliente (nombre, email, usuario_id) VALUES (:n, :e, :u) RETURNING id"),
                {"n": nombre, "e": email, "u": uid},
            )
        ).scalar_one()
        await s.commit()
    return uid, cid


@pytest.fixture
async def mundo(client, sessionmaker_test):
    """Admin, tres libros, Ana (2 ventas) y Lucía (1 venta). Deja al `client` como ADMIN."""
    admin = await entrar_como(client, sessionmaker_test, "ADMIN", email="admin@example.com")
    libros = [await crear_libro(client, f"IA{i}", f"Libro {i}", "100.00", 50) for i in (1, 2, 3)]
    ana, cliente_ana = await _cliente_con_cuenta(sessionmaker_test, "ana.cli@example.com", "Ana")
    lucia, cliente_lucia = await _cliente_con_cuenta(sessionmaker_test, "lucia@example.com", "Lucía")
    ventas = {}
    for clave, cliente, renglones in [
        ("ana1", cliente_ana, [(libros[0], 1), (libros[1], 2)]),
        ("ana2", cliente_ana, [(libros[2], 1)]),
        ("lucia1", cliente_lucia, [(libros[0], 3)]),
    ]:
        r = await client.post("/ventas/", json=cuerpo(cliente, *renglones))
        assert r.status_code == 201, r.text
        ventas[clave] = r.json()
    return {"admin": admin, "ana": ana, "lucia": lucia, "libros": libros, "ventas": ventas}


# ---- GET /ventas/{id}: personal o dueño (5.1) ----

async def test_el_dueno_ve_su_venta_igual_que_en_el_alta(client, mundo):
    _como(client, mundo["ana"], "CLIENTE")
    r = await client.get(f"/ventas/{mundo['ventas']['ana1']['id']}")
    assert r.status_code == 200, r.text
    assert r.json() == mundo["ventas"]["ana1"]


async def test_el_dueno_con_cliente_revocado_sigue_viendo_su_venta(client, sessionmaker_test, mundo):
    """Q3: el dueño es `cliente.usuario_id`; no hace falta el rol CLIENTE vigente."""
    _como(client, mundo["ana"], "CLIENTE")
    async with sessionmaker_test() as s:
        await s.execute(
            text("UPDATE asignacion_rol SET revocada_en = now() WHERE usuario_id = :u AND rol = 'CLIENTE'"),
            {"u": mundo["ana"]},
        )
        await s.commit()
    r = await client.get(f"/ventas/{mundo['ventas']['ana1']['id']}")
    assert r.status_code == 200, r.text
    assert r.json() == mundo["ventas"]["ana1"]


async def test_el_cliente_no_ve_la_venta_de_otro_403(client, mundo):
    _como(client, mundo["ana"], "CLIENTE")
    r = await client.get(f"/ventas/{mundo['ventas']['lucia1']['id']}")
    assert r.status_code == 403
    assert r.json() == {"detail": MENSAJE_SIN_PERMISO}


async def test_el_cliente_pide_una_venta_inexistente_403_no_404(client, mundo):
    _como(client, mundo["ana"], "CLIENTE")
    r = await client.get("/ventas/999")
    assert r.status_code == 403
    assert r.json() == {"detail": MENSAJE_SIN_PERMISO}


async def test_el_personal_ve_cualquiera_y_un_inexistente_es_404(client, sessionmaker_test, mundo):
    vendedor = await insertar_usuario(sessionmaker_test, "vende@example.com", roles=("VENDEDOR",))
    _como(client, vendedor, "VENDEDOR")
    for clave in ("ana1", "lucia1"):
        r = await client.get(f"/ventas/{mundo['ventas'][clave]['id']}")
        assert r.status_code == 200
        assert r.json() == mundo["ventas"][clave]
    r = await client.get("/ventas/999")
    assert r.status_code == 404
    assert r.json() == {"detail": "La venta no existe."}


async def test_un_vendedor_con_el_rol_revocado_pierde_el_acceso_con_la_misma_cookie(client, sessionmaker_test, mundo):
    vendedor = await insertar_usuario(sessionmaker_test, "vende@example.com", roles=("VENDEDOR",))
    _como(client, vendedor, "VENDEDOR")
    venta = mundo["ventas"]["ana1"]["id"]
    assert (await client.get(f"/ventas/{venta}")).status_code == 200
    async with sessionmaker_test() as s:
        await s.execute(text("UPDATE asignacion_rol SET revocada_en = now() WHERE usuario_id = :u"), {"u": vendedor})
        await s.commit()
    assert (await client.get(f"/ventas/{venta}")).status_code == 403


async def test_un_usuario_sin_roles_ni_cliente_403(client, sessionmaker_test, mundo):
    sin_nada = await insertar_usuario(sessionmaker_test, "nadie@example.com", roles=())
    _como(client, sin_nada)
    r = await client.get(f"/ventas/{mundo['ventas']['ana1']['id']}")
    assert r.status_code == 403
    assert r.json() == {"detail": MENSAJE_SIN_PERMISO}


async def test_el_detalle_sin_sesion_da_401(client, mundo):
    client.cookies.clear()
    assert (await client.get(f"/ventas/{mundo['ventas']['ana1']['id']}")).status_code == 401


async def test_el_detalle_emite_las_mismas_consultas_con_2_o_4_renglones(client, sessionmaker_test, mundo):
    _, cliente = await _cliente_con_cuenta(sessionmaker_test, "otra@example.com", "Otra")
    libros = mundo["libros"] + [await _libro_extra(client, sessionmaker_test)]
    v2 = (await client.post("/ventas/", json=cuerpo(cliente, (libros[0], 1), (libros[1], 1)))).json()["id"]
    v4 = (await client.post("/ventas/", json=cuerpo(cliente, *[(lid, 1) for lid in libros]))).json()["id"]
    n2, d2 = await _consultas_de(client, sessionmaker_test, f"/ventas/{v2}")
    n4, d4 = await _consultas_de(client, sessionmaker_test, f"/ventas/{v4}")
    assert (len(d2["renglones"]), len(d4["renglones"])) == (2, 4)
    assert n2 == n4


async def _libro_extra(client, sessionmaker_test):
    return await crear_libro(client, "IA4", "Libro 4", "100.00", 50)


async def _consultas_de(client, sm, ruta):
    """Sentencias de la operación: descuenta las dos lecturas de autorización (usuario y roles vigentes)."""
    with ContadorSQL(sm.kw["bind"]) as contador:
        r = await client.get(ruta)
    assert r.status_code == 200, r.text
    de_autorizacion = [q for q in contador.sentencias if re.search(r"FROM (usuario|asignacion_rol)\b", q)]
    assert len(de_autorizacion) == 2, de_autorizacion
    return len(contador.sentencias) - 2, r.json()


# ---- GET /ventas/: listado del personal (5.3) ----

async def test_listado_con_envoltorio_y_detalle(client, mundo):
    r = await client.get("/ventas/")
    assert r.status_code == 200, r.text
    datos = r.json()
    assert [v["id"] for v in datos["items"]] == [v["id"] for v in mundo["ventas"].values()]
    assert datos["items"][0]["renglones"][0]["titulo"] == "Libro 1"
    assert (datos["total"], datos["page"], datos["size"], datos["pages"]) == (3, 1, 20, 1)


async def test_listado_pagina_y_pagina_inexistente_422(client, mundo):
    r = await client.get("/ventas/", params={"size": 1, "page": 2})
    assert [v["id"] for v in r.json()["items"]] == [mundo["ventas"]["ana2"]["id"]]
    assert (r.json()["total"], r.json()["pages"]) == (3, 3)
    r = await client.get("/ventas/", params={"size": 1, "page": 4})
    assert r.status_code == 422
    assert r.json() == {"detail": "La página 4 no existe: hay 3"}


@pytest.mark.parametrize("params", [{"size": 0}, {"size": 101}, {"page": 0}, {"size": "x"}])
async def test_listado_parametros_invalidos_422(client, mundo, params):
    assert (await client.get("/ventas/", params=params)).status_code == 422


async def test_listado_vacio_tiene_una_pagina(client, sessionmaker_test):
    await entrar_como(client, sessionmaker_test, "ADMIN")
    r = await client.get("/ventas/")
    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0, "page": 1, "size": 20, "pages": 1}


async def test_listado_limit_y_offset_del_tp_ya_no_paginan(client, mundo):
    r = await client.get("/ventas/", params={"limit": 1, "offset": 1})
    assert r.status_code == 200
    assert len(r.json()["items"]) == 3


async def test_listado_emite_las_mismas_consultas_con_1_o_3_ventas(client, sessionmaker_test):
    await entrar_como(client, sessionmaker_test, "ADMIN")
    _, cliente = await _cliente_con_cuenta(sessionmaker_test, "c@example.com", "C")
    libros = [await crear_libro(client, f"IL{i}", f"L{i}", "10.00", 50) for i in (1, 2, 3)]
    await client.post("/ventas/", json=cuerpo(cliente, (libros[0], 1)))
    n_una, _ = await _consultas_de(client, sessionmaker_test, "/ventas/")
    await client.post("/ventas/", json=cuerpo(cliente, (libros[0], 1), (libros[1], 1)))
    await client.post("/ventas/", json=cuerpo(cliente, *[(lid, 1) for lid in libros]))
    n_varias, d = await _consultas_de(client, sessionmaker_test, "/ventas/")
    assert len(d["items"]) == 3
    assert n_una == n_varias


# ---- GET /mis-ventas (5.5) ----

async def test_mis_ventas_muestra_solo_las_propias(client, mundo):
    _como(client, mundo["ana"], "CLIENTE")
    r = await client.get("/mis-ventas")
    assert r.status_code == 200, r.text
    assert [v["id"] for v in r.json()["items"]] == [mundo["ventas"]["ana1"]["id"], mundo["ventas"]["ana2"]["id"]]
    assert r.json()["total"] == 2
    _como(client, mundo["lucia"], "CLIENTE")
    r = await client.get("/mis-ventas")
    assert [v["id"] for v in r.json()["items"]] == [mundo["ventas"]["lucia1"]["id"]]
    assert r.json()["total"] == 1


async def test_mis_ventas_pagina_fuera_de_rango_422(client, mundo):
    _como(client, mundo["ana"], "CLIENTE")
    r = await client.get("/mis-ventas", params={"size": 1, "page": 3})
    assert r.status_code == 422
    assert r.json() == {"detail": "La página 3 no existe: hay 2"}


async def test_mis_ventas_de_un_usuario_sin_cliente_es_vacio_200(client, sessionmaker_test, mundo):
    vendedor = await insertar_usuario(sessionmaker_test, "vende@example.com", roles=("VENDEDOR",))
    _como(client, vendedor, "VENDEDOR")
    r = await client.get("/mis-ventas")
    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0, "page": 1, "size": 20, "pages": 1}
    assert (await client.get("/mis-ventas", params={"page": 2})).status_code == 422


async def test_mis_ventas_sin_sesion_401(client, mundo):
    client.cookies.clear()
    assert (await client.get("/mis-ventas")).status_code == 401


async def test_mis_ventas_con_cambio_de_password_pendiente_403(client, sessionmaker_test, mundo):
    uid = await insertar_usuario(sessionmaker_test, "pend@example.com", roles=("CLIENTE",), debe_cambiar=True)
    _como(client, uid, "CLIENTE")
    assert (await client.get("/mis-ventas")).status_code == 403


async def test_mis_ventas_emite_las_mismas_consultas_con_una_o_varias_ventas(client, sessionmaker_test, mundo):
    uid, cliente = await _cliente_con_cuenta(sessionmaker_test, "nueva@example.com", "Nueva")
    libros = mundo["libros"]
    await client.post("/ventas/", json=cuerpo(cliente, (libros[0], 1)))
    _como(client, uid, "CLIENTE")
    with ContadorSQL(sessionmaker_test.kw["bind"]) as uno:
        assert (await client.get("/mis-ventas")).status_code == 200
    _como(client, mundo["admin"], "ADMIN")
    await client.post("/ventas/", json=cuerpo(cliente, (libros[0], 1), (libros[1], 1)))
    await client.post("/ventas/", json=cuerpo(cliente, *[(lid, 1) for lid in libros]))
    _como(client, uid, "CLIENTE")
    with ContadorSQL(sessionmaker_test.kw["bind"]) as varias:
        r = await client.get("/mis-ventas")
    assert len(r.json()["items"]) == 3
    assert len(uno.sentencias) == len(varias.sentencias)
    assert await contar(sessionmaker_test, "venta", "cliente_id = :c", c=cliente) == 3
