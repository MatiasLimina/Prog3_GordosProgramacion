from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.autores.schemas import AutorCreate, AutorLibroRead, AutorRead, AutorUpdate
from app.modules.libros.schemas import (
    AutorEnLibroRead,
    EditorialSimpleRead,
    GeneroSimpleRead,
    LibroAutorCreate,
    LibroCreate,
    LibroDetalleRead,
    LibroRead,
    LibroUpdate,
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


def test_libro_create_valido():
    dto = LibroCreate(
        isbn="978-950-00-0006-6",
        titulo="Ficciones",
        precio=Decimal("25000.50"),
        stock=10,
        editorial_id=1,
        genero_id=2,
        autores=[LibroAutorCreate(autor_id=1, rol="autor", orden=1)],
    )
    assert dto.isbn == "978-950-00-0006-6"
    assert dto.precio == Decimal("25000.50")
    assert len(dto.autores) == 1


def test_libro_create_rechaza_precio_no_positivo():
    with pytest.raises(ValidationError):
        LibroCreate(
            isbn="123",
            titulo="Libro",
            precio=Decimal("0.00"),
            editorial_id=1,
        )


def test_libro_create_rechaza_stock_negativo():
    with pytest.raises(ValidationError):
        LibroCreate(
            isbn="123",
            titulo="Libro",
            precio=Decimal("100.00"),
            stock=-1,
            editorial_id=1,
        )


def test_libro_update_rechaza_null_en_precio():
    with pytest.raises(ValidationError):
        LibroUpdate(precio=None)


def test_libro_update_permite_genero_id_null():
    dto = LibroUpdate(genero_id=None)
    assert dto.genero_id is None
