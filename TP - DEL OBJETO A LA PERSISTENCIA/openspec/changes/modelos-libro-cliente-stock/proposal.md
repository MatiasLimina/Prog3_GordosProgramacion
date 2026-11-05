# Proposal

## Why

El Ej2 del parcial (10 %) pide modificar `Libro` y `Cliente` y agregar `MovimientoStock` según la Figura 1 (consigna págs. 4–6): borrado lógico con ISBN único sólo entre vigentes, acceso web opcional del cliente y un historial de stock de sólo agregado. Hoy `libro.isbn` es un UNIQUE común (un ISBN dado de baja no se podría volver a cargar, C-13), `cliente` no tiene `usuario_id` y no existe `movimiento_stock`. CHG-08 (migración 0003 autogenerada) necesita estos modelos en el metadata, y CHG-13/15/16 (stock por movimientos, borrado lógico, ventas) se apoyan en ellos: es el segundo eslabón del camino crítico de Nico (CHG-07 → CHG-08 → CHG-13).

## What Changes

- **`Libro`** (`app/modules/libros/models.py`):
  - Nueva columna `borrado_en` (`timestamptz`, nullable).
  - **BREAKING (esquema)**: `isbn` deja de tener la constraint `uq_libro_isbn`; la reemplaza el índice único parcial `uq_libro_isbn_vigente` sobre `(isbn) WHERE borrado_en IS NULL` (`postgresql_where`).
  - Siguen `ck_libro_precio_positivo` y `ck_libro_stock_no_negativo`; `stock` sigue siendo columna (valor acumulado que sólo escribirá el punto único de CHG-13).
  - Nueva relación `Libro.movimientos` ↔ `MovimientoStock.libro`.
- **`MovimientoStock`** (nuevo, en `libros`, tabla `movimiento_stock`): `id`, `libro_id`, `venta_id` (nullable), `usuario_id`, `cantidad` con CHECK `cantidad <> 0`, `motivo`, `cuando` (`timestamptz`, valor por defecto de la base). Índice en cada FK. Navegación en los dos extremos hacia `Libro`, `Venta` y `Usuario`.
- **`Venta`** (`app/modules/ventas/models.py`): nueva relación `Venta.movimientos` (extremo B de `MovimientoStock.venta`). Sin columnas nuevas.
- **`Cliente`** (`app/modules/clientes/models.py`): nueva columna `usuario_id` nullable y UNIQUE (`uq_cliente_usuario_id`, `fk_cliente_usuario_id_usuario`); relación a uno `Cliente.usuario` ↔ `Usuario.cliente` (escalar).
- **Relaciones con `Usuario`** (modelo de CHG-06): `Cliente.usuario`, `MovimientoStock.usuario` y sus extremos `Usuario.cliente` y `Usuario.movimientos` se declaran **en el mismo commit**, después de que el modelo `Usuario` de CHG-06 esté en la rama (ver design D1).
- **Registro**: `MovimientoStock` se importa en `app/models.py`.
- **Mensaje de 409**: `MENSAJES` de `app/modules/libros/service.py` incorpora la clave `uq_libro_isbn_vigente` con el mismo texto actual («Ya existe un libro con ese ISBN.»).
- **Tests de metadata** nuevos y ajuste de los existentes que fijan la estructura anterior (`uq_libro_isbn`, columnas exactas de `cliente`).

**Fuera de alcance**: migraciones 0003/0004 y el disparador de sólo agregado (CHG-08); el punto único de escritura de stock, `stock_inicial`, reposición, baja lógica y filtros de vigentes (CHG-13); contratos (CHG-09a/b); el modelo `Usuario` y las tablas de acceso (CHG-06); seed (CHG-17).

## Capabilities

### New Capabilities

- `catalogo-libros`: identidad y vigencia de un libro en el catálogo: borrado lógico y unicidad del ISBN entre los vigentes, con su 409 propio.
- `movimientos-stock`: estructura e integridad del historial de stock (`movimiento_stock`) y su navegación hacia libro, venta y usuario. CHG-08 le agregará el sólo agregado y CHG-13 el punto único de escritura.
- `clientes`: vínculo opcional y exclusivo de un cliente con un usuario (acceso web).

### Modified Capabilities

Ninguna (no hay specs principales todavía).

## Impact

- **Código**: `app/modules/libros/models.py`, `app/modules/clientes/models.py`, `app/modules/ventas/models.py` (sólo `Venta.movimientos`), `app/modules/usuarios/models.py` (sólo los extremos `Usuario.cliente` y `Usuario.movimientos`, acordado con Lauti; D2), `app/models.py` (registro), `app/modules/libros/service.py` (sólo la clave `uq_libro_isbn_vigente` de `MENSAJES`). Matias aprobó tocar `app/models.py` y `ventas/models.py` (D8). `PLAN_PARCIAL.md` y `AGENTS.md` no se editan acá: los corrige Matias en su PR de docs.
- **Tests**: nuevos de metadata; se ajustan `tests/test_catalogo_models.py`, `tests/test_clientes_ventas_models.py` y `tests/test_catalogo_service.py`.
- **Esquema de la base**: ninguno en este change. Los modelos quedan **por delante** del esquema hasta que exista la migración 0003 (CHG-08): mientras tanto la suite con base (`REQUIRE_TEST_DB=1`) no puede pasar y **CHG-07 no se mergea a `main` solo**; entra en tren CHG-06 → CHG-07 → CHG-08, con merge commit y sin squash (design D3).
- **Coordinación** (confirmada el 2026-11-03, ver «Decisiones confirmadas» del design): con Lauti (contrato de `Usuario` y extremos de la etapa B; `motivo` de `ReponerIn` hasta 255 en CHG-09b) y con Matias (archivos compartidos y tren de merge). Queda abierta sólo la fecha de CHG-06, riesgo para la etapa B.
- **Dependencias**: CHG-00 (mergeado). Para cerrar las relaciones con `Usuario`, el modelo de CHG-06. Desbloquea CHG-08.
