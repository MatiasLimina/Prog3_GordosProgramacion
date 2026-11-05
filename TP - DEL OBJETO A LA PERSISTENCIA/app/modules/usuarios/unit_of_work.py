"""UoW del módulo `usuarios`: compone los repositorios con la misma sesión.

`UsuariosUoW` es el de la petición (registro, login, cambio de contraseña). `IntentosUoW` es
el de `intento_acceso`, que se construye sobre una sesión PROPIA (ver `proveedor_uow_sesion_propia`
en `app/core/dependencies.py`): comparten clase base, no sesión.
"""
from collections.abc import Mapping
from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.core.unit_of_work import UnitOfWork
from app.modules.clientes.models import Cliente
from app.modules.usuarios.repository import (
    AsignacionRolRepository,
    EventoSeguridadRepository,
    IntentoAccesoRepository,
    UsuarioRepository,
)


class UsuariosUoW(UnitOfWork):
    MENSAJES: ClassVar[Mapping[str, str]] = {
        "uq_usuario_email": "Ya existe un usuario con ese correo.",
        "uq_cliente_email": "Ya existe un cliente con ese correo.",
        "uq_asignacion_rol_usuario_rol_vigente": "El usuario ya tiene ese rol vigente.",
    }

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.usuarios = UsuarioRepository(session)
        self.asignaciones = AsignacionRolRepository(session)
        # Sólo lectura acá: las filas de intento_acceso se escriben con IntentosUoW.
        self.intentos = IntentoAccesoRepository(session)
        self.eventos = EventoSeguridadRepository(session)
        # Genérico a propósito: `ClienteRepository` es de CHG-15 (Nico), que cambia esta línea.
        self.clientes = BaseRepository(session, Cliente)


class IntentosUoW(UnitOfWork):
    MENSAJES: ClassVar[Mapping[str, str]] = {}

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.intentos = IntentoAccesoRepository(session)
