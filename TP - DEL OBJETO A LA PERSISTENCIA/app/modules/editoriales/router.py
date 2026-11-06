from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import SOLO_ADMIN, proveedor_uow
from app.core.paginacion import Page, ParametrosPagina, paginacion_params
from app.core.tipos import IdPath
from app.modules.editoriales import service
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate
from app.modules.editoriales.unit_of_work import EditorialesUoW
from app.modules.libros.schemas import LibroRead

# Dos routers con el mismo prefijo (CHG-12): los GET son del catálogo público (grupo abierto de
# `app/main.py`) y las escrituras son de ADMIN (grupo protegido). Las dependencias de un
# `include_router` se aplican a todas las rutas del router, por eso no pueden compartir uno.
router_abierto = APIRouter(prefix="/editoriales", tags=["editoriales"])
router = APIRouter(prefix="/editoriales", tags=["editoriales"])

EditorialesUoWDep = Annotated[EditorialesUoW, Depends(proveedor_uow(EditorialesUoW))]


@router.post(
    "/",
    response_model=EditorialRead,
    status_code=201,
    dependencies=[Depends(SOLO_ADMIN)],
)
async def crear_editorial(datos: EditorialCreate, uow: EditorialesUoWDep) -> EditorialRead:
    return await service.crear(uow, datos)


@router_abierto.get("/", response_model=Page[EditorialRead], status_code=200)
async def listar_editoriales(
    uow: EditorialesUoWDep, p: Annotated[ParametrosPagina, Depends(paginacion_params)]
) -> Page[EditorialRead]:
    return await service.listar(uow, p)


@router_abierto.get("/{editorial_id}", response_model=EditorialRead, status_code=200)
async def obtener_editorial(editorial_id: IdPath, uow: EditorialesUoWDep) -> EditorialRead:
    return await service.obtener(uow, editorial_id)


@router.patch(
    "/{editorial_id}",
    response_model=EditorialRead,
    status_code=200,
    dependencies=[Depends(SOLO_ADMIN)],
)
async def actualizar_editorial(editorial_id: IdPath, datos: EditorialUpdate, uow: EditorialesUoWDep) -> EditorialRead:
    return await service.actualizar(uow, editorial_id, datos)


@router_abierto.get("/{editorial_id}/libros", response_model=Page[LibroRead], status_code=200)
async def listar_libros_de_editorial(
    editorial_id: IdPath, uow: EditorialesUoWDep, p: Annotated[ParametrosPagina, Depends(paginacion_params)]
) -> Page[LibroRead]:
    return await service.listar_libros(uow, editorial_id, p)
