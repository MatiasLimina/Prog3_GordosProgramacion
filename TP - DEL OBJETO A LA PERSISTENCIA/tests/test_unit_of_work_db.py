"""UnitOfWork con base real: rollback ante excepciones y sesión abierta después del bloque.

Dos pruebas del DoD de CHG-04: «rollback cuando hay una excepción» y «la sesión sigue
abierta después del bloque».
"""
from collections.abc import Mapping
from typing import ClassVar

import pytest
from sqlalchemy import inspect, text

from app.core.errors import Conflicto
from app.core.repository import BaseRepository
from app.core.unit_of_work import UnitOfWork
from app.modules.editoriales.models import Editorial

pytestmark = pytest.mark.db


class UoWEditoriales(UnitOfWork):
    MENSAJES: ClassVar[Mapping[str, str]] = {"uq_editorial_nombre": "Ya existe una editorial con ese nombre."}

    def __init__(self, session):
        super().__init__(session)
        self.editoriales = BaseRepository(session, Editorial)


class StockInsuficiente(Exception):
    """Excepción de negocio propia del test."""


async def contar_editoriales(sessionmaker) -> int:
    """Cuenta desde OTRA sesión: sólo ve lo que se confirmó."""
    async with sessionmaker() as otra:
        return (await otra.execute(text("SELECT count(*) FROM editorial"))).scalar()


# ---- DoD 1/2: rollback cuando hay una excepción ----

async def test_excepcion_despues_del_flush_no_deja_ninguna_fila(sessionmaker_test):
    async with sessionmaker_test() as session:
        with pytest.raises(ValueError):
            async with UoWEditoriales(session) as uow:
                await uow.editoriales.add(Editorial(nombre="A", pais="AR"))
                raise ValueError("falló")
    assert await contar_editoriales(sessionmaker_test) == 0


async def test_bloque_exitoso_confirma_las_dos_escrituras(sessionmaker_test):
    async with sessionmaker_test() as session, UoWEditoriales(session) as uow:
        await uow.editoriales.add(Editorial(nombre="A", pais="AR"))
        await uow.editoriales.add(Editorial(nombre="B", pais="UY"))
    assert await contar_editoriales(sessionmaker_test) == 2


async def test_dos_uow_anidados_sobre_la_misma_sesion_real_no_confirman_nada(sessionmaker_test):
    async with sessionmaker_test() as session:
        with pytest.raises(RuntimeError):
            async with UoWEditoriales(session) as externo:
                await externo.editoriales.add(Editorial(nombre="A", pais="AR"))
                async with UoWEditoriales(session):  # otro UoW, misma sesión: confirmaría a medias
                    pass
    assert await contar_editoriales(sessionmaker_test) == 0


async def test_choque_en_la_segunda_escritura_da_conflicto_y_ninguna_fila(sessionmaker_test):
    async with sessionmaker_test() as session:
        with pytest.raises(Conflicto) as exc:
            async with UoWEditoriales(session) as uow:
                await uow.editoriales.add(Editorial(nombre="A", pais="AR"))
                await uow.editoriales.add(Editorial(nombre="A", pais="UY"))
    assert exc.value.mensaje == "Ya existe una editorial con ese nombre."
    assert "uq_editorial_nombre" not in exc.value.mensaje
    assert await contar_editoriales(sessionmaker_test) == 0


async def test_consulta_previa_con_la_sesion_no_impide_el_bloque(sessionmaker_test):
    # El autobegin ya abrió la transacción: el UoW no llama a `session.begin()`.
    async with sessionmaker_test() as session:
        await session.execute(text("SELECT 1"))
        async with UoWEditoriales(session) as uow:
            await uow.editoriales.add(Editorial(nombre="A", pais="AR"))
    assert await contar_editoriales(sessionmaker_test) == 1


async def test_excepcion_de_negocio_revierte_todo_y_llega_sin_traducir(sessionmaker_test):
    error = StockInsuficiente("no alcanza")
    async with sessionmaker_test() as session:
        with pytest.raises(StockInsuficiente) as exc:
            async with UoWEditoriales(session) as uow:
                await uow.editoriales.add(Editorial(nombre="A", pais="AR"))
                await uow.editoriales.add(Editorial(nombre="B", pais="UY"))
                raise error
    assert exc.value is error
    assert await contar_editoriales(sessionmaker_test) == 0


async def test_tras_un_rollback_los_objetos_quedan_expirados_pero_el_id_guardado_sirve(sessionmaker_test):
    # Caracterización de R7: rollback() expira aunque expire_on_commit=False.
    async with sessionmaker_test() as session:
        async with UoWEditoriales(session) as uow:
            editorial = await uow.editoriales.add(Editorial(nombre="A", pais="AR"))
        editorial_id = editorial.id  # valor simple, guardado ANTES de un posible rollback
        assert not inspect(editorial).expired
        with pytest.raises(ValueError):
            async with UoWEditoriales(session):
                # Con la transacción abierta (una dependencia ya consultó con esta sesión)
                # el rollback expira todo; sin transacción abierta no habría nada que revertir.
                await session.execute(text("SELECT 1"))
                raise ValueError("falló")
        assert inspect(editorial).expired
        assert editorial_id == 1
        assert (await session.execute(text("SELECT nombre FROM editorial WHERE id = :i"), {"i": editorial_id})).scalar() == "A"


# ---- DoD 2/2: la sesión sigue abierta después del bloque ----

class EspiaDeCierre:
    """Envuelve `session.close` y cuenta las llamadas."""

    def __init__(self, session):
        self.llamadas = 0
        self._original = session.close
        session.close = self

    async def __call__(self):
        self.llamadas += 1
        return await self._original()


async def test_la_sesion_sigue_abierta_despues_de_un_bloque_exitoso(sessionmaker_test):
    async with sessionmaker_test() as session:
        cierre = EspiaDeCierre(session)
        async with UoWEditoriales(session) as uow:
            editorial = await uow.editoriales.add(Editorial(nombre="A", pais="AR"))
        assert cierre.llamadas == 0
        assert editorial in session  # close() vaciaría la sesión
        assert (await session.execute(text("SELECT 1"))).scalar() == 1


async def test_la_sesion_sigue_abierta_despues_de_un_bloque_que_fallo(sessionmaker_test):
    async with sessionmaker_test() as session:
        cierre = EspiaDeCierre(session)
        with pytest.raises(ValueError):
            async with UoWEditoriales(session) as uow:
                await uow.editoriales.add(Editorial(nombre="A", pais="AR"))
                raise ValueError("falló")
        assert cierre.llamadas == 0
        assert (await session.execute(text("SELECT 1"))).scalar() == 1
