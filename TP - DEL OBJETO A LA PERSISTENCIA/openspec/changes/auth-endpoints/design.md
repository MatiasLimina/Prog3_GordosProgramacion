# Design

## Context

Motivación y alcance: ver `proposal.md`. Requisitos observables: `specs/autenticacion`, `specs/limite-de-intentos`, `specs/registro-de-clientes` y `specs/cambio-de-contrasena`.

Estado de `main` que condiciona el enfoque:

- `app/core/security.py` (CHG-10): `hashear_password(password, *, costo, semaforo)`, `verificar_password(password, hash, *, semaforo)`, `emitir_token(usuario_id, roles, *, secreto, minutos)`, `verificar_token(token, *, secreto) -> DatosToken` con `TokenInvalido`/`TokenVencido`. Sin estado global: quien llama pasa costo, semáforo y clave.
- `app/main.py` (CHG-03/10): el lifespan deja en `app.state` `settings`, `sessionmaker`, `hash_ficticio` y `semaforo_bcrypt`. Handlers de `IntegrityError`, `Conflicto` (409) y `PeticionInvalida` (422).
- `app/core/unit_of_work.py` y `dependencies.py` (CHG-04): `UnitOfWork` confirma al salir, revierte con excepción, no cierra la sesión, prohíbe bloques anidados sobre la misma sesión y traduce `IntegrityError` a `Conflicto` con los `MENSAJES` del módulo. `proveedor_uow(Clase)` construye el UoW con la sesión de la petición sin abrirlo.
- `app/modules/usuarios/` tiene sólo `models.py` y `schemas.py` (`RegistroCreate`, `LoginCreate`, `CambioPasswordCreate`, `UsuarioRead`, `LoginRead`, `AuthYoRead`, con el límite de 72 bytes y `extra="forbid"`).
- `app/modules/clientes/` sigue el patrón del TP 1–4 (servicio con `AsyncSession`); su migración a repositorios es CHG-15 (Nico).
- `tests/conftest.py`: el fixture `client` sobrescribe `get_session`, pero `ASGITransport` **no corre el lifespan**, así que `app.state` no tiene `sessionmaker`, `hash_ficticio`, `semaforo_bcrypt` ni `settings` (nota de CHG-04).
- **Contradicción detectada**: `AGENTS.md` §6 dice que `/auth/yo` vive en el grupo protegido. La consigna (tabla «Endpoints de referencia»: todo `/auth` en el grupo **Abierto**; RN-06: con el cambio pendiente «sólo puede usar las rutas de /auth»; C-09: «Bloqueado (403) salvo /auth») dice lo contrario. Gana la consigna: `/auth/yo` y `/auth/cambiar-password` piden estar autenticados pero **no** pasan por el control del cambio obligatorio.

## Goals / Non-Goals

**Goals:**
- Las cinco rutas `/auth` con las capas Router → Service → UoW → Repository, sin `HTTPException` en el servicio.
- Ninguna llamada a bcrypt con una conexión tomada: el hash y la verificación corren **fuera** de todo bloque `async with uow`.
- Una sola vía de autenticación por cookie (`get_usuario_actual`), que CHG-12 reutiliza sin reescribir.
- Tests de integración deterministas para C-02 a C-05 (sin medir tiempos en pytest).

**Non-Goals:**
- `requiere_rol`, control del cambio obligatorio (RN-06), los dos grupos de rutas de `main.py` (CHG-12).
- Normalizar mayúsculas del correo (afecta a CHG-14 y al seed; hoy se compara tal como lo normaliza `EmailStr`).
- Cabeceras de proxy (`X-Forwarded-For`) para la IP del cliente.
- Medir en pytest que los tiempos de RN-08 sean parecidos: se prueba que ambos caminos hacen exactamente una verificación bcrypt; el tiempo lo muestra el `.http` de C-04 (CHG-18).

## Decisions

### D1 · Frontera CHG-11 / CHG-12: CHG-11 entrega `get_usuario_actual` completo

`/auth/yo` y `/auth/cambiar-password` necesitan al usuario actual, y el DoD de CHG-11 incluye C-03 («sin cookie o con `Authorization: Bearer`, 401»). CHG-11 crea en `app/core/dependencies.py` la dependencia `get_usuario_actual` con **las cinco causas de 401** del Ej5 (sin cookie, token inválido, token vencido, usuario inexistente, usuario inactivo), leyendo sólo `request.cookies["access_token"]` y con la misma sesión de la petición (`Depends(get_session)`). También deja `AsignacionRolRepository.roles_vigentes(usuario_id)`.

