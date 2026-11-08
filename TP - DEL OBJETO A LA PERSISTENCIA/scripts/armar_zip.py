"""Arma el zip de la entrega del parcial (CHG-20).

Uso (desde la carpeta del proyecto, en PowerShell o en Git Bash):

    python scripts/armar_zip.py

Empaqueta dos carpetas: `parcial/` (este proyecto) y `despliegue/` (la carpeta hermana
`Despliegue`, que sólo se lee). La lista de archivos sale de git (`ls-files`: versionados
más los nuevos no ignorados), así que el `.gitignore` de cada carpeta es la exclusión
principal: un `.venv`, un `__pycache__` o un `.env` presentes en disco no entran.
`excluida` es la lista negra de respaldo, y un `.env` listado por git aborta el armado.
"""

import argparse
import os
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

GRUPO = "GordosProgramacion"
NOMBRE_ZIP = f"Parcial_Cap1a6_{GRUPO}.zip"

# Segmentos de ruta que nunca entran, en cualquier nivel.
CARPETAS_EXCLUIDAS = frozenset(
    {".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".git", ".claude"}
)
ARCHIVOS_EXCLUIDOS = frozenset({"CLAUDE.local.md"})
SUFIJOS_EXCLUIDOS = (".pyc", ".pyo")


def excluida(ruta: str) -> bool:
    """True si la ruta (relativa, con `/`) cae en la lista negra de respaldo."""
    partes = PurePosixPath(ruta).parts
    return (
        bool(CARPETAS_EXCLUIDAS.intersection(partes[:-1]))
        or partes[-1] in ARCHIVOS_EXCLUIDOS
        or partes[-1].endswith(SUFIJOS_EXCLUIDOS)
    )


def es_env(ruta: str) -> bool:
    """True para `.env` y sus variantes (`.env.local`, `.env.prod`...), no para `env.example`."""
    nombre = PurePosixPath(ruta).name
    return nombre == ".env" or nombre.startswith(".env.")


def listar_archivos(carpeta: Path) -> list[str]:
    """Rutas (relativas, con `/`, ordenadas) que entran al zip desde `carpeta`.

    Sale de `git ls-files --cached --others --exclude-standard` (el `-z` evita el
    escapado de espacios y acentos), sin lo que `excluida` descarta y sin los
    archivos versionados que ya no existen en disco.

    Raises:
        FileNotFoundError: si la carpeta no existe o `git` no está en el PATH.
        ValueError: si git lista un `.env` o una variante (versionado o sin ignorar): es un secreto.
    """
    if not carpeta.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de origen: {carpeta}")
    try:
        salida = subprocess.run(
            ["git", "-C", str(carpeta), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            check=True,
            capture_output=True,
        ).stdout
    except FileNotFoundError as error:
        raise FileNotFoundError("No se encontró `git` en el PATH.") from error
    except subprocess.CalledProcessError as error:
        detalle = error.stderr.decode("utf-8", "replace").strip()
        raise ValueError(f"`{carpeta}` no es un repositorio git ({detalle}).") from error

    rutas = [r.decode("utf-8") for r in salida.split(b"\0") if r]
    envs = [r for r in rutas if es_env(r)]
    if envs:
        raise ValueError(
            f"git lista un archivo .env en {carpeta}: {', '.join(envs)}. "
            "Si está versionado, sacalo del repositorio (git rm --cached) y rotá sus credenciales; "
            "si no, agregalo al .gitignore o borralo antes de entregar."
        )
    return sorted(r for r in rutas if not excluida(r) and (carpeta / r).is_file())


def armar_zip(origenes: dict[str, Path], destino: Path) -> dict[str, int]:
    """Escribe `destino` con las entradas `<raiz>/<ruta>` y devuelve cuántas hay por raíz.

    Primero lista todas las carpetas (cualquier error corta antes de escribir) y arma
    el zip en un temporal que se renombra al final: nunca queda un zip a medias.
    """
    listados = {raiz: (carpeta, listar_archivos(carpeta)) for raiz, carpeta in sorted(origenes.items())}

    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_name(destino.name + ".tmp")
    try:
        with zipfile.ZipFile(temporal, "w", zipfile.ZIP_DEFLATED) as z:
            for raiz, (carpeta, archivos) in listados.items():
                for ruta in archivos:
                    z.write(carpeta / ruta, f"{raiz}/{ruta}")
        os.replace(temporal, destino)
    except BaseException:
        temporal.unlink(missing_ok=True)
        raise
    return {raiz: len(archivos) for raiz, (_, archivos) in listados.items()}


def main(argv: list[str] | None = None) -> int:
    proyecto = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=f"Arma {NOMBRE_ZIP} con parcial/ y despliegue/.")
    parser.add_argument("--parcial", type=Path, default=proyecto, help="carpeta del parcial")
    parser.add_argument(
        "--despliegue", type=Path, default=proyecto.parent / "Despliegue", help="carpeta del TP 1-4"
    )
    parser.add_argument(
        "--salida", type=Path, default=proyecto / "dist" / NOMBRE_ZIP, help="ruta del zip a escribir"
    )
    args = parser.parse_args(argv)

    try:
        cuentas = armar_zip(
            {"parcial": args.parcial.resolve(), "despliegue": args.despliegue.resolve()},
            args.salida.resolve(),
        )
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Zip armado: {args.salida.resolve()}")
    for raiz, cantidad in cuentas.items():
        print(f"  {raiz}/: {cantidad} archivos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
