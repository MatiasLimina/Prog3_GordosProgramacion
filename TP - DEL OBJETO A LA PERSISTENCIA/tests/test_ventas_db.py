"""Endpoints de ventas con base real."""
import logging
from types import SimpleNamespace

import pytest
from sqlalchemy import event, select

from app.modules.libros.models import Libro
from app.modules.ventas import service as ventas_service

pytestmark = pytest.mark.db


async def crear_cliente(client, nombre="Tomás Ríos", email="tomas@example.com"):
    r = await client.post("/clientes/", json={"nombre": nombre, "email": email})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def crear_libro(client, isbn, titulo, precio, stock=10):
    r = await client.post("/editoriales/", json={"nombre": f"E-{isbn}", "pais": "AR"})
    e = r.json()["id"]
    r = await client.post(
        "/libros/",
        json={"isbn": isbn, "titulo": titulo, "precio": precio, "stock": stock, "editorial_id": e},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def escenario(client):
    """cliente 1; libro 1 (25000, stock 10), libro 2 (27000, stock 6), libro 3 (100.50, stock 20)."""
    c = await crear_cliente(client)
    l1 = await crear_libro(client, "I1", "Rayuela", "25000.00", 10)
    l2 = await crear_libro(client, "I2", "Respiración artificial", "27000.00", 6)
    l3 = await crear_libro(client, "I3", "El Aleph", "100.50", 20)
    return c, l1, l2, l3


async def stocks(sessionmaker_test):
    async with sessionmaker_test() as s:
        filas = (await s.execute(select(Libro.id, Libro.stock).order_by(Libro.id))).all()
    return dict(filas)


def cuerpo(cliente_id, *renglones):
    return {
        "cliente_id": cliente_id,
        "renglones": [{"libro_id": libro, "cantidad": cant} for libro, cant in renglones],
    }


# --- alta válida (C-06) ---

async def test_venta_valida_dos_renglones_201_con_forma_de_la_consigna(client):
    c, l1, l2, _ = await escenario(client)
    r = await client.post("/ventas/", json=cuerpo(c, (l1, 2), (l2, 1)))
    assert r.status_code == 201, r.text
    datos = r.json()
    fecha = datos.pop("fecha")
    assert fecha.endswith("Z") or fecha.endswith("+00:00")
    assert datos == {
        "id": 1,
        "total": "77000.00",
        "cliente": {"id": c, "nombre": "Tomás Ríos", "email": "tomas@example.com"},
        "renglones": [
            {"libro_id": l1, "titulo": "Rayuela", "cantidad": 2,
             "precio_unitario": "25000.00", "subtotal": "50000.00"},
            {"libro_id": l2, "titulo": "Respiración artificial", "cantidad": 1,
             "precio_unitario": "27000.00", "subtotal": "27000.00"},
        ],
    }


async def test_total_y_subtotales_con_decimales(client):
    c, l1, _, l3 = await escenario(client)
    r = await client.post("/ventas/", json=cuerpo(c, (l3, 3), (l1, 1)))
    assert r.status_code == 201, r.text
    datos = r.json()
    assert [x["subtotal"] for x in datos["renglones"]] == ["301.50", "25000.00"]
    assert datos["total"] == "25301.50"


async def test_venta_descuenta_stock(client, sessionmaker_test):
    c, l1, l2, l3 = await escenario(client)
    r = await client.post("/ventas/", json=cuerpo(c, (l1, 2), (l2, 1)))
    assert r.status_code == 201
    assert await stocks(sessionmaker_test) == {l1: 8, l2: 5, l3: 20}
    r = await client.post("/ventas/", json=cuerpo(c, (l1, 8)))
    assert r.status_code == 201  # puede agotar el stock exacto
    assert (await stocks(sessionmaker_test))[l1] == 0


async def test_rn06_cambiar_precio_del_libro_no_altera_la_venta(client):
    c, l1, _, _ = await escenario(client)
    venta = (await client.post("/ventas/", json=cuerpo(c, (l1, 2)))).json()
    r = await client.patch(f"/libros/{l1}", json={"precio": "99999.00"})
    assert r.status_code == 200
    r = await client.get(f"/ventas/{venta['id']}")
    assert r.json()["renglones"][0]["precio_unitario"] == "25000.00"
    assert r.json()["total"] == "50000.00"
    # una venta nueva ya toma el precio nuevo
    nueva = (await client.post("/ventas/", json=cuerpo(c, (l1, 1)))).json()
    assert nueva["renglones"][0]["precio_unitario"] == "99999.00"


# --- errores 409 (C-05) y atomicidad ---

async def test_libro_inexistente_409(client):
    c, _, _, _ = await escenario(client)
    r = await client.post("/ventas/", json=cuerpo(c, (999999, 1)))
    assert r.status_code == 409
    assert r.json() == {"detail": "El libro indicado no existe."}


async def test_libro_inexistente_en_segundo_renglon_no_descuenta_ningun_stock(client, sessionmaker_test):
    c, l1, _, _ = await escenario(client)
    antes = await stocks(sessionmaker_test)
    r = await client.post("/ventas/", json=cuerpo(c, (l1, 3), (999999, 1)))
    assert r.status_code == 409
    assert r.json() == {"detail": "El libro indicado no existe."}
    assert await stocks(sessionmaker_test) == antes
    assert (await client.get("/ventas/")).json() == []


async def test_cliente_inexistente_409_sin_descontar_stock(client, sessionmaker_test):
    _, l1, l2, _ = await escenario(client)
    antes = await stocks(sessionmaker_test)
    r = await client.post("/ventas/", json=cuerpo(999999, (l1, 2), (l2, 1)))
    assert r.status_code == 409
    assert r.json() == {"detail": "El cliente indicado no existe."}
    assert await stocks(sessionmaker_test) == antes


async def test_stock_insuficiente_409_sin_descontar_ningun_stock(client, sessionmaker_test):
    c, l1, l2, _ = await escenario(client)
    antes = await stocks(sessionmaker_test)
    r = await client.post("/ventas/", json=cuerpo(c, (l1, 2), (l2, 7)))  # l2 tiene 6
    assert r.status_code == 409
    assert r.json() == {"detail": "No hay stock suficiente para el libro indicado."}
    assert await stocks(sessionmaker_test) == antes
    assert (await client.get("/ventas/")).json() == []


async def test_el_servicio_sigue_usable_tras_un_409(client):
    c, l1, _, _ = await escenario(client)
    assert (await client.post("/ventas/", json=cuerpo(c, (999999, 1)))).status_code == 409
    assert (await client.post("/ventas/", json=cuerpo(c, (l1, 1)))).status_code == 201


# --- 422 ---

@pytest.mark.parametrize(
    "body",
    [
        {"cliente_id": 1, "renglones": []},
        {"cliente_id": 1},
        {"renglones": [{"libro_id": 1, "cantidad": 1}]},
        {"cliente_id": 1, "renglones": [{"libro_id": 1, "cantidad": 1}, {"libro_id": 1, "cantidad": 2}]},
        {"cliente_id": 1, "renglones": [{"libro_id": 1, "cantidad": 0}]},
        {"cliente_id": 1, "renglones": [{"libro_id": 1, "cantidad": -2}]},
        {"cliente_id": 1, "renglones": [{"libro_id": 1, "cantidad": 1}], "total": "1.00"},
        {"cliente_id": 1, "renglones": [{"libro_id": 1, "cantidad": 1}], "fecha": "2020-01-01T00:00:00Z"},
        {"cliente_id": 1, "renglones": [{"libro_id": 1, "cantidad": 1, "precio_unitario": "1.00"}]},
    ],
)
async def test_contrato_invalido_422(client, body):
    await escenario(client)
    r = await client.post("/ventas/", json=body)
    assert r.status_code == 422


async def test_422_no_descuenta_stock(client, sessionmaker_test):
    await escenario(client)
    antes = await stocks(sessionmaker_test)
    body = {"cliente_id": 1, "renglones": [{"libro_id": 1, "cantidad": 1}], "total": "1"}
    assert (await client.post("/ventas/", json=body)).status_code == 422
    assert await stocks(sessionmaker_test) == antes


# --- listado y detalle ---

async def test_get_venta_inexistente_404(client):
    r = await client.get("/ventas/999")
    assert r.status_code == 404
    assert r.json() == {"detail": "La venta no existe."}


async def test_get_venta_id_invalido_422(client):
    assert (await client.get("/ventas/0")).status_code == 422


async def test_detalle_de_venta_igual_al_de_la_creacion(client):
    c, l1, l2, _ = await escenario(client)
    creada = (await client.post("/ventas/", json=cuerpo(c, (l1, 2), (l2, 1)))).json()
    r = await client.get(f"/ventas/{creada['id']}")
    assert r.status_code == 200
    assert r.json() == creada


async def test_listado_paginado_ordenado_por_id(client):
    c, l1, _, _ = await escenario(client)
    for _ in range(3):
        assert (await client.post("/ventas/", json=cuerpo(c, (l1, 1)))).status_code == 201
    r = await client.get("/ventas/")
    assert r.status_code == 200
    assert [v["id"] for v in r.json()] == [1, 2, 3]
    assert r.json()[0]["renglones"][0]["titulo"] == "Rayuela"
    r = await client.get("/ventas/", params={"limit": 1, "offset": 1})
    assert [v["id"] for v in r.json()] == [2]
    r = await client.get("/ventas/", params={"offset": 5})
    assert r.json() == []


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"limit": "x"}])
async def test_listado_limites_422(client, params):
    assert (await client.get("/ventas/", params=params)).status_code == 422


