from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.pagination import Pagination, pagination_params
from app.core.tipos import IdPath
from app.modules.clientes import service
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteDetalleRead,
    ClienteRead,
    ClienteUpdate,
    PerfilCreate,
    PerfilRead,
)
from app.modules.ventas.schemas import VentaRead

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.post("/", response_model=ClienteRead, status_code=201)
async def crear_cliente(
    datos: ClienteCreate, session: AsyncSession = Depends(get_session)
) -> ClienteRead:
    return await service.crear(session, datos)


@router.get("/", response_model=list[ClienteRead], status_code=200)
async def listar_clientes(
    p: Pagination = Depends(pagination_params),
    session: AsyncSession = Depends(get_session),
) -> list[ClienteRead]:
    return await service.listar(session, p)


@router.get("/{cliente_id}", response_model=ClienteDetalleRead, status_code=200)
async def obtener_cliente(
    cliente_id: IdPath, session: AsyncSession = Depends(get_session)
) -> ClienteDetalleRead:
    return await service.obtener(session, cliente_id)


@router.patch("/{cliente_id}", response_model=ClienteDetalleRead, status_code=200)
async def actualizar_cliente(
    cliente_id: IdPath, datos: ClienteUpdate, session: AsyncSession = Depends(get_session)
) -> ClienteDetalleRead:
    return await service.actualizar(session, cliente_id, datos)


@router.post("/{cliente_id}/perfil", response_model=PerfilRead, status_code=201)
async def crear_perfil(
    cliente_id: IdPath, datos: PerfilCreate, session: AsyncSession = Depends(get_session)
) -> PerfilRead:
    return await service.crear_perfil(session, cliente_id, datos)


@router.get("/{cliente_id}/ventas", response_model=list[VentaRead], status_code=200)
async def listar_ventas_del_cliente(
    cliente_id: IdPath,
    p: Pagination = Depends(pagination_params),
    session: AsyncSession = Depends(get_session),
) -> list[VentaRead]:
    return await service.listar_ventas_de_cliente(session, cliente_id, p)
