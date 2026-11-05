# Design

## Context

Ver `proposal.md` (Why). Estado observado en `feat/migraciones-3-4` (cortada de `feat/modelos-libro-cliente-stock` en 12796c0, con `main` mergeado: CHG-03/04/06/09a/10):

- `migrations/versions/` tiene dos revisiones con id hash: `5600df0fc99c` (catálogo, clientes y ventas sin género) → `9df0eb6a1dd6` (género), que es `head`. Estilo: docstring con el porqué, `import sqlmodel  # noqa: F401` (lo pone `script.py.mako`), bloque autogenerado sin tocar. `alembic.ini` usa el `file_template` por defecto (`%(rev)s_%(slug)s`) y no tiene URL; `migrations/env.py` importa `app.models` (que importa primero `app.core.base`) y usa `compare_type=True`. Este change no toca `env.py` ni `alembic.ini`.
- `libreria` (desarrollo) y `libreria_test` están en `9df0eb6a1dd6`. La base corre en el puerto **5433** del host (el 5432 lo ocupa otro Postgres) y `.env` todavía dice 5432: todo comando con base se corre con `POSTGRES_PORT=5433` en el entorno. Los agentes no editan `.env`.
- `tests/conftest.py`: una vez por corrida hace `DROP SCHEMA public CASCADE` en `libreria_test` y `alembic upgrade head` en un subproceso (con `POSTGRES_DB=libreria_test`); cada test hace `TRUNCATE` de todas las tablas de `SQLModel.metadata.sorted_tables` con `RESTART IDENTITY CASCADE`. `scripts/seed.py` vacía igual (`TRUNCATE`). Ninguno usa `DELETE`.
- **Dry-run de autogenerate** (2026-11-05, Alembic 1.20 / SQLAlchemy 2.1 locales, con `produce_migrations` + `render_python_code` desde un script en el scratchpad contra `libreria_test`, sin escribir archivos en `migrations/versions/`). El `upgrade` que emite hoy:
  1. `create_table` de `evento_seguridad`, `intento_acceso` (+ `ix_intento_acceso_email_ip_cuando`), `usuario` (`uq_usuario_email`), `asignacion_rol` (`ck_asignacion_rol_rol_valido`, dos FK a `usuario`, `ix_asignacion_rol_usuario_id`, `ix_asignacion_rol_otorgada_por` y `uq_asignacion_rol_usuario_rol_vigente` **con** `postgresql_where`), `movimiento_stock` (`ck_movimiento_stock_cantidad_no_cero`, tres FK sin `ondelete`, `server_default=sa.text('now()')` en `cuando`, tres `ix_movimiento_stock_*`), en ese orden (padres antes que hijos).
  2. `cliente`: `add_column usuario_id` nullable, `create_unique_constraint uq_cliente_usuario_id`, `create_foreign_key fk_cliente_usuario_id_usuario` (sin `ix_` extra).
  3. `libro`: `add_column borrado_en` timestamptz nullable, **`drop_constraint uq_libro_isbn` antes de** `create_index uq_libro_isbn_vigente ... postgresql_where=sa.text('borrado_en IS NULL')`.
  4. El `downgrade` es el espejo en orden inverso; para `uq_libro_isbn` emite `create_unique_constraint(..., postgresql_nulls_not_distinct=False)`.

  Es decir: el gotcha #5 del plan (UNIQUE → índice parcial) **no** se reproduce con estas versiones, pero la lectura línea por línea sigue siendo obligatoria (Ej2) y se repite al generar de verdad (D2).
