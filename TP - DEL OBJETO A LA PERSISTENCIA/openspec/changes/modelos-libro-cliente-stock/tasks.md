# Tasks

Strict TDD: cada par RED → GREEN se ejecuta con `python -m pytest -q <archivo>`; el RED tiene que fallar por la razón esperada (no por un error de import) antes de escribir el GREEN. Gate del change: `python -m pytest -q -m "not db"` (design D3).

## 1. Precondiciones y línea base

- [x] 1.1 Con Postgres levantado y la rama limpia, correr `REQUIRE_TEST_DB=1 python -m pytest -q` y anotar acá el «N passed» (sin skips); verificar que es verde. Es la referencia que CHG-08 tiene que recuperar. — N = 321 passed (sin skips), verde (2026-11-03).
- [x] 1.2 Correr `python -m pytest -q -m "not db"` y anotar acá el «M passed»; verificar que ningún test sin marca `db` toca la base (si alguno lo hace, anotarlo). — M = 157 passed (164 deselected); ningún test sin marca `db` toca la base (corrió con Postgres apagado).
- [x] 1.3 Confirmar con Lauti el contrato de design D2 (clase `Usuario`, tabla `usuario`, PK `id` INTEGER, CHG-06 sin `Usuario.cliente` ni `Usuario.movimientos`, usuarios sin borrado físico) y con Matias D3 y D8; verificar que las respuestas queden anotadas en «Decisiones confirmadas» de `design.md` antes de 2.1. — confirmado por Lauti y Matias (2026-11-03); queda abierta sólo la fecha de CHG-06 (riesgo de la etapa B).

## 2. Etapa A · Libro: borrado lógico e ISBN único entre vigentes

- [x] 2.1 RED: en `tests/test_catalogo_models.py`, test de que `libro.borrado_en` existe, admite nulo y es `DateTime(timezone=True)`; verificar que falla porque la columna no existe.
- [x] 2.2 GREEN: agregar `borrado_en: datetime | None` (`DateTime(timezone=True)`, nullable) a `Libro`; verificar que 2.1 pasa.
- [x] 2.3 RED: cambiar `test_libro_estructura_y_constraints` para exigir que **no** esté `uq_libro_isbn` y que exista el índice `uq_libro_isbn_vigente` único, sobre `isbn`, con `postgresql_where` = `borrado_en IS NULL`, manteniendo `ck_libro_precio_positivo` y `ck_libro_stock_no_negativo`; reemplazar el caso `uq_libro_isbn` del test en proceso aislado por uno que busque el índice; verificar que fallan.
- [x] 2.4 GREEN: quitar `unique=True` de `isbn` y agregar el `Index("uq_libro_isbn_vigente", ...)` en `__table_args__` (design D4); verificar que 2.3 pasa y que `tests/test_catalogo_models.py` entero está verde.
- [x] 2.5 RED: en `tests/test_catalogo_service.py`, agregar `uq_libro_isbn_vigente` a las claves esperadas de `MENSAJES` y un caso que traduzca un `IntegrityError` ficticio con ese nombre a 409 «Ya existe un libro con ese ISBN.»; verificar que falla.
- [x] 2.6 GREEN: agregar la clave a `MENSAJES` en `app/modules/libros/service.py`, único cambio permitido en ese archivo (D8); se conserva `uq_libro_isbn` (D4); verificar que `tests/test_catalogo_service.py` y `tests/test_errors.py` pasan.

## 3. Etapa A · MovimientoStock: estructura e integridad

- [x] 3.1 RED: crear `tests/test_movimiento_stock_models.py` con: `movimiento_stock` registrada en el metadata vía `app.models`; columnas exactas `{id, libro_id, venta_id, usuario_id, cantidad, motivo, cuando}`; sólo `venta_id` nullable; `cuando` `DateTime(timezone=True)` con `server_default` `now()`; `motivo` de largo 255; verificar que falla porque el modelo no existe.
- [x] 3.2 GREEN: crear `MovimientoStock` en `app/modules/libros/models.py` según design D5 (FK a `usuario.id` por texto, sin `Relationship` a `Usuario`) e importarlo en `app/models.py`; verificar que 3.1 pasa y que `configure_mappers()` no falla.
- [x] 3.3 RED: tests de `ck_movimiento_stock_cantidad_no_cero` con texto `cantidad <> 0`; `fk_movimiento_stock_libro_id_libro`, `fk_movimiento_stock_venta_id_venta` y `fk_movimiento_stock_usuario_id_usuario` con `ondelete` nulo; índices `ix_movimiento_stock_libro_id`, `ix_movimiento_stock_venta_id`, `ix_movimiento_stock_usuario_id`; y un test en proceso aislado que importe sólo `app.modules.libros.models` y encuentre `ck_movimiento_stock_cantidad_no_cero`; verificar que falla lo que el GREEN de 3.2 todavía no cubre (si ya pasa todo, anotar que 3.2 lo cubrió y seguir). — el GREEN de 3.2 ya cubría todo (modelo escrito completo); los tests se verificaron por mutación (nombre/texto del CHECK y `passive_deletes` rotos a propósito hacen fallar 3 tests).
- [x] 3.4 GREEN: completar constraints e índices de `MovimientoStock`; verificar que `tests/test_movimiento_stock_models.py` pasa. — cubierto por 3.2.

## 4. Etapa A · Navegación de movimientos con libro y venta

