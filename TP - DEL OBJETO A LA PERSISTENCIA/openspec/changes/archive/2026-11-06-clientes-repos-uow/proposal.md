# Proposal

## Why

El módulo `clientes` sigue con el patrón del TP 1–4: el servicio recibe la `AsyncSession`, confirma con `commit_or_409` o con `commit()` a mano, lanza `HTTPException`, pagina con `limit`/`offset` (`app/core/pagination.py`) y devuelve listas sueltas; `GET /clientes/{id}/ventas` llama al servicio viejo de ventas con la misma sesión. Con CHG-04 (repositorios + UoW), CHG-05 (envoltorio), CHG-12 (grupos de rutas) y CHG-13 (patrón del catálogo y `NoEncontrado`) en `main`, CHG-15 pasa clientes y perfil a Router → Service → UoW → Repository (consigna: «todos los módulos pasan a repositorios + Unit of Work») y deja listo lo que CHG-16 (ventas, Matias) necesita de clientes: `ClienteRepository` y un `VentaRepository` con la precarga del detalle de venta.

## What Changes

- **Repositorios + UoW de `clientes`** (`repository.py` y `unit_of_work.py` nuevos): `ClienteRepository` (detalle con el perfil precargado dentro del método) y `PerfilClienteRepository` (su alta traduce la FK del cliente a «el cliente no existe», sin consultar antes); `ClientesUoW` compone `clientes`, `perfiles` y `ventas` con la misma sesión y declara sus `MENSAJES`. El servicio recibe el UoW y lo abre con `async with`; el router lo construye con `proveedor_uow`.
- **`VentaRepository` mínimo** en `app/modules/ventas/repository.py` (archivo nuevo, del módulo de Matias): la precarga del detalle de venta (cliente con `joinedload`; renglones con `selectinload` y el libro de cada renglón con `joinedload`, sin filtrar los dados de baja) y `listar_de_cliente` (en orden de `id`) / `contar_de_cliente` (sin precarga). CHG-16 lo extiende y lo compone en su `VentasUoW`.
- **`GET /clientes/{id}/ventas`** con el envoltorio `{items, total, page, size, pages}` de `VentaRead`, en orden de `id`, con un número fijo de consultas; 404 si el cliente no existe (antes de mirar la página). **BREAKING**: deja `limit`/`offset` y la lista suelta.
- **`GET /clientes`** (ruta del TP que se conserva, `PERSONAL`) con el envoltorio. **BREAKING**: igual que el anterior.
- **Errores de dominio**: `ClienteNoEncontrado(NoEncontrado)` («El cliente no existe.») y `CorreoConCuenta(Conflicto)` en `app/core/errors.py`, más el ayudante público `constraint_violada` para leer el nombre de la constraint violada (`mensaje_para` pasa a usarlo: una sola forma de leerlo). `clientes` deja de lanzar `HTTPException` y de usar `commit_or_409` y `pagination.py`.
- **Correo de un cliente con cuenta** (nuevo): `PATCH /clientes/{id}` que cambia el correo de un cliente con usuario vinculado (`usuario_id` no nulo) responde 409 «El correo de un cliente con cuenta no se puede cambiar.» sin cambiar nada; reenviar el mismo correo sí se acepta. Sin consulta extra: el `PATCH` ya lee el cliente. Evita que el correo del cliente y el del usuario queden distintos (el registro, RN-02, busca la ficha por correo).
- **Mensaje de 409 unificado**: `uq_cliente_email` responde «Ya existe un cliente con ese correo.» en `POST`/`PATCH /clientes`, el mismo texto que ya da el registro (C-02) y el que fija AGENTS §7. **BREAKING** para quien compare el texto viejo («... con ese email.»).
- **Registro (RN-02)**: `UsuariosUoW.clientes` pasa de `BaseRepository(session, Cliente)` a `ClienteRepository` (la línea que CHG-11 dejó marcada para este change); el registro no cambia de comportamiento.
- **Routers**: se conserva `router` con `PERSONAL` en cada ruta (CHG-12); no hay rutas nuevas, así que `tests/matriz_acceso.py` no cambia (las seis rutas de clientes ya están clasificadas). En el mismo PR se corrige la frase de la sección CHG-15 de `PLAN_PARCIAL.md` que dice que «suma las rutas nuevas a `tests/matriz_acceso.py`» (AGENTS §10, punto 3).

Fuera de alcance: `POST /ventas`, `GET /ventas`, `GET /ventas/{id}`, `/mis-ventas`, `ClienteRepository.get_por_usuario` y la comprobación de dueño (CHG-16, Matias; el dueño se mira por `Venta.cliente`); `PATCH` del perfil o baja de clientes (la consigna no los pide); cambiar `cliente.usuario_id` por la API; sincronizar `usuario.email` cuando se edita el correo del cliente (en su lugar, ese cambio se rechaza con 409); borrar `pagination.py`, `commit_or_409` y `traducir_integrity` (los sigue usando ventas hasta CHG-16); contratos nuevos (no hacen falta).

## Capabilities

### New Capabilities
- (ninguna)

### Modified Capabilities
- `clientes`: se agregan el alta, el detalle con perfil, el listado paginado, la edición parcial (con el 409 por el correo de un cliente con cuenta), el alta del perfil y el listado paginado de las ventas de un cliente, con sus 404, 409 y 422.
- `errores-de-dominio`: el requisito de módulos migrados sin errores HTTP en el negocio suma `clientes`.

## Impact

- **Código del change** (Nico): `app/modules/clientes/{repository,unit_of_work}.py` (nuevos), `service.py` y `router.py` reescritos; tests de clientes.
- **Archivos de Matias** (revisión en el PR): `app/modules/ventas/repository.py` (nuevo, mínimo), `app/modules/ventas/service.py` (sólo el nombre `_armar_lectura` → `armar_lectura` y sus usos: Matias reescribe ese archivo en CHG-16), `app/modules/usuarios/unit_of_work.py` (una línea), `app/core/errors.py` (`ClienteNoEncontrado`, `CorreoConCuenta` y `constraint_violada`). Plan: `PLAN_PARCIAL.md` (fila de CHG-15, frase de la matriz en su sección y lo que CHG-16 encuentra hecho). `app/main.py` y `tests/matriz_acceso.py` no cambian.
- **Contratos** (Lauti): sin cambios; `ClienteDetalleRead`, `PerfilRead` y `VentaRead` se usan tal como están.
- **API**: dos listados con otra forma, un texto de 409 distinto y un 409 nuevo (correo de un cliente con cuenta). Los `.http` del TP quedan desactualizados hasta CHG-18.
- **Base**: sin migraciones.
- **Entrega**: un solo PR (`refactor(clientes): repositorios y Unit of Work`) que pone CHG-15 en `mergeado (#N)`, archiva el change y actualiza la «Transición» de AGENTS §9.
- **Desbloquea**: CHG-16 (necesita CHG-15 según el plan).
- **Gobernanza**: MEDIUM (lógica de negocio); los archivos compartidos los revisa Matias.
