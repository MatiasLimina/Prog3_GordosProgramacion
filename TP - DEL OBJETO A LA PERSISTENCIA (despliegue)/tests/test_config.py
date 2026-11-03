import pytest

from app.core.config import get_settings


def test_lee_database_url_del_entorno():
    s = get_settings({"DATABASE_URL": "postgresql+asyncpg://u:p@localhost/db"})
    assert s.database_url == "postgresql+asyncpg://u:p@localhost/db"


def test_falta_database_url_da_error_claro():
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        get_settings({})


@pytest.mark.parametrize("valor", ["true", "TRUE", "1", "yes", " Yes "])
def test_db_echo_verdadero(valor):
    assert get_settings({"DATABASE_URL": "x", "DB_ECHO": valor}).db_echo is True


@pytest.mark.parametrize("valor", ["false", "0", "no", "", "cualquier cosa"])
def test_db_echo_falso(valor):
    assert get_settings({"DATABASE_URL": "x", "DB_ECHO": valor}).db_echo is False


def test_db_echo_por_defecto_es_falso():
    assert get_settings({"DATABASE_URL": "x"}).db_echo is False
