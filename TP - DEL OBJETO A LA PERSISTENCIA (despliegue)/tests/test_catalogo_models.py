import subprocess
import sys
from decimal import Decimal

import pytest
from sqlalchemy import Numeric
from sqlmodel import SQLModel

import app.models  # noqa: F401
from app.modules.autores.models import Autor
from app.modules.libros.models import Libro, LibroAutor


def test_modelos_registrados_en_metadata():
    tablas = SQLModel.metadata.tables
    assert "autor" in tablas
    assert "libro" in tablas
    assert "libro_autor" in tablas


def test_autor_estructura():
    tabla = Autor.__table__
    assert tabla.name == "autor"
    assert "id" in tabla.c
    assert "nombre" in tabla.c
    assert "nacionalidad" in tabla.c
    assert tabla.primary_key.columns.keys() == ["id"]


def test_libro_estructura_y_constraints():
    tabla = Libro.__table__
    assert tabla.name == "libro"
    assert "id" in tabla.c
    assert "isbn" in tabla.c
    assert "titulo" in tabla.c
    assert "precio" in tabla.c
    assert "stock" in tabla.c
    assert "editorial_id" in tabla.c
    assert "genero_id" in tabla.c

    # Tipo NUMERIC(10, 2)
    assert isinstance(tabla.c.precio.type, Numeric)
    assert tabla.c.precio.type.precision == 10
    assert tabla.c.precio.type.scale == 2

    # Índices en claves foráneas
    nombres_indices = {idx.name for idx in tabla.indexes}
    assert "ix_libro_editorial_id" in nombres_indices
    assert "ix_libro_genero_id" in nombres_indices

    # Constraints con nombres de la convención
    nombres_constraints = {c.name for c in tabla.constraints}
    assert "pk_libro" in nombres_constraints
    assert "uq_libro_isbn" in nombres_constraints
    assert "ck_libro_precio_positivo" in nombres_constraints
    assert "ck_libro_stock_no_negativo" in nombres_constraints
    assert "fk_libro_editorial_id_editorial" in nombres_constraints
    assert "fk_libro_genero_id_genero" in nombres_constraints


def test_libro_autor_estructura_y_constraints():
    tabla = LibroAutor.__table__
    assert tabla.name == "libro_autor"
    assert tabla.primary_key.columns.keys() == ["libro_id", "autor_id"]

    # Índices en claves foráneas
    nombres_indices = {idx.name for idx in tabla.indexes}
    assert "ix_libro_autor_libro_id" in nombres_indices
    assert "ix_libro_autor_autor_id" in nombres_indices

    # Constraints con nombres de la convención
    nombres_constraints = {c.name for c in tabla.constraints}
    assert "pk_libro_autor" in nombres_constraints
    assert "ck_libro_autor_orden_positivo" in nombres_constraints
    assert "ck_libro_autor_rol_valido" in nombres_constraints
    assert "fk_libro_autor_libro_id_libro" in nombres_constraints
    assert "fk_libro_autor_autor_id_autor" in nombres_constraints


CODIGO_PROCESO_AISLADO = """
import sys
sys.path.insert(0, '.')
from {modulo} import {clase}
nombres = {{c.name for c in {clase}.__table__.constraints}}
assert "{esperada}" in nombres, nombres
"""


@pytest.mark.parametrize(
    "modulo,clase,esperada",
    [
        ("app.modules.libros.models", "Libro", "uq_libro_isbn"),
        ("app.modules.libros.models", "Libro", "ck_libro_precio_positivo"),
        ("app.modules.libros.models", "LibroAutor", "ck_libro_autor_rol_valido"),
    ],
)
def test_importar_solo_un_modelo_aplica_naming_convention_aislada(modulo, clase, esperada):
    codigo = CODIGO_PROCESO_AISLADO.format(modulo=modulo, clase=clase, esperada=esperada)
    r = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
