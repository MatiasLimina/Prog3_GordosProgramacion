# Design

## Context

Motivación y alcance: ver `proposal.md`. Requisitos observables: `specs/alta-de-personal`, `specs/gestion-de-roles`, `specs/historial-de-seguridad` y los deltas de `grupos-de-rutas` y `contratos-auth-usuarios`.

Estado de `main` (**2f5a148**: CHG-03…13, CHG-15 —PR #58, mergeado— y CHG-17) que condiciona el enfoque. Re-baseline: el plan se escribió sobre de95cb9 con #58 abierto; `feat/usuarios-admin` ya está al día con `main` y todo lo condicional a #58 se quitó.

- **Modelos** (`usuarios/models.py`, CHG-06): `AsignacionRol` con `desde` (`server_default now()`), `vence_en` y `revocada_en` con zona, `otorgada_por` (FK a `usuario`, nullable), CHECK `ck_asignacion_rol_rol_valido` e índice único parcial `uq_asignacion_rol_usuario_rol_vigente` sobre `(usuario_id, rol) WHERE revocada_en IS NULL`. Ese índice **no mira `vence_en`**: una fila vencida pero no revocada sigue «abierta» y bloquea una nueva del mismo rol (por eso la consigna dice «cerrar la fila anterior»). `EventoSeguridad(cuando, actor, accion)`, `actor` y `accion` de hasta 255 caracteres.
- **Contratos** (`usuarios/schemas.py`, CHG-09a, de Lauti): ya existen `UsuarioCreate` (`email`, `nombre`, `password` ≤ 72 bytes, `extra="forbid"`, **sin rol**), `AsignacionRolCreate` (`rol` en `ADMIN`/`VENDEDOR`/`CLIENTE`, `vence_en` con zona y futuro → 422; genérico: no distingue roles), `UsuarioRead` (sin `password_hash`) y `AsignacionRolRead`. El literal de roles es privado (`_ROLES`) y lo usan `AsignacionRolCreate`, `AsignacionRolRead` y `AuthYoRead`. Falta la salida de `evento_seguridad`.
- **Repositorios y UoW** (CHG-11, CHG-15): `UsuarioRepository.get_by_email`, `AsignacionRolRepository.roles_vigentes` (reloj de la base), `EventoSeguridadRepository` sólo con lo heredado. `UsuariosUoW` compone `usuarios`, `asignaciones`, `intentos`, `eventos` y `clientes` (`ClienteRepository` desde CHG-15), y sus `MENSAJES` ya traen `uq_usuario_email` («Ya existe un usuario con ese correo.») y `uq_asignacion_rol_usuario_rol_vigente` («El usuario ya tiene ese rol vigente.»).
- **Errores** (`core/errors.py`, CHG-15 en `main`): el ayudante público `constraint_violada(error) -> str | None` (lo usa `mensaje_para`) y el patrón «FK violada en el `flush` → `NoEncontrado`» (`PerfilClienteRepository.add` → `ClienteNoEncontrado`). `ClienteNoEncontrado` y `CorreoConCuenta` están después de `StockExcedido`.
- **Convención de eventos** (CHG-11, cambio de contraseña): `actor` = correo de quien hace el cambio (o `SISTEMA`, seed), `accion` = frase corta en español.
- **Dependencias** (CHG-12): `SOLO_ADMIN` / `UsuarioAdmin` devuelven un `UsuarioActual` congelado con `id` y `email` como valores simples (sobreviven a un rollback). FastAPI cachea `SOLO_ADMIN` por petición: declararlo en el router y recibirlo como parámetro hace una sola lectura de roles.
- **Hash** (`core/security.py`, CHG-10): `hashear_password(password, *, costo, semaforo)` ya corre en `asyncio.to_thread` bajo el semáforo; `ParametrosSeguridad` lo entrega al servicio.
- **UoW base** (CHG-04): traduce cualquier `IntegrityError` a `Conflicto` (409) con `MENSAJES`; un rollback expira los objetos ORM de la sesión.
- **SQLAlchemy 2.1** con `eager_defaults="auto"` en los mapeos: en PostgreSQL el `INSERT` trae por `RETURNING` los valores por defecto del servidor (`desde`), así que tras el `flush` leer `desde` no dispara una consulta. (CHG-11 evitó leerlo por precaución; acá se comprueba con un test.)

### Discrepancias encontradas (gana la consigna)

1. **Ruta de la revocación**: `PLAN_PARCIAL.md` dice «`GET`, `POST` y `DELETE` de `/usuarios/{id}/roles`»; la tabla de la consigna es `DELETE /usuarios/{id}/roles/{rol}` (200, 404, 409). Se implementa la de la consigna y se corrige la línea de CHG-14 en `PLAN_PARCIAL.md` **en el mismo PR** (AGENTS §10; tarea 9.1). Confirmado por Matias.
2. **FK → 404, excepción explícita a AGENTS §8**: AGENTS §8 dice «se escribe y la base decide (FK … → 409)», pero la consigna da 404 a `POST /usuarios/{id}/roles` (el usuario es el recurso de la ruta). Gana la consigna: se escribe sin consulta previa (la base sigue decidiendo) y sólo la violación de **esa** FK (`fk_asignacion_rol_usuario_id_usuario`) se traduce a 404 `UsuarioNoEncontrado`, como CHG-15 con el perfil. Confirmado por Matias; el docstring de `asignar` lo dice.
3. **Códigos de `DELETE …/{rol}`**: la tabla no lista 422, pero un `{rol}` fuera del CHECK es una entrada inválida (D9). Tampoco lista 422 para `GET /usuarios/{id}/roles` y un `{id}` no entero ya es 422 por C-01: la columna «Códigos» no enumera la validación de la ruta.
4. **Alta de personal sin rol en el contrato**: la consigna dice «alta de personal, con contraseña provisoria» y no menciona el rol; `UsuarioCreate` (CHG-09a) no lo tiene. Ver D1 (confirmada).

## Goals / Non-Goals

**Goals:**
- Ninguna decisión de unicidad o existencia por consulta previa: la base decide (UNIQUE, índice parcial, FK) y las lecturas sólo eligen el mensaje **después** de una escritura fallida (como `LibroRepository._rechazar`).
- RN-05 correcto bajo concurrencia, no sólo en secuencia.
- Cada operación de RN-16 en **un** bloque `async with uow`, con el hash bcrypt fuera de él.
- No tocar `unit_of_work.py` ni los modelos: sin migración y sin cambios en lo que CHG-15 dejó en el UoW.

**Non-Goals:**
- Cambiar el vencimiento de una asignación vigente (se revoca y se reasigna).
- Desactivar usuarios, editar sus datos, resetear su contraseña.
- Normalizar mayúsculas del correo (anotado en CHG-11; sigue fuera).

## Decisions

### D1 · El alta de personal no asigna rol *(confirmado por Matias, 2026-11-07)*

`POST /usuarios/` usa `UsuarioCreate` tal cual: crea el usuario con `debe_cambiar_password=True`, **ninguna** asignación y su evento; el ADMIN le da el rol después con `POST /usuarios/{id}/roles`.

- **Por qué**: el contrato de CHG-09a ya se diseñó así para CHG-14; un único camino para dar roles (con `vence_en`, `otorgada_por` y su evento); RN-16 nombra «alta de personal» y «cambio de rol» como dos líneas distintas. Mientras no tenga rol, el usuario nuevo sólo puede usar `/auth` (y por RN-06, hasta cambiar la contraseña, tampoco otra cosa).
- Alternativa rechazada · `UsuarioCreate` con `rol` obligatorio: cambiaba el contrato de Lauti (**BREAKING**) y duplicaba la lógica de asignación.

### D2 · Actor y acción de los eventos *(confirmado por Matias, 2026-11-07)*

`actor` = `UsuarioActual.email` del ADMIN (valor simple tomado antes del bloque; la misma convención que `cambiar-password`). `accion`, con el **id** del usuario afectado y no su correo (un correo de 255 caracteres desbordaría `accion`):

| Operación | `accion` |
|---|---|
| Alta | `Alta de personal: usuario {id}` |
| Asignación (también la reasignación de un vencido) | `Asignación del rol {rol} al usuario {id}` |
| Revocación | `Revocación del rol {rol} al usuario {id}` |

Una sola línea por operación, dentro del mismo `async with uow`: cerrar la fila vencida y abrir la nueva es **un** cambio de rol. El evento se agrega **dentro** del bloque y después de la escritura que registra; si la escritura falla no se llega a agregarlo, y si el evento falla el UoW revierte todo.

- Alternativa · `actor` = `"usuario:<id>"`: no es la convención de CHG-11 ni la del seed (`SISTEMA` es texto). Rechazada.

### D3 · Asignar: cerrar el vencido con `revocada_en = vence_en` y dejar que el índice decida *(confirmado por Matias, 2026-11-07)*

```python
async def asignar_rol(uow, usuario_id, datos, actor) -> AsignacionRolRead:
    if datos.rol == "ADMIN" and datos.vence_en is not None:
        raise AdminConVencimiento()                                      # 422 (D3b), sin abrir el UoW
    async with uow:
        await uow.asignaciones.cerrar_vencida(usuario_id, datos.rol)       # UPDATE … SET revocada_en = vence_en
        asignacion = await uow.asignaciones.asignar(                       # add + flush
            AsignacionRol(usuario_id=usuario_id, rol=datos.rol, vence_en=datos.vence_en, otorgada_por=actor.id))
        await uow.eventos.add(EventoSeguridad(actor=actor.email, accion=f"Asignación del rol {datos.rol} al usuario {usuario_id}"))
        return AsignacionRolRead.model_validate(asignacion)
```

- `cerrar_vencida`: **una** sentencia `UPDATE asignacion_rol SET revocada_en = vence_en WHERE usuario_id = :u AND rol = :r AND revocada_en IS NULL AND vence_en IS NOT NULL AND vence_en <= now()` (reloj de la base, el mismo de `roles_vigentes`). No lee antes: si no hay fila vencida no toca nada.
- **`revocada_en = vence_en`, no `now()`**: nadie revocó esa asignación; dejó de valer cuando venció. Cerrarla con su propio vencimiento deja el historial fiel (la fila dice «valió hasta `vence_en`» y no inventa una revocación posterior) y `vence_en` no se toca.
- El filtro `vence_en <= now()` hace que una asignación **todavía vigente** no se toque: queda abierta, el `INSERT` choca con `uq_asignacion_rol_usuario_rol_vigente` → `IntegrityError` → el UoW lo traduce a 409 «El usuario ya tiene ese rol vigente.» (RN-03: «índice único parcial; 409»).
- Si el usuario **no existe**, el `INSERT` viola `fk_asignacion_rol_usuario_id_usuario`: `asignar` atrapa ese `IntegrityError` con `constraint_violada` y lanza `UsuarioNoEncontrado` (404), como `PerfilClienteRepository.add` en CHG-15; cualquier otra constraint se relanza para el UoW. Es la excepción explícita a AGENTS §8 (Discrepancia 2).
- **Concurrencia**: dos asignaciones iguales sin fila abierta → el índice deja pasar una y la otra espera y falla (409). Dos reasignaciones de un vencido → el `UPDATE` de la primera bloquea la fila; la segunda, al reevaluar el `WHERE` (READ COMMITTED), ya no la ve abierta, inserta y choca con la nueva → 409.
- `desde` sale cargado del `INSERT` (`eager_defaults="auto"`); un test lo verifica contando sentencias. Si no fuera así, `asignar` hace un `await session.refresh(asignacion)` explícito (no es carga perezosa).
- Alternativa · leer la fila abierta con `SELECT … FOR UPDATE` y decidir en Python vigente/vencida: dos sentencias, decide la aplicación lo que ya decide el índice, y no bloquea el caso «no hay fila». Rechazada.

### D3b · `ADMIN` no lleva vencimiento *(decisión de Matias, 2026-11-07)*

Asignar `ADMIN` con `vence_en` no nulo → 422 `AdminConVencimiento` (subclase de `PeticionInvalida`) con «El rol ADMIN no puede tener vencimiento.», sin abrir el UoW y sin escribir filas ni eventos. Asignar `ADMIN` sin `vence_en` sigue igual.

- **Dónde**: en el **servicio**, no en el contrato. `AsignacionRolCreate` es genérico (Lauti) y no distingue roles; la regla es de negocio (RN-05: que el sistema no pueda quedarse sin ADMIN por vencimiento) y el servicio es su lugar. Es una comparación pura antes del bloque, como la autorrevocación.
- Con esto deja de existir el riesgo «todos los ADMIN vencen»: un ADMIN asignado por API nunca vence, y el seed deja dos sin vencimiento.

### D4 · Revocar: un `UPDATE … RETURNING` y leer sólo si no tocó nada *(confirmado por Matias, 2026-11-07)*

```python
async def revocar_rol(uow, usuario_id, rol, actor) -> AsignacionRolRead:
    if rol == "ADMIN" and usuario_id == actor.id:
        raise AutoRevocacionAdmin()                                       # 409, RN-05 (sin abrir el UoW)
    async with uow:
        if rol == "ADMIN" and actor.id not in await uow.asignaciones.bloquear_admins_vigentes():
            raise SinPermiso(MENSAJE_SIN_PERMISO)                         # D5: FOR UPDATE ORDER BY id; el actor ya no es ADMIN -> 403
        revocada = await uow.asignaciones.revocar_vigente(usuario_id, rol)  # UPDATE … RETURNING
        if revocada is None:
            if await uow.usuarios.get_by_id(usuario_id) is None:
                raise UsuarioNoEncontrado(usuario_id)                     # 404
            raise RolNoVigente(usuario_id, rol)                           # 404
        if rol == "ADMIN" and await uow.asignaciones.contar_admins_vigentes() == 0:
            raise SinAdministradores()                                    # 409; el UoW revierte la revocación
        await uow.eventos.add(EventoSeguridad(actor=actor.email, accion=f"Revocación del rol {rol} al usuario {usuario_id}"))
        return revocada
```

- `revocar_vigente`: `UPDATE asignacion_rol SET revocada_en = now() WHERE usuario_id = :u AND rol = :r AND revocada_en IS NULL AND (vence_en IS NULL OR vence_en > now()) RETURNING <columnas>`; el contrato se arma con las columnas devueltas (no con un objeto ORM expirado). Es atómico: la base bloquea la fila y reevalúa el `WHERE` si otra transacción la cambió. Acá sí es `now()`: es una revocación real.
- **No vigente → 404 `RolNoVigente`**, también si la fila está abierta pero vencida: el recurso de la ruta («el rol vigente de ese usuario») no existe; no es un choque con lo guardado. La lectura de `get_by_id` corre sólo en el camino de rechazo, después de la escritura fallida (mismo criterio que `LibroRepository._rechazar`): elige el mensaje, no valida antes.
- `SinAdministradores` se lanza **dentro** del bloque y después de revocar: el UoW revierte el `UPDATE`, así que la respuesta 409 no deja escrito nada.
- Alternativa · 409 para «no vigente»: la consigna da 409 a la ruta, pero RN-05 ya lo explica; un rol inexistente no choca con nada. Rechazada.

### D5 · RN-05 sin carreras: bloquear las filas `ADMIN` vigentes y contar después *(confirmado por Matias, 2026-11-07)*

- **Autorrevocación**: comparación pura (`usuario_id == actor.id`), antes de abrir el UoW; `actor.id` es un `int`. 409 `AutoRevocacionAdmin`, nunca `SinPermiso`.
- **Nunca cero ADMIN**: con la autorrevocación prohibida, en secuencia la regla sólo se rompe si dos ADMIN se revocan **a la vez** (A revoca a B y B revoca a A): cada transacción ve su propia revocación y no la del otro (sin confirmar), cuenta 1 y confirma → 0 ADMIN (*write skew*).
- **Bloquear, traer y contar después**: `FOR UPDATE` no se puede combinar con `count()` en la misma consulta (PostgreSQL no admite `FOR UPDATE` con funciones de agregado). Por eso son dos pasos:
  1. `bloquear_admins_vigentes()`: `SELECT id, usuario_id FROM asignacion_rol WHERE rol = 'ADMIN' AND revocada_en IS NULL AND (vence_en IS NULL OR vence_en > now()) ORDER BY id FOR UPDATE`; trae las filas (las bloquea) y devuelve los `usuario_id`.
  2. Después de `revocar_vigente`, `contar_admins_vigentes()` (un `SELECT count(*)` común, sin bloqueo) en la misma transacción: ve la propia revocación y, como en READ COMMITTED cada sentencia toma una foto nueva, también lo que confirmó quien tenía el bloqueo. Si da 0 → `SinAdministradores`.
- **Cómo se resuelve la carrera**: la segunda transacción (B revoca a A) espera en el paso 1; cuando la primera (A revoca a B) confirma, la base reevalúa el `WHERE` y la fila de B queda afuera; la segunda revoca a A, cuenta 0 y responde 409, y el UoW revierte su `UPDATE`. Queda exactamente un ADMIN.
- **Carrera de autorización: el actor se comprueba contra las filas bloqueadas** *(hallazgo del advisor, 2026-11-07)*. `SOLO_ADMIN` verifica el `ADMIN` del actor en su propia transacción, ya confirmada, **antes** del bloque; la espera del `FOR UPDATE` puede ser larga. Con tres ADMIN, A revoca a B mientras B revoca a C: B ya pasó `SOLO_ADMIN`, espera en el paso 1 y, cuando A confirma, la base reevalúa el `WHERE` y devuelve las filas de A y C, no la de B. Sin más, B revocaría a C (queda A: el conteo da 1) y confirmaría: un usuario que ya no es administrador habría administrado. Solución: `bloquear_admins_vigentes()` ya devuelve los `usuario_id` de las filas bloqueadas (las que **todavía** son ADMIN vigente tras la espera); si `actor.id` no está entre ellos, `SinPermiso` (403, `MENSAJE_SIN_PERMISO`) dentro del bloque y el UoW revierte: no se escribe nada. Cuesta cero consultas. Efectos: (a) el cruce de dos ADMIN que se revocan entre sí termina para la perdedora en 403 y no en 409 «sin administradores» (spec actualizada); (b) con la comprobación el conteo del paso 2 no puede dar 0 (el actor sigue siendo ADMIN y no puede ser el objetivo), y se conserva como defensa en profundidad con su propio test (el bloqueo se simula devolviendo al actor).
- **`asignar_rol` no recibe la misma comprobación** *(decisión; riesgo documentado para Matias)*. La misma carrera existe en forma débil: B, revocado por A, podría asignar un rol si su INSERT corre justo después del commit de A. No se implementa porque (1) la ventana es la de cualquier ruta protegida —`SOLO_ADMIN` y la operación son transacciones distintas en el alta de personal, en la lectura de roles y en el resto de la API— y RN-04/C-07 sólo prometen que el cambio surte efecto en la petición siguiente; (2) en `revocar_rol` la ventana se estira a la duración del bloqueo y de ella depende el invariante RN-05, mientras que `asignar_rol` no toma ningún bloqueo de administradores y su espera (el índice único) es corta; (3) cerrarla exigiría una consulta extra por asignación (`SELECT … FOR SHARE` de la fila `ADMIN` vigente del actor) que, hecha sólo ahí, deja las demás rutas con la ventana abierta. Si se quiere cerrar en toda la API, el cambio correcto es de arquitectura (que `requiere_rol` y el servicio compartan transacción y la lectura de roles use `FOR SHARE`) y es de Matias (`dependencies.py`); queda fuera de CHG-14.
- **`ORDER BY id` se queda**: todas las transacciones toman los bloqueos de las filas en el mismo orden. Sin orden, una podría bloquear A y esperar B mientras otra bloquea B y espera A: un *deadlock* que PostgreSQL corta abortando una de las dos con un error (500), en lugar del 409 esperado.
- Sólo las revocaciones de `ADMIN` toman ese bloqueo; asignar `ADMIN` o revocar otros roles no lo necesita (no puede bajar la cantidad de ADMIN). `cerrar_vencida` sólo toca filas vencidas, que no están en el conjunto bloqueado.
- Si el objetivo no tiene `ADMIN` vigente, `revocar_vigente` no toca nada y da 404 antes de contar.
- **Alternativa A** · `pg_advisory_xact_lock(<clave fija>)`: serializa igual, pero agrega una clave mágica y no expresa qué se protege. Descartada por Matias. **Alternativa B** · `SERIALIZABLE`: exige reintentos y cambia el aislamiento de la sesión compartida con las dependencias. **Alternativa C** · contar después de revocar **sin** bloqueo: es exactamente el *write skew*. Rechazadas.
- «Vigente» cuenta asignaciones, no mira `usuario.activo` (confirmado por Matias; ver Riesgos).

### D6 · `GET /usuarios/{id}/roles`: historial completo, sin paginar

En un bloque: `uow.usuarios.get_by_id(id)` (404 `UsuarioNoEncontrado` si no existe; acá la lectura **es** la operación) y `uow.asignaciones.historial(id)` (todas las filas, orden por `id`). Lista de `AsignacionRolRead`, sin envoltorio: la tabla de la consigna sólo pagina `/eventos`, y el historial de un usuario es corto. Sin campo calculado `vigente` (cambiaría el contrato de Lauti; el cliente lo ve en `revocada_en`/`vence_en`, y `/auth/yo` da los vigentes).

### D7 · `GET /eventos/`: envoltorio y orden

`EventoSeguridadRepository.listar_recientes(offset, limit)` ordena por `cuando DESC, id DESC` (el `ORDER BY id` que agrega `_listar` queda como desempate redundante) y `count()` heredado da el `total`; el servicio usa `envolver` de `core/paginacion.py` (422 fuera de rango). Del más reciente al más viejo: es lo que un ADMIN quiere ver primero; dentro de una transacción `cuando` es igual para todas las líneas, por eso el desempate por `id`.

### D8 · Excepciones de dominio en `app/core/errors.py`

```python
class UsuarioNoEncontrado(NoEncontrado):      # usuario_id; «El usuario no existe.»
class RolNoVigente(NoEncontrado):             # usuario_id, rol; «El usuario no tiene ese rol vigente.»
class AutoRevocacionAdmin(Conflicto):         # «No podés revocarte tu propio rol de administrador.»
class SinAdministradores(Conflicto):          # «No se puede revocar: el sistema quedaría sin administradores vigentes.»
class AdminConVencimiento(PeticionInvalida):  # «El rol ADMIN no puede tener vencimiento.»
```

Handlers existentes (404/409/422): `main.py` no suma handlers. Se insertan **después de `DemasiadosIntentos`** (antes de `_buscar_atributo`), lejos de lo que agregó CHG-15 (`ClienteNoEncontrado` y `CorreoConCuenta`, después de `StockExcedido`).

### D9 · Router, montaje y matriz

- En `usuarios/router.py`, además de `auth_router`: `router = APIRouter(prefix="/usuarios", tags=["usuarios"], dependencies=[Depends(SOLO_ADMIN)])` y `eventos_router = APIRouter(prefix="/eventos", tags=["eventos"], dependencies=[Depends(SOLO_ADMIN)])`. Los handlers que necesitan al actor reciben `usuario: UsuarioAdmin` (misma función: FastAPI la resuelve una vez). `usuario_id: IdPath` (C-01: no entero → 422). `rol` de la ruta tipado con el literal público `Rol` de `schemas.py` → un rol desconocido es 422 por el tipo del parámetro, igual que en el cuerpo (confirmado por Matias).
- `POST /` → 201 `UsuarioRead`; `GET /{usuario_id}/roles` → `list[AsignacionRolRead]`; `POST /{usuario_id}/roles` → 201 `AsignacionRolRead`; `DELETE /{usuario_id}/roles/{rol}` → 200 `AsignacionRolRead`; `GET /eventos/` → `Page[EventoSeguridadRead]` con `paginacion_params`.
- `app/main.py`: `protegido.include_router(usuarios_router)` y `protegido.include_router(eventos_router)`; nada en el abierto.
- `tests/matriz_acceso.py`: `("POST", "/usuarios/")`, `("GET", "/usuarios/{usuario_id}/roles")`, `("POST", "/usuarios/{usuario_id}/roles")`, `("DELETE", "/usuarios/{usuario_id}/roles/{rol}")`, `("GET", "/eventos/")`, todas `(PROTEGIDO, ADMIN)`. `test_grupos_de_rutas.py` y `test_autorizacion_db.py` (401 sin cookie, 403 vendedor) las cubren sin cambios.

### D10 · Contratos *(dueño Lauti; confirmado por Lauti, 2026-11-07)*

Cambio chico en el archivo de Lauti (`usuarios/schemas.py`), aprobado por él:

- `EventoSeguridadRead(id, cuando, actor, accion)` con `from_attributes=True`, como los demás `*Read`. `GET /eventos/` devuelve el envoltorio de `app/core/paginacion.py` (`Page[EventoSeguridadRead]`).
- **Un solo nombre público para los roles**: `Rol = Literal["ADMIN", "VENDEDOR", "CLIENTE"]`, y `AsignacionRolCreate.rol`, `AsignacionRolRead.rol` y `AuthYoRead.roles_vigentes` / `roles_token` pasan a usar `Rol` (hoy usan el privado `_ROLES`). Si después de eso nada más usa `_ROLES`, se quita; si algo lo usa, queda `_ROLES = Rol` como alias interno. El router tipa el `{rol}` de la ruta con el mismo `Rol`: un rol fuera de la lista es 422 por el tipo, sin código propio.
- El comportamiento de los tres contratos no cambia: sus tests existentes siguen en verde y uno nuevo afirma que comparten el tipo `Rol`.
- `UsuarioCreate` no cambia (D1).

### D11 · Entrega

- Un **solo PR** `feat/usuarios-admin` → `main` (como CHG-15), con commits por tema (errores, alta, roles, eventos, montaje, casos, docs + archive).
- La rama parte de `main` 2f5a148, que ya trae CHG-15: se usa `constraint_violada` tal cual y no hay copia ni merge pendiente con #58. `usuarios/unit_of_work.py` no se toca.
- Si `main` avanza antes del cierre, `git merge origin/main`; conflictos esperables sólo en filas de la tabla de `PLAN_PARCIAL.md` y de `AGENTS.md` §9, que se resuelven conservando las dos.

### D12 · Tests

- `tests/test_usuarios_admin_db.py` (marca `db`): servicio y rutas de alta, roles y eventos según las specs; RN-16 en los dos sentidos (la operación rechazada no deja evento; un `EventoSeguridadRepository.add` que lanza revierte el alta, la asignación y la revocación).
- **Hash antes del UoW** (pedido de Matias, confirmado): se reemplaza `app.modules.usuarios.service.hashear_password` por un doble que anota `("hash", session.info.get("uow_activo"))` y delega en el real, y se envuelve `UsuariosUoW.__aenter__` para anotar `"aenter"`. Se exige el orden `hash → aenter`, que durante el hash la marca de UoW abierto sea falsa y que el semáforo recibido sea `app.state.semaforo_bcrypt`. Con un cuerpo inválido, 0 llamadas al hash.
- **Reasignación de un vencido**: la fila cerrada queda con `revocada_en == vence_en` (no `now()`); mutación de control: con `SET revocada_en = now()` el test falla.
- **`ADMIN` con vencimiento**: `AdminConVencimiento` sin abrir el UoW (espía de `__aenter__` sin llamadas) y sin filas ni eventos; por HTTP, 422 con el mensaje; `VENDEDOR` con el mismo `vence_en` sí se asigna.
- **Concurrencia determinista** (dos sesiones de `sessionmaker_test`, confirmado por Matias): la sesión 1 toma el bloqueo (`bloquear_admins_vigentes` + revocar a B) sin confirmar; se lanza en una tarea `revocar_rol` sobre la sesión 2 (B revoca a A) y se espera, **sin `sleep` fijo**, a que `pg_stat_activity` muestre el backend de la sesión 2 (su `pg_backend_pid()` se captura antes) en `wait_event_type = 'Lock'` (tope de 5 s; si la tarea termina sin haber esperado, el test falla enseguida); se confirma la 1 y la tarea termina con `SinPermiso` (B ya no es ADMIN, D5); queda 1 ADMIN vigente. Con tres ADMIN (A revoca a B mientras B revoca a C): `SinPermiso` y C sigue vigente. Igual para dos asignaciones simultáneas (la segunda espera al índice y termina en `Conflicto`). Mutaciones de control: sin `FOR UPDATE` el primero falla; sin la comprobación del actor fallan los de `SinPermiso`. El conteo final se ejercita simulando un bloqueo que devuelve al actor.
- **`desde` sin consulta extra**: contador `before_cursor_execute` en 0 al leer `asignacion.desde` tras `asignar`.
- **Casos**: `tests/test_casos_usuarios_db.py` con C-07 por API (dos cookies con `cabecera_cookie`, vendedor 201 → revocación 200 → vendedor 403 → `/auth/yo` con la diferencia → la fila sigue; `vence_en` pasado y sin zona → 422 sin filas) y C-08 (409, `ADMIN` sigue vigente, sin evento).
- `tests/test_usuarios_schemas.py`: `EventoSeguridadRead` (claves exactas, zona en `cuando`) y el tipo compartido `Rol` (las anotaciones de `AsignacionRolCreate.rol`, `AsignacionRolRead.rol` y `AuthYoRead.roles_vigentes`/`roles_token` usan `Rol`); los tests de contrato existentes siguen en verde sin cambios.
- `tests/test_codigo_libros.py` (inspección AST): si su lista de módulos migrados admite `usuarios` sin falsos positivos (el módulo tiene `IntentosUoW` y el login), se suma; si no, se anota y no se fuerza.

## Risks / Trade-offs

- [Un ADMIN inactivo cuenta como vigente para RN-05] → confirmado por Matias como hoy: ninguna ruta desactiva usuarios. Si una futura lo hace, `bloquear_admins_vigentes` y `contar_admins_vigentes` deben unir con `usuario.activo`.
- [El bloqueo `FOR UPDATE` serializa las revocaciones de `ADMIN`] → son raras y cortas; el resto de las operaciones no lo toma.
- [La reevaluación del `WHERE` bajo bloqueo y la foto nueva del conteo dependen de READ COMMITTED] → es el aislamiento por defecto de PostgreSQL y el de la fábrica de sesiones; el test de concurrencia lo fija.
- [`service.py` y `router.py` mezclan auth (Matias) y administración (Nico)] → la estructura obligatoria pide un archivo por capa y módulo; se agrega al final de cada archivo, con un comentario de sección, y Matias revisa el PR.
- [Un ADMIN revocado que ya pasó `SOLO_ADMIN` podría completar *otras* operaciones de administración] → en la revocación de `ADMIN` está cerrado (D5, comprobación del actor contra las filas bloqueadas); en `asignar_rol` y el alta es la ventana de milisegundos común a toda ruta protegida. Ver D5; la solución de fondo (lectura de roles con `FOR SHARE` en la transacción del servicio) es de Matias.
- [Un `ADMIN` con `vence_en` cargado antes de este change (a mano o por un seed futuro) igual puede vencer] → el seed actual no lo hace y la API ya no lo permite (D3b); queda fuera de alcance.

## Migration Plan

Sin migraciones ni cambios de datos. Despliegue: el del parcial (sólo código). Rollback: revertir el PR; las filas de `asignacion_rol` y `evento_seguridad` que se hayan creado son válidas con el código anterior.

## Decisiones confirmadas (Matias, 2026-11-07)

«Con esto podés implementar.»

1. **D1** alta sin rol: `POST /usuarios/` crea el usuario con `debe_cambiar_password=true` y su evento; el rol va después por `POST /usuarios/{id}/roles`.
2. **D2** `actor` = correo del ADMIN (igual que `cambiar-password`); `accion` con el id y los textos propuestos; una línea por operación dentro del mismo `async with uow`.
3. **D3** reasignar un vencido cierra la fila con `revocada_en = vence_en` (no `now()`); el `UPDATE` filtra `vence_en <= now()`, así una vigente no se toca y el índice parcial da 409. FK → 404 `UsuarioNoEncontrado`, como excepción explícita a AGENTS §8 (gana la consigna).
4. **D4** revocar un rol no vigente → 404 `RolNoVigente`.
5. **D5** RN-05 con `SELECT … FOR UPDATE ORDER BY id`, sin advisory lock; se bloquea y trae, y se cuenta **después** de revocar (`FOR UPDATE` no admite `count()`); `ORDER BY id` evita *deadlocks*. Test con dos sesiones.
6. **D9** `{rol}` desconocido → 422 por el tipo del parámetro.
7. **D3b** asignar `ADMIN` con `vence_en` → 422 `AdminConVencimiento` («El rol ADMIN no puede tener vencimiento.»), validado en el servicio, no en el contrato.
8. **RN-05 / Riesgos** un ADMIN inactivo cuenta como vigente, como hoy; queda como riesgo.
9. **D11** #58 mergeado: se parte de `main` con `constraint_violada`; las excepciones nuevas van lejos de las de CHG-15 en `errors.py`.
10. **D12** hash antes del UoW con su test de orden.
11. **Discrepancia 1** la ruta de la consigna `/usuarios/{id}/roles/{rol}` es la correcta; la línea de CHG-14 en `PLAN_PARCIAL.md` se corrige en el mismo PR.

## Decisiones confirmadas (Lauti, 2026-11-07)

1. **D10** `EventoSeguridadRead (id, cuando, actor, accion)` con `from_attributes=True`; `GET /eventos/` con el envoltorio de `core/paginacion.py`.
2. **D10** alias público `Rol`, usado también por `AsignacionRolCreate`, `AsignacionRolRead` y `AuthYoRead` (un solo nombre público); `{rol}` fuera de la lista → 422 por el tipo.
3. **D1** alta sin rol aceptada; `UsuarioCreate` sin cambios. Un usuario nuevo sin rol recibe 403 en todo lo protegido (esperado).
4. **CHG-18** C-07 y C-08 se pueden escribir por API; las rutas de `/usuarios` y `/eventos` entran en `tests/matriz_acceso.py` con `SOLO_ADMIN` (D9, ya planeado).

## Open Questions

- ¿El `accion` de la asignación debería incluir el vencimiento (`… hasta 2026-12-01`)? Cabe en 255 caracteres; se decide al revisar el PR.
