"""Rutas HTTP de autenticación: construyen el UoW, llaman al servicio y devuelven el contrato.

Sin lógica de negocio: los errores son excepciones de dominio que traducen los handlers de
`app/main.py`. CHG-14 agrega acá su propio `router` (`/usuarios`, `/eventos`).
"""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import ParametrosSeguridad, get_parametros_seguridad, proveedor_uow
from app.modules.usuarios import service
from app.modules.usuarios.schemas import RegistroCreate, UsuarioRead
from app.modules.usuarios.unit_of_work import UsuariosUoW

auth_router = APIRouter(prefix="/auth", tags=["auth"])

UsuariosUoWDep = Annotated[UsuariosUoW, Depends(proveedor_uow(UsuariosUoW))]
SeguridadDep = Annotated[ParametrosSeguridad, Depends(get_parametros_seguridad)]


@auth_router.post("/registro", response_model=UsuarioRead, status_code=201)
async def registro(datos: RegistroCreate, uow: UsuariosUoWDep, seg: SeguridadDep) -> UsuarioRead:
    return await service.registrar(uow, datos, seg)
