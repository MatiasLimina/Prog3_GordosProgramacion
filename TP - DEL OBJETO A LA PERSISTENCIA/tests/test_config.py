import os
import secrets
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy.engine import make_url

from app.core.config import Settings, get_settings

# Todas las variables que lee (o que alguna vez leyó) la configuración: cada test
# parte de un entorno sin ninguna y sin el .env real (cwd = carpeta temporal).
VARIABLES = (
    "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_HOST", "POSTGRES_PORT",
    "JWT_SECRET", "JWT_EXPIRE_MINUTES", "BCRYPT_COST", "BCRYPT_MAX_CONCURRENTES",
    "COOKIE_SECURE", "DB_POOL_SIZE", "DB_MAX_OVERFLOW", "SQL_ECHO",
    "DATABASE_URL", "DB_ECHO", "REQUIRE_TEST_DB",
)
JWT_VALIDA = secrets.token_urlsafe(48)  # generada en cada corrida: ningún secreto en el repo


@pytest.fixture
def entorno(monkeypatch, tmp_path):
    """Entorno vacío, aislado del .env real, con un helper para fijar variables."""
    for nombre in VARIABLES:
        monkeypatch.delenv(nombre, raising=False)
    monkeypatch.chdir(tmp_path)

    def fijar(**variables):
        for nombre, valor in variables.items():
            monkeypatch.setenv(nombre, str(valor))

    return fijar


@pytest.fixture
def obligatorias(entorno):
    """Entorno con sólo las variables obligatorias definidas."""
    entorno(POSTGRES_USER="u", POSTGRES_PASSWORD="p", POSTGRES_DB="db", JWT_SECRET=JWT_VALIDA)
    return entorno


# --- URL de la base --------------------------------------------------------------


def test_url_armada_con_las_cinco_variables(obligatorias):
    obligatorias(POSTGRES_HOST="db.local", POSTGRES_PORT=5433)
    assert get_settings().database_url == "postgresql+asyncpg://u:p@db.local:5433/db"


def test_host_y_puerto_por_defecto(obligatorias):
    url = make_url(get_settings().database_url)
    assert (url.host, url.port) == ("localhost", 5432)


def test_contrasena_con_caracteres_reservados_se_recupera_intacta(obligatorias):
    # '@', '/' y '%' a la vez: un f-string rompería la URL; URL.create los escapa.
    obligatorias(POSTGRES_PASSWORD="p@ss/w%rd", POSTGRES_HOST="db.local")
    url = make_url(get_settings().database_url)
    assert (url.password, url.host, url.database) == ("p@ss/w%rd", "db.local", "db")


def test_el_entorno_pisa_al_archivo_env(obligatorias, tmp_path):
    (tmp_path / ".env").write_text("POSTGRES_DB=libreria\n", encoding="utf-8")
    obligatorias(POSTGRES_DB="libreria_test")
    assert make_url(get_settings().database_url).database == "libreria_test"


def test_lee_las_variables_del_archivo_env(entorno, tmp_path):
    (tmp_path / ".env").write_text(
        f"POSTGRES_USER=u\nPOSTGRES_PASSWORD=p\nPOSTGRES_DB=desde_env\nJWT_SECRET={JWT_VALIDA}\n",
        encoding="utf-8",
    )
    assert make_url(get_settings().database_url).database == "desde_env"


def test_variables_viejas_o_ajenas_en_env_no_rompen_ni_influyen(obligatorias, tmp_path):
    (tmp_path / ".env").write_text(
        "DATABASE_URL=postgresql+asyncpg://x:y@otro:1/otra\nDB_ECHO=true\nREQUIRE_TEST_DB=1\n",
        encoding="utf-8",
    )
    s = get_settings()
    assert make_url(s.database_url).host == "localhost"  # no sale de DATABASE_URL
    assert s.sql_echo is False  # DB_ECHO ya no se lee


