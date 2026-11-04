"""Repositorios con base real: `BaseRepository` sobre `editorial` y `SoftDeleteRepository`
sobre un modelo sólo de test (`Borrable`, tabla `prueba_borrable`)."""
from datetime import UTC

import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.orm import selectinload

from app.core.repository import BaseRepository, SoftDeleteRepository
from app.modules.editoriales.models import Editorial
from tests.modelos_prueba import (
    BORRAR_TABLAS_PADRE_HIJO,
    CREAR_TABLA_BORRABLE,
    CREAR_TABLAS_PADRE_HIJO,
    Borrable,
    Hijo,
    Padre,
)

pytestmark = pytest.mark.db


async def contar(sessionmaker, tabla="editorial") -> int:
    """Cuenta desde OTRA sesión: sólo ve lo confirmado."""
    async with sessionmaker() as otra:
        return (await otra.execute(text(f"SELECT count(*) FROM {tabla}"))).scalar()


async def sembrar(session, pais_por_editorial):
    repo = BaseRepository(session, Editorial)
    return [
        await repo.add(Editorial(nombre=f"E{i}", pais=pais))
        for i, pais in enumerate(pais_por_editorial, start=1)
    ]


class EspiaDeTransaccion:
    """Cuenta commit/rollback/close que reciba la sesión."""

    def __init__(self, session):
        self.llamadas = {"commit": 0, "rollback": 0, "close": 0}
        for nombre in self.llamadas:
            original = getattr(session, nombre)
            setattr(session, nombre, self._envolver(nombre, original))

    def _envolver(self, nombre, original):
        async def envoltura(*args, **kwargs):
            self.llamadas[nombre] += 1
            return await original(*args, **kwargs)

        return envoltura


# ---- BaseRepository: add / update / delete no confirman ----

async def test_add_asigna_id_y_no_confirma(sessionmaker_test):
    async with sessionmaker_test() as session:
        repo = BaseRepository(session, Editorial)
        editorial = await repo.add(Editorial(nombre="A", pais="AR"))
        assert editorial.id == 1
        await session.rollback()
    assert await contar(sessionmaker_test) == 0


async def test_add_update_y_delete_no_llaman_a_commit_rollback_ni_close(sessionmaker_test):
    async with sessionmaker_test() as session:
        espia = EspiaDeTransaccion(session)
        repo = BaseRepository(session, Editorial)
        editorial = await repo.add(Editorial(nombre="A", pais="AR"))
        await repo.update(editorial, {"pais": "UY"})
        await repo.delete(editorial)
        assert espia.llamadas == {"commit": 0, "rollback": 0, "close": 0}


# ---- get_by_id ----

async def test_get_by_id_existente_devuelve_la_entidad(sessionmaker_test):
    async with sessionmaker_test() as session:
        [e1, _] = await sembrar(session, ["AR", "UY"])
        repo = BaseRepository(session, Editorial)
        assert (await repo.get_by_id(e1.id)).nombre == "E1"
        assert (await repo.get_by_id(2)).nombre == "E2"


async def test_get_by_id_inexistente_devuelve_none(sessionmaker_test):
    async with sessionmaker_test() as session:
        assert await BaseRepository(session, Editorial).get_by_id(999) is None


# ---- get_all / count ----

async def test_get_all_devuelve_todas_ordenadas_por_id(sessionmaker_test):
    async with sessionmaker_test() as session:
        await sembrar(session, ["AR", "UY", "CL"])
        resultado = await BaseRepository(session, Editorial).get_all()
        assert [e.id for e in resultado] == [1, 2, 3]


async def test_get_all_con_offset_y_limit(sessionmaker_test):
    async with sessionmaker_test() as session:
        await sembrar(session, ["AR"] * 5)
        repo = BaseRepository(session, Editorial)
        assert [e.id for e in await repo.get_all(offset=2, limit=2)] == [3, 4]
        assert [e.id for e in await repo.get_all(offset=4, limit=2)] == [5]
        assert await repo.get_all(offset=10, limit=2) == []


async def test_count_cuenta_todas_las_filas(sessionmaker_test):
    async with sessionmaker_test() as session:
        await sembrar(session, ["AR", "UY", "CL"])
        assert await BaseRepository(session, Editorial).count() == 3


