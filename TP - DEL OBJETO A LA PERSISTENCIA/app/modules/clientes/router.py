from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import PERSONAL, proveedor_uow
from app.core.paginacion import Page, ParametrosPagina, paginacion_params
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
from app.modules.clientes.unit_of_work import ClientesUoW
from app.modules.ventas.schemas import VentaRead

router = APIRouter(prefix="/clientes", tags=["clientes"])

ClientesUoWDep = Annotated[ClientesUoW, Depends(proveedor_uow(ClientesUoW))]


@router.post(
    "/",
    response_model=ClienteRead,
    status_code=201,
    dependencies=[Depends(PERSONAL)],
)
async def crear_cliente(datos: ClienteCreate, uow: ClientesUoWDep) -> ClienteRead:
    return await service.crear(uow, datos)


@router.get(
    "/",
    response_model=Page[ClienteRead],
    status_code=200,
    dependencies=[Depends(PERSONAL)],
)
async def listar_clientes(
    uow: ClientesUoWDep, p: Annotated[ParametrosPagina, Depends(paginacion_params)]
) -> Page[ClienteRead]:
    return await service.listar(uow, p)


@router.get(
    "/{cliente_id}",
    response_model=ClienteDetalleRead,
    status_code=200,
    dependencies=[Depends(PERSONAL)],
)
async def obtener_cliente(cliente_id: IdPath, uow: ClientesUoWDep) -> ClienteDetalleRead:
    return await service.obtener(uow, cliente_id)


@router.patch(
    "/{cliente_id}",
    response_model=ClienteDetalleRead,
    status_code=200,
    dependencies=[Depends(PERSONAL)],
)
async def actualizar_cliente(cliente_id: IdPath, datos: ClienteUpdate, uow: ClientesUoWDep) -> ClienteDetalleRead:
    return await service.actualizar(uow, cliente_id, datos)


@router.post(
    "/{cliente_id}/perfil",
    response_model=PerfilRead,
    status_code=201,
    dependencies=[Depends(PERSONAL)],
)
async def crear_perfil(cliente_id: IdPath, datos: PerfilCreate, uow: ClientesUoWDep) -> PerfilRead:
    return await service.crear_perfil(uow, cliente_id, datos)


@router.get(
    "/{cliente_id}/ventas",
    response_model=Page[VentaRead],
    status_code=200,
    dependencies=[Depends(PERSONAL)],
)
async def listar_ventas_del_cliente(
    cliente_id: IdPath, uow: ClientesUoWDep, p: Annotated[ParametrosPagina, Depends(paginacion_params)]
) -> Page[VentaRead]:
    return await service.listar_ventas(uow, cliente_id, p)
