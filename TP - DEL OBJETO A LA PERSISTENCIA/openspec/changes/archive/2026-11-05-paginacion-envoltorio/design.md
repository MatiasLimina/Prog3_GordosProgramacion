# Design

## Context

El parcial reemplaza el `limit`/`offset` del TP 1–4 por el envoltorio `{items, total, page, size, pages}` (consigna, sección 2.9 y Ejercicio 3). `app/core/pagination.py` sigue vivo y lo usan los routers y servicios actuales: se migra en CHG-13/15/16, no acá (ver «Transición» de `AGENTS.md`, sección 9). Este change entrega sólo la pieza de `app/core/paginacion.py` que esos changes van a consumir; ningún listado cambia de comportamiento todavía. Ver `proposal.md` para el porqué.

## Goals / Non-Goals

**Goals:**
- Un único lugar que valide `page`/`size`, calcule `pages` y arme el envoltorio, reutilizable por todos los módulos.
- `Page[T]` genérico: cada módulo lo instancia con su contrato de salida sin acoplar el core a los schemas de dominio.

**Non-Goals:**
- Migrar routers/servicios existentes ni borrar `app/core/pagination.py`.
- Calcular `offset`/`limit` ni `total` (los trae el servicio que consulta, con los mismos filtros que la página).
- Traducir el 422 a otro formato: el cuerpo `{"detail": "..."}` de `HTTPException` ya es el que usan los 422 del proyecto.

## Decisions

- **`Page[T]` como `pydantic.BaseModel` genérico** (Python 3.12: `class Page(BaseModel, Generic[T])` con `items: list[T]`, `total`, `page`, `size`, `pages`). Alternativas: dataclass (necesitaría `response_model` en cada ruta y no valida tipos) o `TypedDict` (sin validación ni serialización de FastAPI). Pydantic ya es la moneda del proyecto para contratos de salida y serializa solo.
- **Parámetros con `fastapi.Query` en una dependencia** (`page: int = Query(1, ge=1)`, `size: int = Query(20, ge=1, le=100)`), mismo patrón que `pagination_params` actual: FastAPI devuelve 422 solo, sin código extra, y el router declara `p: ParametrosPagina = Depends(paginacion_params)`.
- **`pages` = `max(1, ceil(total / size))`** calculado al armar el envoltorio. El mínimo 1 cubre el caso de cero resultados (consigna: «con cero resultados hay una página, vacía»); el techo evita la página vacía extra del múltiplo exacto.
- **La página fuera de rango lanza `HTTPException(422)` con el mensaje exacto** «La página {page} no existe: hay {pages}» desde la función que arma el envoltorio. Se evalúa después de conocer `total`, por eso no puede ser un `Query`. El core de paginación SÍ puede importar FastAPI (a diferencia de `repository.py`/`unit_of_work.py`): es una pieza del borde HTTP, igual que `dependencies.py` y el viejo `pagination.py`.
- **Nombres**: el archivo es `paginacion.py` (lo fija la consigna/AGENTS). Símbolos: `Page[T]` (lo fija el plan del change), `ParametrosPagina` (dataclass con `page` y `size`), la dependencia `paginacion_params` (mismo patrón que `pagination_params` del archivo viejo) y la función `envolver(items, *, total, page, size) -> Page`, que calcula `pages`, valida el rango y devuelve el envoltorio.

## Risks / Trade-offs

- [Risk] CHG-13/15 podrían preferir otra firma (p. ej. que el envoltorio reciba el offset ya calculado) → Mitigation: la firma mínima `envolver(items, *, total, page, size)` cubre el caso general; el offset es `(page - 1) * size`, trivial para el servicio.
- [Risk] Dos archivos de paginación conviviendo (`pagination.py` viejo y `paginacion.py` nuevo) confunde → Mitigation: la «Transición» de AGENTS.md ya documenta que el viejo muere al migrar los módulos (CHG-13/15/16); este change no lo toca.

## Migration Plan

No aplica: código nuevo sin consumidores todavía. Los listados lo adoptan en CHG-13/15/16.

## Open Questions

Ninguna.
