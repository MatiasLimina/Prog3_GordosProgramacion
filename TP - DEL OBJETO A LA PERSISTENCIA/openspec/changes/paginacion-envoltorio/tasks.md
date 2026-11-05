# Tasks

## 1. Artefactos openspec

- [ ] 1.1 Escribir `proposal.md`, `specs/paginacion/spec.md`, `design.md` y `tasks.md` de `paginacion-envoltorio` siguiendo la consigna (sección 2.9, Ejercicio 3 y ejemplo de la página 19) y `PLAN_PARCIAL.md` CHG-05. Verificar `openspec validate paginacion-envoltorio` sin errores.

## 2. Tests del envoltorio (RED)

- [ ] 2.1 Crear `tests/test_paginacion.py` con una app FastAPI de test que declara `GET /items` con `p: ParametrosPagina = Depends(paginacion_params)` y devuelve `envolver([...], total=..., page=p.page, size=p.size)`. Casos: valores por defecto (`page=1`, `size=20`); `page=0`, `size=0`, `size=101` y `page` no entero → 422; `size=1` y `size=100` → 200. Verificar que falla por `ModuleNotFoundError` (no existe `app.core.paginacion`).
- [ ] 2.2 Agregar casos de `envolver` directo (sin HTTP): 0 resultados → `pages=1`, `items` vacío; 1 resultado con `size=20` → `pages=1`; múltiplo exacto (4 resultados, `size=2`) → `pages=2`; sobrante (5 resultados, `size=2`) → `pages=3` con `page=3` trayendo 1 ítem; `page=4` con `pages=3` → `HTTPException` 422 con detalle «La página 4 no existe: hay 3»; `page=2` con lista vacía → 422 «La página 2 no existe: hay 1»; `Page[int]` serializa con `model_dump()`/`model_dump_json()` con los cinco campos. Verificar que fallan por el módulo inexistente.

## 3. Implementación (GREEN)

- [ ] 3.1 Implementar `app/core/paginacion.py`: `ParametrosPagina`, `paginacion_params` con `Query`, `Page[T]` genérico pydantic y `envolver` con `pages = max(1, ceil(total / size))` y el `HTTPException(422, «La página {page} no existe: hay {pages}»)`. Docstrings en español. Verificar `python -m pytest tests/test_paginacion.py -q` en verde.

## 4. Verificación e integración

- [ ] 4.1 Correr `python -m pytest tests/test_paginacion.py tests/test_pagination.py -q`: los tests nuevos en verde y los del archivo viejo (`limit`/`offset`) intactos, porque `pagination.py` no se toca. Verificar `git status --short` mostrando sólo los archivos de este change.
- [ ] 4.2 REFACTOR: revisar nombres, docstrings y comentarios en español; sin cambios de comportamiento. Verificar `python -m pytest tests/test_paginacion.py -q` en verde.
- [ ] 4.3 `PLAN_PARCIAL.md`: dejar la fila de CHG-05 según la regla nueva de `AGENTS.md` §10 (el último PR la pone en `mergeado (#N)` con el número del PR; si el change se parte en varios PRs, `en curso` mientras tanto). Verificar con `git diff` que sólo cambia lo previsto.

## Workflow follow-up

- Commit por hito: artefactos openspec (`docs(openspec): ...`), luego `feat(core): envoltorio de paginación page/size` y, al final, el commit de cierre con `PLAN_PARCIAL.md` + change archivado.
- Crear la PR con la plantilla del repo; al tener el número, actualizar la fila de CHG-05 a `mergeado (#N)` y archivar el change con `openspec archive paginacion-envoltorio` en la misma rama antes de pedir revisión.