async def test_tabla_vacia_cuenta_cero_y_lista_vacia(sessionmaker_test):
    async with sessionmaker_test() as session:
        repo = BaseRepository(session, Editorial)
        assert await repo.count() == 0
        assert await repo.get_all() == []


# ---- update / delete ----

async def test_update_cambia_lo_enviado_conserva_el_resto_y_se_ve_en_la_misma_sesion(sessionmaker_test):
    async with sessionmaker_test() as session:
        [editorial] = await sembrar(session, ["AR"])
        resultado = await BaseRepository(session, Editorial).update(editorial, {"pais": "UY"})
        assert resultado is editorial
        assert (editorial.nombre, editorial.pais) == ("E1", "UY")
        pais = (await session.execute(text("SELECT pais FROM editorial WHERE id = 1"))).scalar()
        assert pais == "UY"


async def test_update_con_otro_campo_conserva_el_pais(sessionmaker_test):
    async with sessionmaker_test() as session:
        [editorial] = await sembrar(session, ["AR"])
        await BaseRepository(session, Editorial).update(editorial, {"nombre": "Nueva"})
        assert (editorial.nombre, editorial.pais) == ("Nueva", "AR")


async def test_delete_quita_la_fila_en_la_misma_transaccion(sessionmaker_test):
    async with sessionmaker_test() as session:
        [e1, e2] = await sembrar(session, ["AR", "UY"])
        repo = BaseRepository(session, Editorial)
        await repo.delete(e1)
        assert await repo.get_by_id(1) is None
        assert (await repo.get_by_id(2)).id == e2.id
        assert await repo.count() == 1


async def test_dos_repositorios_con_la_misma_sesion_ven_sus_escrituras_sin_confirmar(sessionmaker_test):
    async with sessionmaker_test() as session:
        escritor = BaseRepository(session, Editorial)
        lector = BaseRepository(session, Editorial)
        await escritor.add(Editorial(nombre="A", pais="AR"))
        assert await lector.count() == 1
        assert (await lector.get_by_id(1)).nombre == "A"


# ---- punto de extensión: _consulta_base / _listar / _contar ----

class EditorialRepoPrueba(BaseRepository[Editorial]):
    """Imita un repositorio de módulo: métodos nombrados por lo que traen."""

    def __init__(self, session):
        super().__init__(session, Editorial)

    async def buscar_por_pais(self, pais, *, offset=0, limit=None):
        return await self._listar(self._consulta_base().where(Editorial.pais == pais), offset=offset, limit=limit)

    async def contar_por_pais(self, pais):
        return await self._contar(self._consulta_base().where(Editorial.pais == pais))


class PadreRepoPrueba(BaseRepository[Padre]):
    """Igual, sobre un modelo sólo de test: la precarga no depende de `libro` ni de su esquema."""

    def __init__(self, session):
        super().__init__(session, Padre)

    async def get_con_hijos(self, id):
        consulta = self._consulta_base().where(Padre.id == id).options(selectinload(Padre.hijos))
        return (await self.session.execute(consulta)).scalar_one_or_none()


@pytest_asyncio.fixture
async def tablas_padre_hijo(sessionmaker_test):
    """DDL explícito de las tablas de prueba (nunca `create_all`); se borran al terminar."""
    async with sessionmaker_test() as s:
        for sentencia in (*BORRAR_TABLAS_PADRE_HIJO, *CREAR_TABLAS_PADRE_HIJO):
            await s.execute(text(sentencia))
        await s.commit()
    yield sessionmaker_test
    async with sessionmaker_test() as s:
        for sentencia in BORRAR_TABLAS_PADRE_HIJO:
            await s.execute(text(sentencia))
        await s.commit()


async def test_el_total_cuenta_con_los_mismos_filtros_aunque_la_pagina_sea_chica(sessionmaker_test):
    async with sessionmaker_test() as session:
        await sembrar(session, ["AR", "UY", "AR", "UY", "AR"])
        repo = EditorialRepoPrueba(session)
        pagina = await repo.buscar_por_pais("AR", offset=0, limit=1)
        assert [e.id for e in pagina] == [1]
        assert await repo.contar_por_pais("AR") == 3
        assert await repo.contar_por_pais("UY") == 2
        assert await repo.contar_por_pais("CL") == 0
        assert [e.id for e in await repo.buscar_por_pais("AR", offset=1, limit=5)] == [3, 5]


