"""Inspección del código de los módulos migrados (sin base): la arquitectura Router -> Service -> UoW -> Repository.

Vale para el catálogo (CHG-13: `libros`, `editoriales`, `generos` y `autores`) y `clientes` (CHG-15). El negocio informa con excepciones de
dominio (nunca `HTTPException`), el repositorio no confirma, el servicio ya no confirma ni pagina
con el módulo viejo y el router no toca la sesión. Se mira el árbol sintáctico y no el texto, así
un comentario que nombre `HTTPException` no cuenta.
"""
import ast
from pathlib import Path

import pytest

MODULOS = Path(__file__).resolve().parent.parent / "app" / "modules"
CATALOGO = ["libros", "editoriales", "generos", "autores"]
MIGRADOS = CATALOGO + ["clientes"]


def _nombres(modulo: str, archivo: str) -> set[str]:
    """Todo lo que el archivo importa o nombra (identificadores, atributos y módulos importados)."""
    arbol = ast.parse((MODULOS / modulo / archivo).read_text(encoding="utf-8"))
    nombres: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Name):
            nombres.add(nodo.id)
        elif isinstance(nodo, ast.Attribute):
            nombres.add(nodo.attr)
        elif isinstance(nodo, ast.ImportFrom):
            nombres.add(nodo.module or "")
            nombres.update(a.name for a in nodo.names)
        elif isinstance(nodo, ast.Import):
            nombres.update(a.name for a in nodo.names)
    return nombres


@pytest.mark.parametrize("modulo", MIGRADOS)
@pytest.mark.parametrize("archivo", ["service.py", "repository.py", "unit_of_work.py"])
@pytest.mark.parametrize("prohibido", ["HTTPException", "commit_or_409", "traducir_integrity", "app.core.pagination"])
def test_el_negocio_migrado_no_usa_lo_viejo_ni_errores_http(modulo, archivo, prohibido):
    assert prohibido not in _nombres(modulo, archivo)


@pytest.mark.parametrize("modulo", MIGRADOS)
@pytest.mark.parametrize("prohibido", ["AsyncSession", "get_session", "HTTPException", "app.core.pagination"])
def test_el_router_migrado_no_importa_la_sesion_ni_la_paginacion_vieja(modulo, prohibido):
    assert prohibido not in _nombres(modulo, "router.py")


@pytest.mark.parametrize("modulo", MIGRADOS)
@pytest.mark.parametrize("archivo", ["service.py", "repository.py"])
def test_ni_el_servicio_ni_el_repositorio_confirman(modulo, archivo):
    assert "commit" not in _nombres(modulo, archivo)


@pytest.mark.parametrize("modulo", MIGRADOS)
def test_los_mensajes_de_409_viven_solo_en_el_uow(modulo):
    assert "MENSAJES" not in _nombres(modulo, "service.py")
    assert "MENSAJES" in _nombres(modulo, "unit_of_work.py")


@pytest.mark.parametrize("modulo", MIGRADOS)
def test_los_servicios_migrados_reciben_el_uow_y_no_la_sesion(modulo):
    assert "AsyncSession" not in _nombres(modulo, "service.py")