- `app/modules/libros/service.py` todavía tiene en `MENSAJES` las claves `uq_libro_isbn` y `uq_libro_isbn_vigente` (CHG-07 dejó la vieja para que esta rama la quite al aplicar 0003).
- `app/core/errors.py`: `mensaje_para(error, mensajes, default)` busca `constraint_name` primero en `error.orig` y después en `error.orig.__cause__` (con asyncpg, el adaptador de SQLAlchemy copia `sqlstate` pero no `constraint_name`, que vive en la excepción original). Si el nombre está en el dict del módulo, usa ese mensaje; si no, el `default`; si no, `_MENSAJES_POR_SQLSTATE[sqlstate]`, que hoy sólo tiene `23505`, `23503` y `23514`; si no, `_MENSAJE_GENERICO`. El UoW base (`app/core/unit_of_work.py`) llama a `mensaje_para` con el `MENSAJES` de la clase y lanza `Conflicto`. Consecuencia: un `RAISE` sin `CONSTRAINT` y sin `23001` en ese dict termina en el mensaje genérico.
- Modelos de CHG-06 sin `server_default` en `intento_acceso.cuando`, `evento_seguridad.cuando`, `asignacion_rol.desde` y los booleanos de `usuario` (`activo`, `debe_cambiar_password`): sólo `default` de Python. **Resuelto (2026-11-05):** Lauti autorizó a Nico a agregar los `server_default` (`now()` en los tres `cuando`/`desde`, `true`/`false` en los booleanos); ya están en `app/modules/usuarios/models.py` y 0003 los incluye.
- Ningún modelo declara `ondelete`; ninguna FK apunta hoy a `movimiento_stock`.
- La consigna no fija el texto del rechazo de C-14 ni el SQLSTATE: pide que el disparador «rechace cualquier UPDATE o DELETE ... venga de donde venga» (Ej7) y que C-14 muestre «los dos, rechazados por el disparador».

## Goals / Non-Goals

**Goals:**
- 0003 tan cerca de lo autogenerado como se pueda: cada línea que se cambie, con su comentario.
- Probar con pytest, sin intervención manual, la reversibilidad completa sobre una base vacía y que esquema y modelos coinciden.
- Que el conftest y el seed sigan funcionando sin cambios con el disparador instalado.

**Non-Goals:**
- Cambiar `migrations/env.py` (p. ej. `include_object` para ignorar disparadores): autogenerate no los compara, así que no hace falta.
- Datos en migraciones (usuarios, movimientos, roles): son del seed (CHG-17).
- Proteger `movimiento_stock` contra `TRUNCATE` o con permisos del rol de base (sección 6.9, segundo mecanismo): no se pide y rompería el vaciado del seed y del conftest.

## Decisions

### D1 · Ids de revisión legibles: `0003` y `0004`
Se generan con `--rev-id 0003` y `--rev-id 0004`: archivos `0003_acceso_y_stock.py` y `0004_solo_agregado_movimiento_stock.py`, `revision = '0003'` / `'0004'`, `down_revision = '9df0eb6a1dd6'` / `'0003'`. Coinciden con cómo los nombran la consigna («tercera», «cuarta») y el plan («0003», «0004»), se ordenan bien en el listado y son fáciles de citar en el README y en los comentarios.
- *Alternativa*: dejar ids hash como las dos del TP. Más homogéneo, pero obliga a buscar qué hash es «la 0003». Alembic ordena por la cadena `down_revision`, no por el nombre, así que mezclar estilos no tiene efecto técnico; las dos del TP no se renombran (cambiaría `alembic_version` de bases ya migradas).

### D2 · 0003: autogenerate de verdad y lectura con lista de control
Se genera contra una base en `9df0eb6a1dd6` (`libreria_test` recién migrada) con `POSTGRES_PORT=5433 POSTGRES_DB=libreria_test python -m alembic revision --autogenerate --rev-id 0003 -m "acceso y stock"`. Antes de aplicarla se lee y se compara contra esta lista (la del dry-run): cinco tablas nuevas en orden de dependencias; los dos índices parciales con `postgresql_where`; `drop_constraint('uq_libro_isbn')` antes del `create_index('uq_libro_isbn_vigente')` y después del `add_column('borrado_en')`; todos los nombres por convención (`pk_`, `uq_`, `fk_`, `ck_`, `ix_`); un `ix_` por FK salvo `cliente.usuario_id` (lo cubre su UNIQUE); `cuando` de movimiento con `server_default now()`; ninguna columna `NOT NULL` agregada a `cliente` o `libro`; ningún `ondelete`. Si algo no coincide, se corrige a mano con comentario.
Correcciones manuales previstas (cada una con su comentario):
- Docstring con «Leída línea por línea antes de aplicarla (fecha, quién)» y el resumen de qué crea.
- En el `downgrade`, comentario sobre `create_unique_constraint('uq_libro_isbn')`: falla si hay ISBN repetidos entre filas dadas de baja; aceptable en bases de desarrollo y de test.
- Quitar `postgresql_nulls_not_distinct=False` del `downgrade`: es el valor por defecto y lo emite una versión de Alembic más nueva que la mínima del proyecto (1.13); quitarlo deja la migración igual en cualquier versión.
- *Alternativa*: escribir 0003 a mano. La consigna pide expresamente `--autogenerate`.

