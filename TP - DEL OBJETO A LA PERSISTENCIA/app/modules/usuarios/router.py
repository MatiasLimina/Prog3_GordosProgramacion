"""Rutas HTTP de autenticación: construyen el UoW, llaman al servicio y devuelven el contrato.

Sin lógica de negocio: los errores son excepciones de dominio que traducen los handlers de
`app/main.py`. CHG-14 agrega acá su propio `router` (`/usuarios`, `/eventos`).
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.core.dependencies import (
    NOMBRE_COOKIE,
    ParametrosSeguridad,
    UsuarioActual,
    get_parametros_seguridad,
    get_usuario_actual,
    proveedor_uow,
    proveedor_uow_sesion_propia,
)
from app.modules.usuarios import service
from app.modules.usuarios.schemas import AuthYoRead, CambioPasswordCreate, LoginCreate, LoginRead, RegistroCreate, UsuarioRead
from app.modules.usuarios.unit_of_work import IntentosUoW, UsuariosUoW

auth_router = APIRouter(prefix="/auth", tags=["auth"])

UsuariosUoWDep = Annotated[UsuariosUoW, Depends(proveedor_uow(UsuariosUoW))]
# Sesión PROPIA (no la de la petición): la fila de intento_acceso se confirma aunque la petición falle.
IntentosUoWDep = Annotated[IntentosUoW, Depends(proveedor_uow_sesion_propia(IntentosUoW))]
SeguridadDep = Annotated[ParametrosSeguridad, Depends(get_parametros_seguridad)]


@auth_router.post("/registro", response_model=UsuarioRead, status_code=201)
async def registro(datos: RegistroCreate, uow: UsuariosUoWDep, seg: SeguridadDep) -> UsuarioRead:
    return await service.registrar(uow, datos, seg)


@auth_router.post("/login", response_model=LoginRead)
async def login(
    datos: LoginCreate,
    request: Request,
    response: Response,
    uow: UsuariosUoWDep,
    intentos: IntentosUoWDep,
    seg: SeguridadDep,
) -> LoginRead:
    ip = request.client.host if request.client else "desconocida"
    sesion = await service.iniciar_sesion(uow, intentos, datos, ip, seg)
    # El token viaja SÓLO en la cookie: nunca en el cuerpo (AGENTS §6).
    response.set_cookie(
        NOMBRE_COOKIE,
        sesion.token,
        max_age=sesion.expira_en_segundos,
        httponly=True,
        samesite="lax",
        secure=seg.cookie_secure,
        path="/",
    )
    return LoginRead(
        mensaje="Sesión iniciada",
        debe_cambiar_password=sesion.debe_cambiar_password,
        expira_en_segundos=sesion.expira_en_segundos,
    )


@auth_router.get("/yo", response_model=AuthYoRead)
async def yo(usuario: Annotated[UsuarioActual, Depends(get_usuario_actual)], uow: UsuariosUoWDep) -> AuthYoRead:
    return await service.yo(uow, usuario)


@auth_router.post("/logout", response_model=dict[str, str])
async def logout(response: Response, seg: SeguridadDep) -> dict[str, str]:
    # Sin servicio ni base: no hay regla de negocio, sólo se borra la cookie (mismos atributos
    # que al ponerla, así el navegador la reconoce). No exige sesión: cerrar sin sesión es un 200.
    response.delete_cookie(NOMBRE_COOKIE, path="/", httponly=True, samesite="lax", secure=seg.cookie_secure)
    return {"mensaje": "Sesión cerrada"}


@auth_router.post("/cambiar-password", response_model=dict[str, str])
async def cambiar_password(
    datos: CambioPasswordCreate,
    usuario: Annotated[UsuarioActual, Depends(get_usuario_actual)],
    uow: UsuariosUoWDep,
    seg: SeguridadDep,
) -> dict[str, str]:
    await service.cambiar_password(uow, usuario, datos, seg)
    return {"mensaje": "Contraseña actualizada"}
