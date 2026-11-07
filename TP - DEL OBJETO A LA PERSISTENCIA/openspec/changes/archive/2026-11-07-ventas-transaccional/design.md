# Design

## Context

- **Core listo** (CHG-04/05/12/13/14/15): `UnitOfWork` (confirma al salir; ante una excepción revierte; un `IntegrityError` en el flush o el commit → `Conflicto(mensaje_para(e, MENSAJES))`; otra excepción se re-lanza tal cual; prohíbe anidar bloques sobre la misma sesión); `BaseRepository[T]` (`get_by_id`, `get_all`/`count`, `add`/`update` con flush, helpers `_consulta_base`, `_listar` —ordena por PK— y `_contar`); `proveedor_uow`; `paginacion_params` → `ParametrosPagina` y `envolver(...)` (422 con `PeticionInvalida`); excepciones de dominio `Conflicto`, `NoEncontrado`, `SinPermiso`, `LibroNoEncontrado` (404, no conflicto), `LibroDadoDeBaja`/`StockInsuficiente`/`StockExcedido` (409), `ClienteNoEncontrado`; `get_usuario_actual` (devuelve `UsuarioActual` con valores simples), `requiere_rol`, `PERSONAL = requiere_rol("VENDEDOR", "ADMIN")`, alias `UsuarioPersonal`; `AsignacionRolRepository.roles_vigentes(usuario_id)` (lee la base con `now()`).
- **Punto único de stock** (CHG-13): `LibroRepository.registrar_movimiento(libro_id, cantidad, motivo, usuario_id, venta_id=None) -> ResultadoMovimiento(stock, movimiento)`: un `UPDATE libro ... WHERE id = :id AND borrado_en IS NULL AND <límite> RETURNING stock`, y si no alcanza filas, una lectura que decide la excepción. Docstring: quien registra varias líneas MUST llamar en orden ascendente de `libro_id` (orden de bloqueos). El seed (CHG-17) ya lo usa para la venta 1 con `MOTIVO_VENTA = "Venta"` y comenta que CHG-16 MUST usar el mismo literal.
- **Ventas hoy** (TP 1–4): `service.crear(session, datos)` hace un `UPDATE ... RETURNING precio` propio por renglón (sin movimiento, sin mirar `borrado_en`), maneja a mano el rollback, usa `traducir_integrity` y atrapa `DBAPIError` 22003 para el total fuera de `Numeric(12,2)`; `obtener`/`listar` reciben la sesión, `listar` pagina con `app/core/pagination.py` y acepta un `cliente_id` que ya nadie usa. `router.py` tiene las tres rutas con `PERSONAL` (la de detalle, provisoria) y agenda `avisar_comprobante` (logger `uvicorn.error`) después del servicio.
- **Ya existe por CHG-15**: `VentaRepository` con `_con_detalle` (`joinedload(cliente)` + `selectinload(renglones).joinedload(libro)`, sin filtro de baja), `listar_de_cliente`/`contar_de_cliente`; `armar_lectura(venta) -> VentaRead` público; `ClienteRepository` (`get_detalle`). Falta `get_por_usuario`.
- **Últimos usuarios de lo viejo**: `ventas` es el único que importa `app/core/pagination.py`, `commit_or_409` y `traducir_integrity` (`git grep` sobre `app/`); fuera de `app/` sólo los usan sus propios tests (`tests/test_pagination.py`, parte de `tests/test_errors.py`). `_buscar_atributo` se queda: lo usan `constraint_violada`/`mensaje_para` y dos tests de esquema.
- **Consigna** (pág. 18): `POST /ventas` VENDEDOR/ADMIN 201/409/422; `GET /ventas` VENDEDOR/ADMIN 200/422; `GET /ventas/{id}` «el personal, o el cliente dueño» 200/403/404; `GET /mis-ventas` autenticado 200/422. «La decisión la toma el servicio: primero quién es y qué relación tiene con la venta (403 si no es ni personal ni dueño), y recién después qué se devuelve.»
- **Tests de autorización**: `tests/test_autorizacion_db.py` recorre la matriz (401 sin cookie en todo lo protegido; 403 por rol en lo que tiene `frozenset`); `consultas_de` en `tests/test_ventas_db.py` descuenta exactamente dos lecturas de autorización (`FROM usuario` y `FROM asignacion_rol`).

