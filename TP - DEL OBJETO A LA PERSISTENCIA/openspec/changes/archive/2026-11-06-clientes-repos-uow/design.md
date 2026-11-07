# Design

## Context

- **Core listo** (CHG-04/05/13): `BaseRepository[T]` (`get_by_id` con `session.get`, `get_all`/`count`, `add`/`update` con `flush`, helpers `_consulta_base`, `_listar` —ordena por la PK— y `_contar`); `UnitOfWork` (confirma/revierte; un `IntegrityError` en el flush o en el commit → `Conflicto(mensaje_para(e, MENSAJES))`; otra excepción del bloque se re-lanza tal cual después del rollback; prohíbe anidar); `proveedor_uow`; `paginacion_params` → `ParametrosPagina` y `envolver(...)` (422 con `PeticionInvalida`); `NoEncontrado` (404) con su handler en `app/main.py`. `app/core/errors.py` tiene `mensaje_para` y el privado `_buscar_atributo` (el nombre de la constraint vive en `orig.__cause__` con asyncpg).
- **Patrón de referencia**: CHG-13 (`openspec/changes/archive/2026-11-06-catalogo-repos-uow/`): repositorio por entidad con métodos nombrados por lo que traen y la precarga adentro; UoW de módulo que compone repositorios de otro módulo cuando lo necesita (`EditorialesUoW.libros`); `MENSAJES` sólo en el UoW; el servicio arma el DTO dentro del bloque; `router`/`router_abierto` con alias `Annotated`; inspección AST en `tests/test_codigo_libros.py`.
- **Clientes hoy** (TP 1–4 con el router ya protegido por CHG-12): seis rutas en `router`, todas con `dependencies=[Depends(PERSONAL)]` y clasificadas en `tests/matriz_acceso.py` (`POST /`, `GET /`, `GET /{id}`, `PATCH /{id}`, `POST /{id}/perfil`, `GET /{id}/ventas`). El servicio recibe `AsyncSession`; `crear`/`actualizar` usan `commit_or_409` con «Ya existe un cliente con ese email.»; `crear_perfil` escribe sin consultar y distingue a mano la FK (404) del UNIQUE (409); `listar` y `listar_ventas_de_cliente` usan `limit`/`offset`; esta última delega en `ventas.service.listar(session, p, cliente_id=...)`, que precarga cliente y renglones+libro y arma `VentaRead` con el privado `_armar_lectura`.
- **Registro (CHG-11, Matias)**: `UsuariosUoW.clientes = BaseRepository(session, Cliente)` con el comentario «`ClienteRepository` es de CHG-15 (Nico), que cambia esta línea»; `UsuariosUoW.MENSAJES["uq_cliente_email"]` ya es «Ya existe un cliente con ese correo.» y `tests/test_auth_registro_db.py` lo fija (C-02).
- **Consigna** (tabla «Endpoints de referencia»): `POST /clientes` 201/409/422; `GET`, `PATCH /clientes/{id}` (con su perfil) 200/404/409/422; `POST /clientes/{id}/perfil` 201/404/409; `GET /clientes/{id}/ventas` 200/404; todas VENDEDOR o ADMIN. No lista `GET /clientes` (el TP lo tiene y CHG-12, D9, lo conservó con `PERSONAL`). Ej3: «Los listados devuelven el envoltorio»; Ej8: toda relación leída se precarga en el repositorio.
- **Contratos** (CHG-09b, Lauti): `ClienteCreate`/`ClienteUpdate`/`PerfilCreate` con `extra="forbid"`; `ClienteRead`, `PerfilRead` y `ClienteDetalleRead` (hereda `from_attributes`) alcanzan para validar desde el ORM. `VentaRead` no tiene `from_attributes` (el subtotal se calcula al armarlo).

## Goals / Non-Goals

**Goals:**
- `clientes` en Router → Service → UoW → Repository, sin `HTTPException`, `commit_or_409`, `traducir_integrity` ni `pagination.py`.
- Que CHG-16 encuentre `ClienteRepository`, `VentaRepository` (con la precarga del detalle) y `ClienteNoEncontrado` listos para componer su `VentasUoW`, `/mis-ventas` y el chequeo de dueño, sin rehacer nada de CHG-15.
- Un solo texto para el 409 de `uq_cliente_email` en toda la app.

**Non-Goals:**
- Migrar `ventas` (servicio, router, `POST /ventas`, `GET /ventas`): CHG-16. Sólo se agrega un archivo nuevo y se hace pública una función.
- Tocar `tests/matriz_acceso.py`, `app/main.py`, `requiere_rol` o los grupos: no hay rutas nuevas.
- Contratos nuevos o cambios de esquema.