def test_variables_viejas_en_el_entorno_tampoco_influyen(obligatorias):
    obligatorias(DATABASE_URL="postgresql+asyncpg://x:y@otro:1/otra", DB_ECHO="true")
    s = get_settings()
    assert make_url(s.database_url).database == "db"
    assert s.sql_echo is False


# --- Secretos y obligatorias -----------------------------------------------------


def test_sin_jwt_secret_el_error_lo_nombra(obligatorias, monkeypatch):
    monkeypatch.delenv("JWT_SECRET")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        get_settings()


def test_sin_postgres_password_el_error_lo_nombra(obligatorias, monkeypatch):
    monkeypatch.delenv("POSTGRES_PASSWORD")
    with pytest.raises(RuntimeError, match="POSTGRES_PASSWORD"):
        get_settings()


@pytest.mark.parametrize("variable", ["POSTGRES_USER", "POSTGRES_DB"])
def test_sin_usuario_o_base_el_error_nombra_la_que_falta(obligatorias, monkeypatch, variable):
    monkeypatch.delenv(variable)
    with pytest.raises(RuntimeError, match=variable):
        get_settings()


@pytest.mark.parametrize("variable", ["JWT_SECRET", "POSTGRES_PASSWORD"])
def test_secreto_vacio_en_env_falla_como_si_faltara(entorno, tmp_path, variable):
    lineas = {
        "POSTGRES_USER": "u", "POSTGRES_PASSWORD": "p", "POSTGRES_DB": "db", "JWT_SECRET": JWT_VALIDA,
    }
    lineas[variable] = ""
    (tmp_path / ".env").write_text("".join(f"{k}={v}\n" for k, v in lineas.items()), encoding="utf-8")
    with pytest.raises(RuntimeError, match=variable):
        get_settings()


def test_jwt_secret_de_31_caracteres_falla_y_de_32_pasa(obligatorias):
    obligatorias(JWT_SECRET="x" * 31)
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        get_settings()
    obligatorias(JWT_SECRET="x" * 32)
    assert get_settings().jwt_secret.get_secret_value() == "x" * 32


def test_el_error_no_contiene_el_valor_de_ninguna_variable(obligatorias, monkeypatch):
    obligatorias(POSTGRES_PASSWORD="secreto-de-prueba")
    monkeypatch.delenv("JWT_SECRET")
    with pytest.raises(RuntimeError) as exc:
        get_settings()
    assert "JWT_SECRET" in str(exc.value)
    assert "secreto-de-prueba" not in str(exc.value)


def test_el_error_por_clave_corta_no_muestra_la_clave(obligatorias):
    corta = "clave-corta-y-secreta"
    obligatorias(JWT_SECRET=corta)
    with pytest.raises(RuntimeError) as exc:
        get_settings()
    assert corta not in str(exc.value)
    assert exc.value.__cause__ is None  # `from None`: el error original de pydantic no viaja


def test_repr_no_muestra_los_secretos(entorno):
    entorno(POSTGRES_USER="u", POSTGRES_PASSWORD="clave-db-secreta", POSTGRES_DB="db", JWT_SECRET=JWT_VALIDA)
    texto = repr(get_settings())
    assert "clave-db-secreta" not in texto
    assert JWT_VALIDA not in texto


def test_serializar_no_muestra_los_secretos(entorno):
    # `app.state.settings` queda a mano de otros módulos: un log o una respuesta
    # que lo vuelque no puede filtrar la URL con la contraseña.
    entorno(POSTGRES_USER="u", POSTGRES_PASSWORD="clave-db-secreta", POSTGRES_DB="db", JWT_SECRET=JWT_VALIDA)
    s = get_settings()
    for texto in (str(s.model_dump()), s.model_dump_json()):
        assert "clave-db-secreta" not in texto
        assert JWT_VALIDA not in texto
    assert "database_url" not in s.model_dump()
    # La propiedad sigue disponible para quien la pide de forma explícita.
    assert "clave-db-secreta" in s.database_url


