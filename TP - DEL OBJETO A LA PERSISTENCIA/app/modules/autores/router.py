from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.tipos import IdPath
from app.core.pagination import Pagination, pagination_params
from app.modules.autores import service
from app.modules.autores.schemas import AutorCreate, AutorLibroRead, AutorRead, AutorUpdate

router = APIRouter(prefix="/autores", tags=["autores"])


@router.post("/", response_model=AutorRead, status_code=201)
async def crear_autor(
    datos: AutorCreate, session: AsyncSession = Depends(get_session)
) -> AutorRead:
    return await service.crear(session, datos)


@router.get("/", response_model=list[AutorRead], status_code=200)
async def listar_autores(
    p: Pagination = Depends(pagination_params), session: AsyncSession = Depends(get_session)
) -> list[AutorRead]:
    return await service.listar(session, p)


@router.get("/{autor_id}", response_model=AutorRead, status_code=200)
async def obtener_autor(
    autor_id: IdPath, session: AsyncSession = Depends(get_session)
) -> AutorRead:
    return await service.obtener(session, autor_id)


@router.patch("/{autor_id}", response_model=AutorRead, status_code=200)
async def actualizar_autor(
    autor_id: IdPath, datos: AutorUpdate, session: AsyncSession = Depends(get_session)
) -> AutorRead:
    return await service.actualizar(session, autor_id, datos)


@router.get("/{autor_id}/libros", response_model=list[AutorLibroRead], status_code=200)
async def listar_libros_de_autor(
    autor_id: IdPath, session: AsyncSession = Depends(get_session)
) -> list[AutorLibroRead]:
    return await service.listar_libros_de_autor(session, autor_id)
