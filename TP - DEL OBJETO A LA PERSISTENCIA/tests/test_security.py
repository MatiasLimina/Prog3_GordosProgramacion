import secrets

import bcrypt
import pytest

import app.core.security as seguridad
from app.core.security import calcular_hash_ficticio


@pytest.mark.parametrize("costo", [4, 5])
def test_el_hash_ficticio_tiene_el_costo_recibido(costo):
    hash_ficticio = calcular_hash_ficticio(costo)
    assert isinstance(hash_ficticio, str)
    assert hash_ficticio.startswith(f"$2b${costo:02d}$")


def test_usa_gensalt_con_el_costo_recibido(monkeypatch):
    # Mismo costo que los hashes reales: si difiriera, el tiempo del login delataría
    # si el correo existe (RN-08).
    llamadas = []
    real = bcrypt.gensalt

    def espia(rounds=12, prefix=b"2b"):
        llamadas.append(rounds)
        return real(rounds=rounds, prefix=prefix)

    monkeypatch.setattr(seguridad.bcrypt, "gensalt", espia)
    calcular_hash_ficticio(5)
    assert llamadas == [5]


@pytest.mark.parametrize("candidata", ["", "password", secrets.token_urlsafe(16)])
def test_ninguna_contrasena_conocida_coincide(candidata):
    hash_ficticio = calcular_hash_ficticio(4)
    assert bcrypt.checkpw(candidata.encode(), hash_ficticio.encode()) is False


def test_dos_hashes_ficticios_son_distintos():
    assert calcular_hash_ficticio(4) != calcular_hash_ficticio(4)
