import subprocess
import sys

import pytest

# Intérprete nuevo por caso: en el proceso de pytest otros tests ya importaron
# app.core.database y ocultarían el problema del orden de imports.
CODIGO = """
import {modulo}
from {modulo} import {clase}
nombres = {{c.name for c in {clase}.__table__.constraints}}
assert "{esperada}" in nombres, nombres
"""


@pytest.mark.parametrize(
    "modulo,clase,esperada",
    [
        ("app.modules.editoriales.models", "Editorial", "uq_editorial_nombre"),
        ("app.modules.generos.models", "Genero", "uq_genero_nombre"),
    ],
)
def test_importar_solo_un_modelo_ya_aplica_la_naming_convention(modulo, clase, esperada):
    codigo = CODIGO.format(modulo=modulo, clase=clase, esperada=esperada)
    r = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_base_fija_la_convencion_en_el_metadata():
    codigo = (
        "import app.core.base\n"
        "from sqlmodel import SQLModel\n"
        "assert SQLModel.metadata.naming_convention['uq'] == 'uq_%(table_name)s_%(column_0_name)s'\n"
    )
    r = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
