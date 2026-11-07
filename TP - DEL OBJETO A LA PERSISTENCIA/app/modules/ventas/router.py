from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends

from app.core.dependencies import PERSONAL, UsuarioActual, UsuarioPersonal, get_usuario_actual, proveedor_uow
from app.core.paginacion import Page, ParametrosPagina, paginacion_params
from app.core.tipos import IdPath
from app.modules.ventas import service
from app.modules.ventas.schemas import VentaCreate, VentaRead
from app.modules.ventas.unit_of_work import VentasUoW

router = APIRouter(prefix="/ventas", tags=["ventas"])
# `/mis-ventas` no cuelga de `/ventas`: la consigna fija esa ruta. Va en el grupo protegido, sin rol.
router_propio = APIRouter(tags=["ventas"])

VentasUoWDep = Annotated[VentasUoW, Depends(proveedor_uow(VentasUoW))]


@router.post("/", response_model=VentaRead, status_code=201)
async def crear_venta(
    datos: VentaCreate,
    background_tasks: BackgroundTasks,
    uow: VentasUoWDep,
    usuario: UsuarioPersonal,
) -> VentaRead:
    venta = await service.crear(uow, datos, usuario.id)
    # Se agenda recién con la venta ya confirmada (si el servicio lanzó, nunca llega acá);
    # corre después de enviar la respuesta.
    background_tasks.add_task(service.avisar_comprobante, venta.id, venta.cliente.email)
    return venta


@router.get(
    "/",
    response_model=Page[VentaRead],
    status_code=200,
    dependencies=[Depends(PERSONAL)],
)
async def listar_ventas(
    uow: VentasUoWDep, p: Annotated[ParametrosPagina, Depends(paginacion_params)]
) -> Page[VentaRead]:
    return await service.listar(uow, p)


# Sin `requiere_rol`: decide el servicio (el personal, o el cliente dueño de la venta; si no, 403).
# `get_usuario_actual` ya la resolvió el grupo protegido en esta petición: FastAPI la cachea.
@router.get("/{venta_id}", response_model=VentaRead, status_code=200)
async def obtener_venta(
    venta_id: IdPath, uow: VentasUoWDep, usuario: Annotated[UsuarioActual, Depends(get_usuario_actual)]
) -> VentaRead:
    return await service.obtener(uow, venta_id, usuario.id)


@router_propio.get("/mis-ventas", response_model=Page[VentaRead], status_code=200)
async def mis_ventas(
    uow: VentasUoWDep,
    usuario: Annotated[UsuarioActual, Depends(get_usuario_actual)],
    p: Annotated[ParametrosPagina, Depends(paginacion_params)],
) -> Page[VentaRead]:
    return await service.mis_ventas(uow, usuario.id, p)
