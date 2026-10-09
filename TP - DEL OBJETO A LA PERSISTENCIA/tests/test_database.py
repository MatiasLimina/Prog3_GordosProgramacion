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


def test_engine_tiene_timeout_de_conexion(monkeypatch):
    # Sin timeout, /health/ready podría colgar ~60 s si la base no responde.
    capturado = {}
    import app.core.database as db

    def falso(url, **kw):
        capturado.update(kw)
        return object.__new__(db.AsyncEngine)

    monkeypatch.setattr(db, "create_async_engine", falso)
    monkeypatch.setattr(db, "async_sessionmaker", lambda *a, **k: None)
    db.crear_engine_y_sessionmaker("postgresql+asyncpg://u:p@localhost/db")
    assert capturado["connect_args"] == {"timeout": 5}
