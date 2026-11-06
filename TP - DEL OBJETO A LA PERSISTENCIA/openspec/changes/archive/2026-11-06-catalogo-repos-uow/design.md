# Design

## Context

- **Core listo** (CHG-04/05): `BaseRepository[T]` (`get_by_id` con `session.get`, `get_all`, `count`, `add`/`update`/`delete` con `flush`, helpers `_consulta_base`, `_listar` —ordena por la PK del modelo y agrega `ORDER BY` a lo que ya traiga la consulta— y `_contar`); `SoftDeleteRepository[T]` (filtra `borrado_en IS NULL`, `get_by_id_including_deleted` con `session.get`, `soft_delete` con fecha de Python, `delete` → `NotImplementedError`); `UnitOfWork` (confirma/revierte, traduce `IntegrityError` a `Conflicto(mensaje_para(e, MENSAJES))`, prohíbe anidar); `proveedor_uow`; `paginacion_params` → `ParametrosPagina(page, size)` y `envolver(items, total=, page=, size=)` que lanza `PeticionInvalida` (422).
- **Auth y autorización en `main`** (CHG-11 y CHG-12, #54): `get_usuario_actual` (cookie → token → usuario; 401 `NoAutenticado`) devuelve `UsuarioActual` con valores simples; `requiere_rol(*roles)` con las constantes `SOLO_ADMIN` / `PERSONAL` y los alias `UsuarioAdmin` / `UsuarioPersonal` lee los roles vigentes de la base y **devuelve el `UsuarioActual`** (pensado para el actor de un movimiento de stock). Todas usan la misma sesión de la petición (`get_session` cacheado) en bloques cortos **anteriores** al del servicio. `app/main.py` monta un grupo abierto y uno protegido (`control_cambio_obligatorio`, RN-06, una sola vez); por cada módulo del catálogo incluye `router_abierto` (GET públicos) en el abierto y `router` (escrituras) en el protegido. `tests/matriz_acceso.py` clasifica cada ruta `(método, ruta) -> (grupo, acceso)` y `tests/test_grupos_de_rutas.py` falla si una ruta de la app no figura (o figura con otro rol); `tests/test_autorizacion_db.py` recorre la matriz (401 sin cookie, 403 con VENDEDOR/CLIENTE en las de ADMIN).
- **Catálogo hoy** (TP 1–4 con los routers ya partidos por CHG-12): los cuatro servicios reciben `AsyncSession`, confirman con `commit_or_409`, lanzan `HTTPException(404)` y paginan con `app/core/pagination.py` (`limit`/`offset`) devolviendo listas. `POST /libros` y `PATCH /libros/{id}` ya llevan `dependencies=[Depends(SOLO_ADMIN)]`. `libros.crear` escribe `Libro(stock=stock_inicial)` sin movimiento (comentario «transitorio hasta CHG-13»). `obtener` ya usa `populate_existing` y precarga correcta. Los listados de libros por editorial/género/autor no filtran `borrado_en`. `autores` lista con `select(LibroAutor, Libro).join(...)` ordenado por `(orden, libro.id)`.
- **Contratos** (CHG-09b): `LibroCreate` (`stock_inicial`, `autores`, `extra="forbid"`), `LibroUpdate` (sólo `titulo`/`precio`), `ReponerIn` (`cantidad` 1..INT32_MAX, `motivo` opcional 1..255). Las entradas de editoriales, géneros y autores **no** tienen `extra="forbid"`; `EditorialRead` y `GeneroRead` no tienen `from_attributes`. No hay contrato de salida de movimientos.
- **Ventas** (`ventas/service.py`, CHG-16): descuenta con `UPDATE libro SET stock = stock - n ... RETURNING precio` sin movimiento, sin mirar `borrado_en` y con `HTTPException`. Usa `traducir_integrity` y `pagination.py`; clientes usa `commit_or_409` y `pagination.py`.
- **Tablas** (CHG-08): `movimiento_stock` con `ck_movimiento_stock_cantidad_no_cero`, FKs sin `ON DELETE`, `cuando` con `server_default now()` y disparador `movimiento_stock_solo_agregado` (SQLSTATE 23001). `libro.stock` es `INTEGER` con `ck_libro_stock_no_negativo`.
- **Tests**: los archivos HTTP que escriben en el catálogo (`test_libros_crud_db.py`, `test_libros_validaciones.py`, `test_libros_por_editorial_genero.py`, `test_editoriales.py`, `test_generos.py`, `test_ventas_db.py`, `test_clientes_db.py`, `test_seed.py`) ya redefinen la fixture `client` con `entrar_como(client, sessionmaker_test, "ADMIN")` (`tests/auxiliares_auth.py`): inserta el usuario con el rol y pone un token firmado en el cookie jar, sin pasar por `/auth/login`. La cantidad de tests recolectados se re-mide en la tarea 1.2 sobre `main` 5fe3d10.

## Goals / Non-Goals

**Goals:**
- Que CHG-16 componga `LibroRepository` en su `VentasUoW` y llame `registrar_movimiento` por renglón sin tocar nada de CHG-13.
- Que los cuatro módulos del catálogo queden en Router → Service → UoW → Repository sin `HTTPException`, `commit_or_409` ni `pagination.py`.
- Que las tres rutas nuevas de libros queden clasificadas en `tests/matriz_acceso.py` con el rol de la consigna.
- Dejar C-13 y C-16 demostrables por HTTP (los `.http` los escribe CHG-18).

**Non-Goals:**
- Cambiar `requiere_rol`, los grupos de rutas o RN-06 (CHG-12, ya en `main`): sólo se usan.
- Migrar ventas o clientes, borrar `pagination.py`, `commit_or_409`, `traducir_integrity` o `_buscar_atributo` (los siguen usando CHG-15/16).
- Cambiar el esquema: no hay migraciones.

## Decisions

### D1. Repositorios y UoW por módulo

| Módulo | Repositorios (`repository.py`) | UoW (`unit_of_work.py`) |
|---|---|---|
| `editoriales` | `EditorialRepository(BaseRepository[Editorial])` | `EditorialesUoW`: `editoriales`, `libros` |
| `generos` | `GeneroRepository(BaseRepository[Genero])` | `GenerosUoW`: `generos`, `libros` |
| `autores` | `AutorRepository(BaseRepository[Autor])` | `AutoresUoW`: `autores`, `autorias` |
| `libros` | `LibroRepository(SoftDeleteRepository[Libro])`, `LibroAutorRepository(BaseRepository[LibroAutor])`, `MovimientoStockRepository(BaseRepository[MovimientoStock])` | `LibrosUoW`: `libros`, `movimientos` |

Cada repositorio de entidad recibe sólo `(session)` y pasa su modelo a la base. Los de `libros` viven en `app/modules/libros/repository.py` porque `LibroAutor` y `MovimientoStock` son de ese módulo (AGENTS §3); editoriales, géneros y autores los importan para sus sub-listados (dependencia de módulo hacia `libros`, que ya existe hoy con `LibroRead`).

Métodos nombrados por lo que traen, cada uno con su precarga adentro:

| Repositorio | Método | Precarga / filtro |
|---|---|---|
| `LibroRepository` | `get_detalle(id)` | vigente; `joinedload(editorial)`, `joinedload(genero)`, `selectinload(autorias).joinedload(autor)`, `populate_existing` |
| | `buscar(*, titulo, genero_id, offset, limit)` / `contar(*, titulo, genero_id)` | vigentes; `joinedload(editorial)`, `joinedload(genero)` sólo en `buscar` |
| | `listar_por_editorial` / `contar_por_editorial`, `listar_por_genero` / `contar_por_genero` | vigentes; mismas precargas |
| | `registrar_movimiento(...)` | ver D3 |
| `LibroAutorRepository` | `listar_por_autor(autor_id, *, offset, limit)` / `contar_por_autor` | libro vigente; `joinedload(LibroAutor.libro)`; orden `orden` (+ PK que agrega `_listar`) |
| `MovimientoStockRepository` | `listar_de_libro` / `contar_de_libro` | orden por `id` |

- **Conteo sin precarga**: cada par `listar_*`/`contar_*` parte de un helper privado que arma sólo el filtro (p. ej. `_filtrada(titulo, genero_id)`); `listar_*` le agrega las `options(...)` y `contar_*` no. Así `total` usa los mismos filtros y la subconsulta de `_contar` no arrastra `joinedload` (R6).
- **`MENSAJES` por UoW**: `EditorialesUoW` = `uq_editorial_nombre`; `GenerosUoW` = `uq_genero_nombre`; `AutoresUoW` = `{}` (ninguna constraint propia); `LibrosUoW` = los diez de `libros/service.py` hoy + `movimiento_stock_solo_agregado` («Los movimientos de stock no se modifican ni se borran: un error se corrige con otro movimiento.») + `fk_movimiento_stock_usuario_id_usuario` («El usuario indicado no existe.»). `MENSAJES` sale de `service.py` y vive sólo en el UoW.
- Alternativa descartada: un único `CatalogoUoW` para los cuatro módulos. La consigna pide «cada módulo tiene su Unit of Work» y CHG-16 sólo necesita `LibroRepository`.

### D2. Servicios

Funciones `async` que reciben el UoW (y valores simples: `usuario_id: int`, `ParametrosPagina`) y abren un solo `async with uow:` por operación; el DTO de salida se arma **dentro** del bloque (con `expire_on_commit=False` daría igual tras el commit, pero así nada depende de eso). Patrón de listado:

```python
async with uow:
    total = await uow.libros.contar(titulo=titulo, genero_id=genero_id)
    items = await uow.libros.buscar(titulo=titulo, genero_id=genero_id,
                                    offset=(p.page - 1) * p.size, limit=p.size)
    return envolver([LibroRead.model_validate(l) for l in items], total=total, page=p.page, size=p.size)
```

Una página fuera de rango hace una consulta de ítems inútil antes del 422: se acepta por simplicidad (validar antes exigiría duplicar el cálculo de `pages` de `envolver`). `PeticionInvalida` dentro del bloque sólo revierte una transacción de lectura.

Los sub-listados (`/editoriales/{id}/libros`, etc.) leen primero el padre con `get_by_id` para dar 404: es el recurso de la ruta, no una validación antes de escribir (AGENTS §8 sigue intacto).

### D3. Punto único de escritura del stock (firma confirmada por Matias, 2026-11-06)

```python
@dataclass(frozen=True)
class ResultadoMovimiento:
    """Lo que deja una escritura de stock: el stock resultante y el movimiento creado."""
    stock: int
    movimiento: MovimientoStock

async def registrar_movimiento(self, libro_id: int, cantidad: int, motivo: str,
                               usuario_id: int, venta_id: int | None = None) -> ResultadoMovimiento:
```

`ResultadoMovimiento` vive en `app/modules/libros/repository.py` junto al método. La reposición usa los dos campos; el alta y las ventas (CHG-16) pueden usar sólo `stock` o ignorarlo.

1. `cantidad == 0` → `ValueError` (error de programación, antes de escribir; el CHECK `cantidad <> 0` sólo se dispararía después de haber cambiado el stock).
2. Una sentencia ORM:
   ```python
   limite = (Libro.stock + cantidad >= 0) if cantidad < 0 else (Libro.stock <= INT32_MAX - cantidad)
   update(Libro).where(Libro.id == libro_id, Libro.borrado_en.is_(None), limite)
                .values(stock=Libro.stock + cantidad).returning(Libro.stock)
                .execution_options(synchronize_session="fetch")
   ```
   - Para entradas (`cantidad > 0`) la condición es `stock <= INT32_MAX - cantidad`, con `INT32_MAX` de `app/core/tipos.py` calculado en Python y ligado como parámetro: la base nunca hace una suma que desborde (`stock + cantidad` fuera de int32 daría `22003 integer out of range`, un `DataError` que el UoW no traduce → 500, RN-15). Para salidas queda `stock + cantidad >= 0`, que no puede desbordar.
   - `synchronize_session="fetch"`: un `Libro` ya cargado en la sesión (el recién creado en el alta) queda con el stock nuevo; sin eso conservaría el viejo. Riesgo R1: en la implementación `fetch` no alcanzó y se reemplazó por `set_committed_value` (ver R1).
   - Bajo `READ COMMITTED`, PostgreSQL bloquea la fila y reevalúa el `WHERE` con la versión confirmada si otra transacción la cambió: no hay actualizaciones perdidas ni stock negativo sin leer antes.
3. `movimiento = MovimientoStock(libro_id=..., cantidad=..., motivo=..., usuario_id=..., venta_id=...)`, `session.add` + `flush()`. Nunca `commit()`: confirma el UoW de quien llama. `id` y `cuando` (`server_default`) quedan cargados en el objeto por el `RETURNING` del `INSERT` (SQLAlchemy 2.0, `eager_defaults="auto"` en PostgreSQL); el test lo fija leyendo `cuando` sin emitir consultas y, si no alcanzara, se agrega `await session.refresh(movimiento, ["cuando"])`.
4. Devuelve `ResultadoMovimiento(stock=<valor de RETURNING>, movimiento=movimiento)`.
5. **Sin fila**: una sola lectura de diagnóstico y la excepción:
   - lectura **por columnas** `select(Libro.stock, Libro.borrado_en).where(Libro.id == libro_id)` y no `get_by_id_including_deleted`: `session.get` devuelve del mapa de identidad un `Libro` ya cargado sin consultar, con un stock o un `borrado_en` viejos, y el mensaje «hay 2» mentiría. La consulta por columnas siempre va a la base y no toca objetos de la sesión; corre sólo en el camino de rechazo.
   - Cuatro casos: sin fila → `LibroNoEncontrado(libro_id)` (404 si nadie la traduce); `borrado_en` no nulo → `LibroDadoDeBaja(libro_id)`; si no, por el signo: `cantidad < 0` → `StockInsuficiente(libro_id, disponible=stock, pedido=-cantidad)`; `cantidad > 0` → `StockExcedido(libro_id)`.
   - La lectura es posterior a la escritura fallida y sólo para elegir el mensaje: no es «consultar antes para validar».
6. **Docstring**: quien registre varias líneas (ventas) MUST llamar en orden ascendente de `libro_id` para que dos transacciones tomen los bloqueos de fila en el mismo orden (sin deadlock); un libro repetido en una venta lo resuelve el contrato de CHG-16 (unir o 422). Quien necesite el stock o el `usuario_id` después de un posible rollback los guarda como `int` antes del bloque (advertencia del UoW); el `movimiento` del resultado se serializa dentro del bloque.

Alternativas descartadas: `SELECT ... FOR UPDATE` + cálculo en Python (dos idas a la base y lógica de stock en dos lugares); método en un servicio de stock compartido (CHG-16 tendría que componer servicios; el repositorio entra en su UoW); devolver sólo `int` y releer el último movimiento del libro con `ultimo_de_libro` (una consulta más y una garantía apoyada en el bloqueo de fila; Matias eligió devolver los dos).

### D4. Excepciones de dominio (`app/core/errors.py`, revisa Matias)

```python
class NoEncontrado(Exception):            # handler en main.py → 404 {"detail": mensaje}
    def __init__(self, mensaje: str): ...

class LibroNoEncontrado(NoEncontrado):    # libro_id; «El libro no existe.»
class LibroDadoDeBaja(Conflicto):         # libro_id; «El libro {id} está dado de baja.»
class StockInsuficiente(Conflicto):       # libro_id, disponible, pedido;
                                          # «Stock insuficiente para el libro {id}: hay {disponible}, se pidieron {pedido}.»
class StockExcedido(Conflicto):           # libro_id; «El stock del libro {id} superaría el máximo permitido.»
```

- `NoEncontrado` es la base genérica que ya anticipaba el diseño de CHG-04: los servicios del catálogo la lanzan con su mensaje («La editorial no existe.», «El género no existe.», «El autor no existe.», «El libro no existe.»), y CHG-15/16 la reutilizan. El 403 ya existe (`SinPermiso`, CHG-12).
- `LibroNoEncontrado` **no** hereda de `Conflicto`: en la reposición el libro es el recurso de la ruta (404, sin `try` en el servicio); CHG-16 la atrapa y relanza `Conflicto("El libro indicado no existe.")` (409, C-12). Las tres de 409 heredan de `Conflicto`, así el handler existente las responde sin código nuevo y CHG-16 no tiene que traducirlas.
- Todos los mensajes terminan en punto, como el resto del proyecto; los tests fijan el texto exacto.

### D5. `usuario_id` de los movimientos: el ADMIN que devuelve `requiere_rol`

`POST /libros` y `POST /libros/{id}/reponer` declaran `usuario: UsuarioAdmin` (`Annotated[UsuarioActual, Depends(SOLO_ADMIN)]`) y pasan `usuario.id` (un `int`) al servicio; en `POST /libros` reemplaza a `dependencies=[Depends(SOLO_ADMIN)]` (misma dependencia, ahora con valor). Sin cookie válida → 401; sin `ADMIN` vigente → 403; con el cambio de contraseña pendiente → 403 (grupo protegido). En los tres casos no se escribe nada.

- `requiere_rol` y `get_usuario_actual` usan la misma sesión que el UoW (`get_session` cacheado por petición) y sus bloques cortos terminan antes que el del servicio: no hay UoW anidados ni una segunda conexión.
- `DELETE /libros/{id}` y `GET /libros/{id}/movimientos` no necesitan el usuario: llevan `dependencies=[Depends(SOLO_ADMIN)]`, como hoy `PATCH`.
- Alternativa descartada: un usuario fijo «sistema» (no existe en `usuario`, `usuario_id` es NOT NULL con FK, e inventaría una identidad).

### D6. Routers: se conservan `router_abierto` y `router`

Cada módulo del catálogo mantiene los nombres de CHG-12: `router_abierto` (GET públicos de la consigna: listados, detalle y sub-listados) y `router` (escrituras e historial, grupo protegido), con el mismo `prefix`/`tags`. `app/main.py` no cambia en el montaje (sólo suma el handler de `NoEncontrado`, D4).

Rutas nuevas, todas en `router` con `ADMIN` (consigna, tabla «Endpoints de referencia»: `DELETE /libros/{id}` ADMIN 204/404; `POST /libros/{id}/reponer` ADMIN 200/404/409/422; `GET /libros/{id}/movimientos` ADMIN 200/404):

| Ruta | Dependencia de rol | Entrada en `tests/matriz_acceso.py` |
|---|---|---|
| `DELETE /libros/{libro_id}` | `dependencies=[Depends(SOLO_ADMIN)]` | `("DELETE", "/libros/{libro_id}"): (PROTEGIDO, ADMIN)` |
| `POST /libros/{libro_id}/reponer` | `usuario: UsuarioAdmin` | `("POST", "/libros/{libro_id}/reponer"): (PROTEGIDO, ADMIN)` |
| `GET /libros/{libro_id}/movimientos` | `dependencies=[Depends(SOLO_ADMIN)]` | `("GET", "/libros/{libro_id}/movimientos"): (PROTEGIDO, ADMIN)` |

`GET /libros/{libro_id}/movimientos` es un GET en `router` (protegido), no en `router_abierto`: el catálogo público no incluye el historial. Al sumar las entradas a la matriz, `test_autorizacion_db.py` cubre solo el 401 sin cookie y el 403 de VENDEDOR y CLIENTE de las tres rutas; `test_grupos_de_rutas.py`, la clasificación y el control RN-06 montado una vez. La matriz es archivo de Matias (CHG-12): se modifica con su revisión en el PR 1.

Los routers usan alias `Annotated` (`LibrosUoWDep = Annotated[LibrosUoW, Depends(proveedor_uow(LibrosUoW))]`), `ParametrosPagina = Depends(paginacion_params)` y `response_model=Page[...]`; `DELETE` responde `Response(status_code=204)`.

### D7. Libros: alta, baja, reposición e historial

- **Alta**: `Libro(stock=0, **datos)` con sus `LibroAutor` → `uow.libros.add` (flush: FK/UNIQUE fallan acá como `IntegrityError` y el UoW los traduce al salir) → si `stock_inicial > 0`, `registrar_movimiento(libro.id, stock_inicial, "Stock inicial", usuario_id)` → `get_detalle(libro.id)` en el mismo bloque. El stock nunca se escribe en el constructor.
- **Baja**: `get_by_id` (vigente) → `None` → `LibroNoEncontrado`; si no, `soft_delete`. Una segunda baja es 404 porque el libro ya no es vigente (consigna: `DELETE` 204, 404).
- **PATCH**: `get_by_id` (vigente) → 404; `update(libro, datos.model_dump(exclude_unset=True))`; `get_detalle`.
- **Reposición**: `r = registrar_movimiento(libro_id, cantidad, motivo or "Reposición", usuario_id)` y, dentro del bloque, `ReposicionRead(libro_id=libro_id, stock=r.stock, movimiento=MovimientoStockRead.model_validate(r.movimiento))`. Sin consulta extra para el movimiento.
- **Historial**: `get_by_id_including_deleted` → `None` → `LibroNoEncontrado`; también para dados de baja (sus datos se conservan y el historial es de ADMIN). Envoltorio, orden por `id`.
- **Búsqueda**: `Libro.titulo.icontains(titulo, autoescape=True)` → `ILIKE` con parámetro ligado y `%`/`_` escapados (hoy `ilike(f"%{titulo}%")` los toma como comodines). `titulo` vacío o ausente = sin filtro.

### D8. Contratos (dueño Lauti, se avisa en el PR; visto bueno pendiente)

- `extra="forbid"` en `EditorialCreate`, `EditorialUpdate`, `GeneroCreate`, `AutorCreate`, `AutorUpdate` (faltaba: AGENTS §7 y Ej3 lo piden para todas las entradas; CHG-09b sólo cubrió libros, clientes y ventas). Va en el PR 2.
- `from_attributes=True` en `EditorialRead` y `GeneroRead` (como ya tienen `AutorRead` y `LibroRead`): sin eso `Page[EditorialRead](items=[<Editorial ORM>])` no valida. Va en el PR 2.
- Nuevos en `libros/schemas.py`: `MovimientoStockRead` (`id`, `libro_id`, `venta_id`, `usuario_id`, `cantidad`, `motivo`, `cuando`; `from_attributes`) y `ReposicionRead` (`libro_id`, `stock`, `movimiento: MovimientoStockRead`). Los usa el PR 1 (`ReposicionRead` es la respuesta de `/reponer` y la forma que Lauti usará en el `.http` de C-13, CHG-18). El docstring de `ReponerIn` («el endpoint llega con CHG-13») se actualiza.

### D9. Tests

- **Sesión de ADMIN**: se reutiliza lo que dejó CHG-12, sin fixtures nuevas: `entrar_como(client, sessionmaker_test, "ADMIN")` de `tests/auxiliares_auth.py` (devuelve el `usuario_id`, que los tests comparan con el `usuario_id` del movimiento) y la redefinición local de `client` que ya tienen los archivos de catálogo, ventas, clientes y seed. Los 401/403 por ruta los cubre la matriz (D6); los tests de libros sólo agregan los casos que miran escrituras (401/403 sin movimiento nuevo).
- Tests de repositorio contra la base para `registrar_movimiento` (incluye la regresión de `synchronize_session`, el `ResultadoMovimiento` con `cuando` cargado, el mensaje con stock real, el máximo de int32 y la concurrencia con dos sesiones: la primera hace el `UPDATE` sin confirmar, la segunda corre en una tarea y queda bloqueada, se confirma la primera y la segunda recibe `StockInsuficiente`; sin depender del orden de `gather`).
- Invariante `stock = SUM(cantidad)` verificado con SQL desde otra sesión después de alta, reposición y rechazo.
- `tests/test_catalogo_service.py` pierde los tests con sesión simulada (prueban la firma vieja); los conserva para `MENSAJES` (ahora en el UoW) y el armado del detalle.
- Inspección de código: ningún `service.py`/`repository.py`/`unit_of_work.py` de los cuatro módulos importa `HTTPException`, `commit_or_409` ni `app.core.pagination`.

### D10. Entrega en dos PRs (AGENTS §10)

| PR | Contenido | Fila de `PLAN_PARCIAL.md` |
|---|---|---|
| 1 · `refactor(libros)` | excepciones + handler 404, contratos de salida de libros, repositorios/UoW/servicio/router de libros, punto único con `ResultadoMovimiento`, alta con movimiento, baja, reposición, historial, búsqueda; tres entradas nuevas en `tests/matriz_acceso.py`; adaptación de los tests de libros | `en curso` |
| 2 · `refactor(editoriales/generos/autores)` | sus repositorios/UoW/servicios/routers, sub-listados vigentes, `extra="forbid"` y `from_attributes`, `AGENTS.md` §9, `openspec archive` | `mergeado (#N)` |

Libros va primero porque el punto único es lo que espera CHG-16 (P1) y lleva los archivos compartidos que Matias tiene que revisar (`errors.py`, `main.py`, `matriz_acceso.py`). Entre los dos PRs, `/editoriales/{id}/libros`, `/generos/{id}/libros` y `/autores/{id}/libros` siguen con el servicio viejo y todavía muestran libros dados de baja (R8). Si el equipo prefiere un solo PR, las tareas no cambian: se saltea el corte 1.

## Risks / Trade-offs

- **R1** `synchronize_session="fetch"` con `.returning()`: SQLAlchemy puede evaluar `stock + cantidad` en Python sobre el valor en memoria (correcto si estaba al día) o expirar el atributo, y leer un atributo expirado en async falla con `MissingGreenlet`. → Test de regresión: el `Libro` cargado en la sesión muestra el stock de `RETURNING` sin emitir consultas. Si falla, reemplazo local: `set_committed_value(libro, "stock", nuevo)` sobre la instancia del mapa de identidad (consultarlo con Matias).
  - **Aprobado por Matias en la revisión del #55 (2026-11-06):** `synchronize_session=False` + `set_committed_value` con el valor del `RETURNING`.
  - Advisor (FINAL_DIFF, 2026-11-06): recomienda **aprobar `set_committed_value`**. Razones: no deja historial ni estado sucio en el objeto; no hay actualización perdida porque el ORM nunca escribe `stock` desde memoria (el `UPDATE` es el único camino); funciona con `expire_on_commit=False`. Las alternativas (`populate_existing`, `refresh`, `expire`) son peores (consulta extra o `MissingGreenlet` en async). Estado: **pendiente de confirmación de Matias en la revisión del PR**.
  **Resultado (apply, 2026-11-06):** falló. Con `synchronize_session="fetch"` (y también con el `"auto"` por defecto) SQLAlchemy evalúa `stock + cantidad` en Python sobre el valor en memoria: si otra sesión cambió el stock antes (libro cargado con 2, otra sesión lo deja en 1, entrada de +4), la base da 5 y el objeto queda en 6. El test `test_el_libro_cargado_con_un_stock_viejo_queda_con_el_valor_de_la_base` lo fija. Se aplicó el reemplazo: `synchronize_session=False` y, si el `Libro` está en el mapa de identidad (`session.sync_session.identity_map.get(identity_key(Libro, libro_id))`), `attributes.set_committed_value(libro, "stock", <valor de RETURNING>)`. **Pendiente de visto bueno de Matias** (la tarea 4.6 lo pedía antes de aplicarlo).
- **R2** Deadlock entre ventas concurrentes con libros cruzados. → Docstring del orden por `libro_id`; lo aplica CHG-16 (hoy ventas ya ordena).
- **R3** Hasta CHG-16, `POST /ventas` descuenta stock sin movimiento y vende libros dados de baja: el invariante se rompe después de una venta. → Ningún test de CHG-13 verifica el invariante tras una venta; se anota en el PR. Lo cubre Matias en CHG-16 (confirmado 2026-11-06). Los tests de ventas existentes siguen verdes.
- **R4** **BREAKING** para clientes de la API: listados con envoltorio. → Los `.http` del TP quedan desactualizados hasta CHG-18 (se dice en el PR); el despliegue es otro proyecto y no cambia.
- **R5** `tests/matriz_acceso.py` es de CHG-12: si CHG-14 o CHG-16 agregan rutas en paralelo, los PRs chocan en el mismo diccionario. → Entradas agrupadas bajo un comentario `# CHG-13`; conflicto de merge trivial.
- **R6** `_contar` sobre una consulta con `joinedload` podría arrastrar el `JOIN` de la precarga a la subconsulta. → Conteos desde el helper de filtro sin `options` (D1).
- **R7** Mucha reescritura de tests existentes (listas → envoltorio, `limit` → `size`). → Cambios mecánicos en commits separados de los de comportamiento; la cantidad de casos no baja salvo los de `test_catalogo_service.py` con sesión simulada, que se reemplazan por tests con base.
- **R8** Entre PR1 y PR2, los sub-listados viejos muestran libros dados de baja. → Ventana corta; PR2 sigue inmediatamente.
- **R9** La consulta de diagnóstico corre después de un `UPDATE` fallido y puede ver un estado distinto si otra transacción cambió el libro entre medio. → Sólo afecta el texto del mensaje (el rechazo ya ocurrió y nada se escribió); se acepta.

## Migration Plan

Sin migraciones ni datos que migrar. Se despliega al mergear cada PR; se revierte con `git revert` del PR (el esquema no cambia). `scripts/seed.py` sigue escribiendo `libro.stock` sin movimientos hasta CHG-17; no lo usa ninguna ruta.

## Decisiones confirmadas (Matias, 2026-11-06)

1. **Desborde**: aprobado `stock <= INT32_MAX - cantidad` (con `INT32_MAX` de `app/core/tipos.py`) para entradas y `StockExcedido(Conflicto)` → 409 (D3.2, D4).
2. **Diagnóstico**: aprobada la lectura por columnas `select(Libro.stock, Libro.borrado_en)`, sólo en el camino de rechazo, con los cuatro casos: no existe (`LibroNoEncontrado` → 404), dado de baja, insuficiente o excedido según el signo de `cantidad` (D3.5).
3. **Valor de retorno**: `registrar_movimiento` devuelve `ResultadoMovimiento(stock, movimiento)` (dataclass congelada); se descarta `ultimo_de_libro` (D3, D7).
4. **Mensajes**: todos terminan en punto (D4).
5. **Routers**: se conservan `router_abierto` y `router`; no hay `router_protegido`. Toda ruta nueva entra en `tests/matriz_acceso.py` (D6).
6. **Sin paso intermedio de auth**: `requiere_rol` ya está; reponer, `DELETE` y movimientos van en `router` con `SOLO_ADMIN` (consigna), y el `usuario_id` sale de `UsuarioAdmin` con la misma sesión que el UoW. No hay fixture `sesion_iniciada`: se reutiliza `entrar_como` (D5, D9).
7. **Compartidos**: `NoEncontrado` + handler 404 y las subclases en `errors.py`/`main.py` aprobados; los revisa en el PR (D4).
8. **Entrega**: dos PRs; el PR 1 marca CHG-13 `en curso`, sólo el PR 2 pone `mergeado (#N)`, archiva y actualiza la Transición (D10).
9. **Ventas hasta CHG-16**: lo cubre Matias (R3).

## Open Questions

- **Lauti** (no bloquea el trabajo de libros del PR 1): visto bueno de los cambios en `schemas.py` (D8): `extra="forbid"` en las entradas de editoriales, géneros y autores, `from_attributes` en `EditorialRead`/`GeneroRead`, y los nuevos `MovimientoStockRead` y `ReposicionRead`. `ReposicionRead` ya lo usa el PR 1: si Lauti pide otra forma, cambian ese contrato, su test (3.1) y el de la reposición (6.9). Tarea 1.4.