CHG-12 conserva: `requiere_rol` (403, roles vigentes en la base vía `roles_vigentes`), el control del cambio obligatorio (RN-06), los dos grupos de rutas en `main.py` (mueve `auth_router` al grupo abierto) y su DoD (C-01, C-06, C-07, C-09). En el PR de CHG-11 se corrige la sección CHG-12 de `PLAN_PARCIAL.md`: «`get_usuario_actual` ya existe desde CHG-11; CHG-12 lo reutiliza».

- Alternativa A · dependencia mínima privada en `usuarios` (sólo «cookie → usuario») que CHG-12 reemplaza: deja **dos caminos de autenticación** durante un tiempo, duplica los tests de 401 y obliga a CHG-12 a migrar rutas ya probadas. En un dominio CRITICAL, dos caminos son un riesgo (uno puede quedar sin la regla de usuario inactivo). Rechazada.
- Alternativa B · posponer `/auth/yo` y `cambiar-password` a CHG-12: contradice el plan (son entregables de CHG-11) y deja C-03 sin poder probarse. Rechazada.

### D2 · `get_usuario_actual` devuelve valores simples y suelta la conexión

Devuelve un `UsuarioActual` (dataclass congelada: `id`, `email`, `nombre`, `activo`, `debe_cambiar_password`, `roles_token`), **sin** `password_hash`. Lee el usuario dentro de un bloque corto `async with UnitOfWork(session)` (el base, sin repositorios propios: usa `UsuarioRepository(session)`), que al salir confirma una transacción vacía y **devuelve la conexión al pool**.

Por qué: (1) el docstring de `unit_of_work.py` advierte que un rollback posterior expira los objetos ORM y leerlos dispara carga perezosa (`MissingGreenlet`): valores simples lo evitan; (2) sin cerrar la lectura, el autobegin dejaría la conexión tomada mientras `cambiar-password` corre bcrypt (~300 ms), que es justo lo que la consigna prohíbe. El bloque de la dependencia termina antes del del servicio: son sucesivos, no anidados.

- Alternativa · devolver el `Usuario` ORM y leer sin bloque: más simple, pero mantiene la conexión durante bcrypt y expone objetos expirables. Rechazada.
- Costo: un `COMMIT` vacío por petición autenticada (un viaje a la base).

### D3 · `intento_acceso` en sesión y transacción propias, construidas por una dependencia

`app/core/dependencies.py` suma:

```python
async def get_fabrica_sesiones(request: Request) -> async_sessionmaker[AsyncSession]:
    return request.app.state.sessionmaker

def proveedor_uow_sesion_propia[U: UnitOfWork](clase: type[U]):
    async def _proveer(fabrica = Depends(get_fabrica_sesiones)) -> AsyncIterator[U]:
        async with fabrica() as session:   # sesión NUEVA, no la de get_session
            yield clase(session)
    return _proveer
```

El router recibe dos UoW: `UsuariosUoW` (sesión de la petición) e `IntentosUoW` (sesión propia), y se los pasa al servicio **sin abrirlos**. El servicio abre `async with intentos:` sólo para agregar la fila; al salir se confirma, y recién después lanza `NoAutenticado` si el login falló. Se cumple «el router construye, el servicio abre», y la regla de un UoW abierto por sesión (son sesiones distintas). La sesión propia no toma conexión hasta la primera escritura: un 422 o un 429 nunca la usan. Como el bloque de lectura del login ya terminó (D5), la petición usa **una conexión a la vez**.

El comentario de tres partes que pide la consigna va en la función del servicio que escribe el intento (`_anotar_intento`):

```python
# DISTINTO: única escritura del sistema con sesión y transacción propias (IntentosUoW),
#   que se confirma siempre, falle o no la petición.
# POR QUÉ: el fallo que se quiere contar es el mismo que revierte la transacción de la
#   petición; si compartiera el UoW, el 401 borraría la fila y RN-07 nunca bloquearía.
# COSTO: deja filas aunque la petición falle, y usa una segunda sesión (una conexión
#   más del pool, aunque nunca al mismo tiempo que la de la petición).
```

- Alternativa A · `async with request.app.state.sessionmaker()` dentro del servicio: el servicio construiría su UoW y conocería `app.state` (FastAPI). Rechazada por AGENTS §5/§8.
- Alternativa B · `BackgroundTasks`: la fila se escribiría después de la respuesta; C-05 (seis peticiones seguidas) podría contar de menos. Rechazada.
- Tests: `get_fabrica_sesiones` se sobrescribe o `app.state.sessionmaker` se fija en `sessionmaker_test` (D10).

