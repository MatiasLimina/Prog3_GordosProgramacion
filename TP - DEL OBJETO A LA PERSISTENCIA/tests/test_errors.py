import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.core.errors import commit_or_409

TEXTO_INTERNO = 'duplicate key value violates unique constraint "uq_libro_isbn"'


class OrigFalso(Exception):
    """Imita el `orig` de SQLAlchemy con asyncpg."""

    def __init__(self, sqlstate=None, constraint_name=None):
        super().__init__(TEXTO_INTERNO)
        self.sqlstate = sqlstate
        if constraint_name is not None:
            self.constraint_name = constraint_name


class SesionFalsa:
    def __init__(self, error=None):
        self.error = error
        self.commits = 0
        self.rollbacks = 0

    async def commit(self):
        self.commits += 1
        if self.error:
            raise self.error

    async def rollback(self):
        self.rollbacks += 1


def integrity_error(orig):
    return IntegrityError("INSERT ...", {}, orig)


MENSAJES = {
    "uq_libro_isbn": "Ya existe un libro con ese ISBN.",
    "fk_libro_editorial_id_editorial": "La editorial indicada no existe.",
}


async def test_sin_error_hace_commit_y_no_rollback():
    s = SesionFalsa()
    await commit_or_409(s, MENSAJES)
    assert (s.commits, s.rollbacks) == (1, 0)


async def test_elige_mensaje_por_nombre_de_constraint():
    s = SesionFalsa(integrity_error(OrigFalso("23505", "uq_libro_isbn")))
    with pytest.raises(HTTPException) as exc:
        await commit_or_409(s, MENSAJES)
    assert exc.value.status_code == 409
    assert exc.value.detail == "Ya existe un libro con ese ISBN."
    assert s.rollbacks == 1


async def test_otro_constraint_usa_su_propio_mensaje():
    s = SesionFalsa(integrity_error(OrigFalso("23503", "fk_libro_editorial_id_editorial")))
    with pytest.raises(HTTPException) as exc:
        await commit_or_409(s, MENSAJES)
    assert exc.value.detail == "La editorial indicada no existe."


async def test_constraint_en_cause_como_con_asyncpg():
    # SQLAlchemy+asyncpg: orig no trae constraint_name, está en orig.__cause__
    orig = OrigFalso("23505")
    orig.__cause__ = OrigFalso("23505", "uq_libro_isbn")
    s = SesionFalsa(integrity_error(orig))
    with pytest.raises(HTTPException) as exc:
        await commit_or_409(s, MENSAJES)
    assert exc.value.detail == "Ya existe un libro con ese ISBN."


async def test_default_explicito_si_no_matchea():
    s = SesionFalsa(integrity_error(OrigFalso("23505", "uq_desconocido")))
    with pytest.raises(HTTPException) as exc:
        await commit_or_409(s, MENSAJES, default="No se pudo guardar.")
    assert exc.value.status_code == 409
    assert exc.value.detail == "No se pudo guardar."


@pytest.mark.parametrize(
    "sqlstate,fragmento",
    [("23505", "único"), ("23503", "relación"), ("23514", "condiciones")],
)
async def test_default_segun_sqlstate(sqlstate, fragmento):
    s = SesionFalsa(integrity_error(OrigFalso(sqlstate)))
    with pytest.raises(HTTPException) as exc:
        await commit_or_409(s, {})
    assert fragmento in exc.value.detail


async def test_sqlstate_desconocido_usa_mensaje_generico():
    s = SesionFalsa(integrity_error(OrigFalso("23000")))
    with pytest.raises(HTTPException) as exc:
        await commit_or_409(s, {})
    assert exc.value.status_code == 409
    assert exc.value.detail


@pytest.mark.parametrize("constraint", ["uq_libro_isbn", None, "uq_otro"])
async def test_nunca_filtra_texto_de_la_base(constraint):
    s = SesionFalsa(integrity_error(OrigFalso("23505", constraint)))
    with pytest.raises(HTTPException) as exc:
        await commit_or_409(s, MENSAJES)
    detalle = str(exc.value.detail)
    assert "duplicate key" not in detalle
    assert "violates" not in detalle
    assert "uq_libro_isbn" not in detalle
    assert "INSERT" not in detalle


# --- traducir_integrity: cubre flush/execute además del commit ---
from app.core.errors import traducir_integrity  # noqa: E402


async def test_traducir_integrity_flush_da_409_con_rollback():
    s = SesionFalsa()
    with pytest.raises(HTTPException) as exc:
        async with traducir_integrity(s, MENSAJES):
            raise integrity_error(OrigFalso("23505", "uq_libro_isbn"))  # simula un flush()
    assert exc.value.status_code == 409
    assert exc.value.detail == "Ya existe un libro con ese ISBN."
    assert s.rollbacks == 1


async def test_traducir_integrity_sin_error_no_hace_rollback():
    s = SesionFalsa()
    async with traducir_integrity(s, MENSAJES):
        pass
    assert s.rollbacks == 0


async def test_traducir_integrity_no_toca_otras_excepciones():
    s = SesionFalsa()
    with pytest.raises(ValueError):
        async with traducir_integrity(s, MENSAJES):
            raise ValueError("otra cosa")
    assert s.rollbacks == 0


async def test_traducir_integrity_usa_default_y_sqlstate():
    s = SesionFalsa()
    with pytest.raises(HTTPException) as exc:
        async with traducir_integrity(s, {}, default="Conflicto propio."):
            raise integrity_error(OrigFalso("23503"))
    assert exc.value.detail == "Conflicto propio."
    with pytest.raises(HTTPException) as exc:
        async with traducir_integrity(s, {}):
            raise integrity_error(OrigFalso("23503"))
    assert "relación" in exc.value.detail
