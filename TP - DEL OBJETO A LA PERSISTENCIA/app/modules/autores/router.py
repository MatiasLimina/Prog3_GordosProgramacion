from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import SOLO_ADMIN, proveedor_uow
from app.core.paginacion import Page, ParametrosPagina, paginacion_params
from app.core.tipos import IdPath
from app.modules.autores import service
from app.modules.autores.schemas import AutorCreate, AutorLibroRead, AutorRead, AutorUpdate
from app.modules.autores.unit_of_work import AutoresUoW

# Dos routers con el mismo prefijo (CHG-12): los GET son del catálogo público (grupo abierto de
# `app/main.py`) y las escrituras son de ADMIN (grupo protegido). Las dependencias de un
# `include_router` se aplican a todas las rutas del router, por eso no pueden compartir uno.
router_abierto = APIRouter(prefix="/autores", tags=["autores"])
router = APIRouter(prefix="/autores", tags=["autores"])

AutoresUoWDep = Annotated[AutoresUoW, Depends(proveedor_uow(AutoresUoW))]


@router.post(
    "/",
    response_model=AutorRead,
    status_code=201,
    dependencies=[Depends(SOLO_ADMIN)],
)
async def crear_autor(datos: AutorCreate, uow: AutoresUoWDep) -> AutorRead:
    return await service.crear(uow, datos)


@router_abierto.get("/", response_model=Page[AutorRead], status_code=200)
async def listar_autores(
    uow: AutoresUoWDep, p: Annotated[ParametrosPagina, Depends(paginacion_params)]
) -> Page[AutorRead]:
    return await service.listar(uow, p)


@router_abierto.get("/{autor_id}", response_model=AutorRead, status_code=200)
async def obtener_autor(autor_id: IdPath, uow: AutoresUoWDep) -> AutorRead:
    return await service.obtener(uow, autor_id)


@router.patch(
    "/{autor_id}",
    response_model=AutorRead,
    status_code=200,
    dependencies=[Depends(SOLO_ADMIN)],
)
async def actualizar_autor(autor_id: IdPath, datos: AutorUpdate, uow: AutoresUoWDep) -> AutorRead:
    return await service.actualizar(uow, autor_id, datos)


@router_abierto.get("/{autor_id}/libros", response_model=Page[AutorLibroRead], status_code=200)
async def listar_libros_de_autor(
    autor_id: IdPath, uow: AutoresUoWDep, p: Annotated[ParametrosPagina, Depends(paginacion_params)]
) -> Page[AutorLibroRead]:
    return await service.listar_libros_de_autor(uow, autor_id, p)