async def test_listado_vacio_200(client):
    r = await client.get("/ventas/")
    assert r.status_code == 200
    assert r.json() == []


# --- C-07: cantidad de consultas fija ---

class ContadorSQL:
    """Cuenta las sentencias SQL emitidas por el motor de test."""

    def __init__(self, engine):
        self.sentencias: list[str] = []
        self.parametros: list[tuple] = []
        self._engine = engine

    def _hook(self, conn, cursor, statement, parameters, context, executemany):
        self.sentencias.append(statement)
        self.parametros.append(tuple(parameters))

    def __enter__(self):
        event.listen(self._engine.sync_engine, "before_cursor_execute", self._hook)
        return self

    def __exit__(self, *exc):
        event.remove(self._engine.sync_engine, "before_cursor_execute", self._hook)


async def consultas_de(client, sessionmaker_test, ruta):
    with ContadorSQL(sessionmaker_test.kw["bind"]) as contador:
        r = await client.get(ruta)
    assert r.status_code == 200, r.text
    return len(contador.sentencias), r.json()


async def test_detalle_de_venta_emite_las_mismas_consultas_con_1_o_3_renglones(client, sessionmaker_test):
    c, l1, l2, l3 = await escenario(client)
    v1 = (await client.post("/ventas/", json=cuerpo(c, (l1, 1)))).json()["id"]
    v3 = (await client.post("/ventas/", json=cuerpo(c, (l1, 1), (l2, 1), (l3, 1)))).json()["id"]
    n1, d1 = await consultas_de(client, sessionmaker_test, f"/ventas/{v1}")
    n3, d3 = await consultas_de(client, sessionmaker_test, f"/ventas/{v3}")
    assert len(d1["renglones"]) == 1 and len(d3["renglones"]) == 3
    assert n1 == n3
    assert n1 <= 3  # venta+cliente, renglones+libros: nunca una consulta por renglón