### D4 · Consulta del límite: una sola sentencia, con el reloj de la base

`IntentoAccesoRepository.contar_fallos_recientes(email, ip) -> ConteoFallos(fallos, mas_viejo, ahora)` emite una sola consulta con parámetros ligados (SQLAlchemy Core, nunca texto concatenado):

```sql
SELECT count(*), min(cuando), now()
FROM intento_acceso
WHERE email = :email AND ip = :ip AND NOT exito
  AND cuando > now() - interval '60 seconds'
  AND cuando > COALESCE((SELECT max(cuando) FROM intento_acceso
                         WHERE email = :email AND ip = :ip AND exito),
                        '-infinity')
```

- Usa el índice `ix_intento_acceso_email_ip_cuando` en las dos partes.
- `now()` y `cuando` (default del servidor) son el mismo reloj: no hay desfase entre la app y la base.
- El reinicio (RN-07) es la subconsulta: los fallos anteriores al último éxito **del mismo correo e IP** dejan de contar sin borrarse.
- `Retry-After` = `max(1, ceil(60 − (ahora − mas_viejo)))`, en una función pura `calcular_retry_after` con test unitario (58,5 s → 2).
- `LIMITE_FALLOS = 5` y `VENTANA_SEGUNDOS = 60` son constantes del servicio: las fija la consigna, no son configuración.

Decisiones de alcance (confirmar, ver «Decisiones a confirmar»):
- **El reinicio y el conteo son por (correo, IP)**: un atacante sólo puede bloquear la combinación de su propia IP con el correo de la víctima; la víctima desde otra IP no se ve afectada, y un éxito de la víctima no limpia los fallos del atacante.
- **Un intento bloqueado (429) no se anota**: C-05 espera «los cinco fallos» en la tabla; anotar el 429 extendería el bloqueo indefinidamente mientras el atacante insiste, y no es un intento verificado (ni correcto ni fallido).

### D5 · Flujo del login (servicio)

```
iniciar_sesion(uow, intentos, datos, ip, seg) -> SesionIniciada
  async with uow:                                   # bloque de lectura, sin bcrypt
      conteo = uow.intentos.contar_fallos_recientes(email, ip)
      if conteo.fallos >= 5: raise DemasiadosIntentos(calcular_retry_after(...))
      usuario = uow.usuarios.get_by_email(email)    # -> valores simples
      roles = uow.asignaciones.roles_vigentes(id) si existe, si no []
  ok = verificar_password(password, hash_del_usuario o seg.hash_ficticio)   # fuera del bloque
  exito = ok and existe and activo
  _anotar_intento(intentos, email, ip, exito)       # D3: se confirma ya
  if not exito: raise NoAutenticado("Correo o contraseña incorrectos.")
  token = emitir_token(id, roles, secreto, minutos)
  return SesionIniciada(token, debe_cambiar_password, expira_en_segundos=minutos*60)
```

El router toma `ip = request.client.host` (o `"desconocida"`), llama al servicio, pone la cookie (D7) y devuelve `LoginRead`. El token **sólo** sale del servicio hacia `set_cookie`.

- Un usuario inactivo con la contraseña correcta da el mismo 401 y se anota como fallo (no revela que la cuenta existe y está inactiva).
- Un `password_hash` corrupto (bcrypt lanza `ValueError`) se trata como fallo (401) y se registra un aviso en el log con el id del usuario, sin el hash.
- Los roles se leen en el mismo bloque, antes de verificar, para no abrir un segundo bloque: «vigentes al emitirlo» con milisegundos de diferencia.

### D6 · Excepciones de dominio nuevas

En `app/core/errors.py`, junto a `Conflicto` y `PeticionInvalida`:
- `NoAutenticado(mensaje)` → 401 `{"detail": mensaje}`. La usan el login («Correo o contraseña incorrectos.») y `get_usuario_actual` (mensaje fijo «No hay una sesión válida.» para las cinco causas; nunca dice cuál).
- `DemasiadosIntentos(retry_after: int)` → 429 `{"detail": "Demasiados intentos fallidos. Probá de nuevo más tarde."}` con cabecera `Retry-After`.

Los handlers van en `registrar_handlers` de `app/main.py`. La contraseña actual incorrecta en `cambiar-password` usa la existente `PeticionInvalida` (422).