### D3 · 0004: disparador por fila, mensaje propio y SQLSTATE 23001
Escrita a mano con `op.execute`: `CREATE FUNCTION movimiento_stock_solo_agregado() RETURNS trigger LANGUAGE plpgsql` que hace `RAISE EXCEPTION 'movimiento_stock es de sólo agregado: no se permite % sobre el movimiento %. Los errores se corrigen con un movimiento que compense.', TG_OP, OLD.id USING ERRCODE = 'restrict_violation', CONSTRAINT = 'movimiento_stock_solo_agregado', TABLE = 'movimiento_stock'`; y `CREATE TRIGGER tg_movimiento_stock_solo_agregado BEFORE UPDATE OR DELETE ON movimiento_stock FOR EACH ROW EXECUTE FUNCTION movimiento_stock_solo_agregado()`. `downgrade`: `DROP TRIGGER tg_movimiento_stock_solo_agregado ON movimiento_stock` y después `DROP FUNCTION movimiento_stock_solo_agregado()`. Sin `IF EXISTS` ni `OR REPLACE`: si la base no está en el estado esperado, la migración tiene que fallar, no taparlo.
- **SQLSTATE `23001`** (clase 23, violación de integridad): asyncpg lo levanta como `IntegrityConstraintViolationError` y SQLAlchemy como `IntegrityError`, así que si algún código de la app lo dispara, el UoW lo convierte en `Conflicto` → 409 y nunca en 500 (RN-15). Con el `P0001` por defecto de `RAISE` saldría como `InternalError` → 500. Verificado en el dialecto asyncpg de SQLAlchemy 2.1. Confirmado por Matias.
- **`CONSTRAINT = 'movimiento_stock_solo_agregado'`** (confirmado por Matias): llena el campo de nombre de constraint del error, que asyncpg expone como `constraint_name`; así `mensaje_para` puede elegir el mensaje por nombre como con cualquier UNIQUE o FK. Sin él, el 409 cae en el mensaje genérico. Agregar esa clave a los `MENSAJES` de los UoW de módulo es de CHG-13/16; este change sólo prueba que el nombre llega (`IntegrityError` con ese `constraint_name`, `Conflicto` desde el UoW base y `mensaje_para` con un dict que lo contiene).
- **Mensaje con el id de la fila** (`OLD.id`; con `FOR EACH ROW`, `OLD` existe tanto en `UPDATE` como en `DELETE`): confirmado por Matias. Él revisa la sección 6.9 del libro; si trae otra forma se adapta, si no queda ésta (riesgo bajo, no bloquea).
- **`FOR EACH ROW`** (confirmado por Matias): el disparador corre por cada fila afectada y puede nombrar la operación (`TG_OP`) y la fila (`OLD.id`). C-14 apunta a una fila existente, así que alcanza.
  - *Alternativa*: `FOR EACH STATEMENT`, que rechaza incluso un `UPDATE` que no toca filas. Más estricto, pero un `UPDATE ... WHERE id = -1` que «falla» no demuestra nada y se pierde la posibilidad de mirar la fila; descartada.
- **`TRUNCATE` no se protege**: la consigna pide `UPDATE OR DELETE`; el conftest y el seed vacían con `TRUNCATE` y un disparador por fila no se ejecuta con `TRUNCATE`. Consecuencia para CHG-17: el seed nuevo tiene que seguir vaciando con `TRUNCATE` (con `DELETE FROM movimiento_stock` fallaría). El docstring de 0004 **debe** decir que `TRUNCATE` no se bloquea a propósito porque lo usan el conftest y el seed.
- Autogenerate no inspecciona funciones ni disparadores: un `revision --autogenerate` futuro no va a intentar borrarlos. Se deja dicho en el docstring de 0004.

