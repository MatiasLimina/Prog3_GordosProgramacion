# Proposal

## Why

El metadata ya tiene los modelos del parcial (CHG-06 en `main`, CHG-07 en su rama), pero el esquema versionado sigue en la segunda migración del TP (`9df0eb6a1dd6`): `main` está en rojo (192 errores `relation "evento_seguridad" does not exist` en el `TRUNCATE` del conftest) y CHG-11, 13, 15 y 17 no pueden arrancar. El Ej2 (10 %) pide dos migraciones nuevas —la tercera autogenerada y leída, la cuarta escrita a mano— reversibles sobre una base vacía, y el Ej7 (10 %) pide que la base rechace cualquier `UPDATE` o `DELETE` sobre `movimiento_stock` (RN-12, caso C-14). Este change cierra el tren CHG-06 → CHG-07 → CHG-08 y devuelve la suite a verde. **Prioridad (Matias, 2026-11-05):** mergear CHG-07 y CHG-08 lo antes posible para que `main` vuelva a verde (está en rojo desde que CHG-06 entró solo).

## What Changes

- **Precondición de 0003 (resuelta 2026-11-05: Lauti autorizó a Nico a agregar los `server_default`; ya están en los modelos)**: confirmar con Lauti si la falta de `server_default` en sus modelos de CHG-06 (`intento_acceso.cuando`, `evento_seguridad.cuando`, `asignacion_rol.desde`, booleanos de `usuario`) es intencional; si cambian los modelos, se cambian en su archivo antes de generar 0003. Bloquea sólo la generación de 0003.
- **Migración 0003** (`migrations/versions/0003_*.py`, `--autogenerate`, `--rev-id 0003`, `down_revision = '9df0eb6a1dd6'`): crea `usuario`, `asignacion_rol` (CHECK de rol e índice único parcial `uq_asignacion_rol_usuario_rol_vigente`), `intento_acceso` (índice `(email, ip, cuando)`), `evento_seguridad` y `movimiento_stock`; agrega `cliente.usuario_id` (nullable, `uq_cliente_usuario_id`, `fk_cliente_usuario_id_usuario`) y `libro.borrado_en`.
  - **BREAKING (esquema)**: `libro` pierde la constraint `uq_libro_isbn` y gana el índice único parcial `uq_libro_isbn_vigente (isbn) WHERE borrado_en IS NULL`.
  - Comentario de cabecera que dice que se leyó antes de aplicarla; cada corrección manual con su comentario.
  - Sin datos: no crea usuarios ni movimientos «Stock inicial» para libros ya existentes (design D4).
- **Migración 0004** (`migrations/versions/0004_*.py`, a mano, `down_revision = '0003'`): función PL/pgSQL `movimiento_stock_solo_agregado()` y disparador `tg_movimiento_stock_solo_agregado` `BEFORE UPDATE OR DELETE ... FOR EACH ROW`, que rechaza con un mensaje propio en español que nombra la operación y el id de la fila, SQLSTATE `23001` (`restrict_violation`) y `CONSTRAINT = 'movimiento_stock_solo_agregado'` (para que `app/core/errors.py` pueda elegir el mensaje por nombre); `downgrade` borra el disparador y después la función. Su comentario dice que `TRUNCATE` **no** se bloquea a propósito porque lo usan el conftest y el seed.
- **Red de seguridad en `app/core/errors.py`** (commit aparte, archivo compartido que revisa Matias): `"23001"` en `_MENSAJES_POR_SQLSTATE` con un mensaje genérico en español, para que un rechazo del disparador sin clave en el `MENSAJES` del módulo no caiga en el mensaje genérico de conflicto.
- **`test/solo_agregado.sql`** (C-14): script de psql que muestra un movimiento, intenta un `UPDATE` y un `DELETE` (los dos rechazados por el disparador) y muestra que la fila no cambió.
- **`app/modules/libros/service.py`**: se quita la clave vieja `uq_libro_isbn` de `MENSAJES` (queda `uq_libro_isbn_vigente`), como dejó acordado CHG-07 (D4 y «Migration Plan» punto 5).
- **Tests** (pytest, marca `db`):
  - Reversibilidad sobre una base **vacía y descartable** (`libreria_migraciones`): `upgrade head`, `downgrade base`, `upgrade head`; y 0003 aplicada sobre una base con filas del TP.
  - El esquema migrado coincide con el metadata (`alembic check` sin diferencias).
  - Los escenarios de base real que CHG-06/07 dejaron para acá (índices parciales, CHECK, FK sin `ON DELETE`, `cuando` por defecto, reutilizar ISBN).
  - El disparador: `INSERT` permitido; `UPDATE` y `DELETE` rechazados (también desde el ORM y dentro de un UoW, con `constraint_name` = `movimiento_stock_solo_agregado`); `TRUNCATE` sigue funcionando (lo usan el conftest y el seed).
  - Ninguna FK que apunta a `movimiento_stock` tiene `ON DELETE CASCADE` y las FK propias de `movimiento_stock` no tienen `ON DELETE CASCADE` ni `SET NULL` (chocarían con el disparador): test sobre el metadata y chequeo en la base migrada.
