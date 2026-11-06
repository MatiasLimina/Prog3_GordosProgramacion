"""calcular_retry_after: segundos que faltan para que el fallo más viejo salga de la ventana (D4)."""
from datetime import UTC, datetime, timedelta

import pytest

AHORA = datetime(2026, 11, 5, 12, 0, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    "antiguedad_s, esperado",
    [
        (58.5, 2),   # faltan 1,5 s: se redondea hacia arriba
        (0, 60),     # recién ocurrido: la ventana entera
        (59.9, 1),   # faltan 0,1 s: nunca 0
        (10, 50),    # exacto
        (59, 1),
    ],
)
def test_retry_after_es_lo_que_falta_redondeado_hacia_arriba(antiguedad_s, esperado):
    from app.modules.usuarios.service import calcular_retry_after

    assert calcular_retry_after(AHORA, AHORA - timedelta(seconds=antiguedad_s)) == esperado


@pytest.mark.parametrize("antiguedad_s", [60, 61, 600, -5])
def test_retry_after_queda_siempre_entre_1_y_60(antiguedad_s):
    from app.modules.usuarios.service import calcular_retry_after

    resultado = calcular_retry_after(AHORA, AHORA - timedelta(seconds=antiguedad_s))
    assert isinstance(resultado, int)
    assert 1 <= resultado <= 60


def test_las_constantes_del_limite_son_las_de_la_consigna():
    from app.modules.usuarios.service import LIMITE_FALLOS, VENTANA_SEGUNDOS

    assert (LIMITE_FALLOS, VENTANA_SEGUNDOS) == (5, 60)
