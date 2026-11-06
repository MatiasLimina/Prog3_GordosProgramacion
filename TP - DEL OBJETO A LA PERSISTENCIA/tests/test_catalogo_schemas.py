from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.autores.schemas import (
    AutorCreate,
    AutorUpdate,
)
from app.modules.libros.models import MovimientoStock
from app.modules.libros.schemas import (
    LibroAutorCreate,
    LibroCreate,
    LibroUpdate,
    MovimientoStockRead,
    ReponerIn,
    ReposicionRead,
)


def test_autor_create_valido():
    dto = AutorCreate(nombre="Jorge Luis Borges", nacionalidad="Argentina")
    assert dto.nombre == "Jorge Luis Borges"
    assert dto.nacionalidad == "Argentina"


def test_autor_create_rechaza_vacio():
    with pytest.raises(ValidationError):
        AutorCreate(nombre="   ", nacionalidad="Argentina")


def test_autor_update_rechaza_null_explicito():
    with pytest.raises(ValidationError):
        AutorUpdate(nombre=None)


def test_autor_update_omision_valida():
    dto = AutorUpdate(nacionalidad="Uruguaya")
    datos = dto.model_dump(exclude_unset=True)
    assert datos == {"nacionalidad": "Uruguaya"}


def test_libro_autor_create_valido():
    dto = LibroAutorCreate(autor_id=1, rol="autor", orden=1)
    assert dto.autor_id == 1
    assert dto.rol == "autor"
    assert dto.orden == 1


def test_libro_autor_create_rechaza_rol_invalido():
    with pytest.raises(ValidationError):
        LibroAutorCreate(autor_id=1, rol="editor_fantasma", orden=1)


def test_libro_autor_create_rechaza_orden_menor_a_uno():
    with pytest.raises(ValidationError):
        LibroAutorCreate(autor_id=1, rol="autor", orden=0)


def test_libro_autor_create_rechaza_campo_extra():
    with pytest.raises(ValidationError):
        LibroAutorCreate(autor_id=1, rol="autor", orden=1, stock=5)


def _libro_create(**extra):
    datos = {
        "isbn": "978-950-00-0006-6",
        "titulo": "Ficciones",
        "precio": Decimal("25000.50"),
        "stock_inicial": 10,
        "editorial_id": 1,
        "genero_id": 2,
        "autores": [LibroAutorCreate(autor_id=1, rol="autor", orden=1)],
    }
    datos.update(extra)
    return LibroCreate(**datos)


def test_libro_create_valido():
    dto = _libro_create()
    assert dto.isbn == "978-950-00-0006-6"
    assert dto.precio == Decimal("25000.50")
    assert dto.stock_inicial == 10
    assert len(dto.autores) == 1


def test_libro_create_rechaza_precio_no_positivo():
    with pytest.raises(ValidationError):
        _libro_create(precio=Decimal("0.00"))


def test_libro_create_rechaza_stock_inicial_negativo():
    with pytest.raises(ValidationError):
        _libro_create(stock_inicial=-1)


def test_libro_create_rechaza_stock_en_lugar_de_stock_inicial():
    with pytest.raises(ValidationError):
        LibroCreate(
            isbn="978-950-00-0006-6",
            titulo="Ficciones",
            precio=Decimal("25000.50"),
            stock=10,
            editorial_id=1,
        )


def test_libro_create_rechaza_campo_extra():
    with pytest.raises(ValidationError):
        _libro_create(campo_inventado=1)


def test_libro_update_acepta_solo_titulo_y_precio():
    dto = LibroUpdate(titulo="Nuevo titulo", precio=Decimal("100.00"))
    assert dto.model_dump(exclude_unset=True) == {
        "titulo": "Nuevo titulo",
        "precio": Decimal("100.00"),
    }


@pytest.mark.parametrize("campo", ["stock", "isbn", "editorial_id", "genero_id", "autores"])
def test_libro_update_rechaza_campos_no_editables(campo):
    with pytest.raises(ValidationError):
        LibroUpdate(**{campo: 1})


def test_libro_update_rechaza_campo_extra():
    with pytest.raises(ValidationError):
        LibroUpdate(titulo="X", campo_inventado=1)


@pytest.mark.parametrize("campo", ["titulo", "precio"])
def test_libro_update_rechaza_null_explicito(campo):
    with pytest.raises(ValidationError):
        LibroUpdate(**{campo: None})


def _reponer(**extra):
    datos = {"cantidad": 5}
    datos.update(extra)
    return ReponerIn(**datos)


def test_reponer_in_valido_solo_con_cantidad():
    dto = _reponer()
    assert dto.cantidad == 5
    assert dto.motivo is None


def test_reponer_in_valido_con_motivo():
    dto = _reponer(motivo="Llegó mercadería")
    assert dto.motivo == "Llegó mercadería"


@pytest.mark.parametrize("cantidad", [0, -1, 2_147_483_648])
def test_reponer_in_rechaza_cantidad_invalida(cantidad):
    with pytest.raises(ValidationError):
        _reponer(cantidad=cantidad)


def test_reponer_in_rechaza_motivo_vacio():
    with pytest.raises(ValidationError):
        _reponer(motivo="")


def test_reponer_in_rechaza_campo_extra():
    with pytest.raises(ValidationError):
        _reponer(precio="10.00")


# --- contratos de salida de movimientos de stock (CHG-13) ---

def _movimiento(**extra):
    datos = {
        "id": 7, "libro_id": 1, "venta_id": None, "usuario_id": 2, "cantidad": 3,
        "motivo": "Reposición", "cuando": datetime(2026, 11, 6, 12, 30, tzinfo=UTC),
    }
    datos.update(extra)
    return MovimientoStock(**datos)


def test_movimiento_stock_read_desde_el_modelo_tiene_exactamente_sus_campos():
    dto = MovimientoStockRead.model_validate(_movimiento())
    assert set(dto.model_dump()) == {"id", "libro_id", "venta_id", "usuario_id", "cantidad", "motivo", "cuando"}
    assert (dto.id, dto.libro_id, dto.usuario_id, dto.cantidad, dto.motivo) == (7, 1, 2, 3, "Reposición")


def test_movimiento_stock_read_serializa_cuando_en_iso_8601_con_desplazamiento():
    cuando = datetime(2026, 11, 6, 9, 30, tzinfo=timezone(timedelta(hours=-3)))
    dto = MovimientoStockRead.model_validate(_movimiento(cuando=cuando))
    assert dto.model_dump(mode="json")["cuando"] == "2026-11-06T09:30:00-03:00"


def test_movimiento_stock_read_admite_venta_id_nulo_y_con_valor():
    assert MovimientoStockRead.model_validate(_movimiento()).venta_id is None
    assert MovimientoStockRead.model_validate(_movimiento(venta_id=9, cantidad=-2)).venta_id == 9


def test_reposicion_read_serializa_libro_stock_y_movimiento():
    movimiento = MovimientoStockRead.model_validate(_movimiento())
    dto = ReposicionRead(libro_id=1, stock=13, movimiento=movimiento)
    salida = dto.model_dump(mode="json")
    assert set(salida) == {"libro_id", "stock", "movimiento"}
    assert (salida["libro_id"], salida["stock"]) == (1, 13)
    assert salida["movimiento"]["cantidad"] == 3
