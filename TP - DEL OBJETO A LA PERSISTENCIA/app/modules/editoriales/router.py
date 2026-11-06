from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import SOLO_ADMIN
from app.core.tipos import IdPath
from app.core.pagination import Pagination, pagination_params
from app.modules.editoriales import service
from app.modules.libros.schemas import LibroRead
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate

# Dos routers con el mismo prefijo (CHG-12): los GET son del catálogo público (grupo abierto de
# `app/main.py`) y las escrituras son de ADMIN (grupo protegido). Las dependencias de un
# `include_router` se aplican a todas las rutas del router, por eso no pueden compartir uno.
router_abierto = APIRouter(prefix="/editoriales", tags=["editoriales"])
router = APIRouter(prefix="/editoriales", tags=["editoriales"])


@router.post(
    "/",
    response_model=EditorialRead,
    status_code=201,
    dependencies=[Depends(SOLO_ADMIN)],
)
async def crear_editorial(datos: EditorialCreate, session: AsyncSession = Depends(get_session)):
    return await service.crear(session, datos)


@router_abierto.get("/", response_model=list[EditorialRead], status_code=200)
async def listar_editoriales(
    p: Pagination = Depends(pagination_params), session: AsyncSession = Depends(get_session)
):
    return await service.listar(session, p)


@router_abierto.get("/{editorial_id}", response_model=EditorialRead, status_code=200)
async def obtener_editorial(editorial_id: IdPath, session: AsyncSession = Depends(get_session)):
    return await service.obtener(session, editorial_id)


@router.patch(
    "/{editorial_id}",
    response_model=EditorialRead,
    status_code=200,
    dependencies=[Depends(SOLO_ADMIN)],
)
async def actualizar_editorial(
    editorial_id: IdPath, datos: EditorialUpdate, session: AsyncSession = Depends(get_session)
):
    return await service.actualizar(session, editorial_id, datos)


@router_abierto.get("/{editorial_id}/libros", response_model=list[LibroRead], status_code=200)
async def listar_libros_de_editorial(
    editorial_id: IdPath,
    p: Pagination = Depends(pagination_params),
    session: AsyncSession = Depends(get_session),
):
    return await service.listar_libros(session, editorial_id, p)