- Alternativa · `HTTPException` en la dependencia `get_usuario_actual` (es capa HTTP): funcionaría, pero dos formas de producir el mismo 401 complican los tests de C-03/C-06. Se usa `NoAutenticado` en ambos lados.
- Sin `WWW-Authenticate`: la autenticación por cookie no tiene un esquema estándar; se documenta en el docstring de la excepción.

### D7 · Cookie

Router: `response.set_cookie("access_token", token, max_age=minutos*60, httponly=True, samesite="lax", secure=seg.cookie_secure, path="/")`. Logout: `response.delete_cookie("access_token", path="/", httponly=True, samesite="lax", secure=seg.cookie_secure)` (Starlette emite `Max-Age=0`). Starlette escribe `SameSite=lax` en minúsculas: los tests comparan sin distinguir mayúsculas. Logout no tiene servicio ni toca la base (no hay regla de negocio que poner en una capa).

### D8 · Parámetros de seguridad por dependencia

`ParametrosSeguridad` (dataclass congelada: `costo`, `semaforo`, `hash_ficticio`, `secreto`, `minutos_token`, `cookie_secure`) la arma `get_parametros_seguridad(request)` desde `request.app.state`. El router la pasa al servicio; el servicio nunca lee `app.state`. Resuelve la pregunta abierta de CHG-10 (Alternativa B de su D1): se envuelven costo y semáforo en una dependencia, sin tocar `security.py`.

### D9 · Ubicación, repositorios y Unit of Work

- Módulo `usuarios` (la consigna no tiene módulo `auth`): `router.py` exporta `auth_router = APIRouter(prefix="/auth", tags=["auth"])`; CHG-14 agrega su `router` (`/usuarios`, `/eventos`) en el mismo archivo. `service.py` con las funciones de auth. `main.py` sólo hace `include_router(auth_router)`; CHG-12 lo mueve al grupo abierto.
- `repository.py`: `UsuarioRepository.get_by_email`; `AsignacionRolRepository.roles_vigentes` (`revocada_en IS NULL AND (vence_en IS NULL OR vence_en > now())`, ordenados); `IntentoAccesoRepository.contar_fallos_recientes`; `EventoSeguridadRepository` (sólo lo heredado; CHG-14 agrega el listado).
- `unit_of_work.py`: `UsuariosUoW` (usuarios, asignaciones, intentos —sólo lectura—, eventos, clientes) con `MENSAJES = {"uq_usuario_email": "Ya existe un usuario con ese correo.", "uq_cliente_email": "Ya existe un cliente con ese correo.", "uq_asignacion_rol_usuario_rol_vigente": "El usuario ya tiene ese rol vigente."}`; `IntentosUoW` (sólo `intentos`, `MENSAJES = {}`).
- **Cliente**: `UsuariosUoW.clientes = BaseRepository(session, Cliente)` (genérico). No se crea `app/modules/clientes/repository.py`, que es de CHG-15 (Nico); cuando exista `ClienteRepository`, CHG-15 cambia esa línea.
  - Alternativa · crear acá un `ClienteRepository` mínimo: más fiel a «cada entidad tiene el suyo», pero pisa un archivo de otro change en curso posible. Se elige el genérico (ver «Decisiones a confirmar»).

### D10 · Registro

El hash se calcula **antes** de `async with uow`. Adentro: `usuarios.add(Usuario(...))` (flush → id), `asignaciones.add(AsignacionRol(usuario_id, rol="CLIENTE"))`, `clientes.add(Cliente(nombre, email, usuario_id))`. No se consulta antes si el correo existe: el `UNIQUE` de `usuario.email` o de `cliente.email` revienta en el flush y el UoW lo traduce a `Conflicto` con su mensaje, revirtiendo las tres filas. Así nunca se vincula una ficha existente. La respuesta es `UsuarioRead` (no se lee `AsignacionRol.desde`, que queda expirado tras el flush por su default del servidor). El registro **no** inicia sesión (no pone cookie) y **no** deja evento: RN-16 nombra alta de personal, cambio de rol y cambio de contraseña, no el auto-registro.

### D11 · Cambio de contraseña

1. Bloque de lectura: `password_hash` del usuario actual → `str`.
2. Fuera de todo bloque: `verificar_password(actual)`; si falla → `PeticionInvalida("La contraseña actual no es correcta.")` (422). Luego `hashear_password(nueva)`.
3. Bloque de escritura (RN-16): `usuarios.update(usuario, {password_hash, debe_cambiar_password: False})` y `eventos.add(EventoSeguridad(actor=email, accion="Cambio de contraseña"))`.