### D4 · Sin backfill de «Stock inicial» en 0003
0003 no inserta movimientos para los libros que ya existan. Motivos: (1) `movimiento_stock.usuario_id` es `NOT NULL` y al aplicar 0003 no hay ningún usuario: habría que inventar uno (con hash de contraseña) dentro de una migración, que es de esquema; (2) el DoD es sobre una base vacía, donde no hay nada que reconstruir; (3) el seed de CHG-17 trunca todo y carga los movimientos «Stock inicial» con el usuario que corresponda, y la consigna exige `python seed.py` antes de cada caso. Costo: una base de desarrollo migrada en su lugar queda con `stock` ≠ suma de movimientos hasta volver a sembrar; se documenta en el docstring de 0003 y en tasks.
- *Alternativa*: un usuario técnico `SISTEMA` creado por la migración y un movimiento por libro con `stock <> 0`. Rechazada por (1) y porque obligaría a decidir en una migración la contraseña de una cuenta.

### D5 · Tests: base descartable para la reversibilidad y `libreria_test` para lo demás
- `tests/test_migraciones_db.py` (marca `db`): usa una base propia `libreria_migraciones` que el test crea (`CREATE DATABASE` desde una conexión a la base `postgres`, con `assert` del nombre antes de cualquier `DROP DATABASE`) y borra al final. Corre Alembic en subproceso con `POSTGRES_DB=libreria_migraciones`, igual que el conftest. Casos: `upgrade head` → inventario de tablas, función y disparador; `downgrade base` → sólo `alembic_version` y nada del disparador; `upgrade head` otra vez → mismo inventario; `downgrade 0003` / `upgrade head` con un movimiento (el `UPDATE` pasa en 0003 y falla en `head`); y una ida `9df0eb6a1dd6` con filas del TP → `head`. Sin base, se saltea o falla con `REQUIRE_TEST_DB=1`, con la misma regla del conftest (helper local; el conftest no cambia).
  - *Alternativa*: hacer la ida y vuelta sobre `libreria_test`. Rompería el esquema que el fixture de sesión dejó para el resto de la corrida.
- `tests/test_esquema_db.py` (marca `db`, sobre `libreria_test` ya en `head` vía `esquema_test`): `alembic check` en subproceso termina con código 0; y los escenarios de base real que CHG-06/07 difirieron (spec `migraciones-esquema`, «Restricciones de la base migrada» y «Unicidad de ISBN»), con SQL directo y `sessionmaker_test`.
- `tests/test_solo_agregado_db.py` (marca `db`): `INSERT` permitido; `UPDATE` y `DELETE` rechazados con `IntegrityError` de SQLSTATE `23001`, `constraint_name` = `movimiento_stock_solo_agregado` (leído con el mismo `_buscar_atributo` que usa `mensaje_para`) y la fila igual; el mensaje menciona «sólo agregado», la operación y el id; lo mismo desde el ORM (`session.delete` y cambio de atributo + `commit`); dentro del UoW base, un cambio de atributo termina en `Conflicto` (nunca otra excepción) y `mensaje_para(e, {"movimiento_stock_solo_agregado": ...})` elige ese mensaje; y `TRUNCATE` con movimientos funciona.
- `test/solo_agregado.sql` no se ejecuta desde pytest (psql no es dependencia del proyecto); se verifica a mano en la tarea correspondiente y su evidencia es de CHG-20.

### D6 · `test/solo_agregado.sql`
Sin `BEGIN` explícito: cada sentencia en su propia transacción, así el segundo intento muestra el error del disparador y no «current transaction is aborted». `\set VERBOSITY verbose` para que psql muestre el SQLSTATE y el contexto PL/pgSQL. Elige el movimiento con `(SELECT min(id) FROM movimiento_stock)`. Estructura: comentario de cabecera (caso, cómo correrlo con `docker compose exec -T postgres psql ... -f -` o `psql -f`, precondición `python seed.py`), `SELECT` del movimiento, `UPDATE ... SET cantidad = cantidad + 1` con `-- Esperado: ERROR: 23001 ... no se permite UPDATE`, `DELETE` con `-- Esperado: ERROR: 23001 ... no se permite DELETE`, `SELECT` final igual al primero.

