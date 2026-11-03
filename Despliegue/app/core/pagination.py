"""Dependencia de paginación común a todos los listados (RN-10)."""
from dataclasses import dataclass

from fastapi import Query


@dataclass(frozen=True)
class Pagination:
    limit: int
    offset: int


def pagination_params(
    limit: int = Query(20, ge=1, le=100, description="Cantidad máxima de resultados"),
    offset: int = Query(0, ge=0, description="Cantidad de resultados a saltear"),
) -> Pagination:
    return Pagination(limit=limit, offset=offset)
