"""Configuración de la app, leída del entorno y de un `.env` no versionado.

Decisión: la configuración NO se lee al importar el módulo. `get_settings()` la
construye cuando se la llama (en el lifespan, en Alembic o en el seed), así los
tests pueden importar `app` sin variables definidas y aislar el `.env`.
"""
from typing import Any

from pydantic import (
    Field,
    SecretStr,
    SerializerFunctionWrapHandler,
    ValidationError,
    computed_field,
    model_serializer,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    # extra="ignore": un .env viejo (DATABASE_URL, DB_ECHO, REQUIRE_TEST_DB) no rompe el arranque.
    # hide_input_in_errors: el error de validación nunca incluye el valor de una variable.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    # Sin valor por defecto (y no vacíos): si falta alguno, la app no arranca.
    postgres_user: str = Field(min_length=1)
    postgres_password: SecretStr = Field(min_length=1)
    postgres_db: str = Field(min_length=1)
    postgres_host: str = "localhost"
    postgres_port: int = Field(default=5432, ge=1, le=65535)

    # Clave de firma de los tokens: obligatoria y de al menos 32 caracteres, así una
    # línea `JWT_SECRET=` vacía en .env no pasa como "definida".
    jwt_secret: SecretStr = Field(min_length=32)
    # El algoritmo de firma NO es configuración: CHG-10 lo fija como constante (HS256).
    jwt_expire_minutes: int = Field(default=60, ge=1)

    # bcrypt: costo (rango que acepta la librería) y cuántas llamadas pueden correr a la vez.
    bcrypt_cost: int = Field(default=12, ge=4, le=31)
    bcrypt_max_concurrentes: int = Field(default=4, ge=1)

    # Local se sirve por http: la cookie sólo es Secure si se lo pide (producción).
    cookie_secure: bool = False

    # Pool de conexiones y eco de SQL (muestra las consultas emitidas en consola).
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=10, ge=0)
    sql_echo: bool = False

    @computed_field(repr=False)  # repr=False: la URL lleva la contraseña
    @property
    def database_url(self) -> str:
        # URL.create escapa los caracteres reservados (@, /, %) de usuario y contraseña;
        # un f-string los rompería.
        return URL.create(
            "postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)

    @model_serializer(mode="wrap")
    def _sin_url(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        # Un computed_field entra en model_dump()/model_dump_json() y repr=False no lo
        # evita: se quita la URL (lleva la contraseña en claro) de toda serialización.
        datos = handler(self)
        datos.pop("database_url", None)
        return datos


def get_settings() -> Settings:
    """Construye la configuración o falla con un mensaje claro y sin valores."""
    try:
        return Settings()
    except ValidationError as e:
        # Sólo se nombran las variables con problema, nunca sus valores; `from None`
        # evita que el ValidationError original (y su contenido) viaje en el traceback.
        variables = sorted({str(err["loc"][0]).upper() for err in e.errors() if err["loc"]})
        raise RuntimeError(
            f"Configuración incompleta o inválida: {', '.join(variables)}. "
            "Copiá env.example a .env y completalo."
        ) from None