### D7 · Commits y orden dentro del change
Cuatro commits, en este orden (decidido por el orquestador):
1. `feat(migrations): 0003 acceso y stock (autogenerada, revisada)`: `migrations/versions/0003_acceso_y_stock.py`, `app/modules/usuarios/models.py` + `tests/test_usuarios_models.py` (los `server_default` que contiene 0003), `app/modules/libros/service.py` + `tests/test_catalogo_service.py` (`MENSAJES`), `tests/test_esquema_db.py`, `tests/test_movimiento_stock_models.py` (D9).
2. `feat(core): mensaje para restrict_violation (23001)`: `app/core/errors.py` y `tests/test_errors.py` (D8; lo revisa Matias). Va **antes** de 0004 para que los tests de 0004 afirmen de punta a punta el mensaje de respaldo de `23001`.
3. `feat(migrations): 0004 disparador de sólo agregado`: 0004, `test/solo_agregado.sql`, `tests/test_solo_agregado_db.py` y `tests/test_migraciones_db.py` (el archivo entero: espera 0004, así que la reversibilidad de 0003 queda probada desde este commit).
4. `docs(plan): CHG-08 en PR y change migraciones-3-4`: `PLAN_PARCIAL.md` (línea de estado de CHG-08) y la carpeta `openspec/changes/migraciones-3-4/`.

Cada commit deja `REQUIRE_TEST_DB=1 pytest` verde.

### D8 · Red de seguridad: `23001` en `_MENSAJES_POR_SQLSTATE`
Aprobada por Matias como opcional. Se agrega `"23001"` a `_MENSAJES_POR_SQLSTATE` con un mensaje genérico en español que no nombra la tabla ni el disparador (p. ej. «El registro no se puede modificar ni borrar.»): `23001` también lo usa una FK con `ON DELETE RESTRICT`, así que el texto tiene que servir para los dos. Con la clave propia de D3 en el `MENSAJES` de un módulo, ese mensaje gana; sin ella, éste evita el mensaje genérico de conflicto. Commit aparte porque `errors.py` es compartido; va antes del de 0004 (ver D7). TDD: un caso más en el `parametrize` de `test_default_segun_sqlstate` de `tests/test_errors.py` (RED: hoy da el genérico).

### D9 · Acciones referenciales compatibles con el disparador
Ninguna FK que apunte a `movimiento_stock.id` puede tener `ON DELETE CASCADE` (borrar el padre haría un `DELETE` en `movimiento_stock` que el disparador rechaza), y las FK propias de `movimiento_stock` (`libro_id`, `venta_id`, `usuario_id`) no pueden tener `ON DELETE CASCADE` (borraría movimientos) ni `SET NULL` (haría un `UPDATE` que el disparador rechaza). Hoy no hay ninguna; se fija con dos chequeos:
- Test sin base en `tests/test_movimiento_stock_models.py`: una función recorre un `MetaData` y devuelve las FK incompatibles; se triangula con un `MetaData` armado en el test que tiene una FK `CASCADE` hacia `movimiento_stock` y otra `SET NULL` desde ella (la función las detecta) y se afirma que sobre `SQLModel.metadata` devuelve vacío. Es un test de guarda: su parte sobre el metadata real pasa desde el principio; la triangulación prueba que muerde.
- En `tests/test_esquema_db.py`, `pg_constraint.confdeltype` = `'a'` (NO ACTION) para toda FK de o hacia `movimiento_stock` en la base migrada.

## Risks / Trade-offs