# --- Parámetros operativos -------------------------------------------------------


def test_valores_por_defecto(obligatorias):
    s = get_settings()
    assert (s.bcrypt_cost, s.bcrypt_max_concurrentes, s.cookie_secure, s.jwt_expire_minutes) == (
        12, 4, False, 60,
    )
    assert (s.db_pool_size, s.db_max_overflow, s.sql_echo) == (5, 10, False)


def test_valores_tomados_del_entorno(obligatorias):
    obligatorias(
        BCRYPT_COST=4, BCRYPT_MAX_CONCURRENTES=2, COOKIE_SECURE="true", JWT_EXPIRE_MINUTES=15,
        DB_POOL_SIZE=2, DB_MAX_OVERFLOW=1, SQL_ECHO="true",
    )
    s = get_settings()
    assert (s.bcrypt_cost, s.bcrypt_max_concurrentes, s.cookie_secure, s.jwt_expire_minutes) == (
        4, 2, True, 15,
    )
    assert (s.db_pool_size, s.db_max_overflow, s.sql_echo) == (2, 1, True)


@pytest.mark.parametrize(
    ("variable", "valor"),
    [
        ("BCRYPT_COST", 3), ("BCRYPT_COST", 32),
        ("BCRYPT_MAX_CONCURRENTES", 0),
        ("DB_POOL_SIZE", 0),
        ("DB_MAX_OVERFLOW", -1),
        ("JWT_EXPIRE_MINUTES", 0),
    ],
)
def test_valor_fuera_de_rango_falla_nombrando_la_variable(obligatorias, variable, valor):
    obligatorias(**{variable: valor})
    with pytest.raises(RuntimeError, match=variable):
        get_settings()


@pytest.mark.parametrize(
    ("variable", "valor", "campo"),
    [
        ("BCRYPT_COST", 4, "bcrypt_cost"), ("BCRYPT_COST", 31, "bcrypt_cost"),
        ("BCRYPT_MAX_CONCURRENTES", 1, "bcrypt_max_concurrentes"),
        ("DB_POOL_SIZE", 1, "db_pool_size"), ("DB_MAX_OVERFLOW", 0, "db_max_overflow"),
        ("JWT_EXPIRE_MINUTES", 1, "jwt_expire_minutes"),
    ],
)
def test_los_limites_exactos_son_validos(obligatorias, variable, valor, campo):
    obligatorias(**{variable: valor})
    assert getattr(get_settings(), campo) == valor


@pytest.mark.parametrize("valor", ["true", "TRUE", "1", "yes", "Yes"])
def test_sql_echo_verdadero(obligatorias, valor):
    obligatorias(SQL_ECHO=valor)
    assert get_settings().sql_echo is True


@pytest.mark.parametrize("valor", ["false", "FALSE", "0", "no", "No"])
def test_sql_echo_falso(obligatorias, valor):
    obligatorias(SQL_ECHO=valor)
    assert get_settings().sql_echo is False


def test_el_algoritmo_del_token_no_es_configuracion():
    # CHG-10 lo fija como constante (HS256); no debe poder cambiarse por entorno.
    assert not [c for c in Settings.model_fields if "algorithm" in c or "algoritmo" in c]


# --- Importar no lee la configuración --------------------------------------------


def test_importar_la_app_sin_variables_ni_env_no_falla(tmp_path):
    raiz = Path(__file__).resolve().parent.parent
    # Entorno mínimo: en Windows Python necesita SYSTEMROOT para arrancar.
    entorno = {"PYTHONPATH": str(raiz), "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}
    resultado = subprocess.run(
        [sys.executable, "-c", "import app.main"],
        cwd=tmp_path, env=entorno, capture_output=True, text=True, timeout=120, check=False,
    )
    assert resultado.returncode == 0, resultado.stderr
