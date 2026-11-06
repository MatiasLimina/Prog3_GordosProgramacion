"""Libros y stock por HTTP (CHG-13): alta con movimiento, baja lógica, reposición e historial.

Las rutas de escritura son de ADMIN: sin sesión 401 y con VENDEDOR 403, en los dos casos sin escribir
nada. El `usuario_id` de cada movimiento es el del ADMIN que hizo la petición. Mirar la base desde otra
sesión (`contar`, `filas`) asegura que sólo se ve lo confirmado.
"""

import pytest

from tests.auxiliares_auth import contar, entrar_como, filas

pytestmark = pytest.mark.db


async def _editorial(sm, nombre="Eterna Cadencia") -> int:
    from app.modules.editoriales.models import Editorial

    async with sm() as s:
        editorial = Editorial(nombre=nombre, pais="Argentina")
        s.add(editorial)
        await s.commit()
        return editorial.id


def _cuerpo(editorial_id, isbn="ISBN-1", **extra):
    cuerpo = {"isbn": isbn, "titulo": f"Titulo {isbn}", "precio": "25000.00", "stock_inicial": 4, "editorial_id": editorial_id}
    cuerpo.update(extra)
    return cuerpo


async def _stock_igual_a_la_suma_de_movimientos(sm) -> bool:
    """El invariante de RN-11: `libro.stock` = suma de `cantidad` de sus movimientos, en TODOS los libros."""
    resultado = await filas(
        sm,
        "SELECT l.stock = COALESCE((SELECT SUM(m.cantidad) FROM movimiento_stock m WHERE m.libro_id = l.id), 0) AS ok "
        "FROM libro l",
    )
    return len(resultado) > 0 and all(f["ok"] for f in resultado)


# ---- POST /libros: el stock inicial entra como movimiento (6.1) ----

