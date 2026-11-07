"""Rutas HTTP de autenticación: construyen el UoW, llaman al servicio y devuelven el contrato.

Sin lógica de negocio: los errores son excepciones de dominio que traducen los handlers de
`app/main.py`. `auth_router` es el de CHG-11; `router` (`/usuarios`) y `eventos_router` (`/eventos`)
son la administración de usuarios de CHG-14, ambos solo-ADMIN y montados en el grupo protegido.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.core.dependencies import (
    NOMBRE_COOKIE,
    SOLO_ADMIN,
    ParametrosSeguridad,
    UsuarioActual,
    UsuarioAdmin,
    get_parametros_seguridad,
    get_usuario_actual,
    proveedor_uow,
    proveedor_uow_sesion_propia,
)
from app.core.paginacion import Page, ParametrosPagina, paginacion_params
from app.core.tipos import IdPath
from app.modules.usuarios import service
from app.modules.usuarios.schemas import (
    AsignacionRolCreate,
    AsignacionRolRead,
    AuthYoRead,
    CambioPasswordCreate,
    EventoSeguridadRead,
    LoginCreate,
    LoginRead,
    RegistroCreate,
    Rol,
    UsuarioCreate,
    UsuarioRead,
)
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


# ---------------------------------------------------------------------------
# Administración de usuarios (CHG-14). Solo ADMIN: la dependencia `SOLO_ADMIN` va en el router y
# los handlers que necesitan al actor reciben `UsuarioAdmin` (la misma función: FastAPI la
# resuelve una sola vez por petición). Se montan en el grupo protegido de `app/main.py`.
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/usuarios", tags=["usuarios"], dependencies=[Depends(SOLO_ADMIN)])
eventos_router = APIRouter(prefix="/eventos", tags=["eventos"], dependencies=[Depends(SOLO_ADMIN)])


@router.post("/", response_model=UsuarioRead, status_code=201)
async def alta_de_personal(
    datos: UsuarioCreate, actor: UsuarioAdmin, uow: UsuariosUoWDep, seg: SeguridadDep
) -> UsuarioRead:
    return await service.dar_de_alta_personal(uow, datos, actor, seg)


@router.get("/{usuario_id}/roles", response_model=list[AsignacionRolRead])
async def listar_roles(usuario_id: IdPath, uow: UsuariosUoWDep) -> list[AsignacionRolRead]:
    return await service.listar_roles(uow, usuario_id)


@router.post("/{usuario_id}/roles", response_model=AsignacionRolRead, status_code=201)
async def asignar_rol(
    usuario_id: IdPath, datos: AsignacionRolCreate, actor: UsuarioAdmin, uow: UsuariosUoWDep
) -> AsignacionRolRead:
    return await service.asignar_rol(uow, usuario_id, datos, actor)


@router.delete("/{usuario_id}/roles/{rol}", response_model=AsignacionRolRead)
async def revocar_rol(usuario_id: IdPath, rol: Rol, actor: UsuarioAdmin, uow: UsuariosUoWDep) -> AsignacionRolRead:
    return await service.revocar_rol(uow, usuario_id, rol, actor)


@eventos_router.get("/", response_model=Page[EventoSeguridadRead])
async def listar_eventos(
    uow: UsuariosUoWDep, p: Annotated[ParametrosPagina, Depends(paginacion_params)]
) -> Page[EventoSeguridadRead]:
    return await service.listar_eventos(uow, p)