- [Alembic local 1.20 vs mínimo 1.13: el código generado puede traer argumentos que la versión mínima no conoce] → D2 quita `postgresql_nulls_not_distinct`; el resto del bloque usa sólo `op.*` de 1.13. Se anota en el comentario.
- [Autogenerate con otra base de origen emite otra cosa] → se genera contra `libreria_test` recién migrada a `9df0eb6a1dd6`, nunca contra `libreria` (que puede tener cambios hechos a mano), y se compara contra la lista de D2.
- [El usuario de la base no puede crear bases y `test_migraciones_db.py` no corre] → el usuario del contenedor es superusuario; si no lo fuera, el test lo reporta como fallo con `REQUIRE_TEST_DB=1` y skip sin él (nunca un falso verde).
- [Una base de desarrollo con datos queda con `stock` sin movimientos (D4)] → docstring de 0003 y task de re-sembrar; el invariante se exige recién con el seed de CHG-17.
- [Un `DELETE` de un libro con movimientos, hoy sólo posible por SQL] → lo rechaza la FK (`23503`), no el disparador; está cubierto por un escenario.
- [Downgrade de 0003 con ISBN repetidos entre libros dados de baja] → falla al recrear `uq_libro_isbn`; se acepta y se documenta (no hay producción).
- [El rechazo por ORM deja la sesión en estado de error] → los tests usan una sesión nueva después del rechazo; en la app lo maneja el UoW (rollback y `Conflicto`).
- [La sección 6.9 del libro usa otro texto u otra forma del disparador] → Matias la revisa; cambiar el texto es una línea de 0004 y no rompe los tests (buscan «sólo agregado», la operación, el SQLSTATE y el nombre de constraint). Riesgo bajo, no bloquea.
- [Lauti cambia los `server_default` de CHG-06 después de generar 0003] → la tarea 1.3 es precondición de 3.1; si la respuesta llegara tarde, se regenera 0003 (todavía no está en `main`).
- [Un `23001` de otra fuente (FK `RESTRICT`) recibe el mensaje de D8] → por eso es genérico y no menciona movimientos.

## Migration Plan

1. Precondición: Postgres arriba en 5433; `POSTGRES_PORT=5433` en el entorno de cada comando; `libreria_test` en `9df0eb6a1dd6`; respuesta de Lauti sobre los `server_default` (sólo para generar 0003).
2. Generar 0003 (D2), leerla con la lista, corregir con comentarios, aplicar en `libreria_test` vía pytest.
3. Escribir 0004 (D3), aplicar vía pytest. Después, la red de seguridad de D8 en su propio commit.
4. Base de desarrollo `libreria` (con confirmación de Nico, gobernanza HIGH): `alembic upgrade head`, después `python -m scripts.seed` (hasta CHG-17). Rollback: `alembic downgrade 9df0eb6a1dd6` (borra las tablas nuevas y sus datos).
5. Gate del tren: `REQUIRE_TEST_DB=1 python -m pytest -q` verde en la punta de esta rama; después se mergean CHG-07 y CHG-08 a `main` con merge commit (CHG-06 ya entró solo), lo antes posible: `main` está en rojo hasta entonces.
6. Orden de archivo: CHG-07 antes que CHG-08 (la delta de `movimientos-stock` se agrega a la spec que crea CHG-07).

## Decisiones confirmadas (Matias, 2026-11-05)

- Prioridad: mergear CHG-07 y CHG-08 cuanto antes para devolver `main` a verde.
- SQLSTATE `23001` (`restrict_violation`) y `CONSTRAINT = 'movimiento_stock_solo_agregado'` en el `USING` del `RAISE` (D3). La clave en los `MENSAJES` de módulo es de CHG-13/16.
- Red de seguridad `23001` en `_MENSAJES_POR_SQLSTATE`, en commit aparte antes del de 0004 (D7, D8).
- Disparador `BEFORE UPDATE OR DELETE ... FOR EACH ROW`; mensaje con la operación y el id de la fila (D3). Matias revisa la sección 6.9; si trae otra forma se adapta.
- El comentario de 0004 dice que `TRUNCATE` no se bloquea a propósito (conftest y seed).
- Ninguna FK hacia `movimiento_stock` con `ON DELETE CASCADE` ni FK propia con `CASCADE`/`SET NULL`, verificado por test (D9).
- Nico marca CHG-08 en `PLAN_PARCIAL.md` (sólo la línea de estado); la fila de stock/ISBN de «Transición» en `AGENTS.md` no se toca (cierra con CHG-13).
- Ids `0003` / `0004` con `--rev-id`; las dos del TP conservan sus hashes (D1).

## Open Questions

- ~~**Lauti**: ¿la falta de `server_default` en `intento_acceso.cuando`, `evento_seguridad.cuando`, `asignacion_rol.desde` y los booleanos de `usuario` es intencional? Bloquea sólo la generación de 0003; si cambian los modelos, se cambian en su archivo antes.~~ Resuelto: Lauti autorizó a Nico a agregarlos (2026-11-05).
- **Nico**: OK para migrar y re-sembrar la base de desarrollo `libreria` (tasks 10.1) y revisión de cada migración antes de aplicarla (tasks 3.2 y 7.1).