## Goals / Non-Goals

**Goals:**
- `ventas` en Router → Service → UoW → Repository: el servicio recibe el `VentasUoW`, el registro es un solo bloque, el stock pasa sólo por el punto único y nada del negocio conoce HTTP.
- Retirar `app/core/pagination.py`, `commit_or_409` y `traducir_integrity` con su último consumidor.
- Dejar listo para CHG-19 el comportamiento que va a verificar (stock = suma de movimientos tras cada venta, atomicidad de RN-10, conteo de C-15).

**Non-Goals:**
- Cambios de esquema o migraciones (no se agrega `venta.usuario_id`: quién registró la venta queda en `movimiento_stock.usuario_id`, igual que en el seed).
- Contratos nuevos de entrada: `VentaCreate`/`RenglonCreate` ya cumplen RN-09 (CHG-09b). La salida sigue siendo `VentaRead`; los listados usan `Page[VentaRead]`.
- Concurrencia (fuera de la consigna): se conserva el orden ascendente de bloqueos, pero no se agregan tests concurrentes nuevos.
- Archivos `.http` (CHG-18) y evidencia de consola de C-15 (CHG-20).

## Decisions

### D1. `VentasUoW` y repositorios

`app/modules/ventas/unit_of_work.py`, construido sólo con `(session)`:

| Atributo | Repositorio | Para qué |
|---|---|---|
| `ventas` | `VentaRepository` | alta, detalle, listados |
| `libros` | `LibroRepository` (módulo `libros`) | `registrar_movimiento` |
| `clientes` | `ClienteRepository` (módulo `clientes`) | `get_por_usuario` para `/mis-ventas` |
| `asignaciones` | `AsignacionRolRepository` (módulo `usuarios`) | roles vigentes para el detalle |

`MENSAJES`: `fk_venta_cliente_id_cliente` → «El cliente indicado no existe.»; `fk_renglon_venta_libro_id_libro` → «El libro indicado no existe.» (defensa: el punto único ya rechazó el libro antes de insertar renglones). Es el mismo patrón de composición entre módulos que `ClientesUoW.ventas` y `EditorialesUoW.libros`.

`VentaRepository` suma (precarga adentro de cada método, AGENTS §5):
- `get_detalle(venta_id) -> Venta | None`: `_con_detalle` + `where(id)` + `populate_existing` (recién creada, la venta y sus renglones están en el mapa de identidad; sin esto la precarga se saltea).
- `listar(*, offset, limit) -> list[Venta]` con `_con_detalle` y orden por `id` (vía `_listar`); el total con `count()` heredado (sin precarga).

`ClienteRepository.get_por_usuario(usuario_id) -> Cliente | None` (una consulta por `cliente.usuario_id`, UNIQUE).

### D2. Registro de la venta: un bloque, orden de escrituras

`service.crear(uow, datos, usuario_id) -> VentaRead`; `usuario_id` es un `int` tomado del `UsuarioPersonal` antes de abrir el bloque (advertencia de `core/unit_of_work.py`: tras un rollback los objetos ORM expiran).

