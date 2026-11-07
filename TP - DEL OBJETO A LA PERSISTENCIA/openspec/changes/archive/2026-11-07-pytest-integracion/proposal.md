# Proposal

## Why

CHG-19 cierra la red de pruebas de integración del parcial: stock igual a la suma de movimientos después de cada venta, atomicidad de RN-02 y RN-10, y conteo de consultas de C-15. La auditoría de la suite (ver design.md, «Auditoría de cobertura») muestra que RN-10 y C-15 ya están cubiertos a fondo por CHG-16, pero quedan dos huecos reales: la atomicidad de RN-02 sólo se prueba por el camino del `IntegrityError` (nunca con una falla que no venga de la base a mitad del bloque), y el invariante de stock nunca se verifica **sobre los datos del seed y después de cada caso** de venta y de stock (C-10, C-11, C-12, C-13), que es lo que piden el escenario C-11 de la spec de ventas y el punto 5 de la definición de terminado (AGENTS.md §11). La reposición y la baja (C-13) se prueban por separado en `tests/test_libros_stock_db.py`, pero el invariante sólo se mira tras las altas.

## What Changes

- Tests de integración de la atomicidad de RN-02 con fallas inyectadas en cada punto del bloque del auto-registro (después del usuario, después de la asignación y después de las tres escrituras, antes del commit): ninguna de las tres filas queda y el mismo correo se puede registrar después.
- Se completa el test existente del correo de cliente que ya tiene usuario: además de no crear usuarios, MUST NOT dejar asignación y MUST NOT tocar la ficha existente.
- Test de recorrido sobre el seed: carga `seed.py` y ejecuta en orden por HTTP los casos de venta C-10, C-11 y C-12 (cliente inexistente, libro inexistente, libro dado de baja) y los pasos de C-13 (reponer un libro, darlo de baja, reponerlo dado de baja → 409, volver a cargar su ISBN → 201, un segundo vigente con ese ISBN → 409, la venta vieja sigue mostrando el título). Después de **cada** paso comprueba en todos los libros (los cinco del seed y el realtado) que `stock` = suma de `cantidad` de sus movimientos, además de las escrituras esperadas (o su ausencia); la reposición deja exactamente un movimiento nuevo.
- Se explicita en la spec `registro-de-clientes` lo que hoy sólo está implícito: una falla en cualquier punto del bloque revierte las tres filas.
- Sin código de producción nuevo ni modificado. Sin cambios de comportamiento observable.
- Cierre del change según AGENTS.md §10: fila de CHG-19 en `PLAN_PARCIAL.md` en `mergeado (#N)`, sección CHG-19 del plan actualizada y el change archivado en la misma rama.

Fuera de alcance (listado como opcional en design.md): registros concurrentes con el mismo correo, nuevos tests de RN-16 (ya cubiertos con fallas inyectadas en `tests/test_usuarios_admin_db.py` y `tests/test_auth_cambiar_password_db.py`), más tests de C-15 (ya cubierto a nivel HTTP y repositorio).

## Capabilities

### New Capabilities
<!-- Ninguna: el change sólo verifica comportamiento existente. -->

### Modified Capabilities
- `registro-de-clientes`: el requisito «Registro atómico» suma escenarios que hacen explícito que una falla en cualquier punto del bloque (incluida una que no viene de la base) no deja ninguna de las tres filas. El comportamiento ya existe; cambia el criterio de aceptación escrito.

## Impact

- `tests/test_auth_registro_db.py`: nueva sección de atomicidad con fallas inyectadas y un test existente reforzado.
- `tests/test_integracion_recorrido_db.py` (nuevo): recorrido C-10 → C-11 → C-12 → C-13 sobre el seed con el invariante de stock tras cada paso.
- Los escenarios de C-13 ya están en las specs principales (`catalogo-libros`, `movimientos-stock`, `ventas`): no llevan delta.
- `openspec/specs/registro-de-clientes/spec.md` (al archivar).
- `PLAN_PARCIAL.md` (tabla de seguimiento y sección CHG-19).
- Sin cambios en `app/`, migraciones, dependencias ni `seed.py`. Requiere PostgreSQL de test levantado (marca `db`).
