"""Recorrido C-10 -> C-13 sobre el seed (CHG-19): el invariante de stock tras CADA paso.

Un solo test recorre los pasos en orden porque cada caso parte del estado que dejó el
anterior (como los `.http` tras un `python seed.py`). Cada aserción lleva un mensaje con el
paso para que la falla diga dónde se rompió.

Invariante (RN-11): `libro.stock` = suma de `cantidad` de los movimientos del libro, en TODOS
los libros, incluidos los dados de baja.
"""
import asyncio

import pytest
from sqlalchemy import text

from seed import USUARIOS, cargar_datos

pytestmark = pytest.mark.db

ADMIN = USUARIOS[0]  # admin@example.com: puede vender, reponer y dar de baja


async def _consulta(sm, sql: str, **params):
    async with sm() as s:
        return (await s.execute(text(sql), params)).mappings().all()


async def _stocks(sm) -> dict[int, int]:
    return {f["id"]: f["stock"] for f in await _consulta(sm, "SELECT id, stock FROM libro ORDER BY id")}


async def _conteos_de_venta(sm) -> tuple[int, int, int]:
    """(ventas, renglones, movimientos): lo que una venta rechazada no puede cambiar."""
    f = (await _consulta(
        sm,
        "SELECT (SELECT count(*) FROM venta) AS v, (SELECT count(*) FROM renglon_venta) AS r, "
        "(SELECT count(*) FROM movimiento_stock) AS m",
    ))[0]
    return f["v"], f["r"], f["m"]


async def _exigir_invariante(sm, libros: int, paso: str) -> None:
    filas = await _consulta(
        sm,
        "SELECT l.id, l.stock = COALESCE((SELECT SUM(m.cantidad) FROM movimiento_stock m WHERE m.libro_id = l.id), 0) AS ok "
        "FROM libro l ORDER BY l.id",
    )
    # exige la cantidad esperada de filas: una consulta vacía no puede pasar
    assert len(filas) == libros, f"{paso}: se esperaban {libros} libros y hay {len(filas)}"
    desparejos = [f["id"] for f in filas if not f["ok"]]
    assert not desparejos, f"{paso}: stock distinto de la suma de movimientos en los libros {desparejos}"


