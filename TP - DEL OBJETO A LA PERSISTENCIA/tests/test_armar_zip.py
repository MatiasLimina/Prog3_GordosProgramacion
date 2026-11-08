"""Tests del script de armado del zip de la entrega (CHG-20). No usan la base.

Cada test arma dos carpetas `git init` en `tmp_path` (sin commits: `--others` las ve)
con un `.gitignore` como el real y con en disco lo que NUNCA debe entrar al zip.
"""

import subprocess
import zipfile
from pathlib import Path

import pytest

from scripts.armar_zip import armar_zip, excluida, listar_archivos, main

GITIGNORE = """\
.env
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
CLAUDE.local.md
dist/
ignorado.txt
"""

# Lo que está en disco y nunca debe llegar al zip.
PROHIBIDOS_EN_DISCO = [
    ".env",
    ".venv/pyvenv.cfg",
    "app/__pycache__/x.cpython-312.pyc",
    "__pycache__/y.pyc",
    ".pytest_cache/README.md",
    "CLAUDE.local.md",
    ".claude/settings.json",
    "ignorado.txt",
]

LEGITIMOS_PARCIAL = ["README.md", "app/main.py", "env.example", "test/c01.http"]
LEGITIMOS_DESPLIEGUE = ["Dockerfile", ".dockerignore", "DEPLOY.md", "evidencia/D-01.txt"]


def _git(carpeta: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(carpeta), *args], check=True, capture_output=True)


def _escribir(carpeta: Path, ruta: str, texto: str = "contenido") -> None:
    destino = carpeta / ruta
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")


def _armar_origen(carpeta: Path, legitimos: list[str]) -> Path:
    carpeta.mkdir(parents=True)
    _git(carpeta, "init", "-q")
    _escribir(carpeta, ".gitignore", GITIGNORE)
    for ruta in legitimos:
        _escribir(carpeta, ruta, f"legitimo {ruta}")
    for ruta in PROHIBIDOS_EN_DISCO:
        _escribir(carpeta, ruta, "SECRETO=1")
    return carpeta


@pytest.fixture
def origenes(tmp_path: Path) -> dict[str, Path]:
    return {
        "parcial": _armar_origen(tmp_path / "TP - DEL OBJETO", LEGITIMOS_PARCIAL),
        "despliegue": _armar_origen(tmp_path / "Despliegue", LEGITIMOS_DESPLIEGUE),
    }


def _entradas(destino: Path) -> list[str]:
    with zipfile.ZipFile(destino) as z:
        return z.namelist()


def test_el_zip_tiene_solo_las_dos_raices_y_los_archivos_legitimos(origenes, tmp_path):
    destino = tmp_path / "salida" / "entrega.zip"

    armar_zip(origenes, destino)

    entradas = _entradas(destino)
    assert {e.split("/")[0] for e in entradas} == {"parcial", "despliegue"}
    for ruta in LEGITIMOS_PARCIAL:
        assert f"parcial/{ruta}" in entradas
    for ruta in LEGITIMOS_DESPLIEGUE:
        assert f"despliegue/{ruta}" in entradas


def test_nada_prohibido_entra_al_zip_aunque_este_en_disco(origenes, tmp_path):
    destino = tmp_path / "entrega.zip"

    armar_zip(origenes, destino)

    entradas = _entradas(destino)
    assert entradas  # sin esto, el bucle de abajo pasaría con un zip vacío
    for entrada in entradas:
        partes = entrada.split("/")
        assert not {".venv", "__pycache__", ".pytest_cache", ".claude", ".git"} & set(partes)
        assert partes[-1] not in {".env", "CLAUDE.local.md", "ignorado.txt"}
        assert not entrada.endswith((".pyc", ".pyo"))


def test_un_archivo_nuevo_sin_commitear_entra(origenes, tmp_path):
    _escribir(origenes["parcial"], "evidencia/C-14.txt", "salida de psql")
    destino = tmp_path / "entrega.zip"

    armar_zip(origenes, destino)

    with zipfile.ZipFile(destino) as z:
        assert z.read("parcial/evidencia/C-14.txt") == b"salida de psql"