## Decisions

### D1. Repositorios y UoW

| Archivo | Clase | Métodos (precarga / filtro adentro) |
|---|---|---|
| `clientes/repository.py` | `ClienteRepository(BaseRepository[Cliente])` | `get_detalle(id)`: `joinedload(Cliente.perfil)` + `populate_existing`; `None` si no existe. Listado: `get_all`/`count` heredados (`ClienteRead` no lee relaciones). |
| | `PerfilClienteRepository(BaseRepository[PerfilCliente])` | `add(perfil)` redefinido: ver D3. |
| `ventas/repository.py` (nuevo) | `VentaRepository(BaseRepository[Venta])` | `_con_detalle()`: `joinedload(Venta.cliente)`, `selectinload(Venta.renglones).joinedload(RenglonVenta.libro)`, **sin** filtro de borrado lógico sobre el libro (las ventas viejas muestran libros dados de baja); `listar_de_cliente(cliente_id, *, offset, limit)` (con `_con_detalle`, orden por `id` para páginas estables; lo agrega `_listar`) / `contar_de_cliente(cliente_id)` (**sin** precarga ni `options`, R6 de CHG-13). |

`ClientesUoW` (`clientes/unit_of_work.py`) compone `clientes`, `perfiles` y `ventas` con la misma sesión. `MENSAJES`:

| Constraint | Mensaje |
|---|---|
| `uq_cliente_email` | «Ya existe un cliente con ese correo.» |
| `uq_perfil_cliente_cliente_id` | «El cliente ya tiene un perfil.» |

No se agregan `uq_cliente_usuario_id` ni `fk_cliente_usuario_id_usuario`: ninguna entrada de clientes trae `usuario_id` (`extra="forbid"`), así que son inalcanzables desde este UoW. El de la FK del perfil no va acá: no es un 409 (D3).

- **`VentaRepository` en `ventas/`** y no una consulta de `Venta` dentro de `ClienteRepository`: AGENTS §5 pide un repositorio por entidad, y CHG-16 necesita esa misma precarga para el detalle de venta, `GET /ventas` y `/mis-ventas` (C-15). Es el mismo patrón de CHG-13 (`EditorialesUoW.libros`). El archivo es nuevo y mínimo: CHG-16 (Matias) le agrega `get_detalle`, el listado general y lo que necesite, sin conflicto de merge.
- Alternativa descartada: que `clientes` siga llamando a `ventas.service.listar(session, ...)` hasta CHG-16. Dejaría un servicio de clientes recibiendo la sesión y paginando con `limit`/`offset`, que es justo lo que este change elimina.
- Alternativa descartada: perfil por la relación (`cliente.perfil = PerfilCliente(...)` con cascade). Obliga a leer el cliente antes de escribir (D3).

### D2. Servicios

Funciones `async` que reciben `ClientesUoW` (y `ParametrosPagina` o el contrato) y abren un solo `async with uow:`; el DTO se arma dentro del bloque.

| Operación | Pasos |
|---|---|
| `crear` | `uow.clientes.add(Cliente(**datos.model_dump()))` → `ClienteRead`. UNIQUE → 409 por `MENSAJES`. |
| `listar` | `count()` + `get_all(offset, limit)` → `envolver([ClienteRead...])`. |
| `obtener` | `get_detalle(id)` → `None` → `ClienteNoEncontrado(id)`; si no, `ClienteDetalleRead.model_validate(cliente)` (el perfil ya está precargado; reemplaza al `_detalle` manual). |
| `actualizar` | `get_detalle` → 404; `cambios = datos.model_dump(exclude_unset=True)`; si el correo cambia y el cliente tiene cuenta → `CorreoConCuenta` (D10); si no, `uow.clientes.update(cliente, cambios)` → `ClienteDetalleRead`. Con `{}` el flush no emite nada. Correo repetido → 409 al salir del bloque. |
| `crear_perfil` | `uow.perfiles.add(PerfilCliente(cliente_id=id, **datos.model_dump()))` → `PerfilRead`. Sin lectura previa (D3). |
| `listar_ventas` | `get_by_id(id)` → `None` → `ClienteNoEncontrado` (el recurso de la ruta, antes de la página, igual que los sub-listados de CHG-13); `contar_de_cliente` + `listar_de_cliente` → `envolver([armar_lectura(v) ...])`. |