Dentro de `async with uow:`
1. `venta = await uow.ventas.add(Venta(cliente_id=..., fecha=now(UTC), total=0, renglones=[]))`. El flush da el `id` que llevan los movimientos y hace saltar la FK del cliente (→ `Conflicto` por `MENSAJES`) antes de tocar ningún stock. `renglones=[]` explícito: la colección queda inicializada y agregarle renglones después no dispara una carga perezosa.
2. Por cada renglón **en orden ascendente de `libro_id`**: `uow.libros.registrar_movimiento(libro_id, -cantidad, MOTIVO_VENTA, usuario_id, venta_id=venta.id)`. `LibroNoEncontrado` se atrapa y se relanza como `LibroInexistenteEnVenta` (D4); `LibroDadoDeBaja` y `StockInsuficiente` ya son `Conflicto` y salen tal cual. El precio sale del resultado (D3).
3. Renglones en el **orden de entrada** (los `id` crecientes preservan el orden de la respuesta, como hoy), subtotal `(precio * cantidad).quantize(0.01)` y total como suma.
4. Si `total > TOTAL_MAXIMO` (`Decimal("9999999999.99")`, lo que entra en `Numeric(12,2)`) → `TotalExcedido` (D4), **antes** del flush: reemplaza el `except DBAPIError` 22003, que el UoW no traduce (no es `IntegrityError`) y terminaría en 500.
5. `uow.ventas.update(venta, {"total": total})` (flush de renglones y total) y `armar_lectura(await uow.ventas.get_detalle(venta.id))` **dentro** del bloque.

Cualquier excepción sale del bloque y el UoW revierte todo (venta, renglones, descuentos y movimientos): RN-10 sin rollback manual.

`MOTIVO_VENTA = "Venta"` vive en `ventas/service.py`; un test fija que es igual a `seed.MOTIVO_VENTA` (no se toca `seed.py`).

- Alternativa descartada: calcular primero los precios y el total y recién después escribir la venta. Obliga a leer los libros antes de escribir («consultar para validar», prohibido) y no da el `venta_id` que piden los movimientos.
- Alternativa descartada: conservar el `UPDATE ... RETURNING precio` propio de ventas. Es una segunda vía de escritura del stock (RN-11) sin movimiento.

### D3. El precio sale del punto único (pregunta Q1)

`registrar_movimiento` agrega `Libro.precio` a su `RETURNING` y `ResultadoMovimiento` gana el campo `precio: Decimal`. El precio se lee en la misma sentencia que bloquea la fila, así que es el vigente al vender y no hay una consulta más por venta. Los otros dos usuarios (alta y reposición en `libros`, y el seed) ignoran el campo: es compatible hacia atrás. Toca `app/modules/libros/repository.py` (de Nico): se le avisa en el PR.

- Alternativa: un método `LibroRepository.precios(ids) -> dict[int, Decimal]` llamado después de los movimientos (una consulta `WHERE id IN (...)`), sin tocar el punto único. Una consulta más y una lectura separada de la escritura; la fila ya está bloqueada por el `UPDATE`, así que el precio también sería el vigente.

### D4. Excepciones de dominio nuevas (`app/core/errors.py`)

| Excepción | Base | Mensaje | Dónde |
|---|---|---|---|
| `LibroInexistenteEnVenta(libro_id)` | `Conflicto` | «El libro indicado no existe.» | venta: traduce `LibroNoEncontrado` |
| `TotalExcedido()` | `Conflicto` | «El total de la venta supera el máximo permitido.» | venta, antes del flush del total |
| `VentaNoEncontrada(venta_id)` | `NoEncontrado` | «La venta no existe.» | detalle, sólo para el personal |

Los 409 por baja y por stock insuficiente usan el mensaje de las excepciones del punto único (pregunta Q5); el de cliente inexistente sale de `MENSAJES`. Los textos de reglas de negocio viven en la excepción, no en el servicio (`test_los_mensajes_de_409_viven_solo_en_el_uow`). El 403 usa `SinPermiso(MENSAJE_SIN_PERMISO)` de `dependencies.py`: el mismo cuerpo que `requiere_rol`, sin nombrar roles.

### D5. Detalle con control de dueño (preguntas Q2, Q3, Q6)

Router: `GET /ventas/{venta_id}` sin `dependencies=[Depends(PERSONAL)]`; recibe `usuario: Annotated[UsuarioActual, Depends(get_usuario_actual)]` (FastAPI la cachea: es la misma llamada que hizo el control del cambio obligatorio del grupo, sin consultas extra) y pasa `usuario.id` al servicio.

