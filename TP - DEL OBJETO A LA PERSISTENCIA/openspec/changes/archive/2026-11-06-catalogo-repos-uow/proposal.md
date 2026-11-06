# Proposal

## Why

El catálogo (editoriales, géneros, autores y libros) sigue con el patrón del TP 1–4: servicios que reciben la `AsyncSession`, confirman con `commit_or_409`, lanzan `HTTPException`, paginan con `limit`/`offset` y devuelven listas sueltas; `POST /libros` escribe `libro.stock` sin dejar movimiento y no hay reposición, historial ni baja lógica por la API. Con CHG-04 (repositorios + UoW), CHG-05 (envoltorio), CHG-08 (tablas y disparador), CHG-09b (contratos) y CHG-12 (grupos de rutas y `requiere_rol`) en `main`, CHG-13 migra el catálogo a Router → Service → UoW → Repository y crea **el único punto de escritura del stock** (RN-11) que CHG-16 necesita para las ventas. Cubre el Ejercicio 3 (8 %) y la parte de catálogo del Ejercicio 6 (16 %); DoD: casos C-13 y C-16.

## What Changes

- **Repositorios + UoW por módulo** en `editoriales`, `generos`, `autores` y `libros` (`repository.py` y `unit_of_work.py` nuevos); los servicios reciben el UoW y lo abren con `async with`; los routers lo construyen con `proveedor_uow`. `LibroRepository` hereda de `SoftDeleteRepository`; toda precarga se declara dentro del método que la usa.
- **Punto único de escritura del stock** (firma confirmada por Matias): `LibroRepository.registrar_movimiento(libro_id, cantidad, motivo, usuario_id, venta_id=None) -> ResultadoMovimiento` (dataclass congelada con el `stock` resultante y el `movimiento` creado), un `UPDATE` atómico condicionado (vigente; salidas sin pasar de 0, entradas con `stock <= INT32_MAX - cantidad`) con `RETURNING`, más el `movimiento_stock` en la misma sesión. Si el `UPDATE` no toca filas, una sola lectura de diagnóstico por columnas decide `LibroNoEncontrado` (404), `LibroDadoDeBaja` (409), `StockInsuficiente` (409) o `StockExcedido` (409).
- **Libros**: `POST /libros` deja el movimiento «Stock inicial» cuando `stock_inicial > 0`; rutas nuevas, las tres de `ADMIN` en el grupo protegido como pide la consigna: `POST /libros/{id}/reponer` (200, 404, 409, 422), `GET /libros/{id}/movimientos` paginado (200, 404) y `DELETE /libros/{id}` con baja lógica (204, 404); un libro dado de baja no aparece en listados ni en el detalle (404), no se edita (404) ni se repone (409), y su ISBN queda libre.
- **`usuario_id` del movimiento**: `POST /libros` y `POST /libros/{id}/reponer` lo toman del `UsuarioActual` que devuelve `SOLO_ADMIN` (alias `UsuarioAdmin`, CHG-12), con la misma sesión que el UoW. Las tres rutas nuevas se agregan a `tests/matriz_acceso.py` (grupo protegido, `ADMIN`).
- **Listados con el envoltorio** `{items, total, page, size, pages}` (`page`/`size`) en `GET /libros`, `/editoriales`, `/generos`, `/autores` y en los libros de una editorial, un género o un autor (sólo vigentes). **BREAKING**: dejan de aceptar `limit`/`offset` y de devolver una lista. Búsqueda por título con parámetro ligado, sin distinguir mayúsculas y con `%`/`_` escapados; `total` con los mismos filtros.
- **Errores de dominio**: `NoEncontrado` (→ 404) en `app/core/errors.py` con su handler en `app/main.py`, más `LibroNoEncontrado(NoEncontrado)`, `LibroDadoDeBaja(Conflicto)`, `StockInsuficiente(Conflicto)` y `StockExcedido(Conflicto)`, con mensajes en español terminados en punto. Los cuatro módulos dejan de lanzar `HTTPException` y de usar `commit_or_409` y `pagination.py`.
- **Contratos**: `extra="forbid"` en las entradas de editoriales, géneros y autores (faltaba desde CHG-09b); **BREAKING**: un `id` u otro campo extra en el cuerpo pasa de ignorarse a 422 (hoy hay tests que fijan que se ignora). Salidas nuevas `MovimientoStockRead` y `ReposicionRead`.
- **Routers**: se conservan los nombres de CHG-12, `router_abierto` (GET públicos) y `router` (escrituras e historial, grupo protegido); el montaje de `main.py` no cambia.

