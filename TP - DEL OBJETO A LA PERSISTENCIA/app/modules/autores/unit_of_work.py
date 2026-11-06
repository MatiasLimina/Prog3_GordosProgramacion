"""UoW del módulo `autores`: compone los repositorios con la misma sesión.

`autorias` (de `libros`) lee los libros vigentes del autor para `/autores/{id}/libros`. El autor no
tiene constraints propias con mensaje: `MENSAJES` queda vacío y un `IntegrityError` inesperado cae
en el mensaje genérico de `mensaje_para`.
"""
from collections.abc import Mapping
from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.unit_of_work import UnitOfWork
from app.modules.autores.repository import AutorRepository
from app.modules.libros.repository import LibroAutorRepository


class AutoresUoW(UnitOfWork):
    MENSAJES: ClassVar[Mapping[str, str]] = {}

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.autores = AutorRepository(session)
        self.autorias = LibroAutorRepository(session)
