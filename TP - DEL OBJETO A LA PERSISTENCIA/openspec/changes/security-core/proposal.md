# Proposal

## Why

CHG-11 (login, registro, cambio de contraseña) y CHG-17 (seed con usuarios) necesitan hashear y verificar contraseñas y emitir y verificar el token de acceso, y hoy `app/core/security.py` sólo calcula el hash ficticio. Sin este change ninguno de los dos puede arrancar, y el semáforo de bcrypt que pide la sección 6 de `AGENTS.md` (con `BCRYPT_MAX_CONCURRENTES` ya en `Settings`) sigue sin crearse (fila «Semáforo de bcrypt» de la sección 9).

## What Changes

- `app/core/security.py` suma:
  - Hash de contraseña con bcrypt, asincrónico: corre en `asyncio.to_thread`, bajo un `asyncio.Semaphore` y con el costo que recibe (`BCRYPT_COST`).
  - Verificación de contraseña contra un hash, también fuera del bucle y bajo el mismo semáforo. Sirve igual para el hash real y para el ficticio (el login de CHG-11 elige cuál pasar).
  - Guarda defensiva del límite de 72 bytes de bcrypt: el hash rechaza con `ValueError` una contraseña de más de 72 bytes (UTF-8) y la verificación devuelve falso sin llamar a bcrypt. El 422 sigue siendo responsabilidad del contrato (CHG-09a); esta guarda evita que bcrypt 4 trunque en silencio y que bcrypt 5 lance un error.
  - Emisión del JWT (PyJWT, algoritmo HS256 fijo en el código) con `sub` (id del usuario), `exp` (ahora + `JWT_EXPIRE_MINUTES`, en UTC) y `roles`.
  - Verificación del JWT que acepta sólo HS256 y exige los tres claims. Lanza dos excepciones propias: `TokenVencido` y `TokenInvalido` (la primera es subclase de la segunda), sin el token ni la clave en el mensaje ni en la cadena de excepciones. CHG-12 las traduce a 401.
  - `calcular_hash_ficticio(costo)` no cambia de firma ni de comportamiento.
- El lifespan de `app/main.py` crea el `asyncio.Semaphore(BCRYPT_MAX_CONCURRENTES)` y lo guarda en `app.state` (nunca al importar).
- `AGENTS.md` (sección 9, fila «Semáforo de bcrypt») y `PLAN_PARCIAL.md` (estado de CHG-10) se actualizan al cerrar.

Fuera de alcance: endpoints, cookie, `dependencies.py`, `intento_acceso`, límite de intentos y la elección entre hash real y ficticio (CHG-11 y CHG-12); validadores de 72 bytes de los contratos (CHG-09a).

## Capabilities

### New Capabilities
- `hash-de-contrasenas`: cómo se guardan y se verifican las contraseñas (bcrypt con costo de la configuración, fuera del bucle de eventos, concurrencia acotada y límite de 72 bytes).
- `token-de-acceso`: qué lleva el token de acceso firmado, cuánto dura y cómo se distingue un token vencido de uno alterado o inválido, sin filtrar la clave.

### Modified Capabilities
- `ciclo-de-vida`: el arranque también crea el semáforo que limita las llamadas simultáneas a bcrypt y lo deja en el estado de la aplicación (requisito nuevo; los existentes no cambian).

## Impact

- Código: `app/core/security.py`, `app/main.py` (lifespan; archivo compartido, lo modifica el lead).
- Tests: `tests/test_security.py` (se amplía, sin tocar los 4 tests del hash ficticio) y `tests/test_lifespan.py` (semáforo en el estado; la importación sigue sin crear recursos).
- Dependencias: ninguna nueva (`bcrypt>=4.0` y `PyJWT` ya están en `requirements.txt`; el mínimo de PyJWT sube de 2.8 a 2.15 en la revisión de la PR 36, ver `design.md`).
- Consumidores: CHG-11 (login, registro, cambio de contraseña, `/auth/yo`), CHG-12 (`get_usuario_actual`), CHG-14 (alta de personal) y CHG-17 (seed) usan estas funciones.
- Sin cambios de esquema, de migraciones ni de variables de entorno.
