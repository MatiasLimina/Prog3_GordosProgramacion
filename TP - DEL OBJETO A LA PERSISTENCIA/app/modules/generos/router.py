from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.pagination import Pagination, pagination_params
from app.modules.generos import service
from app.modules.generos.schemas import GeneroCreate, GeneroRead

router = APIRouter(prefix="/generos", tags=["generos"])


@router.post("/", response_model=GeneroRead, status_code=201)
async def crear_genero(datos: GeneroCreate, session: AsyncSession = Depends(get_session)):
    return await service.crear(session, datos)


@router.get("/", response_model=list[GeneroRead], status_code=200)
async def listar_generos(
    p: Pagination = Depends(pagination_params), session: AsyncSession = Depends(get_session)
):
    return await service.listar(session, p)
