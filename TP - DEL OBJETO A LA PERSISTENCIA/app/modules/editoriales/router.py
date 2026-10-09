from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.pagination import Pagination, pagination_params
from app.modules.editoriales import service
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate

router = APIRouter(prefix="/editoriales", tags=["editoriales"])


@router.post("/", response_model=EditorialRead, status_code=201)
async def crear_editorial(datos: EditorialCreate, session: AsyncSession = Depends(get_session)):
    return await service.crear(session, datos)


@router.get("/", response_model=list[EditorialRead], status_code=200)
async def listar_editoriales(
    p: Pagination = Depends(pagination_params), session: AsyncSession = Depends(get_session)
):
    return await service.listar(session, p)


@router.get("/{editorial_id}", response_model=EditorialRead, status_code=200)
async def obtener_editorial(editorial_id: int, session: AsyncSession = Depends(get_session)):
    return await service.obtener(session, editorial_id)


@router.patch("/{editorial_id}", response_model=EditorialRead, status_code=200)
async def actualizar_editorial(
    editorial_id: int, datos: EditorialUpdate, session: AsyncSession = Depends(get_session)
):
    return await service.actualizar(session, editorial_id, datos)
