"""Registro central de modelos.

Acá se importan TODOS los modelos de los módulos (editoriales, generos,
autores, libros, clientes, ventas) para que SQLModel.metadata quede completo
y Alembic (migrations/env.py) pueda autogenerar las migraciones.
Ejemplo cuando existan:
    from app.modules.editoriales.models import Editorial  # noqa: F401
"""

# Primero la naming convention: debe fijarse antes de definir cualquier tabla.
import app.core.base  # noqa: F401

# B y C agregan acá los imports de sus modelos (un import por modelo, con noqa: F401).
from app.modules.editoriales.models import Editorial  # noqa: F401,E402
from app.modules.generos.models import Genero  # noqa: F401,E402