`service.obtener(uow, venta_id, usuario_id)`, en un bloque:
1. `roles = await uow.asignaciones.roles_vigentes(usuario_id)`; `personal = not ROLES_PERSONAL.isdisjoint(roles)`.
2. `venta = await uow.ventas.get_detalle(venta_id)`.
3. Si `personal`: `None` → `VentaNoEncontrada`; si no, se devuelve.
4. Si no es personal: si `venta is not None and venta.cliente.usuario_id == usuario_id` se devuelve; en cualquier otro caso (ajena **o inexistente**) → `SinPermiso`.

`ROLES_PERSONAL = frozenset({"VENDEDOR", "ADMIN"})` se exporta desde `app/core/dependencies.py` y `PERSONAL` pasa a construirse con ella: una sola definición de «personal» para la ruta y para el servicio.

La lectura de roles se hace siempre (también para el dueño): así las consultas de autorización son exactamente dos (`usuario` en `get_usuario_actual` y `asignacion_rol` en el servicio), como espera `consultas_de`, y la cantidad no depende de quién pide. El dueño se resuelve con `venta.cliente.usuario_id`, ya precargado por `_con_detalle`: cero consultas extra.

### D6. `/mis-ventas` (pregunta Q4)

Ruta en un segundo router del módulo, `router_propio = APIRouter(tags=["ventas"])` (sin el prefijo `/ventas`), con `GET /mis-ventas` → `Page[VentaRead]`; `app/main.py` lo incluye en `protegido`, sin rol (el grupo ya da 401 y el 403 de RN-06). `service.mis_ventas(uow, usuario_id, p)`: `cliente = await uow.clientes.get_por_usuario(usuario_id)`; sin cliente → `envolver([], total=0, ...)` (así `page=2` da 422 como cualquier listado vacío); con cliente → `contar_de_cliente` + `listar_de_cliente` (de CHG-15).

- Alternativa descartada: montar la ruta como `/ventas/mis` dentro del router existente. La consigna fija `/mis-ventas`.

### D7. Listado del personal y retiro de lo viejo

`GET /ventas/` → `Page[VentaRead]` con `paginacion_params`, conserva `PERSONAL`. `service.listar(uow, p)`: `count()` + `ventas.listar(offset, limit)` + `envolver`. Se borra el parámetro `cliente_id` (sin uso desde CHG-15).

Se borran `app/core/pagination.py`, `tests/test_pagination.py`, `commit_or_409` y `traducir_integrity` (y sus tests en `tests/test_errors.py`, conservando los de `mensaje_para`), y se actualizan los comentarios que los nombran en `app/core/unit_of_work.py` y `app/main.py` (la red de seguridad del `IntegrityError` se queda). `tests/test_codigo_libros.py` suma `ventas` a `MIGRADOS` y un test de que `app/core/pagination.py` no existe y `errors.py` no define los dos ayudantes.

### D8. Router y matriz

- `POST /ventas/`: `uow: VentasUoWDep`, `usuario: UsuarioPersonal` (reemplaza `dependencies=[Depends(PERSONAL)]`; la matriz lo sigue viendo como `PERSONAL` porque la dependencia de primer nivel es la misma función), `background_tasks`. Llama al servicio y **después** agenda `avisar_comprobante(venta.id, venta.cliente.email)`: si el servicio lanzó (incluido un commit fallido), la tarea nunca se agenda; BackgroundTasks la corre después de enviar la respuesta.
- `tests/matriz_acceso.py`: `("GET", "/ventas/{venta_id}") → (PROTEGIDO, AUTENTICADO)` (se borra el comentario «PROVISORIO (D8)») y `("GET", "/mis-ventas") → (PROTEGIDO, AUTENTICADO)`; docstring al día.

### D9. Tests existentes que cambian