`armar_lectura` es el actual `ventas.service._armar_lectura` hecho público (sólo se le quita el guion bajo y se actualizan sus dos usos; nada más en ese archivo, que Matias reescribe en CHG-16, así no hay conflictos): el armado de `VentaRead` (subtotales, orden de renglones) queda en un solo lugar y CHG-16 lo sigue usando. Alternativa descartada: `from_attributes` + `computed_field` en `VentaRead` (cambio de contrato de Lauti y de la salida de ventas, fuera de alcance).

### D3. Perfil de un cliente inexistente: 404 sin consultar antes

AGENTS §8 prohíbe consultar si un id existe «para validar»: se escribe y la base decide. El perfil ya cumple eso hoy y se conserva:

- `PerfilClienteRepository.add` hace `session.add` + `flush` dentro de un `try` que envuelve **sólo el flush del perfil**, dentro del bloque del UoW: si el `IntegrityError` llegara sin atrapar al UoW, éste lo convertiría en 409 y la FK nunca daría 404. Si el `IntegrityError` es de `fk_perfil_cliente_cliente_id_cliente`, lanza `ClienteNoEncontrado(perfil.cliente_id)` `from None`; cualquier otro `IntegrityError` (el UNIQUE del segundo perfil) se re-lanza tal cual y el UoW lo traduce a 409.
- `ClienteNoEncontrado` no es `IntegrityError`: el UoW revierte y la deja pasar; el handler de `NoEncontrado` responde 404. Precedente: `LibroRepository.registrar_movimiento` lanza `LibroNoEncontrado` desde el repositorio (CHG-13, D3).
- El nombre de la constraint se lee con un ayudante público nuevo en `app/core/errors.py`, `constraint_violada(error: IntegrityError) -> str | None` (envuelve `_buscar_atributo(error, "constraint_name")`; `mensaje_para` pasa a usarlo internamente, así hay una sola forma de leer el nombre de la constraint). Reemplaza el truco actual `mensaje_para(e, {FK: msg}, default="") == msg`.
- Alternativa descartada: leer el cliente con `get_by_id` y después escribir. Es una consulta más en el camino feliz y una «validación previa» que el proyecto evita; la ventaja (no tocar `errors.py`) no compensa.
- Alternativa descartada: atrapar el `IntegrityError` en el servicio. Pondría SQLAlchemy y nombres de constraints en el servicio, que hoy sólo conoce el UoW y excepciones de dominio.

### D4. Excepciones de dominio (`app/core/errors.py`, revisa Matias)

```python
class ClienteNoEncontrado(NoEncontrado):   # cliente_id; «El cliente no existe.»
class CorreoConCuenta(Conflicto):          # cliente_id; «El correo de un cliente con cuenta no se puede cambiar.»
def constraint_violada(error: IntegrityError) -> str | None: ...
```

`ClienteNoEncontrado` la usan las cuatro rutas de clientes con id; `CorreoConCuenta`, el `PATCH` (D10), con el mismo patrón que `LibroDadoDeBaja(Conflicto)`. CHG-16 puede reutilizar `ClienteNoEncontrado` (por ejemplo, si `/mis-ventas` decide qué hacer con un usuario sin ficha de cliente), igual que `LibroNoEncontrado`. Mensaje con punto final, como el resto.

### D5. Mensaje de `uq_cliente_email` unificado

El registro (RN-02, C-02) responde «Ya existe un cliente con ese correo.» y AGENTS §7 usa ese texto de ejemplo; clientes respondía «... con ese email.». `ClientesUoW.MENSAJES` toma el de la consigna/registro. Los dos textos quedan fijados por tests: el existente del registro y uno nuevo que compara `ClientesUoW.MENSAJES["uq_cliente_email"] == UsuariosUoW.MENSAJES["uq_cliente_email"]`. **BREAKING** de texto, anotado en el PR.

### D6. Registro: `UsuariosUoW.clientes` con `ClienteRepository`

Se cambia sólo la línea marcada por CHG-11 (`self.clientes = ClienteRepository(session)`) y se borra su comentario. `registrar` usa `add`, que `ClienteRepository` hereda sin cambios: el comportamiento de RN-02 no cambia (sus tests siguen verdes sin tocarlos). `UsuariosUoW.MENSAJES` no se toca. El archivo es de Matias: se avisa en el PR.

### D7. Router