async def test_listado_de_ventas_emite_las_mismas_consultas_con_1_o_varias_ventas(client, sessionmaker_test):
    c, l1, l2, l3 = await escenario(client)
    await client.post("/ventas/", json=cuerpo(c, (l1, 1)))
    n_una, _ = await consultas_de(client, sessionmaker_test, "/ventas/")
    await client.post("/ventas/", json=cuerpo(c, (l1, 1), (l2, 1)))
    await client.post("/ventas/", json=cuerpo(c, (l1, 1), (l2, 1), (l3, 1)))
    n_varias, d = await consultas_de(client, sessionmaker_test, "/ventas/")
    assert len(d) == 3
    assert n_una == n_varias


# --- orden de bloqueo (prevención de deadlocks) ---

async def test_updates_de_stock_en_orden_ascendente_de_libro_id_y_respuesta_en_orden_de_entrada(
    client, sessionmaker_test
):
    c, l1, l2, _ = await escenario(client)
    with ContadorSQL(sessionmaker_test.kw["bind"]) as contador:
        r = await client.post("/ventas/", json=cuerpo(c, (l2, 1), (l1, 2)))
    assert r.status_code == 201, r.text
    ids_actualizados = [
        params[-1]
        for sql, params in zip(contador.sentencias, contador.parametros)
        if sql.startswith("UPDATE libro")
    ]
    assert ids_actualizados == [l1, l2]
    # Los renglones se guardan (y se devuelven) en el orden de entrada.
    assert [x["libro_id"] for x in r.json()["renglones"]] == [l2, l1]
    assert [x["precio_unitario"] for x in r.json()["renglones"]] == ["27000.00", "25000.00"]
    assert r.json()["total"] == "77000.00"


