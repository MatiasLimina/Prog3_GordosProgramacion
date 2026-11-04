"""Repositorios base: construcción y contratos que no necesitan base."""
import ast
import inspect
from pathlib import Path

import pytest
from sqlalchemy.dialects import postgresql
from sqlmodel import SQLModel

import app.core.repository as modulo_repository
from app.core.repository import BaseRepository, SoftDeleteRepository
from app.modules.editoriales.models import Editorial
from tests.modelos_prueba import Borrable


class SesionFalsa:
    def __init__(self):
        self.llamadas = []

    async def delete(self, entidad):
        self.llamadas.append("delete")

    async def flush(self):
        self.llamadas.append("flush")


def sql(consulta) -> str:
    return str(consulta.compile(dialect=postgresql.dialect()))


def test_base_repository_guarda_sesion_y_modelo():
    sesion = SesionFalsa()
    repo = BaseRepository(sesion, Editorial)
    assert repo.session is sesion
    assert repo.model is Editorial


def test_soft_delete_repository_rechaza_un_modelo_sin_borrado_en():
    with pytest.raises(TypeError, match="Editorial"):
        SoftDeleteRepository(SesionFalsa(), Editorial)


def test_soft_delete_repository_acepta_un_modelo_con_borrado_en():
    repo = SoftDeleteRepository(SesionFalsa(), Borrable)
    assert repo.model is Borrable


def test_el_modelo_de_prueba_no_esta_en_el_metadata_global():
    assert "prueba_borrable" not in SQLModel.metadata.tables


def test_consulta_base_filtra_borrados_solo_en_soft_delete():
    con_filtro = sql(SoftDeleteRepository(SesionFalsa(), Borrable)._consulta_base())
    sin_filtro = sql(BaseRepository(SesionFalsa(), Editorial)._consulta_base())
    assert "borrado_en IS NULL" in con_filtro
    assert "WHERE" not in sin_filtro


async def test_delete_fisico_de_soft_delete_no_esta_permitido_y_no_toca_la_sesion():
    sesion = SesionFalsa()
    repo = SoftDeleteRepository(sesion, Borrable)
    with pytest.raises(NotImplementedError, match="Usá soft_delete"):
        await repo.delete(Borrable(nombre="x"))
    assert sesion.llamadas == []


def test_el_modulo_no_importa_fastapi():
    arbol = ast.parse(Path(inspect.getsourcefile(modulo_repository)).read_text(encoding="utf-8"))
    importados = {
        (n.module or "").split(".")[0] if isinstance(n, ast.ImportFrom) else a.name.split(".")[0]
        for n in ast.walk(arbol)
        if isinstance(n, (ast.Import, ast.ImportFrom))
        for a in (n.names if isinstance(n, ast.Import) else [n])
    }
    assert "fastapi" not in importados
