"""UnitOfWork base: confirma al salir del bloque, revierte ante cualquier excepción.

Sin base: una sesión falsa registra qué se le pidió (mismo estilo que tests/test_errors.py).
"""
import ast
import inspect
from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError

import app.core.unit_of_work as modulo_uow
from app.core.errors import Conflicto
from app.core.unit_of_work import UnitOfWork

TEXTO_INTERNO = 'duplicate key value violates unique constraint "uq_x"'


class OrigFalso(Exception):
    """Imita el `orig` de SQLAlchemy con asyncpg."""

    def __init__(self, sqlstate=None, constraint_name=None):
        super().__init__(TEXTO_INTERNO)
        self.sqlstate = sqlstate
        if constraint_name is not None:
            self.constraint_name = constraint_name


def integrity_error(sqlstate="23505", constraint="uq_x"):
    return IntegrityError("INSERT ...", {}, OrigFalso(sqlstate, constraint))


class StockInsuficiente(Exception):
    """Excepción de negocio propia del test."""


class SesionFalsa:
    def __init__(self, error_en_commit=None):
        self.error_en_commit = error_en_commit
        self.commits = 0
        self.rollbacks = 0
        self.closes = 0
        self.begins = 0
        self.info = {}  # como `AsyncSession.info`: el UoW marca ahí que hay un bloque abierto

    async def commit(self):
        self.commits += 1
        if self.error_en_commit:
            raise self.error_en_commit

    async def rollback(self):
        self.rollbacks += 1

    async def close(self):
        self.closes += 1

    async def begin(self):
        self.begins += 1


class UoWPrueba(UnitOfWork):
    MENSAJES: ClassVar[Mapping[str, str]] = {"uq_x": "Ya existe."}


class OtroUoWPrueba(UnitOfWork):
    pass


def contadores(s):
    return (s.commits, s.rollbacks, s.closes, s.begins)


# ---- commit / rollback / no cerrar ----

async def test_bloque_sin_error_confirma_una_vez_y_no_cierra_ni_abre_transaccion():
    s = SesionFalsa()
    async with UoWPrueba(s):
        pass
    assert contadores(s) == (1, 0, 0, 0)


async def test_bloque_con_excepcion_revierte_y_deja_pasar_el_mismo_objeto():
    s = SesionFalsa()
    error = ValueError("falló")
    with pytest.raises(ValueError) as exc:
        async with UoWPrueba(s):
            raise error
    assert exc.value is error
    assert contadores(s) == (0, 1, 0, 0)


async def test_excepcion_de_negocio_revierte_sin_traducir():
    s = SesionFalsa()
    error = StockInsuficiente("no alcanza")
    with pytest.raises(StockInsuficiente) as exc:
        async with UoWPrueba(s):
            raise error
    assert exc.value is error
    assert contadores(s) == (0, 1, 0, 0)


async def test_http_exception_revierte_y_sigue_igual():
    s = SesionFalsa()
    error = HTTPException(status_code=404, detail="No existe.")
    with pytest.raises(HTTPException) as exc:
        async with UoWPrueba(s):
            raise error
    assert exc.value is error
    assert contadores(s) == (0, 1, 0, 0)


async def test_entrega_la_misma_instancia_y_expone_la_sesion():
    s = SesionFalsa()
    uow = UoWPrueba(s)
    async with uow as u:
        assert u is uow
    assert uow.session is s


def test_no_tiene_commit_ni_rollback_publicos():
    assert not hasattr(UnitOfWork, "commit")
    assert not hasattr(UnitOfWork, "rollback")


def test_el_modulo_no_importa_fastapi():
    arbol = ast.parse(Path(inspect.getsourcefile(modulo_uow)).read_text(encoding="utf-8"))
    importados = {
        (n.module if isinstance(n, ast.ImportFrom) else a.name).split(".")[0]
        for n in ast.walk(arbol)
        if isinstance(n, (ast.Import, ast.ImportFrom))
        for a in (n.names if isinstance(n, ast.Import) else [n])
        if not (isinstance(n, ast.ImportFrom) and n.level)
    }
    assert "fastapi" not in importados


# ---- anidado y reuso ----

async def test_bloque_anidado_con_la_misma_instancia_lanza_runtime_error_y_el_externo_revierte():
    s = SesionFalsa()
    uow = UoWPrueba(s)
    with pytest.raises(RuntimeError):
        async with uow:  # noqa: SIM117  el anidado es justamente lo que se prueba
            async with uow:
                pass
    assert contadores(s) == (0, 1, 0, 0)


