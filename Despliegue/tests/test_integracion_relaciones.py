import pytest
from sqlalchemy.orm import configure_mappers

from app.modules.editoriales.models import Editorial
from app.modules.generos.models import Genero
from app.modules.libros.models import Libro


def test_mappers_resuelven_y_back_populates_coinciden():
    configure_mappers()
    assert Editorial.libros.property.back_populates == "editorial"
    assert Genero.libros.property.back_populates == "genero"
    assert Libro.editorial.property.back_populates == "libros"
    assert Libro.genero.property.back_populates == "libros"
    assert Editorial.libros.property.mapper.class_ is Libro
    assert Genero.libros.property.mapper.class_ is Libro
