# Design

## Context

Motivación y alcance: ver `proposal.md`. Requisitos observables: `specs/autorizacion` y `specs/grupos-de-rutas`.

Estado de `main` (tras CHG-11, PR #53) que condiciona el enfoque:

- `app/core/dependencies.py`: `get_usuario_actual(request, session=Depends(get_session), seg=...)` devuelve un `UsuarioActual` congelado (`id`, `email`, `nombre`, `activo`, `debe_cambiar_password`, `roles_token`) y lanza `NoAutenticado` (401) por las cinco causas. Lee el usuario en un bloque corto `async with UnitOfWork(session)` que termina antes del bloque del servicio (sucesivos, no anidados). `proveedor_uow(Clase)` construye el UoW de módulo con la **misma** sesión.
- `app/modules/usuarios/repository.py`: `AsignacionRolRepository.roles_vigentes(usuario_id) -> list[str]` (no revocadas y `vence_en` nulo o `> now()` de la base).
- `app/core/errors.py`: `Conflicto` (409), `PeticionInvalida` (422), `NoAutenticado` (401), `DemasiadosIntentos` (429); handlers en `app/main.py` (`registrar_handlers`). No hay excepción para 403.
- `app/main.py`: incluye **nueve** routers directamente en `app`, sin grupos: `health`, `auth_router` y los seis de catálogo, clientes y ventas.
- Los routers de `editoriales`, `generos`, `autores`, `libros`, `clientes` y `ventas` siguen el patrón del TP 1–4 (servicios con `AsyncSession`, `Depends(get_session)`) y **mezclan** GET públicos y escrituras en un mismo `APIRouter`. Su migración a UoW es de CHG-13 (Nico), CHG-15 (Nico) y CHG-16 (Matias).
- Rutas que hoy existen pero **no figuran** en la tabla de la consigna: `GET /editoriales/{id}`, `GET /autores/`, `GET /autores/{id}`, `GET /clientes/` (listado).
- Rutas de la tabla que **todavía no existen**: `DELETE /libros/{id}`, `POST /libros/{id}/reponer`, `GET /libros/{id}/movimientos` (CHG-13); `/usuarios…`, `/eventos` (CHG-14); `GET /mis-ventas` (CHG-16).
- Siete módulos de tests hacen POST/PATCH a esas rutas sin cookie (≈150 llamadas): `test_editoriales.py`, `test_generos.py`, `test_libros_crud_db.py`, `test_libros_por_editorial_genero.py`, `test_libros_validaciones.py`, `test_clientes_db.py`, `test_ventas_db.py`. Con este change responderían 401.
- FastAPI 0.162: las dependencias de un `APIRouter` se anteponen a las de cada ruta al incluirlo, y una misma dependencia (misma función) se resuelve **una vez por petición** (caché por defecto). Las dependencias se resuelven **antes** de validar parámetros de ruta y cuerpo.

## Goals / Non-Goals

**Goals:**
- Un único camino de autorización (`requiere_rol`) y un único punto donde se monta el control RN-06.
- Cada petición autorizada usa una sola sesión (`get_session` cacheado) y no retiene la conexión entre la autorización y la operación.
- Que olvidar clasificar una ruta nueva (CHG-13, 14, 16) sea un test rojo y no un agujero silencioso.
- Tocar de los módulos ajenos **sólo** el montaje de sus rutas, sin cambiar servicios, firmas ni contratos.

**Non-Goals:**
- Comprobación de dueño de `GET /ventas/{id}` y `GET /mis-ventas` (CHG-16), gestión de roles por API y RN-05 (CHG-14).
- Reducir los viajes a la base de la autorización (ver Risks).
- Cambiar `get_usuario_actual` o `/auth/*`: se reutilizan tal cual.

## Decisions

### D1 · `requiere_rol(*roles)` lee los roles vigentes de la base con la sesión de la petición

`requiere_rol` es una fábrica que devuelve una dependencia `async`:

```python
def requiere_rol(*roles: str) -> Callable[..., Awaitable[UsuarioActual]]:
    exigidos = frozenset(roles)          # valida contra ADMIN/VENDEDOR/CLIENTE: ValueError al importar si hay un typo

    async def _requiere(
        usuario: Annotated[UsuarioActual, Depends(get_usuario_actual)],   # 401 primero
        session: Annotated[AsyncSession, Depends(get_session)],           # la MISMA sesión (caché)
    ) -> UsuarioActual:
        async with UnitOfWork(session):                                   # bloque corto, como get_usuario_actual
            vigentes = await AsignacionRolRepository(session).roles_vigentes(usuario.id)
        if exigidos.isdisjoint(vigentes):
            raise SinPermiso(MENSAJE_SIN_PERMISO)
        return usuario

    _requiere.roles = exigidos          # lo lee el test de la matriz (D6)
    return _requiere
```

- **Misma sesión**: `get_session`, `get_usuario_actual` y `requiere_rol` dependen de la misma función `get_session`; FastAPI la resuelve una vez por petición, y el UoW de módulo (`proveedor_uow`) o la sesión de los servicios viejos reciben esa misma instancia. Se prueba contando las sesiones que entrega un `get_session` espía durante una petición (spec «Una sola conexión por petición autorizada»).
- **Bloque corto**: igual que `get_usuario_actual` (CHG-11 D2): la lectura confirma una transacción vacía y devuelve la conexión al pool antes del servicio; los bloques son sucesivos, nunca anidados, así que no choca con la marca anti-anidamiento del UoW.
- **Roles del token ignorados**: sólo se consulta `asignacion_rol`. `roles_token` sigue siendo informativo (`/auth/yo`).
- **Devuelve el `UsuarioActual`**: CHG-13 (usuario del movimiento de stock), CHG-14 (actor del evento) y CHG-16 (vendedor) lo reciben de la dependencia que ya autoriza, sin otra lectura.
- Alternativa A · leer usuario y roles en una sola consulta dentro de `get_usuario_actual`: ahorra un viaje, pero agrega la consulta de roles a **toda** petición autenticada (también `/auth/*`, que no la necesita) y cambia una dependencia ya probada de CHG-11. Rechazada.
- Alternativa B · confiar en los roles del token: contradice RN-04 y C-07. Rechazada.

### D2 · Dependencias únicas `SOLO_ADMIN` y `PERSONAL`

`dependencies.py` exporta `SOLO_ADMIN = requiere_rol("ADMIN")` y `PERSONAL = requiere_rol("VENDEDOR", "ADMIN")`, y los alias `UsuarioAdmin = Annotated[UsuarioActual, Depends(SOLO_ADMIN)]` y `UsuarioPersonal = Annotated[UsuarioActual, Depends(PERSONAL)]`. Los routers usan **siempre** estas constantes, nunca `requiere_rol(...)` en línea.

Por qué: la caché de FastAPI es por función. `requiere_rol("ADMIN")` escrito dos veces crea dos funciones distintas: si una ruta lo pone en `dependencies=[...]` y otra vez como parámetro, la consulta de roles correría dos veces. Con una constante, corre una vez.

### D3 · Control del cambio obligatorio (RN-06) como dependencia del grupo

```python
async def control_cambio_obligatorio(
    usuario: Annotated[UsuarioActual, Depends(get_usuario_actual)],
) -> UsuarioActual:
    if usuario.debe_cambiar_password:
        raise SinPermiso(MENSAJE_CAMBIO_PENDIENTE)
    return usuario
```

No consulta la base: `debe_cambiar_password` ya viene leído de la base en esta petición por `get_usuario_actual` (no del token), así que un cambio de contraseña hecho con la misma cookie se ve en la petición siguiente (C-09). Como depende de `get_usuario_actual`, también da el **401** de toda ruta protegida, incluidas las que no exigen rol (`GET /mis-ventas`, `GET /ventas/{id}` en CHG-16).

Orden resultante en una ruta protegida: `get_usuario_actual` (401) → control RN-06 (403, va primero porque es dependencia del router) → rol de la ruta (403) → validación de parámetros y cuerpo (422) → handler. El spec «El cambio pendiente gana sobre la falta de rol» fija ese orden.

### D4 · Dos grupos en `main.py`; el control se declara una vez

```python
abierto = APIRouter()
protegido = APIRouter(dependencies=[Depends(control_cambio_obligatorio)])   # ÚNICO lugar

abierto.include_router(health_router)
abierto.include_router(auth_router)                     # todo /auth: yo y cambiar-password piden sesión, sin RN-06
abierto.include_router(editoriales.router_abierto)      # y géneros, autores, libros
protegido.include_router(editoriales.router)            # y géneros, autores, libros, clientes, ventas
app.include_router(abierto)
app.include_router(protegido)
```

FastAPI suma dependencias y no las resta (consigna, Ej5): por eso `/auth` no puede vivir bajo un router que tenga el control y «sacárselo»; va en el abierto y sus rutas piden `get_usuario_actual` por su cuenta (ya lo hacen desde CHG-11).

- Alternativa · `app.include_router(x, dependencies=[Depends(control)])` por cada módulo protegido: el control quedaría declarado N veces (viola «montado una sola vez») y un `include_router` sin el parámetro dejaría un módulo afuera. Rechazada.

### D5 · Cada módulo de catálogo se parte en `router_abierto` y `router` (protegido) — **decisión a confirmar**

Problema: los routers de catálogo mezclan GET públicos y escrituras en un solo `APIRouter`, y las dependencias de un `include_router` se aplican a **todas** sus rutas. No se pueden poner en dos grupos sin tocar el `router.py` del módulo, que es de CHG-13/15/16.

Recomendación (opción A): CHG-12 hace en cada `router.py` **sólo** esto:
- `editoriales`, `generos`, `autores`, `libros`: un segundo `APIRouter` con el mismo `prefix` y `tags`, `router_abierto`, al que se mueven los decoradores de los GET; `router` queda con las escrituras, cada una con `dependencies=[Depends(SOLO_ADMIN)]`.
- `clientes`, `ventas`: sólo `router` (protegido), cada ruta con `dependencies=[Depends(PERSONAL)]`.
- No cambia ningún cuerpo de handler, firma, servicio ni contrato. Cuando CHG-13/16 necesiten al usuario, cambian `dependencies=[Depends(SOLO_ADMIN)]` por el parámetro `usuario: UsuarioAdmin` (misma constante: una sola consulta).

Coordinación: avisar a Nico **antes** de empezar el apply; si su rama de CHG-13 ya tocó esos `router.py`, el que mergea segundo resuelve el conflicto conservando la división y las constantes. El test de la matriz (D6) detecta si una ruta queda mal montada.

- Opción B · separar en `main.py` por introspección (recorrer `router.routes` y mandar cada GET al abierto): no toca los módulos, pero la autorización queda escondida en `main.py`, los roles por ruta se declaran lejos de la ruta y un GET protegido futuro (`/libros/{id}/movimientos`, `/clientes/{id}`) quedaría abierto por accidente. Rechazada.
- Opción C · CHG-12 entrega sólo el mecanismo y los grupos con `health` y `/auth`, y cada dueño clasifica sus rutas en su change: no protege nada hasta CHG-13/15/16 y deja sin cumplir el DoD de CHG-12 (C-06 «un vendedor que crea un libro, 403» y C-09 «bloqueado salvo /auth»). Rechazada.

### D6 · Matriz de acceso como fuente de verdad de los tests

`tests/matriz_acceso.py` (no es un test) declara un diccionario `(método, ruta) → (grupo, roles)` copiado de los requisitos de clasificación de `specs/grupos-de-rutas`. Dos tests la usan:

- **Estructural, sin base** (`tests/test_grupos_de_rutas.py`): recorre `app.routes` (`APIRoute`); exige que el conjunto de rutas de la app y el de la matriz sean **iguales** (una ruta nueva sin clasificar falla nombrándola); que cada ruta protegida tenga `control_cambio_obligatorio` exactamente una vez entre sus dependencias de primer nivel y ninguna abierta lo tenga; y que los roles exigidos (atributo `roles` de la dependencia de `requiere_rol`, D1) coincidan con la matriz.
- **Con base** (`tests/test_autorizacion_db.py`): parametrizado sobre las rutas protegidas, sin cookie → 401; con un `CLIENTE` (sin rol de personal) → 403 en las de `VENDEDOR`/`ADMIN`; con un `VENDEDOR` → 403 en las de `ADMIN`. Los parámetros de ruta se rellenan con `1` y el cuerpo va vacío: las dependencias se resuelven antes que la validación, así que el 401/403 sale antes que el 422.

CHG-13, 14 y 16 agregan sus rutas a la matriz en su propio PR (se anota en sus secciones del plan).

### D7 · `SinPermiso` → 403, con dos mensajes fijos

`app/core/errors.py` suma `SinPermiso(mensaje)` (dominio, sin HTTP), y `registrar_handlers` en `app/main.py` la traduce a `403 {"detail": mensaje}`. Mensajes (constantes en `dependencies.py`):
- falta de rol: «No tenés permiso para esta operación.» — no nombra roles (spec «Respuesta 403 sin detalles internos»);
- cambio pendiente: «Tenés que cambiar la contraseña antes de continuar.» — distinto a propósito, para que el cliente sepa qué hacer.

CHG-16 reutiliza `SinPermiso` para el 403 de «no sos el dueño de la venta».

### D8 · `GET /ventas/{id}` exige `PERSONAL` hasta CHG-16 — **decisión a confirmar**

El estado final (AGENTS §6, consigna) es: grupo protegido, **sin** `requiere_rol`, y el servicio decide (personal o cliente dueño; si no, 403). Esa comprobación es de CHG-16. Si CHG-12 dejara la ruta sin rol, cualquier usuario autenticado (un `CLIENTE` recién registrado) vería **cualquier** venta hasta que llegue CHG-16.

Recomendación: CHG-12 la monta en el grupo protegido con `PERSONAL` (cerrado por defecto) y lo anota en la matriz y en la «Transición» de `AGENTS.md` §9; CHG-16 quita `PERSONAL` y agrega la decisión del servicio. Alternativa: sin rol desde ya (fiel al estado final, pero con la fuga descrita mientras tanto).

### D9 · Rutas fuera de la tabla de la consigna — **decisión a confirmar**

- `GET /editoriales/{id}`, `GET /autores/`, `GET /autores/{id}`: **abiertas**. La consigna dice que «el catálogo es público» y `AGENTS.md` §6 pone «catálogo público en GET» en el abierto; son lecturas del mismo catálogo que `GET /editoriales/` y `GET /autores/{id}/libros`, que sí figuran como abiertas.
- `GET /clientes/` (listado): **protegida con `PERSONAL`**, igual que `GET /clientes/{id}`: son datos personales.

### D10 · Tests existentes: sesión de ADMIN por módulo

`tests/auxiliares_auth.py` suma `async def entrar_como(client, sessionmaker, *roles, email=..., debe_cambiar=False) -> int`: inserta el usuario con `insertar_usuario` y pone en el `client` la cookie con `token_de_prueba` (sin pasar por `/auth/login`: no deja filas en `intento_acceso` ni gasta bcrypt por test). Los siete módulos afectados redefinen el fixture localmente, sin tocar ninguna función de test:

```python
@pytest.fixture
async def client(client, sessionmaker_test):
    """Sesión de ADMIN: las escrituras del catálogo, clientes y ventas son del grupo protegido (CHG-12)."""
    await entrar_como(client, sessionmaker_test, "ADMIN")
    return client
```

(Un fixture que pide su propio nombre recibe el del nivel superior: el de `conftest.py`.) `ADMIN` alcanza para las rutas `PERSONAL` porque `PERSONAL` acepta `VENDEDOR` o `ADMIN`.

- Alternativa A · que el `client` de `conftest.py` venga con sesión de ADMIN por defecto: rompe los tests de `/auth` que esperan 401 sin cookie. Rechazada.
- Alternativa B · `dependency_overrides` de `get_usuario_actual` en esos tests: no ejercita la autorización real y esconde errores de montaje. Rechazada.
- Alternativa C · renombrar `client` → `client_admin` en cada función: cientos de líneas cambiadas en archivos de otros dueños. Rechazada.

### D11 · C-01 y orden de la validación

FastAPI resuelve las dependencias antes de validar los parámetros. `GET /libros/{id}` es abierto y no tiene dependencias de sesión: con la cookie de un administrador, `GET /libros/abc` valida y responde 422 enseguida. `PATCH /editoriales/abc` es protegido: corren el usuario actual, el control RN-06 y el rol (todos pasan para un ADMIN) y recién después la validación. En ambos casos la respuesta es 422 y el handler no corre. Se prueba con un espía sobre el servicio del módulo (`service.obtener` / `service.actualizar`) que debe quedar sin llamadas. No requiere código nuevo: es una caracterización que fija el comportamiento (C-01) ahora que hay grupos.

## Risks / Trade-offs

- [Dos lecturas cortas por petición protegida con rol (usuario y roles) más sus `COMMIT` vacíos] → ~2 viajes extra a la base frente a una sola consulta combinada; se acepta por claridad y por no tocar `get_usuario_actual` (D1-A). Se puede optimizar después sin cambiar los specs.
- [Conflictos de merge con CHG-13/15 en los `router.py`] → la división es mecánica y el test de la matriz detecta un montaje perdido; aviso a Nico antes del apply (D5).
- [Un GET protegido futuro agregado por error a `router_abierto`] → la matriz lo marca como abierto/protegido explícitamente y el test estructural falla si no coincide.
- [Rutas con cuerpo inválido y sin permiso responden 401/403 y no 422] → es lo esperado (la consigna lista 401/403 para todo el grupo protegido); los tests de 422 de los módulos ya corren con sesión de ADMIN (D10).
- [`GET /ventas/{id}` provisorio con `PERSONAL`] → si CHG-16 se atrasa, el cliente dueño no ve su venta (falla cerrada); queda anotado en AGENTS §9 (D8).
- [El test de la matriz obliga a CHG-13/14/16 a tocar `tests/matriz_acceso.py`] → es el objetivo; se anota en sus secciones del plan.

## Migration Plan

Sin migraciones ni variables nuevas. Commits: (1) `SinPermiso` + `requiere_rol` + control RN-06 con sus tests; (2) grupos en `main.py`, división de routers y adaptación de los tests existentes (tienen que ir juntos para que la suite no quede roja); (3) matriz y tests de casos C; (4) documentación y archivo del change. Rollback: revertir el PR; la API vuelve a quedar abierta como en CHG-11.

## Decisiones a confirmar (CRITICAL: aprobación de Matias antes de escribir código)

1. **D5 · División de los `router.py` de catálogo, clientes y ventas** (opción A): CHG-12 toca esos seis archivos sólo para el montaje y el rol, y se avisa a Nico. *Recomendación: aprobar A.* Implica corregir la línea «Archivos» de CHG-12 en el plan.
2. **D8 · `GET /ventas/{id}` con `PERSONAL` provisorio** hasta CHG-16. *Recomendación: aprobar (cerrado por defecto).*
3. **D9 · Rutas fuera de la tabla**: `GET /editoriales/{id}`, `GET /autores/`, `GET /autores/{id}` abiertas; `GET /clientes/` con `PERSONAL`. *Recomendación: aprobar.*
4. **D6 · Matriz de acceso obligatoria** que hace fallar la suite ante una ruta sin clasificar, y que CHG-13/14/16 actualizan. *Recomendación: aprobar.*
5. **D10 · Tests existentes con sesión de ADMIN** vía fixture local en siete módulos de otros dueños (sin tocar funciones de test). *Recomendación: aprobar.*
6. **D7 · Mensajes de 403**: «No tenés permiso para esta operación.» y «Tenés que cambiar la contraseña antes de continuar.» *Recomendación: aprobar o ajustar el texto.*
7. **D1 · Dos lecturas cortas** (usuario y roles) en vez de una combinada, sin tocar `get_usuario_actual`. *Recomendación: aprobar.*
8. **Alcance del DoD**: C-06 sólo en «sin sesión 401» y «vendedor crea libro 403» (la parte de la venta propia/ajena es de CHG-16); C-07 con la revocación hecha en la base (la revocación por API es de CHG-14). *Recomendación: aprobar y corregir el DoD de CHG-12 en el plan.*