`router` (mismo nombre, prefijo y tags) con `ClientesUoWDep = Annotated[ClientesUoW, Depends(proveedor_uow(ClientesUoW))]`, `ParametrosPagina` por `Depends(paginacion_params)`, `response_model=Page[ClienteRead]` y `Page[VentaRead]` en los dos listados, y `dependencies=[Depends(PERSONAL)]` en cada ruta como hoy. Sin `AsyncSession`, `get_session` ni `app.core.pagination`. `tests/matriz_acceso.py` no cambia; `test_grupos_de_rutas.py` y `test_autorizacion_db.py` siguen cubriendo 401/403 de las seis rutas.

### D8. Tests

- Nuevo `tests/test_clientes_repository_db.py` (marca `db`): `get_detalle` con el perfil leído sin consultas extra (contador `before_cursor_execute` = 0 al leer `cliente.perfil`) y `None` si no existe; `PerfilClienteRepository.add` con cliente inexistente → `ClienteNoEncontrado` y 0 perfiles; segundo perfil dentro de `ClientesUoW` → `Conflicto` «El cliente ya tiene un perfil.»; `VentaRepository.listar_de_cliente`/`contar_de_cliente` (filtro, orden, `contar` igual con `limit=1`); `ClientesUoW` compone los tres repositorios con la misma sesión; `UsuariosUoW(session).clientes` es `ClienteRepository`; ningún repositorio confirma (espía de `commit`).
- `tests/test_errores_dominio.py`: `ClienteNoEncontrado(7)` es `NoEncontrado`, no `Conflicto`, guarda `cliente_id`, mensaje «El cliente no existe.»; `CorreoConCuenta(3)` es `Conflicto`, guarda `cliente_id`, mensaje «El correo de un cliente con cuenta no se puede cambiar.»; `constraint_violada` devuelve el nombre para un `IntegrityError` real (con base) y `None` para uno sin constraint.
- `tests/test_clientes_db.py`: listas → envoltorio, `limit`/`offset` → `page`/`size` (y `limit=1` ya no pagina), «email» → «correo»; casos nuevos de la spec (página fuera de rango, `usuario_id` en el cuerpo → 422, ventas de inexistente con `page=5` → 404, libro dado de baja en una venta vieja, `PATCH` del correo de un cliente con cuenta → 409 sin cambios en cliente ni usuario y mismo correo → 200 (D10), misma cantidad de consultas en `GET /clientes/{id}/ventas` con 1×1 y 3×2 ventas×renglones). Las ventas de prueba se crean por `POST /ventas` (sigue el servicio viejo hasta CHG-16).
- `tests/test_codigo_libros.py`: se agrega `clientes` a la inspección AST (sin `HTTPException`, `commit_or_409`, `traducir_integrity`, `app.core.pagination`, `commit` en servicio/repositorio, `MENSAJES` sólo en el UoW, router sin `AsyncSession`/`get_session`, servicio sin `AsyncSession`), con una lista `MIGRADOS = CATALOGO + ["clientes"]` y el docstring actualizado.

### D9. Entrega

Un solo PR desde `feat/clientes-repos-uow` (el plan lo marca chico), commit principal `refactor(clientes): repositorios y Unit of Work`; los ajustes mecánicos de tests en commits `test(clientes): ...` propios. El PR trae la fila de CHG-15 en `mergeado (#N)`, `openspec archive clientes-repos-uow` y la «Transición» de AGENTS §9 (filas de servicios con sesión, `pagination.py`, `commit_or_409`/`traducir_integrity` —quedan sólo para ventas— y routers), más en `PLAN_PARCIAL.md`: en la sección CHG-15, la frase «suma las rutas nuevas a `tests/matriz_acceso.py`» se corrige (no hay rutas nuevas; AGENTS §10, punto 3), y en la sección CHG-16 lo que ya existe: `VentaRepository` con `_con_detalle`, `listar_de_cliente`/`contar_de_cliente`, `armar_lectura` público y `ClienteNoEncontrado`.

### D10. Correo de un cliente con cuenta: 409

Un cliente con usuario vinculado (`usuario_id` no nulo, p. ej. Ana del seed) no puede cambiar su correo por `PATCH /clientes/{id}`: 409 `CorreoConCuenta` con «El correo de un cliente con cuenta no se puede cambiar.», sin escribir nada (tampoco el `nombre` que viniera en el mismo cuerpo).

