from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.database import crear_engine_y_sessionmaker
from app.core.errors import mensaje_para
import app.models  # noqa: F401  (registra todos los modelos en el metadata)
from app.modules.editoriales.router import router as editoriales_router
from app.modules.health.router import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Motor y sessionmaker se crean una vez al arrancar y viven en app.state.
    # El esquema NO se crea acá: se crea sólo con `alembic upgrade head`.
    settings = get_settings()
    engine, sessionmaker = crear_engine_y_sessionmaker(settings.database_url, settings.db_echo)
    app.state.engine = engine
    app.state.sessionmaker = sessionmaker
    yield
    await engine.dispose()


def registrar_handlers(app: FastAPI) -> None:
    # Red de seguridad: un IntegrityError que no pasó por traducir_integrity
    # igual responde 409 (mensaje genérico por sqlstate), nunca 500 ni texto interno.
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        return JSONResponse(status_code=409, content={"detail": mensaje_para(exc, {})})


app = FastAPI(title="Librería", lifespan=lifespan)
registrar_handlers(app)

app.include_router(health_router)
app.include_router(editoriales_router)
