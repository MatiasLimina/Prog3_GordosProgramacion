"""Inspección del código del módulo `libros` (CHG-13, sin base): la arquitectura Router -> Service -> UoW -> Repository.

El negocio informa con excepciones de dominio (nunca `HTTPException`), el repositorio no confirma,
el servicio ya no confirma ni pagina con el módulo viejo y el router no toca la sesión. Se mira el
árbol sintáctico y no el texto, así un comentario que nombre `HTTPException` no cuenta.
"""
import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent / "app" / "modules" / "libros"


def _nombres(archivo: str) -> set[str]:
    """Todo lo que el archivo importa o nombra (identificadores, atributos y módulos importados)."""
    arbol = ast.parse((RAIZ / archivo).read_text(encoding="utf-8"))
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


@pytest.mark.parametrize("archivo", ["service.py", "repository.py", "unit_of_work.py"])
@pytest.mark.parametrize("prohibido", ["HTTPException", "commit_or_409", "traducir_integrity", "app.core.pagination"])
def test_el_negocio_de_libros_no_usa_lo_viejo_ni_errores_http(archivo, prohibido):
    assert prohibido not in _nombres(archivo)


@pytest.mark.parametrize("prohibido", ["AsyncSession", "get_session", "HTTPException"])
def test_el_router_de_libros_no_importa_la_sesion(prohibido):
    assert prohibido not in _nombres("router.py")


@pytest.mark.parametrize("archivo", ["service.py", "repository.py"])
def test_ni_el_servicio_ni_el_repositorio_confirman(archivo):
    assert "commit" not in _nombres(archivo)


def test_los_mensajes_de_409_viven_solo_en_el_uow():
    assert "MENSAJES" not in {n for n in _nombres("service.py")}
    assert "MENSAJES" in _nombres("unit_of_work.py")
