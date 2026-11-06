"""UoW del módulo `editoriales`: compone los repositorios con la misma sesión.

`libros` es el repositorio de libros (del módulo `libros`) que usa el sub-listado
`/editoriales/{id}/libros`. `MENSAJES` elige el 409 por nombre de constraint.
"""
from collections.abc import Mapping
from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.unit_of_work import UnitOfWork
from app.modules.editoriales.repository import EditorialRepository
from app.modules.libros.repository import LibroRepository


class EditorialesUoW(UnitOfWork):
    MENSAJES: ClassVar[Mapping[str, str]] = {
        "uq_editorial_nombre": "Ya existe una editorial con ese nombre.",
    }

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.editoriales = EditorialRepository(session)
        self.libros = LibroRepository(session)
