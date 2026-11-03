import pytest
from sqlalchemy import text

pytestmark = pytest.mark.db


async def test_la_base_de_test_arranca_vacia_y_con_esquema(sessionmaker_test):
    async with sessionmaker_test() as s:
        assert (await s.execute(text("SELECT count(*) FROM editorial"))).scalar() == 0
        await s.execute(text("INSERT INTO editorial (nombre, pais) VALUES ('x', 'y')"))
        await s.commit()


async def test_ids_se_reinician_entre_tests(sessionmaker_test):
    async with sessionmaker_test() as s:
        await s.execute(text("INSERT INTO editorial (nombre, pais) VALUES ('z', 'y')"))
        await s.commit()
        assert (await s.execute(text("SELECT id FROM editorial"))).scalar() == 1
