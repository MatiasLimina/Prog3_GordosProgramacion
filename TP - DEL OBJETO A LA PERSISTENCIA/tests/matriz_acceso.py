"""Matriz de acceso: la clasificación de TODAS las rutas de la API (CHG-12, no es un test).

Fuente de verdad de `test_grupos_de_rutas.py` (estructura, sin base) y de
`test_autorizacion_db.py` (comportamiento, con base). Una ruta nueva que no figure acá hace
fallar la suite nombrándola; quien agrega rutas (CHG-13, 14, 16) las suma en su propio PR.

Cada entrada es `(método, ruta) -> (grupo, acceso)`, con la ruta tal como la declara FastAPI
(`/libros/{libro_id}`). `grupo` es `ABIERTO` o `PROTEGIDO`. `acceso` es:
- `CUALQUIERA`: no pide sesión (sólo en el grupo abierto);
- `AUTENTICADO`: pide sesión (401 sin ella) pero ningún rol; en el abierto son `/auth/yo` y
  `/auth/cambiar-password` (no pasan por el control del cambio obligatorio), en el protegido
  irá `/mis-ventas` (CHG-16);
- un `frozenset` de roles: alguno de ellos vigente (`SOLO_ADMIN` / `PERSONAL`).
"""
import re
from collections.abc import Iterator

from fastapi import FastAPI
from fastapi.routing import APIRoute

ABIERTO = "abierto"
PROTEGIDO = "protegido"
CUALQUIERA = "cualquiera"
AUTENTICADO = "autenticado"
ADMIN = frozenset({"ADMIN"})
PERSONAL = frozenset({"VENDEDOR", "ADMIN"})

MATRIZ: dict[tuple[str, str], tuple[str, str | frozenset[str]]] = {
    # salud y auth: grupo abierto
    ("GET", "/health/live"): (ABIERTO, CUALQUIERA),
    ("GET", "/health/ready"): (ABIERTO, CUALQUIERA),
    ("POST", "/auth/registro"): (ABIERTO, CUALQUIERA),
    ("POST", "/auth/login"): (ABIERTO, CUALQUIERA),
    ("POST", "/auth/logout"): (ABIERTO, CUALQUIERA),
    ("GET", "/auth/yo"): (ABIERTO, AUTENTICADO),
    ("POST", "/auth/cambiar-password"): (ABIERTO, AUTENTICADO),
    # catálogo público: los GET (D9: incluye GET /editoriales/{id} y GET /autores/ y /autores/{id})
    ("GET", "/libros/"): (ABIERTO, CUALQUIERA),
    ("GET", "/libros/{libro_id}"): (ABIERTO, CUALQUIERA),
    ("GET", "/editoriales/"): (ABIERTO, CUALQUIERA),
    ("GET", "/editoriales/{editorial_id}"): (ABIERTO, CUALQUIERA),
    ("GET", "/editoriales/{editorial_id}/libros"): (ABIERTO, CUALQUIERA),
    ("GET", "/generos/"): (ABIERTO, CUALQUIERA),
    ("GET", "/generos/{genero_id}/libros"): (ABIERTO, CUALQUIERA),
    ("GET", "/autores/"): (ABIERTO, CUALQUIERA),
    ("GET", "/autores/{autor_id}"): (ABIERTO, CUALQUIERA),
    ("GET", "/autores/{autor_id}/libros"): (ABIERTO, CUALQUIERA),
    # administración del catálogo: ADMIN
    ("POST", "/editoriales/"): (PROTEGIDO, ADMIN),
    ("PATCH", "/editoriales/{editorial_id}"): (PROTEGIDO, ADMIN),
    ("POST", "/generos/"): (PROTEGIDO, ADMIN),
    ("POST", "/autores/"): (PROTEGIDO, ADMIN),
    ("PATCH", "/autores/{autor_id}"): (PROTEGIDO, ADMIN),
    ("POST", "/libros/"): (PROTEGIDO, ADMIN),
    ("PATCH", "/libros/{libro_id}"): (PROTEGIDO, ADMIN),
    # CHG-13: baja lógica, reposición e historial de stock de un libro (consigna: ADMIN)
    ("DELETE", "/libros/{libro_id}"): (PROTEGIDO, ADMIN),
    ("POST", "/libros/{libro_id}/reponer"): (PROTEGIDO, ADMIN),
    ("GET", "/libros/{libro_id}/movimientos"): (PROTEGIDO, ADMIN),
    # personal: VENDEDOR o ADMIN (D9: GET /clientes/ también)
    ("POST", "/clientes/"): (PROTEGIDO, PERSONAL),
    ("GET", "/clientes/"): (PROTEGIDO, PERSONAL),
    ("GET", "/clientes/{cliente_id}"): (PROTEGIDO, PERSONAL),
    ("PATCH", "/clientes/{cliente_id}"): (PROTEGIDO, PERSONAL),
    ("POST", "/clientes/{cliente_id}/perfil"): (PROTEGIDO, PERSONAL),
    ("GET", "/clientes/{cliente_id}/ventas"): (PROTEGIDO, PERSONAL),
    ("POST", "/ventas/"): (PROTEGIDO, PERSONAL),
    ("GET", "/ventas/"): (PROTEGIDO, PERSONAL),
    # PROVISORIO (D8): el estado final es protegido SIN rol y decide el servicio (CHG-16).
    ("GET", "/ventas/{venta_id}"): (PROTEGIDO, PERSONAL),
}


def rutas_de_la_app(app: FastAPI) -> dict[tuple[str, str], list]:
    """`(método, ruta) -> funciones de sus dependencias de primer nivel`, ya con las del grupo.

    FastAPI 0.162 incluye los routers de forma perezosa (`_IncludedRouter`): `app.routes` no
    trae las `APIRoute` aplanadas. Se desciende con `effective_candidates()` (API interna de
    FastAPI; si cambia, este es el único lugar que se ajusta). Se ignoran las rutas que no son
    de la API (`/docs`, `/openapi.json`, `/redoc`).
    """
    resultado: dict[tuple[str, str], list] = {}

    def recorrer(rutas) -> Iterator:
        for ruta in rutas:
            if hasattr(ruta, "effective_candidates"):
                yield from recorrer(ruta.effective_candidates())
            else:
                yield ruta

    for ruta in recorrer(app.router.routes):
        dependant = getattr(ruta, "dependant", None)
        if dependant is None:
            continue  # /docs, /openapi.json, /redoc
        if isinstance(ruta, APIRoute) or hasattr(ruta, "original_route"):
            llamadas = [d.call for d in dependant.dependencies]
            for metodo in ruta.methods:
                resultado[(metodo, ruta.path)] = llamadas
    return resultado


def ruta_concreta(ruta: str) -> str:
    """Rellena los parámetros de ruta con `1`: `/libros/{libro_id}` -> `/libros/1`."""
    return re.sub(r"\{[^}]+\}", "1", ruta)