- [x] 4.1 RED: tests de `back_populates` y destino para `Libro.movimientos` ↔ `MovimientoStock.libro` y `Venta.movimientos` ↔ `MovimientoStock.venta`; las colecciones con `uselist` verdadero, `passive_deletes == "all"` y sin `cascade.delete`; los lados del movimiento, a uno; verificar que fallan.
- [x] 4.2 GREEN: declarar las cuatro relaciones (design D6/D7) en `app/modules/libros/models.py` y `app/modules/ventas/models.py`, con imports cruzados bajo `TYPE_CHECKING`; verificar que 4.1 pasa y que `tests/test_clientes_ventas_models.py` y `tests/test_integracion_relaciones.py` siguen verdes.

## 5. Etapa A · Cliente: columna de acceso

- [x] 5.1 RED: en `tests/test_clientes_ventas_models.py`, ajustar `test_tabla_y_columnas` para que `cliente` tenga `{id, nombre, email, usuario_id}` con sólo `usuario_id` nullable, y agregar `uq_cliente_usuario_id` y `fk_cliente_usuario_id_usuario` a los constraints esperados y `ix_cliente_usuario_id` a los índices prohibidos; verificar que fallan.
- [x] 5.2 GREEN: agregar `usuario_id: int | None` a `Cliente` con `foreign_key="usuario.id"`, `unique=True`, nullable y sin `index=True`; verificar que 5.1 pasa.
- [x] 5.3 Gate de etapa A: `python -m pytest -q -m "not db"` verde con M + los tests nuevos; anotar el número acá. — 180 passed (157 + 23 nuevos), 164 deselected.

## 6. Etapa B · Relaciones con Usuario (requiere el modelo de CHG-06 en la rama)

- [x] 6.1 Traer `Usuario` a la rama con merge (no rebase) de la rama de CHG-06 de Lauti, que no entra sola a `main` (design D3), y verificar el contrato de 1.3: `from app.modules.usuarios.models import Usuario` funciona, `Usuario.__tablename__ == "usuario"`, `python -m pytest -q -m "not db"` sigue verde. (Hecho: merge de main en f1c34ab.)
- [x] 6.2 RED: tests de `Cliente.usuario` ↔ `Usuario.cliente` (los dos a uno, `uselist` falso) y `MovimientoStock.usuario` ↔ `Usuario.movimientos` (`passive_deletes == "all"`, sin `cascade.delete`), y un test de que `SQLModel.metadata.sorted_tables` se arma sin error y las FK `cliente.usuario_id` y `movimiento_stock.usuario_id` resuelven a la tabla `usuario`; verificar que fallan.
- [x] 6.3 GREEN: declarar los cuatro extremos en el mismo commit (design D2): `Cliente.usuario` y `MovimientoStock.usuario` en los modelos de CHG-07, y editar `app/modules/usuarios/models.py` (archivo de Lauti) para agregar `Usuario.cliente` (`sa_relationship_kwargs={"uselist": False}`) y `Usuario.movimientos` (`passive_deletes="all"`), con imports bajo `TYPE_CHECKING` y sin tocar nada más de ese archivo; coordinarlo con la rama de Lauti (avisarle antes y pedirle revisión del commit); verificar que 6.2 pasa y `configure_mappers()` no falla.
- [x] 6.4 REFACTOR: comentarios que expliquen el índice parcial, `server_default` y `passive_deletes`, `import app.core.base` primero en cada `models.py`; verificar `python -m pytest -q -m "not db"` verde después de cada paso.

## 7. Cierre del change (integración)

- [x] 7.1 Correr `python -m pytest -q -m "not db"` completo y anotar el número; verificar que sólo cambió por los tests nuevos/ajustados de este change. Resultado: 379 passed (376 + 3 nuevos de la etapa B).
- [x] 7.2 Correr `python -c "import app.models; from sqlalchemy.orm import configure_mappers; configure_mappers(); from sqlmodel import SQLModel; print([t.name for t in SQLModel.metadata.sorted_tables])"` y verificar que lista `usuario`, `movimiento_stock` y el resto sin error (insumo directo de 0003). Resultado: 14 tablas sin error, con `usuario` y `movimiento_stock`.
- [ ] 7.3 Commit `feat(libros): borrado lógico, movimiento_stock y acceso del cliente` y PR **en borrador** con la primera línea «No mergear solo: entra en tren CHG-06 → CHG-07 → CHG-08 con merge commit, sin squash (design D3)» y una nota que remita al PR de docs de Matias para `PLAN_PARCIAL.md` y `AGENTS.md` (este change no los edita); verificar con `git status` y `git diff --stat main...` que no entran `.env`, `__pycache__/`, `PLAN_PARCIAL.md`, `AGENTS.md` ni archivos ajenos.
- [ ] 7.4 Merge del tren (design «Plan de merge»): cuando `REQUIRE_TEST_DB=1 python -m pytest -q` está verde en la punta de CHG-08, sacar los PR de borrador y mergear a `main` CHG-06, después CHG-07 y después CHG-08, cada uno con «Create a merge commit» (sin squash ni rebase) y con revisión de otro integrante; verificar con `git log --first-parent main` que quedan tres merge commits en ese orden y que `REQUIRE_TEST_DB=1 python -m pytest -q` sigue verde en `main`.

## Workflow follow-up

- CHG-08 sale de esta rama: genera 0003 siguiendo «Migration Plan» de `design.md`, agrega los tests `db` de los escenarios que necesitan la base y recupera el N de 1.1.
- Riesgo abierto: la fecha de CHG-06 (la planifica Lauti) condiciona el grupo 6 y el tren entero (7.4).
- Archivar el change después del merge del tren (7.4); el estado `mergeado` de CHG-07 en `PLAN_PARCIAL.md` lo actualiza Matias en su PR de docs.
