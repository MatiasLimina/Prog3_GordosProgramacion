"""Modelos de clientes y ventas: estructura, constraints y relaciones (sin base)."""

import pytest
from sqlalchemy import DateTime, Numeric
from sqlalchemy.orm import configure_mappers
from sqlmodel import SQLModel

import app.models  # noqa: F401
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.libros.models import Libro
from app.modules.ventas.models import RenglonVenta, Venta


def _constraints(modelo):
    return {c.name for c in modelo.__table__.constraints}


def _indices(modelo):
    return {i.name for i in modelo.__table__.indexes}


def test_modelos_registrados_en_metadata():
    tablas = SQLModel.metadata.tables
    for nombre in ("cliente", "perfil_cliente", "venta", "renglon_venta"):
        assert nombre in tablas


@pytest.mark.parametrize(
    "modelo,tabla,columnas",
    [
        (Cliente, "cliente", {"id", "nombre", "email"}),
        (PerfilCliente, "perfil_cliente", {"id", "cliente_id", "telefono", "direccion"}),
        (Venta, "venta", {"id", "cliente_id", "fecha", "total"}),
        (
            RenglonVenta,
            "renglon_venta",
            {"id", "venta_id", "libro_id", "cantidad", "precio_unitario"},
        ),
    ],
)
def test_tabla_y_columnas(modelo, tabla, columnas):
    t = modelo.__table__
    assert t.name == tabla
    assert set(t.c.keys()) == columnas
    assert t.primary_key.columns.keys() == ["id"]
    assert all(not t.c[c].nullable for c in columnas)


def test_numeric_total_12_2_y_precio_unitario_10_2():
    total = Venta.__table__.c.total.type
    assert isinstance(total, Numeric) and (total.precision, total.scale) == (12, 2)
    precio = RenglonVenta.__table__.c.precio_unitario.type
    assert isinstance(precio, Numeric) and (precio.precision, precio.scale) == (10, 2)


def test_venta_fecha_con_zona_horaria():
    tipo = Venta.__table__.c.fecha.type
    assert isinstance(tipo, DateTime)
    assert tipo.timezone is True


@pytest.mark.parametrize(
    "modelo,nombre",
    [
        (Cliente, "uq_cliente_email"),
        (PerfilCliente, "uq_perfil_cliente_cliente_id"),
        (PerfilCliente, "fk_perfil_cliente_cliente_id_cliente"),
        (Venta, "fk_venta_cliente_id_cliente"),
        (Venta, "ck_venta_total_no_negativo"),
        (RenglonVenta, "fk_renglon_venta_venta_id_venta"),
        (RenglonVenta, "fk_renglon_venta_libro_id_libro"),
        (RenglonVenta, "ck_renglon_venta_cantidad_positiva"),
        (RenglonVenta, "ck_renglon_venta_precio_unitario_positivo"),
    ],
)
def test_constraints_con_nombre_de_la_convencion(modelo, nombre):
    assert nombre in _constraints(modelo)


def test_indices_en_claves_foraneas():
    assert "ix_venta_cliente_id" in _indices(Venta)
    assert {"ix_renglon_venta_venta_id", "ix_renglon_venta_libro_id"} <= _indices(RenglonVenta)


def test_unicos_sin_indice_redundante():
    # unique=True sin index=True: el UNIQUE ya indexa; no debe existir ix_ extra.
    assert "ix_cliente_email" not in _indices(Cliente)
    assert "ix_perfil_cliente_cliente_id" not in _indices(PerfilCliente)


def test_check_expresiones():
    textos = {c.name: str(c.sqltext) for c in RenglonVenta.__table__.constraints if hasattr(c, "sqltext")}
    assert textos["ck_renglon_venta_cantidad_positiva"] == "cantidad > 0"
    assert textos["ck_renglon_venta_precio_unitario_positivo"] == "precio_unitario > 0"
    assert "total >= 0" in {str(c.sqltext) for c in Venta.__table__.constraints if hasattr(c, "sqltext")}


@pytest.mark.parametrize(
    "lado_a,lado_b,destino",
    [
        (Cliente.perfil, "cliente", PerfilCliente),
        (PerfilCliente.cliente, "perfil", Cliente),
        (Venta.cliente, "ventas", Cliente),
        (Cliente.ventas, "cliente", Venta),
        (Venta.renglones, "venta", RenglonVenta),
        (RenglonVenta.venta, "renglones", Venta),
        (RenglonVenta.libro, "renglones", Libro),
        (Libro.renglones, "libro", RenglonVenta),
    ],
)
def test_back_populates_y_destino(lado_a, lado_b, destino):
    configure_mappers()
    assert lado_a.property.back_populates == lado_b
    assert lado_a.property.mapper.class_ is destino


def test_cliente_perfil_es_uno_a_uno():
    configure_mappers()
    assert Cliente.perfil.property.uselist is False
    assert Cliente.ventas.property.uselist is True


def test_venta_renglones_en_cascada():
    configure_mappers()
    cascade = Venta.renglones.property.cascade
    assert cascade.delete is True
    assert cascade.delete_orphan is True
