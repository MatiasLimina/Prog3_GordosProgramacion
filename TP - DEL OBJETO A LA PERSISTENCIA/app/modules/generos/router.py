from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import SOLO_ADMIN, proveedor_uow
from app.core.paginacion import Page, ParametrosPagina, paginacion_params
from app.core.tipos import IdPath
from app.modules.generos import service
from app.modules.generos.schemas import GeneroCreate, GeneroRead
from app.modules.generos.unit_of_work import GenerosUoW
from app.modules.libros.schemas import LibroRead

# Dos routers con el mismo prefijo (CHG-12): los GET son del catálogo público (grupo abierto de
# `app/main.py`) y las escrituras son de ADMIN (grupo protegido). Las dependencias de un
# `include_router` se aplican a todas las rutas del router, por eso no pueden compartir uno.
router_abierto = APIRouter(prefix="/generos", tags=["generos"])
router = APIRouter(prefix="/generos", tags=["generos"])

GenerosUoWDep = Annotated[GenerosUoW, Depends(proveedor_uow(GenerosUoW))]


@router.post(
    "/",
    response_model=GeneroRead,
    status_code=201,
    dependencies=[Depends(SOLO_ADMIN)],
)
async def crear_genero(datos: GeneroCreate, uow: GenerosUoWDep) -> GeneroRead:
    return await service.crear(uow, datos)


@router_abierto.get("/", response_model=Page[GeneroRead], status_code=200)
async def listar_generos(
    uow: GenerosUoWDep, p: Annotated[ParametrosPagina, Depends(paginacion_params)]
) -> Page[GeneroRead]:
    return await service.listar(uow, p)


@router_abierto.get("/{genero_id}/libros", response_model=Page[LibroRead], status_code=200)
async def listar_libros_de_genero(
    genero_id: IdPath, uow: GenerosUoWDep, p: Annotated[ParametrosPagina, Depends(paginacion_params)]
) -> Page[LibroRead]:
    return await service.listar_libros(uow, genero_id, p)
