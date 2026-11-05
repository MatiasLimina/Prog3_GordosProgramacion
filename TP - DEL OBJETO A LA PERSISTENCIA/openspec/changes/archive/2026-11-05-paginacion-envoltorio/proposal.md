# Proposal

## Why

El parcial exige que todos los listados devuelvan el envoltorio `{items, total, page, size, pages}` de la sección 2.9 de la consigna (Ejercicio 3, 10 puntos): `page` empieza en 1, `size` va de 1 a 100 (por defecto 20), pedir una página más allá de la última da 422 con el mensaje «La página 4 no existe: hay 3», y con cero resultados hay una página, vacía. Hoy sólo existe `app/core/pagination.py` del TP 1–4, que trabaja con `limit`/`offset` y no tiene ni `total` ni `pages`. CHG-05 es chico y sin dependencias de código (sólo CHG-00): entrega la pieza que CHG-13 y CHG-15 (oleada 3) van a usar en todos sus listados.

## What Changes

- `app/core/paginacion.py` (nuevo):
  - `Page[T]` con los campos `items`, `total`, `page`, `size` y `pages`, genérico en el tipo de cada ítem para que cada módulo lo use con su propio contrato de salida.
  - Una dependencia de parámetros de consulta (`page` ≥ 1, `size` de 1 a 100, por defecto 20) que FastAPI valida y traduce a 422 cuando no cumplen.
  - La función que arma el envoltorio: calcula `pages` como el techo de `total / size` con mínimo 1 (con cero resultados `pages = 1` y `items` vacío), y rechaza con 422 «La página {page} no existe: hay {pages}» cuando `page` supera la última.
- `tests/test_paginacion.py` (nuevo): tests unitarios de los parámetros, del cálculo de páginas y del rechazo de página fuera de rango, con 0 resultados, 1 resultado, un múltiplo exacto y un sobrante (DoD del change).

**Fuera de alcance**: migrar los listados existentes ni tocar `app/core/pagination.py` ni ningún router/servicio (eso es CHG-13, 15 y 16, que consumen esta pieza); el cálculo de `offset`/`limit` para el repositorio queda del lado del servicio que lo use; `total` siempre llega ya calculado con los mismos filtros que la página (responsabilidad del servicio/repo que consulta, no de este módulo).

## Capabilities

### New Capabilities

- `paginacion`: envoltorio común de los listados de la API: parámetros `page`/`size` validados, cálculo de `pages` con mínimo 1 y rechazo 422 de la página fuera de rango con mensaje propio.

### Modified Capabilities

<!-- Ninguna: el comportamiento de los listados existentes no cambia en este change. -->

## Impact

- Código nuevo: `app/core/paginacion.py` y `tests/test_paginacion.py`. Ningún archivo existente se modifica.
- APIs: ninguna ruta cambia todavía; los listados adoptan el envoltorio en CHG-13/15/16.
- Dependencias: ninguna nueva (FastAPI y pydantic ya están).