async def test_recorrido_de_ventas_y_stock_sobre_el_seed(client, sessionmaker_test):
    sm = sessionmaker_test
    async with sm() as s:
        await cargar_datos(s, costo=4, semaforo=asyncio.Semaphore(4))
    r = await client.post("/auth/login", json={"email": ADMIN.email, "password": ADMIN.password})
    assert r.status_code == 200, r.text

    # Estado inicial del seed
    assert await _stocks(sm) == {1: 10, 2: 5, 3: 8, 4: 3, 5: 1}
    await _exigir_invariante(sm, 5, "inicial")
    _, _, movimientos_antes = await _conteos_de_venta(sm)

    # C-10: venta válida de dos renglones
    r = await client.post(
        "/ventas/", json={"cliente_id": 2, "renglones": [{"libro_id": 1, "cantidad": 2}, {"libro_id": 4, "cantidad": 1}]}
    )
    assert r.status_code == 201, f"C-10: {r.text}"
    venta_id = r.json()["id"]
    await _exigir_invariante(sm, 5, "C-10")
    assert await _stocks(sm) == {1: 8, 2: 5, 3: 8, 4: 2, 5: 1}, "C-10: stocks tras la venta"
    nuevos = await _consulta(
        sm, "SELECT libro_id, cantidad, venta_id FROM movimiento_stock WHERE venta_id = :v ORDER BY libro_id", v=venta_id
    )
    assert [(m["libro_id"], m["cantidad"]) for m in nuevos] == [(1, -2), (4, -1)], "C-10: un movimiento por renglón"
    assert (await _conteos_de_venta(sm))[2] == movimientos_antes + 2, "C-10: movimientos nuevos"

    # C-11: no alcanza el stock de Bestiario (hay 1) -> 409 y no queda NADA, ni el descuento de Rayuela
    antes = await _conteos_de_venta(sm)
    stocks_antes = await _stocks(sm)
    r = await client.post(
        "/ventas/", json={"cliente_id": 2, "renglones": [{"libro_id": 1, "cantidad": 1}, {"libro_id": 5, "cantidad": 2}]}
    )
    assert r.status_code == 409, f"C-11: {r.text}"
    assert r.json() == {"detail": "Stock insuficiente para el libro 5: hay 1, se pidieron 2."}, "C-11: mensaje"
    assert await _conteos_de_venta(sm) == antes, "C-11: quedó una venta, un renglón o un movimiento"
    assert await _stocks(sm) == stocks_antes, "C-11: cambió algún stock"
    await _exigir_invariante(sm, 5, "C-11")

    # C-12: tres rechazos más, cada uno sin escrituras de venta nuevas
    async def rechazada(paso: str, cuerpo: dict, detalle: str) -> None:
        antes, stocks = await _conteos_de_venta(sm), await _stocks(sm)
        r = await client.post("/ventas/", json=cuerpo)
        assert r.status_code == 409, f"{paso}: {r.status_code} {r.text}"
        # el mensaje ata el 409 a su causa: un 409 por otro motivo no pasa
        assert r.json() == {"detail": detalle}, f"{paso}: mensaje"
        assert await _conteos_de_venta(sm) == antes, f"{paso}: quedaron escrituras de venta"
        assert await _stocks(sm) == stocks, f"{paso}: cambió algún stock"
        await _exigir_invariante(sm, 5, paso)

    await rechazada(
        "C-12 cliente inexistente",
        {"cliente_id": 9999, "renglones": [{"libro_id": 1, "cantidad": 1}]},
        "El cliente indicado no existe.",
    )
    # el renglón válido (libro 1) se procesa antes que el inexistente: si algo se confirmó a medias, se nota
    await rechazada(
        "C-12 libro inexistente",
        {"cliente_id": 2, "renglones": [{"libro_id": 1, "cantidad": 1}, {"libro_id": 9999, "cantidad": 1}]},
        "El libro indicado no existe.",
    )
    r = await client.delete("/libros/4")  # Respiración artificial, con stock 2
    assert r.status_code == 204, f"C-12 baja: {r.text}"
    await _exigir_invariante(sm, 5, "C-12 tras la baja")
    await rechazada(
        "C-12 libro dado de baja",
        {"cliente_id": 2, "renglones": [{"libro_id": 4, "cantidad": 1}]},
        "El libro 4 está dado de baja.",
    )
    await rechazada(
        "C-12 libro dado de baja con otro válido",
        {"cliente_id": 2, "renglones": [{"libro_id": 1, "cantidad": 1}, {"libro_id": 4, "cantidad": 1}]},
        "El libro 4 está dado de baja.",
    )

    # C-13.a: reponer 3 de Rayuela (libro 1) deja exactamente un movimiento nuevo
    async def movimientos() -> list[dict]:
        return [dict(f) for f in await _consulta(sm, "SELECT id, libro_id, cantidad, motivo, venta_id FROM movimiento_stock ORDER BY id")]

    stock_rayuela = (await _stocks(sm))[1]
    antes = await movimientos()
    r = await client.post("/libros/1/reponer", json={"cantidad": 3})
    assert r.status_code == 200, f"C-13.a: {r.text}"
    assert r.json()["stock"] == stock_rayuela + 3, "C-13.a: stock resultante"
    despues = await movimientos()
    assert despues[:len(antes)] == antes and len(despues) == len(antes) + 1, "C-13.a: exactamente un movimiento nuevo"
    assert (despues[-1]["libro_id"], despues[-1]["cantidad"], despues[-1]["motivo"], despues[-1]["venta_id"]) == (
        1, 3, "Reposición", None
    ), "C-13.a: el movimiento"
    assert (await _stocks(sm))[1] == stock_rayuela + 3, "C-13.a: stock guardado"
    await _exigir_invariante(sm, 5, "C-13.a")

    # C-13.b: la baja de Rayuela no deja movimiento y la saca del catálogo, conservando su fila
    async def catalogo() -> dict:
        return (await client.get("/libros/", params={"size": 100})).json()

    total_antes = (await catalogo())["total"]
    antes, stocks = await movimientos(), await _stocks(sm)
    r = await client.delete("/libros/1")
    assert r.status_code == 204, f"C-13.b: {r.text}"
    assert await movimientos() == antes, "C-13.b: la baja dejó un movimiento"
    assert (await catalogo())["total"] == total_antes - 1, "C-13.b: el total del catálogo no bajó en 1"
    ids = [i["id"] for i in (await catalogo())["items"]]
    assert 1 not in ids, "C-13.b: Rayuela sigue en el catálogo"
    assert await _stocks(sm) == stocks, "C-13.b: la fila perdió su stock"
    await _exigir_invariante(sm, 5, "C-13.b")

    # C-13.c: reponer un libro dado de baja -> 409 sin movimiento
    r = await client.post("/libros/1/reponer", json={"cantidad": 1})
    assert r.status_code == 409, f"C-13.c: {r.status_code} {r.text}"
    assert r.json() == {"detail": "El libro 1 está dado de baja."}, "C-13.c: mensaje"
    assert await movimientos() == antes, "C-13.c: el rechazo dejó un movimiento"
    await _exigir_invariante(sm, 5, "C-13.c")

    # C-13.d: volver a cargar el ISBN de Rayuela -> libro nuevo con un solo movimiento «Stock inicial»
    isbn = (await _consulta(sm, "SELECT isbn FROM libro WHERE id = 1"))[0]["isbn"]
    cuerpo = {
        "isbn": isbn, "titulo": "Rayuela (nueva edición)", "precio": "26000.00", "stock_inicial": 6,
        "editorial_id": 1, "genero_id": 1, "autores": [{"autor_id": 1, "rol": "autor", "orden": 1}],
    }
    r = await client.post("/libros/", json=cuerpo)
    assert r.status_code == 201, f"C-13.d: {r.text}"
    nuevo_id = r.json()["id"]
    assert nuevo_id == 6, "C-13.d: id del libro nuevo"
    despues = await movimientos()
    assert despues[:len(antes)] == antes and len(despues) == len(antes) + 1, "C-13.d: exactamente un movimiento nuevo"
    assert (despues[-1]["libro_id"], despues[-1]["cantidad"], despues[-1]["motivo"]) == (
        nuevo_id, 6, "Stock inicial"
    ), "C-13.d: el movimiento"
    await _exigir_invariante(sm, 6, "C-13.d")

    # C-13.e: un segundo libro vigente con ese ISBN -> 409 sin libro ni movimiento
    # (caracterización: lo decide el índice único parcial de la base; sin sabotaje posible en `app/`)
    r = await client.post("/libros/", json=cuerpo)
    assert r.status_code == 409, f"C-13.e: {r.status_code} {r.text}"
    assert r.json() == {"detail": "Ya existe un libro con ese ISBN."}, "C-13.e: mensaje"
    assert await movimientos() == despues, "C-13.e: el rechazo dejó un movimiento"
    assert len(await _stocks(sm)) == 6, "C-13.e: quedó un libro de más"
    await _exigir_invariante(sm, 6, "C-13.e")

    # C-13.f: la venta vieja sigue mostrando el título del libro dado de baja (caracterización)
    r = await client.get("/ventas/1")
    assert r.status_code == 200, f"C-13.f: {r.text}"
    assert "Rayuela" in [x["titulo"] for x in r.json()["renglones"]], "C-13.f: la venta 1 perdió el título"