`tests/test_ventas_db.py` es el contrato del TP; se ajusta en commits `test(ventas): ...` propios, antes del código que los pone en verde: listados al envoltorio (`page`/`size`), texto del stock insuficiente (Q5), el ya existente «libro inexistente» y «cliente inexistente» sin cambios, `consultas_de` sin cambios, y el test del orden ascendente de los `UPDATE libro` adaptado a la sentencia del punto único (el `libro_id` ya no es el último parámetro: se busca por posición del `WHERE` o se lee de los movimientos en orden de `id`).

## Risks / Trade-offs

- [Q1 toca un archivo de Nico (`libros/repository.py`)] → cambio aditivo de una línea de `RETURNING` y un campo; test propio en `tests/test_libros_stock_db.py`; aviso en el PR. Si no se acepta, la alternativa de D3 no cambia specs de `ventas` (sólo se cae el delta de `movimientos-stock`).
- [Textos de 409 distintos a los del TP] → **BREAKING** declarado; los `.http` se ajustan en CHG-18 y Lauti queda avisado.
- [Flush de la venta antes que los movimientos] → una venta con `total = 0` existe dentro de la transacción; nunca se confirma así porque el total se escribe antes de salir del bloque y cualquier fallo revierte. El CHECK `total >= 0` lo admite.
- [Orden de bloqueos] → el docstring del punto único lo exige; se conserva el test que verifica el orden ascendente de los `UPDATE libro`.
- [403 para un cliente con una venta inexistente] → el personal sí distingue 404; el cliente no puede enumerar ventas (Q2).
- [Borrar ayudantes de `core`] → `git grep` en `app/`, `tests/` y `seed.py` antes de borrar; la suite completa después.

## Migration Plan

Un solo PR desde `feat/ventas-transaccional` (sin migraciones). Rollback: revertir el merge; no hay datos que migrar. El seed sigue funcionando sin cambios.

## Decisiones a confirmar (antes de aplicar)

Las specs ya siguen la opción recomendada (primera de cada línea); cambiar alguna ajusta specs y tareas, por eso se confirman en la tarea 1.3.

- **Q1 · Precio del renglón**: (a, recomendada) `registrar_movimiento` devuelve también `precio` (delta en `movimientos-stock`, toca `libros/repository.py`) o (b) método `LibroRepository.precios(ids)` aparte, sin tocar el punto único.
- **Q2 · `GET /ventas/{id}` inexistente para quien no es personal**: (a, recomendada) 403, igual que una ajena: no revela qué ids existen y sigue «primero quién es y qué relación tiene»; (b) 404 para todos.
- **Q3 · Quién es el dueño**: (a, recomendada) el usuario vinculado al cliente de la venta (`cliente.usuario_id`), tenga o no `CLIENTE` vigente; (b) además exigir `CLIENTE` vigente (un cliente con el rol revocado dejaría de ver sus ventas, también en `/mis-ventas`).
- **Q4 · `/mis-ventas` sin cliente vinculado** (p. ej. un vendedor): (a, recomendada) 200 con envoltorio vacío (la consigna lista sólo 200/422); (b) 403.
- **Q5 · Texto de los 409 de stock y baja**: (a, recomendada) el de las excepciones del punto único («Stock insuficiente para el libro 5: hay 1, se pidieron 2.», «El libro 3 está dado de baja.»), igual que la reposición; (b) conservar «No hay stock suficiente para el libro indicado.» envolviendo `StockInsuficiente`.
- **Q6 · Definición de «personal»**: VENDEDOR o ADMIN vigente, con `ROLES_PERSONAL` exportada desde `app/core/dependencies.py` (archivo compartido) y usada por `PERSONAL` y por el servicio. Se asume confirmada salvo objeción.

## Decisiones confirmadas

Matias, 2026-11-07: acepta la opción (a) de Q1 a Q5 y Q6 tal como está. Specs y tareas no cambian. Pendiente avisar a Nico (Q1, `libros/repository.py`) y a Lauti (textos de 409 y envoltorio del listado, para CHG-18).
