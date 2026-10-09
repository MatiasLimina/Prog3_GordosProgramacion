from sqlmodel import SQLModel

import app.core.database  # noqa: F401  (al importarlo se fija la convención)
from app.core.database import crear_engine_y_sessionmaker


def test_naming_convention_de_constraints():
    nc = SQLModel.metadata.naming_convention
    assert nc["pk"] == "pk_%(table_name)s"
    assert nc["uq"] == "uq_%(table_name)s_%(column_0_name)s"
    assert nc["ck"] == "ck_%(table_name)s_%(constraint_name)s"
    assert nc["fk"] == "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
    assert nc["ix"] == "ix_%(column_0_label)s"


async def test_sessionmaker_no_expira_al_commit_y_respeta_echo():
    engine, sessionmaker = crear_engine_y_sessionmaker(
        "postgresql+asyncpg://u:p@localhost/db", echo=True
    )
    try:
        assert engine.echo is True
        assert sessionmaker.kw["expire_on_commit"] is False
    finally:
        await engine.dispose()
