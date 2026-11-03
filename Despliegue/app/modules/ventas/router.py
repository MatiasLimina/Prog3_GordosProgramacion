from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.pagination import Pagination, pagination_params
from app.core.tipos import IdPath
from app.modules.ventas import service
from app.modules.ventas.schemas import VentaCreate, VentaRead

router = APIRouter(prefix="/ventas", tags=["ventas"])


@router.post("/", response_model=VentaRead, status_code=201)
async def crear_venta(
    datos: VentaCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> VentaRead:
    venta = await service.crear(session, datos)
    # Se agenda recién con la venta ya confirmada; corre después de enviar la respuesta.
    background_tasks.add_task(service.avisar_comprobante, venta.id, venta.cliente.email)
    return venta


@router.get("/", response_model=list[VentaRead], status_code=200)
async def listar_ventas(
    p: Pagination = Depends(pagination_params),
    session: AsyncSession = Depends(get_session),
) -> list[VentaRead]:
    return await service.listar(session, p)


@router.get("/{venta_id}", response_model=VentaRead, status_code=200)
async def obtener_venta(
    venta_id: IdPath, session: AsyncSession = Depends(get_session)
) -> VentaRead:
    return await service.obtener(session, venta_id)
