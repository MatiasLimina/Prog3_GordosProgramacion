"""Registro central de modelos.

Acá se importan TODOS los modelos de los módulos (editoriales, generos,
autores, libros, clientes, ventas) para que SQLModel.metadata quede completo
y Alembic (migrations/env.py) pueda autogenerar las migraciones.
Ejemplo cuando existan:
    from app.modules.editoriales.models import Editorial  # noqa: F401
"""
