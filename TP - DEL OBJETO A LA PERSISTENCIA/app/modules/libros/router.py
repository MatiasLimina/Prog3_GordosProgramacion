from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.pagination import Pagination, pagination_params
from app.modules.libros import service
from app.modules.libros.schemas import (
    LibroCreate,
    LibroDetalleRead,
    LibroRead,
    LibroUpdate,
)

router = APIRouter(prefix="/libros", tags=["libros"])


@router.post("/", response_model=LibroDetalleRead, status_code=201)
async def crear_libro(
    datos: LibroCreate, session: AsyncSession = Depends(get_session)
) -> LibroDetalleRead:
    return await service.crear(session, datos)


@router.get("/", response_model=list[LibroRead], status_code=200)
async def listar_libros(
    p: Pagination = Depends(pagination_params),
    titulo: str | None = Query(
        default=None,
        description="Filtrar por título (búsqueda parcial insensible a mayúsculas)",
    ),
    genero_id: int | None = Query(
        default=None,
        description="Filtrar por ID de género",
    ),
    session: AsyncSession = Depends(get_session),
) -> list[LibroRead]:
    return await service.listar(session, p, titulo=titulo, genero_id=genero_id)


@router.get("/{libro_id}", response_model=LibroDetalleRead, status_code=200)
async def obtener_libro(
    libro_id: int, session: AsyncSession = Depends(get_session)
) -> LibroDetalleRead:
    return await service.obtener(session, libro_id)


@router.patch("/{libro_id}", response_model=LibroDetalleRead, status_code=200)
async def actualizar_libro(
    libro_id: int, datos: LibroUpdate, session: AsyncSession = Depends(get_session)
) -> LibroDetalleRead:
    return await service.actualizar(session, libro_id, datos)
