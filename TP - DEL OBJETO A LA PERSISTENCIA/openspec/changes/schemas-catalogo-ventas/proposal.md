# Proposal

## Why

CHG-13 necesita los contratos de catálogo y ventas para migrar esos módulos a repositorios y Unit of Work. Hoy `LibroCreate` usa `stock` (la consigna exige `stock_inicial`), `LibroUpdate` admite campos que la consigna prohíbe editar (isbn, editorial, género y sobre todo `stock`, RN-11) y ningún contrato de entrada del catálogo rechaza campos extra. Sin corregir la frontera, un `PATCH` con `stock` se aplicaría en silencio y el stock se escribiría por fuera del punto único de movimientos.

## What Changes

- `LibroCreate` viaja `stock_inicial` en lugar de `stock`, y conserva `autores`.
- `LibroUpdate` queda sólo con `titulo` y `precio`, ambos opcionales; el stock y el resto de los campos ya no son editables por `PATCH` (RN-11).
- Nuevo contrato `ReponerIn` para el cuerpo de `POST /libros/{id}/reponer` (cantidad positiva y motivo opcional).
- `extra="forbid"` en los contratos de entrada que toca este change: `LibroCreate`, `LibroUpdate`, `LibroAutorCreate` y `ReponerIn`. Clientes y ventas ya lo cumplen.
- `VentaCreate` ya no declara precio, total ni fecha (verificado; sin cambios).

Fuera de alcance: endpoints nuevos (`/reponer`, `/movimientos`, `DELETE /libros/{id}`), repositorios, UoW, el punto único de escritura de stock (CHG-13), borrado lógico (CHG-07/08 ya mergeados), y los contratos de editoriales, géneros y autores, que no son parte de este change.

## Capabilities

### New Capabilities
- `contratos-catalogo-ventas`: contratos y validaciones de las entradas y salidas de libros, reposición y ventas.

### Modified Capabilities
- Ninguna.

## Impact

- Código: `app/modules/libros/schemas.py` y el mapeo `stock_inicial` → `stock` en `app/modules/libros/service.py::crear` (transitorio hasta CHG-13).
- Tests: `tests/test_catalogo_schemas.py`, `tests/test_catalogo_service.py`, `tests/test_libros_crud_db.py`, `tests/test_libros_validaciones.py` y los cuerpos de `test/libros.http` y `test/editoriales_generos.http`.
- No agrega dependencias ni modifica otros changes.
