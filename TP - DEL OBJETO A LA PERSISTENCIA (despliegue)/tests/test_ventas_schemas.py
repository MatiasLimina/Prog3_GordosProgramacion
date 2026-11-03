"""Validaciones de los DTO de ventas (sin base)."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.tipos import INT32_MAX
from app.modules.ventas.schemas import (
    ClienteSimpleRead,
    RenglonRead,
    VentaCreate,
    VentaRead,
)


def venta(**extra):
    d = {"cliente_id": 2, "renglones": [{"libro_id": 1, "cantidad": 2}, {"libro_id": 4, "cantidad": 1}]}
    d.update(extra)
    return d


def test_venta_create_del_ejemplo_de_la_consigna():
    v = VentaCreate(**venta())
    assert v.cliente_id == 2
    assert [(r.libro_id, r.cantidad) for r in v.renglones] == [(1, 2), (4, 1)]


def test_venta_create_un_solo_renglon_es_valido():
    v = VentaCreate(cliente_id=1, renglones=[{"libro_id": 3, "cantidad": 1}])
    assert len(v.renglones) == 1


def test_renglones_vacios_rn05():
    with pytest.raises(ValidationError):
        VentaCreate(cliente_id=1, renglones=[])


def test_renglones_ausentes():
    with pytest.raises(ValidationError):
        VentaCreate(cliente_id=1)


def test_libro_repetido_rn05():
    with pytest.raises(ValidationError, match="repetir un libro"):
        VentaCreate(
            cliente_id=1,
            renglones=[{"libro_id": 1, "cantidad": 1}, {"libro_id": 2, "cantidad": 1}, {"libro_id": 1, "cantidad": 5}],
        )


@pytest.mark.parametrize("cantidad", [0, -1, INT32_MAX + 1])
def test_cantidad_fuera_de_rango(cantidad):
    with pytest.raises(ValidationError):
        VentaCreate(cliente_id=1, renglones=[{"libro_id": 1, "cantidad": cantidad}])


def test_cantidad_maxima_valida():
    VentaCreate(cliente_id=1, renglones=[{"libro_id": 1, "cantidad": INT32_MAX}])


@pytest.mark.parametrize("cliente_id", [0, -3, INT32_MAX + 1])
def test_cliente_id_invalido(cliente_id):
    with pytest.raises(ValidationError):
        VentaCreate(**venta(cliente_id=cliente_id))


@pytest.mark.parametrize("extra", ["precio_unitario", "total", "fecha", "id"])
def test_campos_calculados_por_el_servidor_se_rechazan_en_la_venta(extra):
    with pytest.raises(ValidationError, match="Extra inputs"):
        VentaCreate(**venta(**{extra: 1}))


@pytest.mark.parametrize("extra", ["precio_unitario", "subtotal"])
def test_campos_calculados_se_rechazan_en_el_renglon(extra):
    with pytest.raises(ValidationError, match="Extra inputs"):
        VentaCreate(cliente_id=1, renglones=[{"libro_id": 1, "cantidad": 1, extra: "10.00"}])


def test_venta_read_serializa_forma_de_la_consigna():
    leida = VentaRead(
        id=2,
        fecha=datetime(2026, 10, 8, 21, 14, 11, 751581, tzinfo=timezone.utc),
        total=Decimal("77000.00"),
        cliente=ClienteSimpleRead(id=2, nombre="Tomás Ríos", email="tomas@example.com"),
        renglones=[
            RenglonRead(libro_id=1, titulo="Rayuela", cantidad=2,
                        precio_unitario=Decimal("25000.00"), subtotal=Decimal("50000.00")),
            RenglonRead(libro_id=4, titulo="Respiración artificial", cantidad=1,
                        precio_unitario=Decimal("27000.00"), subtotal=Decimal("27000.00")),
        ],
    )
    assert leida.model_dump(mode="json") == {
        "id": 2,
        "fecha": "2026-10-08T21:14:11.751581Z",
        "total": "77000.00",
        "cliente": {"id": 2, "nombre": "Tomás Ríos", "email": "tomas@example.com"},
        "renglones": [
            {"libro_id": 1, "titulo": "Rayuela", "cantidad": 2,
             "precio_unitario": "25000.00", "subtotal": "50000.00"},
            {"libro_id": 4, "titulo": "Respiración artificial", "cantidad": 1,
             "precio_unitario": "27000.00", "subtotal": "27000.00"},
        ],
    }
