import asyncio
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.database import crear_fabrica_sesiones, crear_motor
from app.core.dependencies import control_cambio_obligatorio
from app.core.errors import (
    Conflicto,
    DemasiadosIntentos,
    NoAutenticado,
    NoEncontrado,
    PeticionInvalida,
    SinPermiso,
    mensaje_para,
)
from app.core.security import calcular_hash_ficticio
import app.models  # noqa: F401  (registra todos los modelos en el metadata)
from app.modules.autores import router as autores
from app.modules.clientes import router as clientes
from app.modules.editoriales import router as editoriales
from app.modules.generos import router as generos
from app.modules.health.router import router as health_router
from app.modules.libros import router as libros
from app.modules.usuarios.router import auth_router, eventos_router, router as usuarios_router
from app.modules.ventas import router as ventas


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

    # Conflicto lo lanza el UnitOfWork (core no conoce HTTP): mismo 409 y mismo cuerpo
    # que HTTPException, así el cliente no distingue de dónde salió.
    @app.exception_handler(Conflicto)
    async def conflicto_handler(request: Request, exc: Conflicto):
        return JSONResponse(status_code=409, content={"detail": exc.mensaje})

    # PeticionInvalida la lanza el código de negocio (core no conoce HTTP): mismo
    # 422 y mismo cuerpo que HTTPException, así el cliente no distingue el origen.
    @app.exception_handler(PeticionInvalida)
    async def peticion_invalida_handler(request: Request, exc: PeticionInvalida):
        return JSONResponse(status_code=422, content={"detail": exc.mensaje})

    # NoEncontrado la lanzan los servicios cuando el recurso de la ruta no existe (core no conoce
    # HTTP): mismo cuerpo `{"detail": mensaje}` que el resto de los errores.
    @app.exception_handler(NoEncontrado)
    async def no_encontrado_handler(request: Request, exc: NoEncontrado):
        return JSONResponse(status_code=404, content={"detail": exc.mensaje})

    # NoAutenticado y DemasiadosIntentos las lanzan el login y la dependencia del usuario
    # actual (core no conoce HTTP). El 429 lleva `Retry-After` y un detalle fijo.
    @app.exception_handler(NoAutenticado)
    async def no_autenticado_handler(request: Request, exc: NoAutenticado):
        return JSONResponse(status_code=401, content={"detail": exc.mensaje})

    # SinPermiso la lanzan requiere_rol y el control del cambio obligatorio (core no conoce HTTP).
    @app.exception_handler(SinPermiso)
    async def sin_permiso_handler(request: Request, exc: SinPermiso):
        return JSONResponse(status_code=403, content={"detail": exc.mensaje})

    @app.exception_handler(DemasiadosIntentos)
    async def demasiados_intentos_handler(request: Request, exc: DemasiadosIntentos):
        return JSONResponse(
            status_code=429,
            content={"detail": "Demasiados intentos fallidos. Probá de nuevo más tarde."},
            headers={"Retry-After": str(exc.retry_after)},
        )


app = FastAPI(title="Librería", lifespan=lifespan)
registrar_handlers(app)

# Dos grupos de rutas (CHG-12):
# - `abierto`: salud, TODO `/auth` y los GET del catálogo público. No pasa por el control del
#   cambio obligatorio de contraseña (RN-06). `/auth/yo` y `/auth/cambiar-password` piden
#   sesión por su cuenta (401 sin ella) pero tienen que atender a quien debe cambiar la
#   contraseña; por eso `/auth` entero va acá: FastAPI SUMA las dependencias de un router y
#   no las resta, así que no se puede montar bajo el protegido y «sacarle» el control.
# - `protegido`: el control de RN-06 se declara UNA sola vez, acá. Pide sesión (401) y bloquea
#   con 403 al usuario con el cambio pendiente; el rol de cada ruta (`SOLO_ADMIN` /
#   `PERSONAL`) lo declara su propio router. `tests/matriz_acceso.py` clasifica cada ruta y
#   `tests/test_grupos_de_rutas.py` falla si una ruta nueva no está clasificada.
abierto = APIRouter()
protegido = APIRouter(dependencies=[Depends(control_cambio_obligatorio)])

abierto.include_router(health_router)
abierto.include_router(auth_router)
for modulo in (editoriales, generos, autores, libros):
    abierto.include_router(modulo.router_abierto)
    protegido.include_router(modulo.router)
for modulo in (clientes, ventas):
    protegido.include_router(modulo.router)
# CHG-14: administración de usuarios e historial de seguridad (solo ADMIN, declarado en cada router).
protegido.include_router(usuarios_router)
protegido.include_router(eventos_router)

app.include_router(abierto)
app.include_router(protegido)
