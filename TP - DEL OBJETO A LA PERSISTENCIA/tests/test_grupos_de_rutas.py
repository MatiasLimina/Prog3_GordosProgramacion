"""Estructura de los dos grupos de rutas (CHG-12, sin base).

La clasificación de `tests/matriz_acceso.py` es la fuente de verdad: este test compara la app
real contra ella, así una ruta sin clasificar, un control mal montado o un rol mal puesto
fallan acá y no se descubren en producción.
"""
import pytest

from app.core.dependencies import control_cambio_obligatorio
from app.main import app
from tests.matriz_acceso import ABIERTO, CUALQUIERA, MATRIZ, PROTEGIDO, rutas_de_la_app

_RUTAS = rutas_de_la_app(app)


def test_la_matriz_clasifica_exactamente_las_rutas_de_la_app():
    de_la_app, de_la_matriz = set(_RUTAS), set(MATRIZ)
    assert de_la_app == de_la_matriz, (
        f"Rutas sin clasificar en tests/matriz_acceso.py: {sorted(de_la_app - de_la_matriz)}. "
        f"Rutas de la matriz que no existen en la app: {sorted(de_la_matriz - de_la_app)}."
    )


def _con_control(llamadas) -> int:
    return sum(1 for llamada in llamadas if llamada is control_cambio_obligatorio)


@pytest.mark.parametrize("clave", sorted(MATRIZ), ids=lambda c: f"{c[0]} {c[1]}")
def test_el_control_del_cambio_obligatorio_esta_una_vez_en_cada_ruta_protegida_y_en_ninguna_abierta(clave):
    grupo, _ = MATRIZ[clave]
    esperado = 1 if grupo == PROTEGIDO else 0
    assert _con_control(_RUTAS[clave]) == esperado, f"{clave} ({grupo})"


@pytest.mark.parametrize("clave", sorted(MATRIZ), ids=lambda c: f"{c[0]} {c[1]}")
def test_los_roles_exigidos_por_cada_ruta_coinciden_con_la_matriz(clave):
    _, acceso = MATRIZ[clave]
    exigidos = {llamada.roles for llamada in _RUTAS[clave] if hasattr(llamada, "roles")}
    if isinstance(acceso, frozenset):
        assert exigidos == {acceso}, f"{clave}: exige {exigidos or 'ningún rol'}, la matriz dice {set(acceso)}"
    else:
        assert exigidos == set(), f"{clave}: la matriz dice «{acceso}» pero exige {exigidos}"


def test_la_matriz_es_coherente_consigo_misma():
    # Un «cualquiera» no puede estar en el grupo protegido (el control pide sesión a todo lo protegido).
    assert not [c for c, (g, a) in MATRIZ.items() if g == PROTEGIDO and a == CUALQUIERA]
    assert {g for g, _ in MATRIZ.values()} == {ABIERTO, PROTEGIDO}
