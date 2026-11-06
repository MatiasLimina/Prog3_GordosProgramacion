from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.modules.autores import service as autores_service
from app.modules.libros import service as libros_service
from app.modules.libros.unit_of_work import LibrosUoW


def test_mensajes_de_integridad_en_libros():
    esperadas = [
        "uq_libro_isbn_vigente",
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
        assert constraint in LibrosUoW.MENSAJES
        assert LibrosUoW.MENSAJES[constraint]
    # La 3ª migración reemplazó la constraint por el índice parcial: la clave vieja ya no existe.
    assert "uq_libro_isbn" not in LibrosUoW.MENSAJES


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
