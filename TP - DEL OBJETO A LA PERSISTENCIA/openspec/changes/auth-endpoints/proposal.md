# Proposal

## Why

Ya están en `main` todas las piezas que el acceso necesita: tablas `usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad` y `cliente.usuario_id` (CHG-06/07/08), contratos de auth (CHG-09a), bcrypt fuera del bucle y JWT (CHG-10) y repositorios + Unit of Work (CHG-04). Lo que falta es lo que el usuario ve: no hay ninguna ruta `/auth`, nadie puede registrarse, iniciar ni cerrar sesión. CHG-11 es el punto donde se juntan las dos ramas críticas del plan y destraba CHG-12 (autorización) y, por él, CHG-14 y CHG-16. Cubre el Ejercicio 4 (14 %) y la mitad del Ejercicio 7 (`intento_acceso` en sesión propia) de la consigna.

## What Changes

- **`POST /auth/registro`** (RN-02): crea usuario, asignación `CLIENTE` y ficha de `cliente` vinculada, en un solo bloque `async with uow`; el hash se calcula **antes** de abrir la transacción. Correo repetido de usuario o de cliente → 409 con mensaje propio y ninguna fila suelta; nunca se apropia de una ficha de cliente existente.
- **`POST /auth/login`** en orden fijo: (1) límite de intentos (RN-07): con 5 fallos del mismo correo desde la misma IP en 60 s, el sexto recibe 429 con `Retry-After` sin calcular ningún hash; un login correcto reinicia la cuenta; (2) verificación contra el hash del usuario o contra el hash ficticio si el correo no existe (RN-08: misma respuesta, mismo trabajo). Respuesta `{mensaje, debe_cambiar_password, expira_en_segundos}` **sin el token**.
- **Cookie `access_token`**: `HttpOnly`, `SameSite=Lax`, `Max-Age` = duración del token, `Secure` según `COOKIE_SECURE`, `Path=/`. El JWT lleva `sub`, `exp` y los roles vigentes al emitirlo. Nunca se lee de `Authorization`.
- **`intento_acceso`** (Ej7): cada login verificado (correcto o fallido) se anota desde una **sesión y transacción propias**, que se confirman aunque la petición falle, con el comentario de tres partes que pide la consigna.
- **`POST /auth/logout`**: borra la cookie (200, sin requerir sesión).
- **`GET /auth/yo`**: devuelve el usuario, sus roles vigentes (leídos de la base) y los roles del token.
- **`POST /auth/cambiar-password`**: verifica la contraseña actual, guarda la nueva, apaga `debe_cambiar_password` y deja una línea en `evento_seguridad` en la misma transacción (RN-16). No invalida sesiones ni emite un token nuevo.
- **Dependencia `get_usuario_actual`** (en `app/core/dependencies.py`): lee la cookie, verifica el token y el usuario, y responde 401 si falta la cookie, el token es inválido o venció, o el usuario no existe o está inactivo. CHG-12 la reutiliza y le suma `requiere_rol`, el control del cambio obligatorio y los dos grupos de rutas (ver decisión D1 de `design.md`).
- **Excepciones de dominio nuevas** en `app/core/errors.py` (`NoAutenticado` → 401, `DemasiadosIntentos` → 429 con `Retry-After`) con sus handlers en `app/main.py`: el código de negocio sigue sin lanzar `HTTPException`.
- **Corrección de `AGENTS.md` §6**: dice que `/auth/yo` vive en el grupo protegido; la consigna (tabla de endpoints, RN-06 y C-09) lo pone en el grupo **abierto**, autenticado pero sin el control del cambio obligatorio. Gana la consigna.

Fuera de alcance: `requiere_rol`, el control del cambio obligatorio de contraseña (RN-06), los dos grupos de rutas en `main.py` (CHG-12); alta de personal, gestión de roles y `GET /eventos` (CHG-14); migrar `clientes` a repositorios (CHG-15); casos `.http` (CHG-18); seed (CHG-17).

## Capabilities

### New Capabilities
- `autenticacion`: inicio de sesión (orden de verificación, hash ficticio, respuesta sin token), cookie de sesión, cierre de sesión, identificación del usuario actual por cookie (401) y consulta `/auth/yo`.
- `limite-de-intentos`: conteo de fallos por correo e IP en una ventana de 60 s, respuesta 429 con `Retry-After`, reinicio tras un login correcto y registro de cada intento en `intento_acceso` con transacción propia.
- `registro-de-clientes`: auto-registro atómico de usuario, rol `CLIENTE` y ficha de cliente, con 409 propios y sin apropiarse de fichas existentes.
- `cambio-de-contrasena`: cambio de la contraseña propia con verificación de la actual, baja del cambio obligatorio y evento de seguridad en la misma transacción.

### Modified Capabilities
(ninguna: las capacidades existentes —`token-de-acceso`, `hash-de-contrasenas`, `contratos-auth-usuarios`, `unidad-de-trabajo`, `ciclo-de-vida`— se usan tal cual, sin cambiar sus requisitos)

## Impact

- **Código nuevo**: `app/modules/usuarios/repository.py`, `unit_of_work.py`, `service.py`, `router.py`.
- **Archivos compartidos** (lead: Matias): `app/core/errors.py` (dos excepciones), `app/core/dependencies.py` (`get_usuario_actual`, parámetros de seguridad, UoW con sesión propia), `app/main.py` (dos handlers e `include_router` del router de auth), `tests/conftest.py` (estado de la app en los tests: `sessionmaker`, semáforo, hash ficticio y costo bajo de bcrypt).
- **API**: cinco rutas nuevas bajo `/auth`. Sin cambios en rutas existentes.
- **Base**: sin migraciones; usa las tablas de la 0003.
- **Dependencias Python**: ninguna nueva.
- **Documentación**: `PLAN_PARCIAL.md` (fila CHG-11 y sección CHG-12, que ya no crea `get_usuario_actual` sino que lo reutiliza), `AGENTS.md` §6 (`/auth/yo` en el grupo abierto) y §9 si algo queda desactualizado.
- **Desbloquea**: CHG-12, y por él CHG-14 y CHG-16. Casos de la consigna: C-02, C-03, C-04 y C-05.
- **Gobernanza**: dominio **CRITICAL** (auth). Ningún código se escribe sin la aprobación explícita de Matias de las decisiones de `design.md`.
