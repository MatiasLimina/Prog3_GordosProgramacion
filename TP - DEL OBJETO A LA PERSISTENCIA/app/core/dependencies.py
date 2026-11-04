"""Dependencias de FastAPI compartidas.

Hoy: `proveedor_uow`, la fábrica que CONSTRUYE el UnitOfWork de una petición sin abrirlo.
CHG-12 suma acá las dependencias de usuario actual y de rol; reciben la misma sesión
(`Depends(get_session)`, que FastAPI cachea por petición), así una petición autenticada
usa una sola conexión del pool.
"""
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.unit_of_work import UnitOfWork


def proveedor_uow[U: UnitOfWork](clase: type[U]) -> Callable[..., Awaitable[U]]:
    """Dependencia que construye `clase(session)` con la sesión de la petición.

    Condición: todo UoW de módulo se construye sólo con `(session)`; lo que necesite más
    se arma adentro. Un solo UoW abierto por sesión a la vez: un handler puede recibir
    varios UoW (comparten la sesión de la petición), pero nunca anidar sus `async with`,
    ni con UoW distintos (lanza `RuntimeError`). Ejemplo de un módulo:

        # app/modules/editoriales/unit_of_work.py
        class EditorialesUoW(UnitOfWork):
            MENSAJES = {"uq_editorial_nombre": "Ya existe una editorial con ese nombre."}

            def __init__(self, session: AsyncSession) -> None:
                super().__init__(session)
                self.editoriales = EditorialRepository(session)

        EditorialesUoWDep = Annotated[EditorialesUoW, Depends(proveedor_uow(EditorialesUoW))]

        # router.py: construye el UoW y se lo pasa al servicio sin abrirlo
        @router.post("/", status_code=201)
        async def crear(datos: EditorialCreate, uow: EditorialesUoWDep):
            return await service.crear(uow, datos)

        # service.py: abre el bloque (confirma o revierte al salir)
        async def crear(uow: EditorialesUoW, datos: EditorialCreate) -> Editorial:
            async with uow:
                return await uow.editoriales.add(Editorial(**datos.model_dump()))
    """

    # `async def`: una dependencia `def` correría en el threadpool sin necesidad.
    async def _proveer(session: Annotated[AsyncSession, Depends(get_session)]) -> U:
        return clase(session)

    return _proveer