- **Por qué** (Matias, 2026-11-06): sincronizar obligaría a `clientes` a escribir `usuario` y a manejar `uq_usuario_email`; dejarlos distintos rompe RN-02 (el registro busca la ficha del cliente por correo). Rechazarlo es lo más chico y no deja datos inconsistentes.
- **Cuándo**: sólo si el `PATCH` trae `email` **y** es distinto del guardado (comparación exacta con `cliente.email`). Reenviar el mismo correo se acepta (200, sin cambios): el `PATCH` es idempotente y nada queda distinto. Sin `email` en el cuerpo (sólo `nombre`) se acepta. Un cliente sin cuenta cambia su correo como siempre.
- **Sin consulta extra**: `actualizar` ya lee el cliente con `get_detalle` para el 404; la regla mira `cliente.usuario_id` de esa lectura. No es una «validación previa» de existencia (AGENTS §8): es una regla de negocio sobre una fila ya leída.
- **Dónde**: en el servicio, dentro del bloque y antes de `update`; `CorreoConCuenta` no es `IntegrityError`, el UoW revierte y la re-lanza, y el handler de `Conflicto` de `app/main.py` responde 409. El texto vive en la excepción (`errors.py`), no en `MENSAJES` (que son sólo de constraints).
- Alternativas descartadas: sincronizar `usuario.email` (ver arriba); permitirlo y anotarlo como riesgo (el riesgo que antes figuraba como R4).

## Risks / Trade-offs

- **R1** `ventas/repository.py` y `ventas/service.py` son de Matias y CHG-16 los va a reescribir → archivo nuevo mínimo y un solo renombre (confirmado por Matias); se le avisa antes de abrir el PR para que CHG-16 parta de `main` con esto.
- **R2** Atrapar `IntegrityError` en el flush del repositorio deja la transacción abortada → se lanza enseguida una excepción que no es `IntegrityError`; el UoW revierte al salir. Test: después del 404, un bloque sucesivo con la misma sesión escribe bien.
- **R3** **BREAKING** de API (dos listados con envoltorio, texto del 409) → los `.http` del TP quedan desactualizados hasta CHG-18; se dice en el PR.
- **R4** `populate_existing` en `get_detalle` pisa cambios no confirmados del mismo objeto si se llamara después de modificarlo → el servicio siempre lee antes de `update` y nunca después dentro del mismo bloque.
- **R5** `ventas.service.listar(..., cliente_id=)` queda sin uso desde clientes → no se borra (es de CHG-16); se anota en `PLAN_PARCIAL.md`.

## Migration Plan

Sin migraciones ni datos que migrar. Se despliega al mergear el PR y se revierte con `git revert` (el esquema no cambia). `seed.py` (raíz, CHG-17) no cambia: carga clientes por ORM directo, sin el servicio de clientes.

## Decisiones confirmadas (Matias, 2026-11-06)

- **(a)** `VentaRepository` mínimo en `ventas/repository.py` y `armar_lectura` público: sí. `_con_detalle` con `joinedload(Venta.cliente)` y `selectinload(Venta.renglones).joinedload(RenglonVenta.libro)`, sin filtro de borrado lógico; `listar_de_cliente` por `id`; `contar_de_cliente` sin precarga. En `ventas/service.py` sólo el nombre y sus usos (D1, D2, R1).
- **(b)** `ClienteNoEncontrado(NoEncontrado)` y `constraint_violada` público en `errors.py`: sí; `mensaje_para` lo usa adentro. El `IntegrityError` se atrapa alrededor del flush del perfil, dentro del bloque del UoW (D3, D4).
- **(c)** `UsuariosUoW.clientes → ClienteRepository`: sí (D6).
- **(d)** `ClienteRepository.get_por_usuario`: **no** en CHG-15; lo agrega Matias en CHG-16 con `/mis-ventas`. El chequeo de dueño usa `Venta.cliente`.
- **(e)** Nuevo: el `PATCH` que cambia el correo de un cliente con cuenta → 409 (D10). Resuelve el riesgo que antes figuraba como R4.
- **(f)** Mensaje «correo» unificado y envoltorio en los dos listados: sí. Sin rutas nuevas: en el mismo PR se corrige la frase de la matriz en la sección CHG-15 de `PLAN_PARCIAL.md` (D9).
- **Lauti** (2026-11-06, tarea 1.4): sin cambios de contratos; el listado de ventas de un cliente devuelve `VentaRead` completo (con renglones); `ClienteDetalleRead` sin `usuario_id`; `GET /clientes` con `page`/`size`; 409 «Ya existe un cliente con ese correo.». Él actualiza los `.http` en CHG-18.

## Open Questions

- Ninguna abierta para este change. Si más adelante el equipo quiere que un cliente con cuenta pueda cambiar su correo (sincronizando `usuario.email`), sería un change propio que reemplace D10.
