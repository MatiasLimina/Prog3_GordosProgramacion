import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.database import crear_fabrica_sesiones, crear_motor
from app.core.errors import mensaje_para
from app.core.security import calcular_hash_ficticio
import app.models  # noqa: F401  (registra todos los modelos en el metadata)
from app.modules.autores.router import router as autores_router
from app.modules.clientes.router import router as clientes_router
from app.modules.editoriales.router import router as editoriales_router
from app.modules.generos.router import router as generos_router
from app.modules.health.router import router as health_router
from app.modules.libros.router import router as libros_router
from app.modules.ventas.router import router as ventas_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Los recursos se crean una vez al arrancar y viven en app.state; nada se crea al
    # importar el módulo. El esquema NO se crea acá: sólo con `alembic upgrade head`.
    # Si la configuración es inválida, falla acá, antes de crear cualquier recurso.
    settings = get_settings()
    # Hash ficticio del login (RN-08): bcrypt bloquea ~300 ms con costo 12, por eso
    # corre fuera del bucle de eventos; se calcula una sola vez, con el costo real.
    hash_ficticio = await asyncio.to_thread(calcular_hash_ficticio, settings.bcrypt_cost)
    engine = crear_motor(settings)
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessionmaker = crear_fabrica_sesiones(engine)
    app.state.hash_ficticio = hash_ficticio
    # Un único semáforo para todo bcrypt de la app (hash y verificación): acota los hilos
    # que ocupa. Se crea acá y no al importar: cada arranque (y cada bucle de tests) tiene el suyo.
    app.state.semaforo_bcrypt = asyncio.Semaphore(settings.bcrypt_max_concurrentes)
    try:
        yield
    finally:
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
app.include_router(generos_router)
app.include_router(autores_router)
app.include_router(libros_router)
app.include_router(clientes_router)
app.include_router(ventas_router)