def test_el_zip_lleva_el_contenido_del_disco_y_el_dockerignore(origenes, tmp_path):
    destino = tmp_path / "entrega.zip"

    armar_zip(origenes, destino)

    with zipfile.ZipFile(destino) as z:
        assert z.read("despliegue/.dockerignore") == b"legitimo .dockerignore"
        assert z.read("parcial/README.md") == b"legitimo README.md"


def test_devuelve_la_cantidad_de_archivos_por_raiz(origenes, tmp_path):
    # Cada origen tiene su .gitignore (no ignorado) + sus legitimos.
    cuentas = armar_zip(origenes, tmp_path / "entrega.zip")

    assert cuentas == {
        "parcial": len(LEGITIMOS_PARCIAL) + 1,
        "despliegue": len(LEGITIMOS_DESPLIEGUE) + 1,
    }
    entradas = _entradas(tmp_path / "entrega.zip")
    assert sum(e.startswith("parcial/") for e in entradas) == cuentas["parcial"]


def test_las_entradas_estan_ordenadas_y_usan_barra_comun(origenes, tmp_path):
    armar_zip(origenes, tmp_path / "entrega.zip")

    entradas = _entradas(tmp_path / "entrega.zip")
    assert entradas == sorted(entradas)
    assert all("\\" not in e and not e.startswith("/") and ".." not in e.split("/") for e in entradas)


def test_las_carpetas_de_origen_quedan_iguales(origenes, tmp_path):
    def foto() -> dict[str, bytes]:
        return {
            str(p.relative_to(tmp_path)): p.read_bytes()
            for raiz in origenes.values()
            for p in raiz.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(raiz).parts
        }

    antes = foto()
    armar_zip(origenes, tmp_path / "entrega.zip")
    assert foto() == antes


def test_un_archivo_versionado_que_ya_no_esta_en_disco_no_figura(origenes, tmp_path):
    _git(origenes["parcial"], "add", "env.example")
    (origenes["parcial"] / "env.example").unlink()

    armar_zip(origenes, tmp_path / "entrega.zip")

    assert "parcial/env.example" not in _entradas(tmp_path / "entrega.zip")


def test_listar_archivos_devuelve_rutas_relativas_con_barra_y_acentos(origenes):
    _escribir(origenes["parcial"], "docs/añadido con espacio.md")

    archivos = listar_archivos(origenes["parcial"])

    assert "docs/añadido con espacio.md" in archivos
    assert "app/main.py" in archivos
    assert ".env" not in archivos


@pytest.mark.parametrize(
    "ruta",
    [
        ".venv/Lib/site.py",
        "app/__pycache__/x.cpython-312.pyc",
        "a/b/.pytest_cache/v/cache",
        ".claude/skills/x/SKILL.md",
        ".git/config",
        "modulo/viejo.pyc",
        "CLAUDE.local.md",
        "sub/CLAUDE.local.md",
    ],
)
def test_excluida_rechaza_lo_de_la_lista_negra(ruta):
    assert excluida(ruta) is True


@pytest.mark.parametrize(
    "ruta",
    [
        "app/main.py",
        "CLAUDE.md",
        "env.example",
        ".dockerignore",
        "docs/venv.md",
        "app/pycache_utils.py",
    ],
)
def test_excluida_deja_pasar_lo_legitimo(ruta):
    assert excluida(ruta) is False


def test_un_env_versionado_aborta_y_no_deja_zip(origenes, tmp_path):
    _git(origenes["despliegue"], "add", "-f", ".env")
    destino = tmp_path / "salida" / "entrega.zip"

    with pytest.raises(ValueError, match=r"\.env"):
        armar_zip(origenes, destino)

    assert not destino.exists()


def test_un_env_en_una_subcarpeta_versionado_tambien_aborta(origenes, tmp_path):
    _escribir(origenes["parcial"], "config/.env", "X=1")
    _git(origenes["parcial"], "add", "-f", "config/.env")

    with pytest.raises(ValueError, match=r"config/\.env"):
        armar_zip(origenes, tmp_path / "entrega.zip")


def test_carpeta_de_origen_inexistente_da_un_error_claro(origenes, tmp_path):
    origenes["despliegue"] = tmp_path / "no_existe"
    destino = tmp_path / "entrega.zip"

    with pytest.raises(FileNotFoundError, match="no_existe"):
        armar_zip(origenes, destino)

    assert not destino.exists()


