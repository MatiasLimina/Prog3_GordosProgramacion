# Proposal

## Why

El Ejercicio 1 del parcial (6 %) y la pág. 4 de la consigna exigen que la configuración se lea con una clase `Settings` de pydantic-settings, que la URL de la base se arme con `@computed_field` desde `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` y `POSTGRES_PORT`, y que ni la contraseña de la base ni la clave de firma del token tengan valor por defecto: si faltan, la aplicación no arranca. Hoy `app/core/config.py` es un `dataclass` que lee una `DATABASE_URL` entera y `DB_ECHO`, no conoce la clave JWT, el costo de bcrypt, el tamaño del pool, `COOKIE_SECURE` ni la duración del token, y el lifespan no calcula el hash ficticio del login. CHG-03 es la raíz de la fila de Nico y bloquea a CHG-04 y a CHG-10 de Matias, que necesita leer de `Settings` el costo de bcrypt, la clave y la duración del token y `COOKIE_SECURE`, y encontrar el hash ficticio ya calculado en el lifespan.

## What Changes

- **BREAKING (entorno local)** `app/core/config.py`: `Settings` pasa a ser una clase de pydantic-settings que lee el entorno y `.env`.
  - URL de la base como `@computed_field` `database_url` (driver `postgresql+asyncpg`) armada con `sqlalchemy.engine.URL.create` (nunca f-string) a partir de las cinco variables `POSTGRES_*`; `DATABASE_URL` deja de leerse.
  - Contraseña de la base y clave JWT obligatorias, sin valor por defecto y sin aceptar texto vacío (`JWT_SECRET` ≥ 32 caracteres); su valor nunca aparece en el `repr` ni en el mensaje de error.
  - Costo de bcrypt (`BCRYPT_COST`), máximo de bcrypt simultáneos para el semáforo de CHG-10 (`BCRYPT_MAX_CONCURRENTES`), tamaño del pool (`DB_POOL_SIZE`, que llega a `create_async_engine(pool_size=...)`), `COOKIE_SECURE`, duración del token (`JWT_EXPIRE_MINUTES`) y `SQL_ECHO` salen de la configuración (con valores por defecto no secretos y rangos validados).
  - `DB_ECHO` deja de leerse, sin alias; el nombre nuevo es `SQL_ECHO` (confirmado por Matias).
  - `get_settings()` sigue siendo el único punto de entrada y traduce la falta de variables a un `RuntimeError` en español que nombra las variables faltantes y no muestra ningún valor.
- `app/core/database.py`: funciones separadas que crean el motor (con el tamaño del pool y el eco de la configuración) y la fábrica de sesiones (`expire_on_commit=False`); `get_session` sigue tomando la fábrica de `app.state` y cierra la sesión al terminar.
- `app/main.py`: el lifespan construye `Settings`, el motor y la fábrica, los guarda en `app.state`, calcula **una sola vez** el hash ficticio del login con `asyncio.to_thread` y llama a `dispose()` al apagar. Nada de esto ocurre al importar un módulo.
- Hash ficticio: `app/core/security.py` (archivo nuevo que CHG-10 completa) sólo con `calcular_hash_ficticio(costo)`, que usa `bcrypt.gensalt(rounds=costo)` con el mismo `BCRYPT_COST` que los hashes reales (RN-08); queda en `app.state.hash_ficticio`.
- `health`: queda sólo con `router.py` (los dos modelos de respuesta pasan adentro del router y se borra `schemas.py`); `/health/ready` conserva `SELECT 1` y el 503 sin texto interno.
- `env.example` lista todas las variables nuevas, sin ningún secreto, con la forma de generar la clave de firma.
- Consumidores que se adaptan sin cambiar su comportamiento: `migrations/env.py` (conserva el `.replace("%", "%%")`), `scripts/seed.py` (sólo su `main()`; se avisa a Lauti), `tests/conftest.py` (la base `libreria_test` se elige pasando `POSTGRES_DB` al subproceso de Alembic, y fija una `JWT_SECRET` de prueba), y los tests existentes de configuración, base y salud.
- Documentación mínima: la línea de `DATABASE_URL` en `migrations/README`, el comentario de `alembic.ini`, las 4 líneas de `README.md` que nombran `DATABASE_URL`/`DB_ECHO` y el estado de CHG-03 en `PLAN_PARCIAL.md`.

**Fuera de alcance**: hash y verificación de contraseñas, el semáforo en sí y JWT, incluido su algoritmo, que CHG-10 fija como constante `HS256` (CHG-10); cookie y login (CHG-11); los dos grupos de rutas (CHG-12); Unit of Work (CHG-04); el resto de `README.md` (CHG-20); `AGENTS.md` (sus menciones a `DATABASE_URL`/`DB_ECHO` las corrige Matias); `docs/evidencia_c07.md` y demás evidencia del TP 1–4 (históricos); los `.http` que todavía nombran `DB_ECHO` (CHG-18); la carpeta de despliegue del TP 1–4, que sigue leyendo `DATABASE_URL` (CHG-01/02).

## Capabilities

### New Capabilities

- `configuracion`: lectura de la configuración desde el entorno y `.env` con `Settings`, armado de la URL de la base, secretos obligatorios sin valor por defecto ni filtración en errores, y parámetros operativos (bcrypt, pool, cookie, token, eco de SQL).
- `ciclo-de-vida`: recursos que se crean en el lifespan y viven en `app.state` (motor, fábrica de sesiones, configuración, hash ficticio), su liberación al apagar, y la sesión por petición de `get_session`.
- `salud`: endpoints `/health/live` (no toca la base) y `/health/ready` (`SELECT 1`, 503 sin texto interno si la base no contesta).

### Modified Capabilities

Ninguna (no hay specs principales todavía).

## Impact

- **Código**: `app/core/config.py` (reescritura), `app/core/database.py`, `app/main.py`, `app/core/security.py` (nuevo, mínimo), `app/modules/health/router.py`, borrado de `app/modules/health/schemas.py`, `migrations/env.py`, `scripts/seed.py` (`main()`), `tests/conftest.py`, `tests/test_config.py`, `tests/test_database.py`, `tests/test_health.py`, y tests nuevos del lifespan y de `security.py`.
- **Documentación**: `env.example`, `alembic.ini`, `migrations/README`, 4 líneas de `README.md`, `PLAN_PARCIAL.md`.
- **Entorno**: cada integrante actualiza su `.env` (agrega `POSTGRES_HOST`, `POSTGRES_PORT`, `JWT_SECRET`; `DATABASE_URL` y `DB_ECHO` quedan ignoradas). Sin dependencias nuevas: `pydantic-settings` ya está en `requirements.txt` desde CHG-00.
- **API**: sin cambios visibles; `/health/live` y `/health/ready` mantienen ruta, códigos y cuerpos.
- **Gobernanza**: HIGH (configuración de secretos y de la conexión a la base). Archivos compartidos de `core/`, `main.py` y `migrations/env.py`: revisa Matias. Nombres de variables, ubicación del hash ficticio y archivos extra (`migrations/env.py`, `tests/conftest.py`, `alembic.ini`, `migrations/README`, `scripts/seed.py`) confirmados por Matias el 2026-11-03 (ver «Decisiones confirmadas» de `design.md`); la descripción del PR lista esos archivos.
- **Desbloquea**: CHG-04 y CHG-10.