No emite token ni toca la cookie. Convención de evento que hereda CHG-14: `actor` = correo de quien hace el cambio (o `SISTEMA`), `accion` = frase corta en español.

- Por qué 422 y no 401 para la contraseña actual incorrecta: 401 en este proyecto significa «no hay sesión válida» (AGENTS §6) y un cliente lo interpretaría como sesión vencida. La consigna admite 200, 401 y 422 para esta ruta.

### D12 · Tests (Strict TDD)

- `tests/conftest.py`: el fixture `client` fija y restaura `fastapi_app.state` con `settings` (copia de `get_settings()` con `bcrypt_cost=4`), `hash_ficticio` (costo 4), `semaforo_bcrypt` y `sessionmaker = sessionmaker_test`. Así los tests no tocan la base de desarrollo ni tardan 300 ms por hash.
- Archivos: `tests/test_auth_limite.py` (unitario: `calcular_retry_after`), `tests/test_auth_dependencias_db.py` (`get_usuario_actual`, sesión propia), `tests/test_auth_registro_db.py`, `tests/test_auth_login_db.py`, `tests/test_auth_sesion_db.py` (yo, logout), `tests/test_auth_cambiar_password_db.py`; todos los `_db` con `pytestmark = pytest.mark.db`.
- RN-08 sin medir tiempos: se espía `verificar_password` en el módulo del servicio (llamada única y con `hash_ficticio` cuando el correo no existe). «Hash antes del bloque»: se registra el orden de `hashear_password` y de `UsuariosUoW.__aenter__`.
- Datos de borde (roles revocados o vencidos, fallos de hace 61 s, otra IP) se insertan directo con `sessionmaker_test`.

## Risks / Trade-offs

- [El conteo se lee antes de escribir el intento: con peticiones concurrentes pueden pasar más de 5 fallos] → aceptable; el límite es aproximado bajo concurrencia y C-05 es secuencial. `Retry-After` usa el fallo más viejo que cuenta.
- [Tras un proxy inverso todas las peticiones comparten IP → bloqueo compartido] → fuera de alcance; en un despliegue se usa `uvicorn --proxy-headers` con `--forwarded-allow-ips`.
- [La lectura de roles sólo ocurre si el correo existe: diferencia de tiempo de ~1 ms frente a ~250 ms de bcrypt] → aceptable para RN-08; documentado en el servicio.
- [Correos con distinta capitalización cuentan como distintos (registro, login y límite)] → fuera de alcance (Non-Goals); se anota para CHG-14/17.
- [Si la base cae justo después de verificar, el intento no se anota y la petición da 500] → caída de infraestructura, no entrada inválida (RN-15 no aplica).
- [Un `COMMIT` vacío extra por petición autenticada (D2)] → un viaje a la base a cambio de no retener la conexión.
- [`tests/conftest.py` es compartido: tocar `client` afecta a toda la suite] → el cambio sólo agrega estado que hoy falta; se corre la suite completa antes de cada commit.
- [`AGENTS.md` §6 contradice la consigna sobre `/auth/yo`] → se corrige en este PR (gana la consigna).

## Migration Plan

Sin variables nuevas. Una sola migración, agregada en la revisión: `0005_evento_seguridad_actor_255` (ensancha `evento_seguridad.actor` de 100 a 255, porque guarda el correo, que admite 255; ver tasks 8.4a). Un commit por endpoint (registro, login, logout, yo, cambiar-password), precedidos por la infraestructura compartida, y un commit final de documentación (`PLAN_PARCIAL.md`, `AGENTS.md`, archivo del change). Rollback: revertir el PR; nadie depende todavía de `/auth`.

## Decisiones a confirmar (CRITICAL: aprobación de Matias antes de escribir código)

1. **D1**: `get_usuario_actual` completo en CHG-11; CHG-12 lo reutiliza (y se corrige su sección en el plan).
2. **D2**: la dependencia lee en un bloque corto del UoW base y devuelve valores simples.
3. **D4**: conteo y reinicio por (correo, IP); los 429 no se anotan.
4. **D11**: contraseña actual incorrecta → 422 (no 401).
5. **D9**: cliente con `BaseRepository(session, Cliente)` genérico, sin crear el archivo de CHG-15 (coordinar con Nico).
6. **D10**: el registro no inicia sesión ni deja evento de seguridad.
7. **Contexto**: corregir `AGENTS.md` §6 (`/auth/yo` en el grupo abierto).
