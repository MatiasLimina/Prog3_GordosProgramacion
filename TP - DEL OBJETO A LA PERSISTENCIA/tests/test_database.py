import secrets
from types import SimpleNamespace

import pytest
from sqlmodel import SQLModel

import app.core.database as db
from app.core.config import Settings
from app.core.database import crear_fabrica_sesiones, crear_motor, get_session


def _settings(**extra) -> Settings:
    """Settings válido y aislado del entorno y del .env real."""
    return Settings(
        _env_file=None,
        postgres_user="u", postgres_password="p", postgres_db="db",
        jwt_secret=secrets.token_urlsafe(48),
        **extra,
    )


def test_naming_convention_de_constraints():
    nc = SQLModel.metadata.naming_convention
    assert nc["pk"] == "pk_%(table_name)s"
    assert nc["uq"] == "uq_%(table_name)s_%(column_0_name)s"
    assert nc["ck"] == "ck_%(table_name)s_%(constraint_name)s"
    assert nc["fk"] == "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
    assert nc["ix"] == "ix_%(column_0_label)s"


@pytest.fixture
def espia_create_async_engine(monkeypatch):
    """Registra los argumentos con que se llama a create_async_engine (y lo deja crear el motor)."""
    llamadas = []
    real = db.create_async_engine

    def espia(url, **kw):
        llamadas.append(kw)
        return real(url, **kw)

    monkeypatch.setattr(db, "create_async_engine", espia)
    return llamadas


async def test_motor_con_la_configuracion_por_defecto(espia_create_async_engine):
    motor = crear_motor(_settings())
    try:
        kw = espia_create_async_engine[0]
        assert kw["pool_size"] == 5
        assert kw["max_overflow"] == 10
        assert kw["echo"] is False
        # Sin timeout, /health/ready podría colgar ~60 s si la base no responde.
        assert kw["connect_args"] == {"timeout": 5}
        assert motor.pool.size() == 5
    finally:
        await motor.dispose()


async def test_motor_toma_pool_overflow_y_eco_de_la_configuracion(espia_create_async_engine):
    motor = crear_motor(_settings(db_pool_size=3, db_max_overflow=2, sql_echo=True))
    try:
        kw = espia_create_async_engine[0]
        assert (kw["pool_size"], kw["max_overflow"]) == (3, 2)
        assert motor.pool.size() == 3
        assert motor.echo is True
    finally:
        await motor.dispose()


async def test_motor_usa_la_url_de_la_configuracion():
    settings = _settings(postgres_host="db.local", postgres_port=5433)
    motor = crear_motor(settings)
    try:
        assert motor.url.render_as_string(hide_password=False) == settings.database_url
    finally:
        await motor.dispose()


async def test_fabrica_de_sesiones_no_expira_al_commit():
    motor = crear_motor(_settings())
    try:
        fabrica = crear_fabrica_sesiones(motor)
        assert fabrica.kw["expire_on_commit"] is False
        async with fabrica() as sesion:
            assert sesion.sync_session.expire_on_commit is False
            assert sesion.bind is motor
    finally:
        await motor.dispose()


# --- get_session (caracterización: ya cumplía, la spec lo fija) --------------------


class SesionRegistradora:
    """Sesión falsa que anota si se cerró."""

    def __init__(self):
        self.cerrada = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.cerrada = True


def _request_con_fabrica():
    sesiones = []

    def fabrica():
        sesion = SesionRegistradora()
        sesiones.append(sesion)
        return sesion

    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(sessionmaker=fabrica)))
    return request, sesiones


async def test_get_session_cierra_la_sesion_al_terminar_la_peticion():
    request, sesiones = _request_con_fabrica()
    gen = get_session(request)
    sesion = await anext(gen)
    assert sesion is sesiones[0] and not sesion.cerrada
    with pytest.raises(StopAsyncIteration):
        await anext(gen)
    assert sesion.cerrada


async def test_get_session_cierra_la_sesion_aunque_el_manejador_falle():
    request, sesiones = _request_con_fabrica()
    gen = get_session(request)
    await anext(gen)
    with pytest.raises(ValueError):
        await gen.athrow(ValueError("falla del manejador"))
    assert sesiones[0].cerrada


async def test_get_session_entrega_una_sesion_distinta_por_peticion():
    request, sesiones = _request_con_fabrica()
    primera = await anext(get_session(request))
    segunda = await anext(get_session(request))
    assert primera is not segunda
    assert len(sesiones) == 2
