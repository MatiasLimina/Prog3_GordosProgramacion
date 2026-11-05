"""Envoltorio de paginación de los listados (consigna, sección 2.9).

Todo listado responde `{items, total, page, size, pages}`: `page` empieza en 1,
`size` va de 1 a 100 (por defecto 20), `pages` es el techo de `total / size` con
mínimo 1 (con cero resultados hay una página, vacía) y pedir una página más allá
de la última responde 422 con «La página {page} no existe: hay {pages}».

El core no conoce HTTP: la página fuera de rango lanza `PeticionInvalida` (excepción
de dominio de `core/errors.py`) y el handler de `app/main.py` la traduce a 422.
"""
from dataclasses import dataclass
from math import ceil
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

from app.core.errors import PeticionInvalida

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Envoltorio de un listado; `T` es el contrato de salida de cada ítem."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int


@dataclass(frozen=True)
class ParametrosPagina:
    page: int
    size: int


def paginacion_params(
    page: int = Query(1, ge=1, description="Página pedida, empezando en 1"),
    size: int = Query(20, ge=1, le=100, description="Cantidad de resultados por página"),
) -> ParametrosPagina:
    return ParametrosPagina(page=page, size=size)


def envolver(items: list[T], *, total: int, page: int, size: int) -> Page[T]:
    """Arma el envoltorio de una página ya leída.

    `total` es la cantidad de resultados con los mismos filtros que la página,
    sin paginar; `items` son sólo los de la página pedida. `page` se valida acá
    porque el rango válido depende de `total`, que recién se conoce al consultar.
    """
    if size < 1:
        raise PeticionInvalida("El tamaño de página debe ser al menos 1")
    pages = max(1, ceil(total / size))
    if not 1 <= page <= pages:
        raise PeticionInvalida(f"La página {page} no existe: hay {pages}")
    return Page(items=items, total=total, page=page, size=size, pages=pages)
