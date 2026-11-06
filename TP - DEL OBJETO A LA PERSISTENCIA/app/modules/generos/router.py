from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import SOLO_ADMIN
from app.core.tipos import IdPath
from app.core.pagination import Pagination, pagination_params
from app.modules.generos import service
from app.modules.generos.schemas import GeneroCreate, GeneroRead
from app.modules.libros.schemas import LibroRead

# Dos routers con el mismo prefijo (CHG-12): los GET son del catálogo público (grupo abierto de
# `app/main.py`) y las escrituras son de ADMIN (grupo protegido). Las dependencias de un
# `include_router` se aplican a todas las rutas del router, por eso no pueden compartir uno.
router_abierto = APIRouter(prefix="/generos", tags=["generos"])
router = APIRouter(prefix="/generos", tags=["generos"])


@router.post(
    "/",
    response_model=GeneroRead,
    status_code=201,
    dependencies=[Depends(SOLO_ADMIN)],
)
async def crear_genero(datos: GeneroCreate, session: AsyncSession = Depends(get_session)):
    return await service.crear(session, datos)


@router_abierto.get("/", response_model=list[GeneroRead], status_code=200)
async def listar_generos(
    p: Pagination = Depends(pagination_params), session: AsyncSession = Depends(get_session)
):
    return await service.listar(session, p)


@router_abierto.get("/{genero_id}/libros", response_model=list[LibroRead], status_code=200)
async def listar_libros_de_genero(
    genero_id: IdPath,
    p: Pagination = Depends(pagination_params),
    session: AsyncSession = Depends(get_session),
):
    return await service.listar_libros(session, genero_id, p)
