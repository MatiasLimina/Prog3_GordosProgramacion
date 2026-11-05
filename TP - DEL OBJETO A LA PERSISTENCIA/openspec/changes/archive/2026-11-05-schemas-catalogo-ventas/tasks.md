# Tasks

TDD estricto: cada comportamiento tuvo una tarea RED antes de la implementación GREEN. Este change contiene sólo CHG-09b.

## 1. Contratos y validaciones

- [x] 1.1 RED — Actualizar `tests/test_catalogo_schemas.py` y `tests/test_libros_validaciones.py` con los casos nuevos (stock_inicial, LibroUpdate sólo título/precio, ReponerIn, PATCH con stock → 422) y confirmar que fallan contra los schemas actuales.
- [x] 1.2 GREEN — Actualizar `app/modules/libros/schemas.py` (`stock_inicial`, `LibroUpdate` reducido, `ReponerIn`, `extra="forbid"`) y el mapeo en `app/modules/libros/service.py::crear`.
- [x] 1.3 Ajustar los tests de servicio/DB y los `.http` que usaban el contrato viejo (`stock` en POST, PATCH de editorial/género).
- [x] 1.4 Verificar las validaciones: límites de `ReponerIn`, rechazo de extras y PATCH con stock → 422.

## 2. Cierre del change

- [x] 2.1 Correr las pruebas focalizadas de schemas y la suite disponible.
- [x] 2.2 Revisar el diff y confirmar que sólo incluye archivos de CHG-09b.
- [x] 2.3 Archivar el change y actualizar la fila de CHG-09b en `PLAN_PARCIAL.md`.