@pytest.mark.parametrize("clase_interna", [UoWPrueba, OtroUoWPrueba])
async def test_bloque_anidado_con_otro_uow_sobre_la_misma_sesion_lanza_runtime_error_sin_commits(clase_interna):
    # La guarda es por sesión: dos UoW (p. ej. UoWADep + UoWBDep en un handler) comparten
    # transacción, y el bloque interno confirmaría a medias la operación del externo.
    s = SesionFalsa()
    externo = UoWPrueba(s)
    interno = clase_interna(s)
    with pytest.raises(RuntimeError):
        async with externo:  # noqa: SIM117  el anidado es justamente lo que se prueba
            async with interno:
                pass
    assert contadores(s) == (0, 1, 0, 0)


async def test_bloques_sucesivos_con_dos_uow_distintos_sobre_la_misma_sesion_confirman_cada_uno():
    s = SesionFalsa()
    async with UoWPrueba(s):
        pass
    async with OtroUoWPrueba(s):
        pass
    assert s.commits == 2


async def test_tras_un_bloque_fallido_otro_uow_sobre_la_misma_sesion_puede_abrir_bloque():
    s = SesionFalsa()
    with pytest.raises(ValueError):
        async with UoWPrueba(s):
            raise ValueError("falló")
    async with OtroUoWPrueba(s):
        pass
    assert (s.commits, s.rollbacks) == (1, 1)


async def test_uow_sobre_sesiones_distintas_no_se_bloquean_entre_si():
    s1, s2 = SesionFalsa(), SesionFalsa()
    async with UoWPrueba(s1), OtroUoWPrueba(s2):
        pass
    assert (s1.commits, s2.commits) == (1, 1)


async def test_bloques_sucesivos_con_la_misma_instancia_confirman_cada_uno():
    s = SesionFalsa()
    uow = UoWPrueba(s)
    async with uow:
        pass
    async with uow:
        pass
    assert s.commits == 2


async def test_tras_un_bloque_fallido_otro_bloque_sucesivo_confirma():
    s = SesionFalsa()
    uow = UoWPrueba(s)
    with pytest.raises(ValueError):
        async with uow:
            raise ValueError("falló")
    async with uow:
        pass
    assert (s.commits, s.rollbacks) == (1, 1)


async def test_si_el_commit_falla_el_bloque_queda_libre_para_reusar():
    s = SesionFalsa(error_en_commit=RuntimeError("commit roto"))
    uow = UoWPrueba(s)
    with pytest.raises(RuntimeError, match="commit roto"):
        async with uow:
            pass
    s.error_en_commit = None
    async with uow:
        pass
    assert s.commits == 2


# ---- integridad: IntegrityError -> Conflicto ----

async def test_integrity_error_dentro_del_bloque_se_traduce_a_conflicto():
    s = SesionFalsa()
    with pytest.raises(Conflicto) as exc:
        async with UoWPrueba(s):
            raise integrity_error()
    assert not isinstance(exc.value, HTTPException)
    assert exc.value.mensaje == "Ya existe."
    assert (s.commits, s.rollbacks) == (0, 1)
    assert exc.value.__cause__ is None
    assert exc.value.__suppress_context__ is True


async def test_integrity_error_en_el_commit_se_traduce_a_conflicto():
    s = SesionFalsa(error_en_commit=integrity_error())
    with pytest.raises(Conflicto) as exc:
        async with UoWPrueba(s):
            pass
    assert exc.value.mensaje == "Ya existe."
    assert (s.commits, s.rollbacks) == (1, 1)
    assert exc.value.__cause__ is None
    assert exc.value.__suppress_context__ is True


async def test_constraint_desconocida_usa_el_mensaje_generico_de_unicidad():
    s = SesionFalsa()
    with pytest.raises(Conflicto) as exc:
        async with UoWPrueba(s):
            raise integrity_error("23505", "uq_desconocida")
    assert exc.value.mensaje == "Ya existe un registro con un valor único repetido."


async def test_el_mensaje_no_filtra_constraint_ni_texto_de_la_base():
    s = SesionFalsa()
    with pytest.raises(Conflicto) as exc:
        async with UoWPrueba(s):
            raise integrity_error("23505", "uq_desconocida")
    assert "uq_desconocida" not in exc.value.mensaje
    assert "duplicate key" not in exc.value.mensaje
    assert "INSERT" not in exc.value.mensaje


async def test_uow_sin_mensajes_propios_usa_diccionario_vacio_y_mensaje_por_sqlstate():
    assert UnitOfWork.MENSAJES == {}
    s = SesionFalsa()
    with pytest.raises(Conflicto) as exc:
        async with UnitOfWork(s):
            raise integrity_error("23503", "fk_x")
    assert exc.value.mensaje == "El registro referencia o depende de otro que no permite la relación."


async def test_error_operacional_en_el_commit_revierte_y_no_se_traduce():
    error = OperationalError("COMMIT", {}, OrigFalso())
    s = SesionFalsa(error_en_commit=error)
    with pytest.raises(OperationalError) as exc:
        async with UoWPrueba(s):
            pass
    assert exc.value is error
    assert (s.commits, s.rollbacks) == (1, 1)
