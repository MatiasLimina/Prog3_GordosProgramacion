"""UoW del módulo `clientes`: compone los repositorios con la misma sesión.

`ventas` es el repositorio de ventas que usa `/clientes/{id}/ventas`. `MENSAJES` elige el 409 por nombre de constraint. La FK del perfil no va acá: no es un 409 sino
un 404 (`ClienteNoEncontrado`), y la decide `PerfilClienteRepository.add`.
"""
from collections.abc import Mapping
from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.unit_of_work import UnitOfWork
from app.modules.clientes.repository import ClienteRepository, PerfilClienteRepository
from app.modules.ventas.repository import VentaRepository


class ClientesUoW(UnitOfWork):
    MENSAJES: ClassVar[Mapping[str, str]] = {
        "uq_cliente_email": "Ya existe un cliente con ese correo.",
        "uq_perfil_cliente_cliente_id": "El cliente ya tiene un perfil.",
    }

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.clientes = ClienteRepository(session)
        self.perfiles = PerfilClienteRepository(session)
        # Repositorio de ventas (del módulo `ventas`) para el sub-listado `/clientes/{id}/ventas`.
        self.ventas = VentaRepository(session)
