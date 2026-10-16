from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

from app.core.errors import commit_or_409, mensaje_para
from app.core.pagination import Pagination
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteDetalleRead,
    ClienteRead,
    ClienteUpdate,
    PerfilCreate,
    PerfilRead,
)
from app.modules.ventas import service as ventas_service
from app.modules.ventas.schemas import VentaRead

MENSAJES = {
    "uq_cliente_email": "Ya existe un cliente con ese email.",
}

MENSAJES_PERFIL = {
    "uq_perfil_cliente_cliente_id": "El cliente ya tiene un perfil.",
}
FK_PERFIL_CLIENTE = "fk_perfil_cliente_cliente_id_cliente"
MENSAJE_CLIENTE_INEXISTENTE = "El cliente no existe."


async def crear(session: AsyncSession, datos: ClienteCreate) -> ClienteRead:
    cliente = Cliente(**datos.model_dump())
    session.add(cliente)
    await commit_or_409(session, MENSAJES)
    return ClienteRead.model_validate(cliente)


async def _cargar(session: AsyncSession, cliente_id: int) -> Cliente:
    resultado = await session.execute(
        select(Cliente).where(Cliente.id == cliente_id).options(joinedload(Cliente.perfil))
    )
    cliente = resultado.scalars().first()
    if cliente is None:
        raise HTTPException(status_code=404, detail=MENSAJE_CLIENTE_INEXISTENTE)
    return cliente


def _detalle(cliente: Cliente) -> ClienteDetalleRead:
    return ClienteDetalleRead(
        id=cliente.id,
        nombre=cliente.nombre,
        email=cliente.email,
        perfil=PerfilRead.model_validate(cliente.perfil) if cliente.perfil else None,
    )


async def obtener(session: AsyncSession, cliente_id: int) -> ClienteDetalleRead:
    return _detalle(await _cargar(session, cliente_id))


async def listar(session: AsyncSession, p: Pagination) -> list[ClienteRead]:
    consulta = select(Cliente).order_by(Cliente.id).limit(p.limit).offset(p.offset)
    resultado = await session.execute(consulta)
    return [ClienteRead.model_validate(c) for c in resultado.scalars().all()]


async def actualizar(session: AsyncSession, cliente_id: int, datos: ClienteUpdate) -> ClienteDetalleRead:
    cliente = await _cargar(session, cliente_id)
    cambios = datos.model_dump(exclude_unset=True)
    if cambios:
        cliente.sqlmodel_update(cambios)
        session.add(cliente)
        await commit_or_409(session, MENSAJES)
    return _detalle(cliente)


async def crear_perfil(session: AsyncSession, cliente_id: int, datos: PerfilCreate) -> PerfilRead:
    """Alta del perfil sin consultar antes si el cliente existe: la base decide.

    FK violada -> el cliente no existe (404, no 409: el recurso de la URL no existe).
    UNIQUE violado -> el cliente ya tiene perfil (409).
    """
    perfil = PerfilCliente(cliente_id=cliente_id, **datos.model_dump())
    session.add(perfil)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        # default="" -> sólo coincide con el mensaje de la FK si esa fue la constraint violada.
        es_fk = mensaje_para(e, {FK_PERFIL_CLIENTE: MENSAJE_CLIENTE_INEXISTENTE}, default="")
        if es_fk == MENSAJE_CLIENTE_INEXISTENTE:
            raise HTTPException(status_code=404, detail=MENSAJE_CLIENTE_INEXISTENTE) from None
        raise HTTPException(status_code=409, detail=mensaje_para(e, MENSAJES_PERFIL)) from None
    return PerfilRead.model_validate(perfil)


async def listar_ventas_de_cliente(
    session: AsyncSession, cliente_id: int, p: Pagination
) -> list[VentaRead]:
    await _cargar(session, cliente_id)  # 404 si no existe
    return await ventas_service.listar(session, p, cliente_id=cliente_id)
