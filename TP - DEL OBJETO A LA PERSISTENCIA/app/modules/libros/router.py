from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.core.dependencies import SOLO_ADMIN, UsuarioAdmin, proveedor_uow
from app.core.paginacion import Page, ParametrosPagina, paginacion_params
from app.core.tipos import INT32_MAX, IdPath
from app.modules.libros import service
from app.modules.libros.schemas import (
    LibroCreate,
    LibroDetalleRead,
    LibroRead,
    LibroUpdate,
    MovimientoStockRead,
    ReponerIn,
    ReposicionRead,
)
from app.modules.libros.unit_of_work import LibrosUoW

# Dos routers con el mismo prefijo (CHG-12): los GET son del catálogo público (grupo abierto de
# `app/main.py`) y las escrituras son de ADMIN (grupo protegido). Las dependencias de un
# `include_router` se aplican a todas las rutas del router, por eso no pueden compartir uno.
router_abierto = APIRouter(prefix="/libros", tags=["libros"])
router = APIRouter(prefix="/libros", tags=["libros"])

LibrosUoWDep = Annotated[LibrosUoW, Depends(proveedor_uow(LibrosUoW))]


@router.post("/", response_model=LibroDetalleRead, status_code=201)
async def crear_libro(datos: LibroCreate, uow: LibrosUoWDep, usuario: UsuarioAdmin) -> LibroDetalleRead:
    # El `usuario_id` del movimiento de stock inicial es el del ADMIN de la petición.
    return await service.crear(uow, datos, usuario.id)


@router_abierto.get("/", response_model=Page[LibroRead], status_code=200)
async def listar_libros(
    uow: LibrosUoWDep,
    p: Annotated[ParametrosPagina, Depends(paginacion_params)],
    titulo: str | None = Query(
        default=None,
        description="Filtrar por título (búsqueda parcial insensible a mayúsculas)",
    ),
    genero_id: int | None = Query(
        default=None,
        ge=1,
        le=INT32_MAX,
        description="Filtrar por ID de género",
    ),
) -> Page[LibroRead]:
    return await service.listar(uow, p, titulo=titulo, genero_id=genero_id)


@router_abierto.get("/{libro_id}", response_model=LibroDetalleRead, status_code=200)
async def obtener_libro(libro_id: IdPath, uow: LibrosUoWDep) -> LibroDetalleRead:
    return await service.obtener(uow, libro_id)


@router.patch(
    "/{libro_id}",
    response_model=LibroDetalleRead,
    status_code=200,
    dependencies=[Depends(SOLO_ADMIN)],
)
async def actualizar_libro(libro_id: IdPath, datos: LibroUpdate, uow: LibrosUoWDep) -> LibroDetalleRead:
    return await service.actualizar(uow, libro_id, datos)


@router.delete("/{libro_id}", status_code=204, dependencies=[Depends(SOLO_ADMIN)])
async def dar_de_baja_libro(libro_id: IdPath, uow: LibrosUoWDep) -> Response:
    await service.dar_de_baja(uow, libro_id)
    return Response(status_code=204)


@router.post("/{libro_id}/reponer", response_model=ReposicionRead, status_code=200)
async def reponer_libro(libro_id: IdPath, datos: ReponerIn, uow: LibrosUoWDep, usuario: UsuarioAdmin) -> ReposicionRead:
    # El `usuario_id` del movimiento es el del ADMIN de la petición.
    return await service.reponer(uow, libro_id, datos, usuario.id)


# Historial de stock: sólo ADMIN, por eso va en `router` (grupo protegido) y no en `router_abierto`.
@router.get(
    "/{libro_id}/movimientos",
    response_model=Page[MovimientoStockRead],
    status_code=200,
    dependencies=[Depends(SOLO_ADMIN)],
)
async def listar_movimientos_del_libro(
    libro_id: IdPath, uow: LibrosUoWDep, p: Annotated[ParametrosPagina, Depends(paginacion_params)]
) -> Page[MovimientoStockRead]:
    return await service.listar_movimientos(uow, libro_id, p)