def test_main_arma_el_zip_e_informa_ruta_y_conteos(origenes, tmp_path, capsys):
    destino = tmp_path / "dist" / "entrega.zip"

    codigo = main(
        ["--parcial", str(origenes["parcial"]), "--despliegue", str(origenes["despliegue"]), "--salida", str(destino)]
    )

    salida = capsys.readouterr().out
    assert codigo == 0
    assert destino.is_file()
    assert "entrega.zip" in salida
    assert f"parcial/: {len(LEGITIMOS_PARCIAL) + 1} archivos" in salida
    assert f"despliegue/: {len(LEGITIMOS_DESPLIEGUE) + 1} archivos" in salida


def test_main_devuelve_codigo_distinto_de_cero_ante_un_error(origenes, tmp_path, capsys):
    destino = tmp_path / "dist" / "entrega.zip"

    codigo = main(
        ["--parcial", str(origenes["parcial"]), "--despliegue", str(tmp_path / "no_existe"), "--salida", str(destino)]
    )

    assert codigo != 0
    assert "no_existe" in capsys.readouterr().err
    assert not destino.exists()


def test_main_con_un_env_versionado_falla_y_nombra_el_archivo(origenes, tmp_path, capsys):
    _git(origenes["parcial"], "add", "-f", ".env")
    destino = tmp_path / "entrega.zip"

    codigo = main(
        ["--parcial", str(origenes["parcial"]), "--despliegue", str(origenes["despliegue"]), "--salida", str(destino)]
    )

    assert codigo == 1
    assert ".env" in capsys.readouterr().err
    assert not destino.exists()


@pytest.mark.parametrize("nombre", [".env.local", ".env.prod", "config/.env.bak"])
def test_una_variante_de_env_no_ignorada_aborta(origenes, tmp_path, nombre):
    _escribir(origenes["parcial"], nombre, "X=1")  # sin commitear y fuera del .gitignore de la fixture
    destino = tmp_path / "entrega.zip"

    with pytest.raises(ValueError, match=r"\.env"):
        armar_zip(origenes, destino)

    assert not destino.exists()


def test_env_example_no_se_confunde_con_un_env(origenes, tmp_path):
    armar_zip(origenes, tmp_path / "entrega.zip")

    assert "parcial/env.example" in _entradas(tmp_path / "entrega.zip")


def test_un_fallo_al_escribir_no_pisa_el_zip_anterior_ni_deja_temporales(origenes, tmp_path, monkeypatch):
    destino = tmp_path / "salida" / "entrega.zip"
    armar_zip(origenes, destino)
    anterior = destino.read_bytes()

    def falla(self, *args, **kwargs):
        raise OSError("disco lleno")

    monkeypatch.setattr(zipfile.ZipFile, "write", falla)
    with pytest.raises(OSError, match="disco lleno"):
        armar_zip(origenes, destino)

    assert destino.read_bytes() == anterior
    assert [p.name for p in destino.parent.iterdir()] == ["entrega.zip"]


def test_si_no_se_puede_reemplazar_el_destino_no_queda_temporal(origenes, tmp_path, monkeypatch):
    destino = tmp_path / "salida" / "entrega.zip"

    def bloqueado(origen, nuevo):
        raise PermissionError("el zip está abierto en otro programa")

    monkeypatch.setattr("scripts.armar_zip.os.replace", bloqueado)
    with pytest.raises(PermissionError):
        armar_zip(origenes, destino)

    assert list(destino.parent.iterdir()) == []


def test_main_informa_un_error_de_sistema_sin_traceback(origenes, tmp_path, capsys, monkeypatch):
    def bloqueado(origen, nuevo):
        raise PermissionError("el zip está abierto en otro programa")

    monkeypatch.setattr("scripts.armar_zip.os.replace", bloqueado)

    codigo = main(
        ["--parcial", str(origenes["parcial"]), "--despliegue", str(origenes["despliegue"]),
         "--salida", str(tmp_path / "entrega.zip")]
    )

    assert codigo == 1
    assert "abierto en otro programa" in capsys.readouterr().err