async def test_alta_sin_sesion_da_401_y_no_escribe(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    r = await client.post("/libros/", json=_cuerpo(e))
    assert r.status_code == 401
    assert await contar(sessionmaker_test, "libro") == 0
    assert await contar(sessionmaker_test, "movimiento_stock") == 0


async def test_alta_con_vendedor_da_403_y_no_escribe(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "VENDEDOR")
    r = await client.post("/libros/", json=_cuerpo(e))
    assert r.status_code == 403
    assert await contar(sessionmaker_test, "libro") == 0
    assert await contar(sessionmaker_test, "movimiento_stock") == 0


async def test_alta_con_stock_inicial_deja_un_movimiento_del_admin(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    uid = await entrar_como(client, sessionmaker_test, "ADMIN")
    r = await client.post("/libros/", json=_cuerpo(e, stock_inicial=4))
    assert r.status_code == 201, r.text
    assert r.json()["stock"] == 4
    movimientos = await filas(sessionmaker_test, "SELECT libro_id, cantidad, motivo, venta_id, usuario_id FROM movimiento_stock")
    assert len(movimientos) == 1
    m = movimientos[0]
    assert (m["libro_id"], m["cantidad"], m["motivo"], m["venta_id"], m["usuario_id"]) == (
        r.json()["id"], 4, "Stock inicial", None, uid,
    )


async def _autor(sm, nombre="Borges") -> int:
    from app.modules.autores.models import Autor

    async with sm() as s:
        autor = Autor(nombre=nombre, nacionalidad="Argentina")
        s.add(autor)
        await s.commit()
        return autor.id


async def _nada_escrito(sm) -> bool:
    return all([await contar(sm, t) == 0 for t in ("libro", "libro_autor", "movimiento_stock")])


async def test_alta_con_autor_inexistente_da_409_y_no_escribe_nada(client, sessionmaker_test):
    """Caracterización: la FK de la autoría falla en el flush y el UoW revierte libro y movimiento."""
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    r = await client.post(
        "/libros/", json=_cuerpo(e, stock_inicial=4, autores=[{"autor_id": 999999, "rol": "autor", "orden": 1}])
    )
    assert r.status_code == 409, r.text
    assert r.json() == {"detail": "Uno de los autores indicados no existe."}
    assert await _nada_escrito(sessionmaker_test)


async def test_alta_con_autor_repetido_da_409_y_no_escribe_nada(client, sessionmaker_test):
    """Caracterización: la PK compuesta de `libro_autor` rechaza el mismo autor dos veces."""
    e = await _editorial(sessionmaker_test)
    a = await _autor(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    r = await client.post(
        "/libros/",
        json=_cuerpo(e, stock_inicial=4, autores=[
            {"autor_id": a, "rol": "autor", "orden": 1}, {"autor_id": a, "rol": "autor", "orden": 2},
        ]),
    )
    assert r.status_code == 409, r.text
    assert r.json() == {"detail": "No se puede repetir el mismo autor en un libro."}
    assert await _nada_escrito(sessionmaker_test)


async def test_alta_con_stock_inicial_cero_no_deja_movimiento(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    r = await client.post("/libros/", json=_cuerpo(e, stock_inicial=0))
    assert r.status_code == 201, r.text
    assert r.json()["stock"] == 0
    assert await contar(sessionmaker_test, "libro") == 1
    assert await contar(sessionmaker_test, "movimiento_stock") == 0


async def test_alta_con_editorial_inexistente_da_409_y_no_deja_nada(client, sessionmaker_test):
    await entrar_como(client, sessionmaker_test, "ADMIN")
    r = await client.post("/libros/", json=_cuerpo(999999))
    assert r.status_code == 409
    assert r.json() == {"detail": "La editorial indicada no existe."}
    for tabla in ("libro", "libro_autor", "movimiento_stock"):
        assert await contar(sessionmaker_test, tabla) == 0


async def test_alta_con_isbn_repetido_da_409_sin_movimiento_nuevo(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    assert (await client.post("/libros/", json=_cuerpo(e, "ISBN-DUP", stock_inicial=2))).status_code == 201
    r = await client.post("/libros/", json=_cuerpo(e, "ISBN-DUP", stock_inicial=7))
    assert r.status_code == 409
    assert r.json() == {"detail": "Ya existe un libro con ese ISBN."}
    assert await contar(sessionmaker_test, "libro") == 1
    assert await contar(sessionmaker_test, "movimiento_stock") == 1  # sólo el del primero


async def test_el_stock_de_cada_libro_es_la_suma_de_sus_movimientos_tras_las_altas(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    for i, stock in enumerate((4, 0, 11), start=1):
        assert (await client.post("/libros/", json=_cuerpo(e, f"ISBN-{i}", stock_inicial=stock))).status_code == 201
    assert (await client.post("/libros/", json=_cuerpo(999999, "ISBN-X"))).status_code == 409  # un rechazo en el medio
    assert await _stock_igual_a_la_suma_de_movimientos(sessionmaker_test)


# ---- DELETE /libros/{id}: baja lógica (6.7) ----

async def _alta(client, editorial_id, isbn="ISBN-1", **extra):
    r = await client.post("/libros/", json=_cuerpo(editorial_id, isbn, **extra))
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def test_baja_con_admin_da_204_sin_cuerpo_y_conserva_la_fila_con_borrado_en(client, sessionmaker_test):
    from app.modules.autores.models import Autor

    e = await _editorial(sessionmaker_test)
    async with sessionmaker_test() as s:
        autor = Autor(nombre="Borges", nacionalidad="Argentina")
        s.add(autor)
        await s.commit()
        autor_id = autor.id
    await entrar_como(client, sessionmaker_test, "ADMIN")
    libro_id = await _alta(client, e, autores=[{"autor_id": autor_id, "rol": "autor", "orden": 1}], stock_inicial=4)
    r = await client.delete(f"/libros/{libro_id}")
    assert r.status_code == 204
    assert r.content == b""
    fila = (await filas(sessionmaker_test, "SELECT borrado_en, stock FROM libro WHERE id = :i", i=libro_id))[0]
    assert fila["borrado_en"] is not None and fila["borrado_en"].tzinfo is not None
    assert fila["stock"] == 4
    assert await contar(sessionmaker_test, "movimiento_stock", "libro_id = :i", i=libro_id) == 1
    assert await contar(sessionmaker_test, "libro_autor", "libro_id = :i", i=libro_id) == 1


async def test_segunda_baja_y_baja_de_un_inexistente_dan_404_y_no_cambian_la_fecha(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    libro_id = await _alta(client, e)
    assert (await client.delete(f"/libros/{libro_id}")).status_code == 204
    primera = (await filas(sessionmaker_test, "SELECT borrado_en FROM libro WHERE id = :i", i=libro_id))[0]["borrado_en"]
    r = await client.delete(f"/libros/{libro_id}")
    assert r.status_code == 404
    assert r.json() == {"detail": "El libro no existe."}
    segunda = (await filas(sessionmaker_test, "SELECT borrado_en FROM libro WHERE id = :i", i=libro_id))[0]["borrado_en"]
    assert segunda == primera
    assert (await client.delete("/libros/999999")).status_code == 404


async def test_baja_con_vendedor_da_403_y_el_libro_sigue_vigente(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    libro_id = await _alta(client, e)
    await entrar_como(client, sessionmaker_test, "VENDEDOR", email="vendedor@example.com")
    assert (await client.delete(f"/libros/{libro_id}")).status_code == 403
    assert await contar(sessionmaker_test, "libro", "borrado_en IS NULL") == 1


async def test_baja_saca_al_libro_del_catalogo_y_libera_el_isbn_para_un_solo_vigente(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    libro_id = await _alta(client, e, "ISBN-REUSO")
    assert (await client.get("/libros/")).json()["total"] == 1
    assert (await client.delete(f"/libros/{libro_id}")).status_code == 204
    assert (await client.get("/libros/")).json()["total"] == 0
    # El ISBN queda libre para un nuevo libro vigente...
    assert (await client.post("/libros/", json=_cuerpo(e, "ISBN-REUSO"))).status_code == 201
    # ...pero no para un segundo vigente.
    r = await client.post("/libros/", json=_cuerpo(e, "ISBN-REUSO"))
    assert r.status_code == 409
    assert r.json() == {"detail": "Ya existe un libro con ese ISBN."}


# ---- POST /libros/{id}/reponer (6.9) ----

async def test_reponer_con_admin_da_200_con_el_stock_resultante_y_el_movimiento(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    uid = await entrar_como(client, sessionmaker_test, "ADMIN")
    libro_id = await _alta(client, e, stock_inicial=10)
    r = await client.post(f"/libros/{libro_id}/reponer", json={"cantidad": 3})
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert (cuerpo["libro_id"], cuerpo["stock"]) == (libro_id, 13)
    m = cuerpo["movimiento"]
    assert (m["libro_id"], m["cantidad"], m["motivo"], m["usuario_id"], m["venta_id"]) == (libro_id, 3, "Reposición", uid, None)
    assert m["id"] > 0 and m["cuando"]
    assert (await client.get(f"/libros/{libro_id}")).json()["stock"] == 13


async def test_reponer_respeta_el_motivo_enviado(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    libro_id = await _alta(client, e, stock_inicial=0)
    r = await client.post(f"/libros/{libro_id}/reponer", json={"cantidad": 5, "motivo": "Llegó el pedido"})
    assert r.status_code == 200, r.text
    assert r.json()["movimiento"]["motivo"] == "Llegó el pedido"


async def test_reponer_un_libro_dado_de_baja_da_409_sin_movimiento(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    libro_id = await _alta(client, e, stock_inicial=2)
    assert (await client.delete(f"/libros/{libro_id}")).status_code == 204
    r = await client.post(f"/libros/{libro_id}/reponer", json={"cantidad": 1})
    assert r.status_code == 409
    assert r.json() == {"detail": f"El libro {libro_id} está dado de baja."}
    assert await contar(sessionmaker_test, "movimiento_stock") == 1  # sólo el del alta


async def test_reponer_un_libro_inexistente_da_404(client, sessionmaker_test):
    await entrar_como(client, sessionmaker_test, "ADMIN")
    r = await client.post("/libros/999999/reponer", json={"cantidad": 1})
    assert r.status_code == 404
    assert r.json() == {"detail": "El libro no existe."}
    assert await contar(sessionmaker_test, "movimiento_stock") == 0


async def test_reponer_pasando_el_maximo_de_int32_da_409_y_no_500(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    libro_id = await _alta(client, e, stock_inicial=2_147_483_647)
    r = await client.post(f"/libros/{libro_id}/reponer", json={"cantidad": 1})
    assert r.status_code == 409
    assert r.json() == {"detail": f"El stock del libro {libro_id} superaría el máximo permitido."}


async def test_reponer_sin_sesion_da_401_y_con_vendedor_403_sin_movimiento_nuevo(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    libro_id = await _alta(client, e, stock_inicial=2)
    client.cookies.clear()
    assert (await client.post(f"/libros/{libro_id}/reponer", json={"cantidad": 1})).status_code == 401
    await entrar_como(client, sessionmaker_test, "VENDEDOR", email="vendedor@example.com")
    assert (await client.post(f"/libros/{libro_id}/reponer", json={"cantidad": 1})).status_code == 403
    assert await contar(sessionmaker_test, "movimiento_stock") == 1


@pytest.mark.parametrize("cantidad", [0, -1])
async def test_reponer_con_cantidad_no_positiva_da_422(client, sessionmaker_test, cantidad):
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    libro_id = await _alta(client, e, stock_inicial=2)
    assert (await client.post(f"/libros/{libro_id}/reponer", json={"cantidad": cantidad})).status_code == 422
    assert await contar(sessionmaker_test, "movimiento_stock") == 1


async def test_el_stock_sigue_siendo_la_suma_de_los_movimientos_tras_reponer_y_tras_un_rechazo(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    libro_id = await _alta(client, e, stock_inicial=4)
    assert (await client.post(f"/libros/{libro_id}/reponer", json={"cantidad": 6})).status_code == 200
    assert (await client.post("/libros/999999/reponer", json={"cantidad": 6})).status_code == 404
    assert (await client.post(f"/libros/{libro_id}/reponer", json={"cantidad": 0})).status_code == 422
    assert await _stock_igual_a_la_suma_de_movimientos(sessionmaker_test)
    assert (await filas(sessionmaker_test, "SELECT stock FROM libro"))[0]["stock"] == 10


async def test_flujo_c13_reponer_baja_catalogo_y_reuso_del_isbn(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    libro_id = await _alta(client, e, "ISBN-C13", stock_inicial=4)
    r = await client.post(f"/libros/{libro_id}/reponer", json={"cantidad": 3})
    assert r.status_code == 200 and r.json()["stock"] == 7
    assert await contar(sessionmaker_test, "movimiento_stock", "libro_id = :i", i=libro_id) == 2
    assert (await client.delete(f"/libros/{libro_id}")).status_code == 204
    assert (await client.get("/libros/")).json()["items"] == []
    assert (await client.post("/libros/", json=_cuerpo(e, "ISBN-C13"))).status_code == 201  # mismo ISBN, ahora libre
    assert (await client.post("/libros/", json=_cuerpo(e, "ISBN-C13"))).status_code == 409  # un segundo vigente, no
    assert await _stock_igual_a_la_suma_de_movimientos(sessionmaker_test)


# ---- GET /libros/{id}/movimientos (6.11) ----

async def test_historial_lista_los_movimientos_en_orden_con_el_envoltorio(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    uid = await entrar_como(client, sessionmaker_test, "ADMIN")
    libro_id = await _alta(client, e, stock_inicial=4)
    assert (await client.post(f"/libros/{libro_id}/reponer", json={"cantidad": 3})).status_code == 200
    r = await client.get(f"/libros/{libro_id}/movimientos")
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert set(cuerpo) == {"items", "total", "page", "size", "pages"}
    assert (cuerpo["total"], cuerpo["pages"]) == (2, 1)
    assert [(m["cantidad"], m["motivo"]) for m in cuerpo["items"]] == [(4, "Stock inicial"), (3, "Reposición")]
    assert {m["usuario_id"] for m in cuerpo["items"]} == {uid}
    assert cuerpo["items"][0]["id"] < cuerpo["items"][1]["id"]


async def test_historial_pagina_con_size_y_page(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    libro_id = await _alta(client, e, stock_inicial=4)
    assert (await client.post(f"/libros/{libro_id}/reponer", json={"cantidad": 3})).status_code == 200
    r = await client.get(f"/libros/{libro_id}/movimientos", params={"size": 1, "page": 2})
    assert r.status_code == 200
    assert (r.json()["total"], r.json()["pages"], r.json()["page"]) == (2, 2, 2)
    assert [m["motivo"] for m in r.json()["items"]] == ["Reposición"]


async def test_historial_de_un_libro_dado_de_baja_conserva_sus_movimientos(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    libro_id = await _alta(client, e, stock_inicial=4)
    assert (await client.delete(f"/libros/{libro_id}")).status_code == 204
    r = await client.get(f"/libros/{libro_id}/movimientos")
    assert r.status_code == 200
    assert [m["cantidad"] for m in r.json()["items"]] == [4]


async def test_historial_de_un_libro_inexistente_da_404(client, sessionmaker_test):
    await entrar_como(client, sessionmaker_test, "ADMIN")
    r = await client.get("/libros/999999/movimientos")
    assert r.status_code == 404
    assert r.json() == {"detail": "El libro no existe."}


async def test_historial_de_un_libro_sin_movimientos_es_una_pagina_vacia(client, sessionmaker_test):
    e = await _editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")
    libro_id = await _alta(client, e, stock_inicial=0)
    r = await client.get(f"/libros/{libro_id}/movimientos")
    assert r.status_code == 200
    assert (r.json()["items"], r.json()["total"], r.json()["pages"]) == ([], 0, 1)