- **`PLAN_PARCIAL.md`**: Nico marca el estado de CHG-08 en la tabla de seguimiento (sólo esa línea).

**Fuera de alcance**: el punto único de escritura de stock, `stock_inicial` y la reposición (CHG-13); el seed nuevo con usuarios y movimientos (CHG-17); la captura de psql en `evidencia/` (CHG-20); el segundo mecanismo de la sección 6.9 (permisos del rol de base), que la consigna no pide; agregar la clave `movimiento_stock_solo_agregado` a los `MENSAJES` de los UoW de módulo (CHG-13/16); cambios en `migrations/env.py` o `AGENTS.md` (la fila de stock/ISBN de «Transición» se cierra con CHG-13).

## Capabilities

### New Capabilities

- `migraciones-esquema`: cómo evoluciona y se verifica el esquema versionado con Alembic: cadena de revisiones, reversibilidad sobre una base vacía, aplicación sobre una base con datos del TP y coincidencia entre el esquema migrado y los modelos.

### Modified Capabilities

- `movimientos-stock` (capability que introduce CHG-07, todavía sin archivar): se agrega el requisito de sólo agregado garantizado por la base (disparador de la cuarta migración) y su demostración C-14. Se escribe como `ADDED` sobre la spec de CHG-07; por eso CHG-07 se archiva antes que este change.

## Impact

- **Archivos nuevos**: `migrations/versions/0003_*.py`, `migrations/versions/0004_*.py`, `test/solo_agregado.sql`, `tests/test_migraciones_db.py`, `tests/test_esquema_db.py`, `tests/test_solo_agregado_db.py`.
- **Archivos modificados**: `app/modules/libros/service.py` (una clave de `MENSAJES`) y su test `tests/test_catalogo_service.py`; `tests/test_movimiento_stock_models.py` (test de las acciones referenciales); `app/core/errors.py` y `tests/test_errors.py` (red de seguridad `23001`, commit aparte); `PLAN_PARCIAL.md` (línea de estado de CHG-08).
- **Base**: `libreria_test` pasa a `0004` en cada corrida (conftest, sin cambios); la base de desarrollo `libreria` se migra a mano y queda con `libro.stock` sin movimientos hasta el seed de CHG-17. Un `downgrade` de 0003 falla si hay ISBN repetidos entre libros dados de baja (aceptable fuera de producción; queda en el comentario).
- **Consumidores**: CHG-11 (`usuario`, `asignacion_rol`, `intento_acceso`), CHG-13/16 (`movimiento_stock`, `borrado_en`; agregan `movimiento_stock_solo_agregado` a sus `MENSAJES`), CHG-14 (`evento_seguridad`), CHG-17 (el seed tiene que vaciar con `TRUNCATE`, no con `DELETE`), CHG-18/20 (C-14).
- **Gobernanza**: HIGH (esquema y datos): cada migración se revisa antes de aplicarse y el diff final pasa por el advisor. `app/core/errors.py` es compartido: su commit lo revisa Matias.