Fuera de alcance: cambiar `requiere_rol`, los grupos de rutas o RN-06 (CHG-12, ya en `main`: sólo se usan); ventas por el punto único, 409 de libro dado de baja en ventas y detalle de venta con libro dado de baja (CHG-16); clientes (CHG-15); seed con movimientos (CHG-17); casos `.http` C-01 a C-16 (CHG-18); borrar `pagination.py`, `commit_or_409` y `traducir_integrity`, que siguen usando clientes y ventas.

## Capabilities

### New Capabilities
- `catalogo-editoriales-generos-autores`: alta, consulta, edición y listados paginados de editoriales, géneros y autores, con sus libros vigentes, 404 y 409 propios.
- `errores-de-dominio`: recurso inexistente como excepción de dominio que la app responde 404, y el código de negocio migrado sin `HTTPException`.

### Modified Capabilities
- `catalogo-libros`: se agregan el alta con movimiento inicial, el detalle, el listado y la búsqueda paginados, la edición parcial y la baja lógica por la API, con la invisibilidad del libro dado de baja.
- `movimientos-stock`: se agregan el punto único de escritura del stock con sus rechazos, la reposición, el historial paginado de movimientos y el invariante stock = suma de movimientos.
- `contratos-catalogo-ventas`: se agregan el rechazo de campos no declarados en las entradas de editoriales, géneros y autores, y los contratos de salida de movimiento y de reposición.
- `grupos-de-rutas`: las rutas protegidas de administración suman `DELETE /libros/{id}`, `POST /libros/{id}/reponer` y `GET /libros/{id}/movimientos`.

## Impact

- **Código del change** (Nico): `app/modules/{editoriales,generos,autores,libros}/{repository,unit_of_work,service,router}.py` (los dos primeros nuevos) y sus tests.
- **Archivos compartidos** (revisión de Matias): `app/core/errors.py` (cinco excepciones), `app/main.py` (handler 404), `tests/matriz_acceso.py` (tres rutas nuevas de libros, `ADMIN`). Los tests reutilizan `entrar_como` de `tests/auxiliares_auth.py`: no hay fixtures nuevas en `tests/conftest.py`.
- **Contratos** (dueño Lauti, visto bueno pendiente): `schemas.py` de editoriales, géneros, autores (`extra="forbid"`, `from_attributes` en `EditorialRead`/`GeneroRead`) y libros (`MovimientoStockRead` y `ReposicionRead`, que ya usa el PR 1).
- **API**: dos rutas nuevas y `DELETE /libros/{id}`, las tres de `ADMIN`; listados con otra forma. Los `.http` del TP quedan desactualizados hasta CHG-18.
- **Base**: sin migraciones.
- **Transitorio hasta CHG-16**: `POST /ventas` sigue descontando `libro.stock` sin movimiento y sin mirar `borrado_en`, así que después de una venta el invariante no se cumple. Lo cierra Matias en CHG-16 con el punto único.
- **Entrega**: dos PRs; el PR 1 (libros) marca CHG-13 `en curso` y sólo el PR 2 (editoriales, géneros y autores) pone `mergeado (#N)`, archiva y actualiza la Transición.
- **Documentación**: fila CHG-13 de `PLAN_PARCIAL.md`, «Transición» de `AGENTS.md` §9 (fila de stock/ISBN y la de servicios con sesión para el catálogo).
- **Desbloquea**: CHG-16 (punto único de stock) y CHG-18 (casos C-13 y C-16).
- **Gobernanza**: MEDIUM (lógica de negocio); los archivos compartidos y la firma del punto único los revisa Matias.
