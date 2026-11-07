"""`mensaje_para`: el mensaje propio en español de un `IntegrityError`, sin filtrar texto de la base.

Desde CHG-16 los ayudantes con sesión (`commit_or_409`, `traducir_integrity`) no existen: la traducción
la hace el UoW (`tests/test_unit_of_work.py`, `tests/test_conflicto.py`) con esta función.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from app.core.errors import mensaje_para

TEXTO_INTERNO = 'duplicate key value violates unique constraint "uq_libro_isbn"'


class OrigFalso(Exception):
    """Imita el `orig` de SQLAlchemy con asyncpg."""

    def __init__(self, sqlstate=None, constraint_name=None):
        super().__init__(TEXTO_INTERNO)
        self.sqlstate = sqlstate
        if constraint_name is not None:
            self.constraint_name = constraint_name


def integrity_error(orig):
    return IntegrityError("INSERT ...", {}, orig)


MENSAJES = {
    "uq_libro_isbn": "Ya existe un libro con ese ISBN.",
    "fk_libro_editorial_id_editorial": "La editorial indicada no existe.",
}


def test_elige_mensaje_por_nombre_de_constraint():
    assert mensaje_para(integrity_error(OrigFalso("23505", "uq_libro_isbn")), MENSAJES) == "Ya existe un libro con ese ISBN."


def test_otro_constraint_usa_su_propio_mensaje():
    error = integrity_error(OrigFalso("23503", "fk_libro_editorial_id_editorial"))
    assert mensaje_para(error, MENSAJES) == "La editorial indicada no existe."


def test_constraint_en_cause_como_con_asyncpg():
    # SQLAlchemy+asyncpg: orig no trae constraint_name, está en orig.__cause__
    orig = OrigFalso("23505")
    orig.__cause__ = OrigFalso("23505", "uq_libro_isbn")
    assert mensaje_para(integrity_error(orig), MENSAJES) == "Ya existe un libro con ese ISBN."


def test_default_explicito_si_no_matchea():
    error = integrity_error(OrigFalso("23505", "uq_desconocido"))
    assert mensaje_para(error, MENSAJES, default="No se pudo guardar.") == "No se pudo guardar."


@pytest.mark.parametrize(
    "sqlstate,fragmento",
    [
        ("23505", "único"),
        ("23503", "relación"),
        ("23514", "condiciones"),
        ("23001", "modificar ni borrar"),
    ],
)
def test_default_segun_sqlstate(sqlstate, fragmento):
    assert fragmento in mensaje_para(integrity_error(OrigFalso(sqlstate)), {})


def test_sqlstate_desconocido_usa_mensaje_generico():
    assert mensaje_para(integrity_error(OrigFalso("23000")), {})


@pytest.mark.parametrize("constraint", ["uq_libro_isbn", None, "uq_otro"])
def test_nunca_filtra_texto_de_la_base(constraint):
    detalle = mensaje_para(integrity_error(OrigFalso("23505", constraint)), {})
    assert "duplicate key" not in detalle
    assert "violates" not in detalle
    assert "uq_libro_isbn" not in detalle
    assert "INSERT" not in detalle
