# Design

## Context

Ver `proposal.md` (Why). Estado observado en la rama `feat/modelos-libro-cliente-stock` (cortada de `main` en 054cf91; CHG-03 está en el PR #33 y **no** está en esta rama, así que este change no usa `Settings`):

- `Libro.isbn` es `Field(max_length=30, unique=True)` → constraint `uq_libro_isbn`. `MENSAJES` de `app/modules/libros/service.py` usa esa clave para el 409 «Ya existe un libro con ese ISBN.».
- Tests que fijan la estructura actual: `tests/test_catalogo_models.py` (`uq_libro_isbn` en las líneas 54 y 92), `tests/test_clientes_ventas_models.py::test_tabla_y_columnas` (columnas **exactas** de `cliente` = `{id, nombre, email}` y todas no nulas), `tests/test_catalogo_service.py::test_mensajes_de_integridad_en_libros` (claves de `MENSAJES`). `tests/test_errors.py` y `tests/test_health.py` usan `uq_libro_isbn` sólo como nombre ficticio: no cambian.
- `app/core/base.py` fija la naming convention; `ix` es `ix_%(column_0_label)s`, `uq` `uq_%(table_name)s_%(column_0_name)s`, `fk` usa `%(referred_table_name)s`.
- `tests/conftest.py`: el esquema de `libreria_test` se crea con `alembic upgrade head` y cada test hace `TRUNCATE` de **todas** las tablas de `SQLModel.metadata.sorted_tables`. `scripts/seed.py` y `migrations/env.py` también importan `app.models` completo.
- No existe `app/modules/usuarios/` (CHG-06, de Lauti, sin empezar). No hay CI en `.github/`: «verde» es una disciplina local.

Comprobado con un script descartable (SQLModel 0.0.24 / SQLAlchemy 2, sin tocar el proyecto):

1. Un `Index("uq_libro_isbn_vigente", "isbn", unique=True, postgresql_where=text("borrado_en IS NULL"))` conserva su nombre explícito bajo la convención y compila a `CREATE UNIQUE INDEX uq_libro_isbn_vigente ON libro (isbn) WHERE borrado_en IS NULL`.
2. Una FK declarada por texto (`foreign_key="usuario.id"`) sin la tabla `usuario` en el metadata produce los nombres correctos (`fk_cliente_usuario_id_usuario`, `fk_movimiento_stock_usuario_id_usuario`) y `configure_mappers()` pasa **si no hay `Relationship` hacia `Usuario`**.
3. En ese mismo estado, `SQLModel.metadata.sorted_tables` lanza `NoReferencedTableError` (no encuentra `usuario`). Eso rompe el fixture `sessionmaker_test` (el `TRUNCATE`), el seed y `alembic revision --autogenerate`.
4. `cuando` con `server_default=func.now()`, `nullable=False` y valor Python `None` se omite del INSERT (la base lo completa).

## Goals / Non-Goals

**Goals:**
- Dejar el metadata exactamente como lo necesita la migración 0003 de CHG-08 (Figura 1 y págs. 5–6), con nombres de constraints e índices estables para el diccionario de 409.
- Avanzar ya, sin esperar a CHG-06, en todo lo que no depende de `Usuario`, sin dejar nunca la configuración de mappers rota.
- Fijar por escrito el contrato mínimo con CHG-06 y el orden de merge que mantiene `main` verde.

**Non-Goals:**
- Comportamiento de la API (filtrar vigentes, baja con 204, reposición, `stock_inicial`, punto único de stock): CHG-13. El `DELETE /libros/{id}` no existe hoy y no se agrega.
- Garantizar en la base el sólo agregado (disparador, 0004) o verificar con la base real los rechazos de las specs: CHG-08 (ver «Migration Plan»).
- Forzar `lazy="raise"` u `order_by` en las colecciones nuevas: la precarga y el orden los decide el repositorio (CHG-13).

## Decisions

### D1 · Dos etapas dentro del change: A (independiente) y B (con `Usuario`)
- **Etapa A**, desde ya: `Libro.borrado_en` + índice parcial; `MovimientoStock` completo salvo la relación `usuario`; `Libro.movimientos` y `Venta.movimientos`; `Cliente.usuario_id` y `MovimientoStock.usuario_id` como FK **por texto** a `usuario.id`, sin `Relationship`. Por el hallazgo 2, los mappers configuran y todos los tests sin base pasan.
- **Etapa B**, cuando el modelo `Usuario` de CHG-06 esté en la rama (merge de `main` o de la rama de CHG-06): `Cliente.usuario`, `MovimientoStock.usuario` y sus extremos `Usuario.cliente` / `Usuario.movimientos`, más el test de que el metadata se ordena (`sorted_tables`) con la FK resuelta.

**Alternativas descartadas:** (a) esperar a que CHG-06 esté mergeado para empezar — Lauti no arrancó y CHG-07 está en el camino crítico; (b) un `Usuario` provisorio dentro de CHG-07 — duplica el modelo de otro dueño y garantiza un conflicto de merge con una tabla definida dos veces; (c) declarar ya `Relationship("Usuario")` — `configure_mappers()` falla y con él cualquier test que instancie un modelo.

### D2 · Los pares recíprocos con `Usuario` se declaran en un solo commit, por CHG-07
Un `back_populates` sólo configura si los dos extremos existen. Si CHG-06 declara `Usuario.cliente = Relationship(back_populates="usuario")` antes de que exista `Cliente.usuario`, la rama de CHG-06 queda con los mappers rotos (y viceversa). Regla: **el change que llega segundo declara los dos extremos de cada par.** Con el orden del tren (CHG-06 primero, D3), CHG-07 etapa B edita `app/modules/usuarios/models.py` (archivo de Lauti) para agregar sólo dos atributos, `Usuario.cliente` y `Usuario.movimientos`, y sus imports bajo `TYPE_CHECKING`, en el mismo commit en que declara `Cliente.usuario` y `MovimientoStock.usuario`; se coordina con la rama de Lauti y él revisa el commit:

| Par | Lado A (CHG-07) | Lado B (en `Usuario`) |
|---|---|---|
| Cliente–Usuario | `Cliente.usuario: Optional["Usuario"]`, `back_populates="cliente"` | `Usuario.cliente: Optional["Cliente"]`, `back_populates="usuario"`, `sa_relationship_kwargs={"uselist": False}` |
| Movimiento–Usuario | `MovimientoStock.usuario: Optional["Usuario"]`, `back_populates="movimientos"` | `Usuario.movimientos: list["MovimientoStock"]`, `back_populates="usuario"`, `passive_deletes="all"` |

**Contrato con CHG-06 (confirmado por Lauti, 2026-11-03):** clase `Usuario` en `app/modules/usuarios/models.py`, tabla `usuario`, PK `id: int | None` (INTEGER), módulo que arranca con `import app.core.base`; CHG-06 sale **sin** `Usuario.cliente` ni `Usuario.movimientos` (los agrega CHG-07 en la etapa B); los usuarios no se borran físicamente (se desactivan con `activo`), por eso ninguna FK a `usuario` lleva `ON DELETE`. Matias se lo comunica a Lauti como parte del acuerdo. **Alternativa descartada:** que Lauti declare él esos dos atributos con su rama saliendo de la etapa A de CHG-07; el resultado en `main` sería idéntico, pero ataba CHG-06 a la rama de CHG-07.

### D3 · Integración: CHG-06 → CHG-07 → CHG-08 (0003) entran juntos a `main`
Con modelos por delante del esquema, la suite con base no puede pasar: el `TRUNCATE` del conftest nombra `movimiento_stock` (y `usuario`) que no existen, y todo `SELECT`/`INSERT` de `libro` y `cliente` incluye `borrado_en` / `usuario_id`. Sin `usuario` en el metadata ni siquiera se arma la lista de tablas (hallazgo 3). Y la consigna (Ej2) fija que la **tercera** migración trae, junta, las tablas de acceso, `movimiento_stock` y los cambios de `cliente` y `libro`: no se puede adelantar una migración parcial sólo para CHG-07.

Por lo tanto:
- **Gate de CHG-07** (etapas A y B): `python -m pytest -q -m "not db"` verde + los tests de metadata nuevos. La suite con base **no** se corre como gate de este change (falla por diseño hasta 0003).
- **Línea base**: antes de la primera línea de código, `REQUIRE_TEST_DB=1 python -m pytest -q` en la rama limpia (Postgres levantado) para dejar anotado el «N passed» de referencia; CHG-08 tiene que volver a ese N más sus tests nuevos.
- **Merge en tren (confirmado por Matias, 2026-11-03)**: el PR de CHG-07 se abre en borrador para revisión de modelos (cumple «los `models.py` en PRs propios y primero»), pero **no se mergea a `main` solo**; tampoco CHG-06. CHG-07 trae la rama de CHG-06 para la etapa B y CHG-08 sale de la rama de CHG-07. Cuando `REQUIRE_TEST_DB=1 python -m pytest -q` está verde en la punta de CHG-08, los tres PR se mergean a `main` en el orden **CHG-06 → CHG-07 → CHG-08**, en la misma sesión, cada uno con **merge commit (sin squash ni rebase)**. Con squash, los commits de CHG-06 que ya viven en las ramas de CHG-07 y CHG-08 dejarían de coincidir con los de `main` y el PR siguiente mostraría el diff duplicado o con conflictos; con merge commit cada PR sólo agrega lo suyo. Pasos en «Plan de merge».

**Alternativas descartadas:** (a) mergear CHG-07 solo y tolerar `main` rojo — rompe el trabajo de Lauti y Matias en paralelo; (b) que el conftest haga `TRUNCATE` sólo de las tablas que existen — oculta el desfase y no arregla los `SELECT` de columnas nuevas; (c) migración intermedia para CHG-07 — contradice el Ej2.

### D4 · Índice único parcial `uq_libro_isbn_vigente` y su 409
- `isbn` queda `Field(max_length=30)` sin `unique`; en `__table_args__` se agrega `Index("uq_libro_isbn_vigente", "isbn", unique=True, postgresql_where=text("borrado_en IS NULL"))` junto a los dos CHECK.
- El prefijo `uq_` lo agrupa con las claves de unicidad del diccionario de 409 (lo que importa es el nombre que informa PostgreSQL, que para un índice único es el del índice); el sufijo `_vigente` dice la condición y es el patrón que también usa el índice parcial de `asignacion_rol` (confirmado por Lauti; Matias aprueba el nombre `uq_libro_isbn_vigente`).
- `MENSAJES` agrega `"uq_libro_isbn_vigente": "Ya existe un libro con ese ISBN."` (mismo texto: `test_alta_isbn_repetido_da_409_con_mensaje_propio` no cambia). La clave vieja `uq_libro_isbn` se deja hasta que 0003 borre la constraint y la quita CHG-08 (confirmado por Nico; con la base del TP 1–4 sigue siendo la que dispara el 409).

**Alternativas descartadas:** (a) reutilizar el nombre `uq_libro_isbn` para el índice — no habría que tocar `MENSAJES`, pero en 0003 la constraint vieja y el índice nuevo tendrían el mismo nombre de relación: el orden de `drop_constraint`/`create_index` pasa a ser crítico justo donde el gotcha #5 avisa que autogenerate se equivoca, y el nombre mentiría (no es un UNIQUE común); (b) `ix_libro_isbn_vigente` — `ix_` es la familia de índices no únicos de las FK y no entra en el diccionario de 409.

### D5 · Columnas de `MovimientoStock`
| Columna | Declaración | Por qué |
|---|---|---|
| `id` | `int \| None`, PK | igual que el resto |
| `libro_id` | `int`, FK `libro.id`, `index=True` | NOT NULL; `ix_movimiento_stock_libro_id` |
| `venta_id` | `int \| None`, FK `venta.id`, `index=True`, nullable | sólo los de venta la tienen |
| `usuario_id` | `int`, FK `usuario.id` (texto), `index=True` | NOT NULL: la Figura 1 no lo marca «nulo»; el seed usa un admin para «Stock inicial» |
| `cantidad` | `int` (INTEGER) + `CheckConstraint("cantidad <> 0", name="cantidad_no_cero")` | `ck_movimiento_stock_cantidad_no_cero`; signo = entrada/salida |
| `motivo` | `str`, `max_length=255` (VARCHAR(255)), NOT NULL, sin CHECK de valores | confirmado por Nico; si `ReponerIn` (CHG-09b) lleva `motivo`, lo limita a 255 (confirmado por Lauti); la consigna no fija tipo; los textos («Stock inicial», reposición, venta, compensaciones) los decide CHG-13; 255 = largo de texto largo ya usado en el repo |
| `cuando` | `datetime \| None = None`, `DateTime(timezone=True)`, `nullable=False`, `server_default=func.now()` | timestamptz; un solo reloj (la base) también para inserciones desde psql (C-14) y el seed |

Con `server_default`, SQLAlchemy 2 en PostgreSQL trae `cuando` con `RETURNING` al hacer flush (`eager_defaults="auto"`), así que leerlo después no dispara una carga perezosa; CHG-08/13 lo cubren con un test con base. **Alternativa descartada para `cuando`:** `default_factory=lambda: datetime.now(UTC)` — las filas cargadas fuera del ORM quedarían sin valor y habría dos relojes.

### D6 · FKs sin `ON DELETE` y colecciones con `passive_deletes="all"`
`movimiento_stock` es de sólo agregado: el disparador de 0004 rechazaría el `UPDATE ... SET NULL` o el `DELETE` en cascada. Libros se dan de baja lógica, ventas no se modifican y usuarios se desactivan, así que el borrado físico de un padre con movimientos debe fallar por FK (23503 → 409 genérico o propio). Para que el ORM tampoco intente poner nulos al borrar un padre con la colección cargada, `Libro.movimientos`, `Venta.movimientos` y `Usuario.movimientos` llevan `passive_deletes="all"` y **no** `cascade_delete`. `cliente.usuario_id` tampoco lleva `ON DELETE`.

### D7 · Nombres de relaciones
Los de `AGENTS.md` §7: `Libro.movimientos` ↔ `MovimientoStock.libro`, `Venta.movimientos` ↔ `MovimientoStock.venta`, `Usuario.movimientos` ↔ `MovimientoStock.usuario`, `Cliente.usuario` ↔ `Usuario.cliente`. Tipos cruzados bajo `if TYPE_CHECKING:` y destinos como string. `Cliente.usuario` es a uno por ser el lado de la FK (la consigna exige «devuelve un objeto»); `Usuario.cliente` lleva `uselist=False`. `Libro.stock` sigue siendo columna (`default=0`, `ck_libro_stock_no_negativo`); que sólo la escriba el punto único es regla de CHG-13.

### D8 · Archivos fuera de la lista del plan
La sección «Archivos» de CHG-07 en `PLAN_PARCIAL.md` sólo nombra `libros/models.py` y `clientes/models.py`, pero cumplir el modelo exige además: `app/models.py` (registro de `MovimientoStock`; compartido), `app/modules/ventas/models.py` (`Venta.movimientos`; área de Matias), `app/modules/usuarios/models.py` (D2; de Lauti) y `app/modules/libros/service.py` (D4). Matias aprueba (2026-11-03) que CHG-07 toque `app/models.py` y `ventas/models.py`, y en `libros/service.py` **sólo** la clave nueva `uq_libro_isbn_vigente` de `MENSAJES`. Las correcciones de `PLAN_PARCIAL.md` (archivos y dependencias de CHG-07, merge en tren) y de `AGENTS.md` §7 (nombre `uq_libro_isbn_vigente`, regla de pares recíprocos de D2) las hace Matias en su propio PR de docs: **este change no edita esos dos archivos**; la descripción del PR sólo lo menciona.

### D9 · Tests
- Sólo metadata y mappers, sin base: inspección de `__table__` (columnas, nulabilidad, tipos, `server_default`, constraints, índices, `dialect_options["postgresql"]["where"]`, `ondelete`), `configure_mappers()` y propiedades de las relaciones (`back_populates`, `uselist`, `passive_deletes`, `cascade.delete`).
- Un test en proceso aislado (patrón de `test_naming_convention.py`) que importe sólo `app.modules.libros.models` y encuentre `ck_movimiento_stock_cantidad_no_cero` y el índice `uq_libro_isbn_vigente`.
- Archivo nuevo `tests/test_movimiento_stock_models.py`; los cambios de `Libro` van en `tests/test_catalogo_models.py` y los de `Cliente` en `tests/test_clientes_ventas_models.py`.
- Los escenarios de las specs que exigen la base real (rechazo por índice parcial, por CHECK, por FK, reutilizar ISBN, `cuando` por defecto, borrado de padre rechazado) se verifican en CHG-08 con tests `db` sobre la base migrada.

## Risks / Trade-offs

- [La fecha de CHG-06 sigue abierta (la planifica Lauti); si se demora, la etapa B queda bloqueada] → la etapa A es la mayor parte del change; la etapa B son dos relaciones y un test. CHG-08 también espera a CHG-06, así que no se suma demora al camino crítico, pero el tren entero se corre con CHG-06.
- [Lauti nombra distinto la clase, la tabla o la PK de `Usuario`] → contrato de D2 ya confirmado por escrito; el test de etapa B (`sorted_tables` y FK resuelta) lo detecta igual.
- [Alguien mergea CHG-06 o CHG-07 solo a `main`, o con squash] → la descripción de los PR lo dice en la primera línea; los PR quedan en borrador hasta que CHG-08 esté verde y se mergean con merge commit (D3, «Plan de merge»).
- [Autogenerate de 0003 maneja mal UNIQUE → índice parcial (gotcha #5)] → notas para CHG-08 abajo; el nombre distinto (D4) evita la colisión.
- [Python 3.14 local frente a 3.12 objetivo] → no se usa sintaxis nueva; los tipos `X | None` ya están en el código.
- [Mientras dure el tren, el seed y la suite con base no corren en estas ramas] → la línea base de D3 se toma antes de tocar código.

## Migration Plan

Este change **no** modifica la base. Notas para la migración 0003 de CHG-08 (leer y corregir a mano lo que autogenerate haga mal, con comentario):
1. En `libro`: `add_column borrado_en TIMESTAMP WITH TIME ZONE NULL`; `drop_constraint('uq_libro_isbn', 'libro', type_='unique')` **antes** de `create_index('uq_libro_isbn_vigente', 'libro', ['isbn'], unique=True, postgresql_where=sa.text('borrado_en IS NULL'))`. Verificar que autogenerate no deje la constraint vieja ni omita el `postgresql_where`.
2. `movimiento_stock` se crea **después** de `usuario` y `venta`; `server_default=sa.text('now()')` en `cuando`; tres índices `ix_movimiento_stock_*`; sin `ondelete`.
3. En `cliente`: `add_column usuario_id` nullable, `create_unique_constraint('uq_cliente_usuario_id')`, `create_foreign_key('fk_cliente_usuario_id_usuario')`, sin `ix_` extra.
4. `downgrade` en orden inverso; volver a crear `uq_libro_isbn` falla si hay ISBN repetidos entre filas dadas de baja (aceptable en una base de prueba; anotarlo en el comentario).
5. Al aplicar 0003, quitar de `MENSAJES` la clave `uq_libro_isbn` y agregar los tests `db` de los escenarios de D9.

Rollback de este change: revertir el commit (no hay datos ni esquema que deshacer).

### Plan de merge (tren CHG-06 → CHG-07 → CHG-08)
1. CHG-06 (Lauti) y CHG-07 quedan como PR en borrador; CHG-07 trae la rama de CHG-06 para la etapa B y CHG-08 sale de la rama de CHG-07.
2. Gate del tren: `REQUIRE_TEST_DB=1 python -m pytest -q` verde en la punta de CHG-08 (recupera el N de la línea base más los tests nuevos).
3. En la misma sesión se mergean a `main` CHG-06, después CHG-07 y después CHG-08, cada uno con **merge commit** («Create a merge commit»; sin squash ni rebase) y con la revisión de al menos otro integrante en cada PR.
4. Si `main` avanzó mientras tanto, se trae `main` a la rama de CHG-06 y se propaga hacia CHG-07 y CHG-08 con merge (no rebase) antes de volver a correr el gate.

## Decisiones confirmadas (2026-11-03)

- **Nico** (dueño de CHG-07): acepta el merge en tren; `motivo` VARCHAR(255) sin CHECK de valores (D5); la clave vieja `uq_libro_isbn` de `MENSAJES` la quita CHG-08 (D4).
- **Lauti** (dueño de CHG-06): acepta el contrato de `Usuario` tal como está en D2 (clase `Usuario` en `app/modules/usuarios/models.py`, tabla `usuario`, PK `id` INTEGER, arranca con `import app.core.base`, usuarios desactivados y nunca borrados); CHG-06 sale **sin** `Usuario.cliente` ni `Usuario.movimientos` y CHG-07 agrega los dos extremos (también en su archivo) en el mismo commit de la etapa B; el índice parcial de `asignacion_rol` usa el sufijo `_vigente`, igual que `uq_libro_isbn_vigente`; si `ReponerIn` (CHG-09b) lleva `motivo`, se limita a 255 caracteres.
- **Matias** (lead): tren CHG-06 → CHG-07 → CHG-08, que entran juntos cuando `REQUIRE_TEST_DB=1 pytest` está verde en la punta de CHG-08, con merge commit y sin squash (D3); aprueba que CHG-07 toque `app/models.py` y `app/modules/ventas/models.py` y, en `app/modules/libros/service.py`, sólo la clave `uq_libro_isbn_vigente` (D8); OK con el nombre `uq_libro_isbn_vigente`; le comunica a Lauti que CHG-06 no declara esas relaciones; las correcciones de `PLAN_PARCIAL.md` y `AGENTS.md` las hace él en su propio PR de docs.

**Único punto abierto (riesgo para la etapa B):** la fecha de CHG-06, que está planificando Lauti. Hasta que su modelo `Usuario` exista en una rama, la etapa B (grupo 6 de `tasks.md`) no puede empezar.
