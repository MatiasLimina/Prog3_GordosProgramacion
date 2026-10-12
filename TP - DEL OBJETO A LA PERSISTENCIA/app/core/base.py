"""Fija la naming convention de constraints sobre SQLModel.metadata.

Debe importarse ANTES de definir cualquier tabla (cada models.py lo hace),
para que el resultado no dependa del orden en que se importen los módulos.
Nombres predecibles: los mensajes 409 se eligen por nombre de constraint y
Alembic puede crearlos/borrarlos sin depender de nombres autogenerados.
"""
from sqlmodel import SQLModel

SQLModel.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
