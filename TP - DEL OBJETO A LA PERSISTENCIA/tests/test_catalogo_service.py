from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.core.pagination import Pagination
from app.modules.autores import service as autores_service
from app.modules.autores.models import Autor
from app.modules.autores.schemas import AutorCreate, AutorUpdate
from app.modules.libros import service as libros_service
from app.modules.libros.models import Libro, LibroAutor
from app.modules.libros.schemas import (
    LibroAutorCreate,
    LibroCreate,
    LibroUpdate,
)

def test_mensajes_de_integridad_en_libros():
    esperadas = [
        "uq_libro_isbn",
        "fk_libro_editorial_id_editorial",
        "fk_libro_genero_id_genero",
        "fk_libro_autor_autor_id_autor",
        "fk_libro_autor_libro_id_libro",
        "pk_libro_autor",
        "ck_libro_precio_positivo",
        "ck_libro_stock_no_negativo",
        "ck_libro_autor_orden_positivo",
        "ck_libro_autor_rol_valido",
    ]
    for constraint in esperadas:
        assert constraint in libros_service.MENSAJES
        assert libros_service.MENSAJES[constraint]


def test_armar_detalle_libro():
    editorial_falsa = MagicMock(id=1, nombre="Editorial Sudamericana", pais="Argentina")
    genero_falso = MagicMock(id=2, nombre="Ficción")
    autor_falso = MagicMock(id=3, nombre="Jorge Luis Borges", nacionalidad="Argentina")
    autoria_falsa = MagicMock(orden=1, rol="autor", autor=autor_falso)

    libro = MagicMock(
        id=10,
        isbn="978-950-00-0001-1",
        titulo="Ficciones",
        precio=Decimal("25000.00"),
        stock=5,
        editorial=editorial_falsa,
        genero=genero_falso,
        autorias=[autoria_falsa],
    )

    detalle = libros_service._armar_detalle(libro)
    assert detalle.id == 10
    assert detalle.isbn == "978-950-00-0001-1"
    assert detalle.editorial.nombre == "Editorial Sudamericana"
    assert detalle.genero is not None
    assert detalle.genero.nombre == "Ficción"
    assert len(detalle.autores) == 1
    assert detalle.autores[0].autor_id == 3
    assert detalle.autores[0].rol == "autor"
    assert detalle.autores[0].orden == 1


async def test_obtener_autor_no_existente_lanza_404():
    session = AsyncMock()
    session.get.return_value = None

    with pytest.raises(HTTPException) as exc:
        await autores_service.obtener(session, 999)
    assert exc.value.status_code == 404
    assert exc.value.detail == "El autor no existe."


async def test_obtener_libro_no_existente_lanza_404():
    session = AsyncMock()
    ejecucion_mock = MagicMock()
    ejecucion_mock.scalars.return_value.first.return_value = None
    session.execute.return_value = ejecucion_mock

    with pytest.raises(HTTPException) as exc:
        await libros_service.obtener(session, 999)
    assert exc.value.status_code == 404
    assert exc.value.detail == "El libro no existe."


async def test_crear_libro_fk_editorial_invalida_lanza_409():
    session = AsyncMock()
    session.add = MagicMock()
    orig = Exception("violates foreign key constraint")
    orig.constraint_name = "fk_libro_editorial_id_editorial"
    orig.sqlstate = "23503"
    session.commit.side_effect = IntegrityError("INSERT", {}, orig)

    datos = LibroCreate(
        isbn="12345",
        titulo="Libro Test",
        precio=Decimal("1000.00"),
        editorial_id=999,
        autores=[LibroAutorCreate(autor_id=1, rol="autor", orden=1)],
    )

    with pytest.raises(HTTPException) as exc:
        await libros_service.crear(session, datos)
    assert exc.value.status_code == 409
    assert exc.value.detail == "La editorial indicada no existe."
    assert session.rollback.call_count == 1


async def test_crear_libro_isbn_duplicado_lanza_409():
    session = AsyncMock()
    session.add = MagicMock()
    orig = Exception("duplicate key")
    orig.constraint_name = "uq_libro_isbn"
    orig.sqlstate = "23505"
    session.commit.side_effect = IntegrityError("INSERT", {}, orig)

    datos = LibroCreate(
        isbn="978-950-00-0001-1",
        titulo="Libro Test",
        precio=Decimal("1000.00"),
        editorial_id=1,
    )

    with pytest.raises(HTTPException) as exc:
        await libros_service.crear(session, datos)
    assert exc.value.status_code == 409
    assert exc.value.detail == "Ya existe un libro con ese ISBN."
    assert session.rollback.call_count == 1


async def test_crear_libro_autor_invalido_lanza_409():
    session = AsyncMock()
    session.add = MagicMock()
    orig = Exception("violates foreign key constraint")
    orig.constraint_name = "fk_libro_autor_autor_id_autor"
    orig.sqlstate = "23503"
    session.commit.side_effect = IntegrityError("INSERT", {}, orig)

    datos = LibroCreate(
        isbn="12345",
        titulo="Libro Test",
        precio=Decimal("1000.00"),
        editorial_id=1,
        autores=[LibroAutorCreate(autor_id=999, rol="autor", orden=1)],
    )

    with pytest.raises(HTTPException) as exc:
        await libros_service.crear(session, datos)
    assert exc.value.status_code == 409
    assert exc.value.detail == "Uno de los autores indicados no existe."
    assert session.rollback.call_count == 1
