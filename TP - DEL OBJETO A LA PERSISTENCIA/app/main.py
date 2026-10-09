from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.database import crear_engine_y_sessionmaker
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


app = FastAPI(title="Librería", lifespan=lifespan)

app.include_router(health_router)