# --- RN-08: las ventas no se modifican ni se borran ---

@pytest.mark.parametrize("metodo", ["PATCH", "DELETE", "PUT"])
async def test_venta_no_admite_modificar_ni_borrar_405(client, metodo):
    c, l1, _, _ = await escenario(client)
    await client.post("/ventas/", json=cuerpo(c, (l1, 1)))
    r = await client.request(metodo, "/ventas/1", json={} if metodo != "DELETE" else None)
    assert r.status_code == 405


# --- BackgroundTasks (Ej. 7) ---

def parchar_sleep(monkeypatch, pausas):
    async def sleep_falso(segundos):
        pausas.append(segundos)

    monkeypatch.setattr(ventas_service, "asyncio", SimpleNamespace(sleep=sleep_falso))


def logs_del_servicio(caplog):
    return [m.getMessage() for m in caplog.records if m.name == ventas_service.logger.name]


async def test_comprobante_se_agenda_y_loguea_tras_el_alta(client, monkeypatch, caplog):
    pausas = []
    parchar_sleep(monkeypatch, pausas)
    c, l1, _, _ = await escenario(client)
    with caplog.at_level(logging.INFO, logger=ventas_service.logger.name):
        r = await client.post("/ventas/", json=cuerpo(c, (l1, 1)))
    assert r.status_code == 201
    assert pausas == [0.5]
    mensajes = logs_del_servicio(caplog)
    assert len(mensajes) == 1
    assert "venta 1" in mensajes[0] and "tomas@example.com" in mensajes[0]


async def test_comprobante_no_se_envia_si_la_venta_falla(client, monkeypatch, caplog):
    pausas = []
    parchar_sleep(monkeypatch, pausas)
    c, _, _, _ = await escenario(client)
    with caplog.at_level(logging.INFO, logger=ventas_service.logger.name):
        r = await client.post("/ventas/", json=cuerpo(c, (999999, 1)))
    assert r.status_code == 409
    assert logs_del_servicio(caplog) == []
    assert pausas == []


async def test_avisar_comprobante_loguea_id_y_email(monkeypatch, caplog):
    parchar_sleep(monkeypatch, [])
    with caplog.at_level(logging.INFO, logger=ventas_service.logger.name):
        await ventas_service.avisar_comprobante(42, "x@example.com")
    mensajes = logs_del_servicio(caplog)
    assert len(mensajes) == 1
    assert "venta 42" in mensajes[0] and "x@example.com" in mensajes[0]
