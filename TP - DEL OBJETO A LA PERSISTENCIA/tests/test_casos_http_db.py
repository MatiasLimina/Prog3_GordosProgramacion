"""Corre cada `test/cNN_*.http` contra la app sobre el seed y compara los códigos (CHG-18).

Equivale a `python seed.py` + correr el archivo en REST Client: cada archivo parte de la carga
inicial (el `client` vacía las tablas por test y acá se carga el seed). Sólo se compara el código
HTTP con el `# Esperado:` de cada pedido; lo demás (cuerpos, tiempos, consola, SQL) queda en los
comentarios para la corrección manual. Intérprete: `tests/casos_http.py`.
"""
import asyncio
from pathlib import Path

import pytest

from seed import cargar_datos
from tests.casos_http import ejecutar, leer

pytestmark = pytest.mark.db

TEST_DIR = Path(__file__).resolve().parent.parent / "test"
ARCHIVOS_CASO = sorted(TEST_DIR.glob("c[0-9][0-9]_*.http"))


async def _sembrar(sessionmaker) -> None:
    async with sessionmaker() as s:
        await cargar_datos(s, costo=4, semaforo=asyncio.Semaphore(4))


# --- el ejecutor mismo (archivos mínimos en tmp_path) ---

async def test_ejecutor_acepta_el_codigo_esperado(client, tmp_path):
    f = tmp_path / "c97_vivo.http"
    f.write_text("### vivo\n# Esperado: 200\n# @no-cookie-jar\nGET {{host}}/health/live\n", encoding="utf-8")
    resultados = await ejecutar(client, leer(f.read_text(encoding="utf-8")), host="http://test", nombre_archivo=f.name)
    assert [r.codigo for r in resultados] == [200]


async def test_ejecutor_falla_nombrando_archivo_linea_y_ambos_codigos(client, tmp_path):
    f = tmp_path / "c96_mal.http"
    f.write_text("### mal\n# Esperado: 404\n# @no-cookie-jar\nGET {{host}}/health/live\n", encoding="utf-8")
    with pytest.raises(AssertionError) as e:
        await ejecutar(client, leer(f.read_text(encoding="utf-8")), host="http://test", nombre_archivo=f.name)
    mensaje = str(e.value)
    assert "c96_mal.http:4" in mensaje and "404" in mensaje and "200" in mensaje


async def test_ejecutor_rechaza_un_pedido_sin_esperado(client):
    with pytest.raises(AssertionError, match="Esperado"):
        await ejecutar(client, leer("### x\nGET {{host}}/health/live\n"), host="http://test", nombre_archivo="x.http")


async def test_ejecutor_no_arrastra_cookies_entre_pedidos(client, sessionmaker_test):
    """Tras un login, un pedido siguiente SIN `Cookie` explícita debe ser anónimo (401)."""
    await _sembrar(sessionmaker_test)
    texto = (
        "@p = admin-seed-1\n"
        "### login\n# Esperado: 200\n# @no-cookie-jar\nPOST {{host}}/auth/login\nContent-Type: application/json\n\n"
        '{"email": "admin@example.com", "password": "{{p}}"}\n'
        "### anónimo\n# Esperado: 401\n# @no-cookie-jar\nGET {{host}}/auth/yo\n"
    )
    resultados = await ejecutar(client, leer(texto), host="http://test", nombre_archivo="cookies.http")
    assert [r.codigo for r in resultados] == [200, 401]


# --- los casos del parcial ---

@pytest.mark.parametrize("ruta", ARCHIVOS_CASO, ids=lambda r: r.name)
async def test_caso_http(ruta, client, sessionmaker_test):
    await _sembrar(sessionmaker_test)
    archivo = leer(ruta.read_text(encoding="utf-8"))
    await ejecutar(client, archivo, host="http://test", nombre_archivo=ruta.name)