async def test_la_precarga_declarada_en_el_metodo_evita_consultas_al_leer_la_coleccion(tablas_padre_hijo):
    async with tablas_padre_hijo() as session:
        padre = await BaseRepository(session, Padre).add(Padre(nombre="P"))
        await BaseRepository(session, Hijo).add(Hijo(nombre="H1", padre_id=padre.id))
        await BaseRepository(session, Hijo).add(Hijo(nombre="H2", padre_id=padre.id))
        session.expunge_all()  # fuerza la lectura desde la base
        consultas = []
        motor = session.bind.sync_engine
        event.listen(motor, "before_cursor_execute", lambda *a: consultas.append(a[2]))
        cargado = await PadreRepoPrueba(session).get_con_hijos(padre.id)
        antes = len(consultas)
        assert sorted(hijo.nombre for hijo in cargado.hijos) == ["H1", "H2"]
        assert len(consultas) == antes  # leer la colección no emitió ninguna consulta


# ---- SoftDeleteRepository sobre `prueba_borrable` ----

@pytest_asyncio.fixture
async def tabla_borrable(sessionmaker_test):
    """DDL explícito de la tabla de prueba (nunca `create_all`); se borra al terminar."""
    async with sessionmaker_test() as s:
        await s.execute(text("DROP TABLE IF EXISTS prueba_borrable"))
        await s.execute(text(CREAR_TABLA_BORRABLE))
        await s.commit()
    yield sessionmaker_test
    async with sessionmaker_test() as s:
        await s.execute(text("DROP TABLE IF EXISTS prueba_borrable"))
        await s.commit()


async def sembrar_borrables(session, cantidad=3):
    repo = SoftDeleteRepository(session, Borrable)
    return repo, [await repo.add(Borrable(nombre=f"B{i}")) for i in range(1, cantidad + 1)]


async def test_get_all_y_count_ignoran_los_dados_de_baja(tabla_borrable):
    async with tabla_borrable() as session:
        repo, [_, b2, _] = await sembrar_borrables(session)
        await repo.soft_delete(b2)
        assert [b.nombre for b in await repo.get_all()] == ["B1", "B3"]
        assert await repo.count() == 2


async def test_get_by_id_no_trae_al_dado_de_baja_aunque_este_en_el_mapa_de_identidad(tabla_borrable):
    async with tabla_borrable() as session:
        repo, [b1, b2, _] = await sembrar_borrables(session)
        await repo.soft_delete(b2)
        assert b2 in session  # sigue en el mapa de identidad: session.get lo devolvería
        assert await repo.get_by_id(b2.id) is None
        assert (await repo.get_by_id(b1.id)).nombre == "B1"


async def test_get_by_id_including_deleted_trae_al_dado_de_baja(tabla_borrable):
    async with tabla_borrable() as session:
        repo, [_, b2, _] = await sembrar_borrables(session)
        await repo.soft_delete(b2)
        assert (await repo.get_by_id_including_deleted(b2.id)) is b2
        assert await repo.get_by_id_including_deleted(999) is None


async def test_soft_delete_fija_fecha_con_zona_conserva_la_fila_y_no_confirma(tabla_borrable):
    async with tabla_borrable() as session:
        repo, [_, b2, _] = await sembrar_borrables(session)
        resultado = await repo.soft_delete(b2)
        assert resultado is b2
        assert b2.borrado_en is not None
        assert b2.borrado_en.tzinfo is not None
        assert b2.borrado_en.utcoffset() == UTC.utcoffset(None)
        assert (await session.execute(text("SELECT count(*) FROM prueba_borrable"))).scalar() == 3
        await session.rollback()
    assert await contar(tabla_borrable, "prueba_borrable") == 0


async def test_segunda_baja_conserva_la_primera_fecha(tabla_borrable):
    async with tabla_borrable() as session:
        repo, [b1, _, _] = await sembrar_borrables(session)
        await repo.soft_delete(b1)
        primera = b1.borrado_en
        await repo.soft_delete(b1)
        assert b1.borrado_en == primera


async def test_leer_borrado_en_despues_del_flush_no_emite_consultas(tabla_borrable):
    async with tabla_borrable() as session:
        repo, [b1, _, _] = await sembrar_borrables(session)
        consultas = []
        event.listen(session.bind.sync_engine, "before_cursor_execute", lambda *a: consultas.append(a[2]))
        await repo.soft_delete(b1)
        antes = len(consultas)
        assert b1.borrado_en is not None
        assert len(consultas) == antes
