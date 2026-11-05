# Design

## Context

Motivación: ver `proposal.md` (Why). Requisitos: `specs/configuracion`, `specs/ciclo-de-vida` y `specs/salud`.

Estado observado en `feat/settings-lifespan` (desde `main` con CHG-00 mergeado):

- **Ya cumple buena parte del Ej1**: el lifespan de `app/main.py` crea motor y sessionmaker y los guarda en `app.state.engine` / `app.state.sessionmaker`; `get_session` los toma de ahí con `async with` (cierra la sesión); `expire_on_commit=False`; `connect_args={"timeout": 5}`; `/health/ready` hace `SELECT 1` y responde 503 con mensaje fijo (lo cubren 4 tests de `tests/test_health.py`). Lo que falta es la configuración en sí, el pool configurable, el hash ficticio y `health` sólo con `router.py`.
- `app/core/config.py`: `dataclass Settings(database_url, db_echo)` + `get_settings(environ=None)`, que lanza `RuntimeError` si falta `DATABASE_URL`. Hace `load_dotenv()` **al importar** (carga `.env` en `os.environ`).
- `app/core/database.py`: `crear_engine_y_sessionmaker(url, echo)` (una sola función) y `get_session(request)`.
- **Consumidores de la configuración** (grep de `get_settings`, `database_url`, `db_echo`, `crear_engine_y_sessionmaker`, `DATABASE_URL`):

| Consumidor | Qué usa hoy |
|---|---|
| `app/main.py` (lifespan) | `get_settings().database_url`, `.db_echo`, `crear_engine_y_sessionmaker` |
| `migrations/env.py` | `get_settings().database_url` (con `%` → `%%` para ConfigParser) |
| `scripts/seed.py` → `main()` | `get_settings()`, `crear_engine_y_sessionmaker(...)` (el resto del seed recibe la sesión; `tests/test_seed.py` sólo importa `cargar_datos`) |
| `tests/conftest.py` | `get_settings().database_url` → `make_url(...).set(database="libreria_test")`; `except RuntimeError` → skip/fail; al subproceso de Alembic le pasa `DATABASE_URL=<url de test>` |
| `tests/test_config.py` | `get_settings({...})` con un dict (12 casos) |
| `tests/test_database.py` | `crear_engine_y_sessionmaker` (2 tests) + naming convention (1) |
| 7 routers | sólo `get_session` (no cambia) |

- Verificado en el entorno del grupo (pydantic 2.13, pydantic-settings 2.15, SQLAlchemy 2.1, bcrypt 5.0, Python 3.14): con la configuración por defecto de `BaseSettings`, (a) una clave de `.env` que no es campo (`DB_ECHO=true`) hace **fallar** la construcción con `extra_forbidden`, y (b) el error de un campo faltante muestra `input_value={'postgres_password': 'su...eto', ...}`, es decir, **filtra la contraseña de la base** al log. Con `hide_input_in_errors=True` el error queda en `Field required [type=missing]`.
- Línea base: `REQUIRE_TEST_DB=1 pytest -q` → 321 passed (archivo `tasks.md` de `bootstrap-parcial`).

## Goals / Non-Goals

**Goals:**
- Que CHG-10/11 lean de un único objeto `Settings` todo lo que necesitan (costo de bcrypt, tamaño del semáforo de bcrypt, clave y duración del token, `COOKIE_SECURE`) y encuentren el hash ficticio en `app.state`, sin reabrir `config.py` ni el lifespan.
- Migrar todos los consumidores en el mismo change, con la suite en el mismo «321 passed» más los tests nuevos.
- Que ningún test nuevo necesite la base real (todos corren sin Docker).

**Non-Goals:**
- Hash/verificación de contraseñas, el semáforo de bcrypt en sí (acá sólo su tamaño en `Settings`), JWT y cookie (CHG-10/11). Acá sólo existe el hash ficticio.
- El algoritmo del JWT **no** entra en `Settings`: CHG-10 lo fija como constante `HS256` en `app/core/security.py` (confirmado por Matias).
- Documentación de evidencia del TP 1–4 (`docs/evidencia_c07.md` y similares): es histórica y nombra `DB_ECHO` a propósito; no se toca.
- Menciones de `DATABASE_URL`/`DB_ECHO` en `AGENTS.md`: las corrige Matias por su cuenta, fuera de este change.
- Dependencia de FastAPI para inyectar `Settings` en rutas: la agrega quien la necesite primero (CHG-10/11) leyendo `request.app.state.settings`.
- Cambiar `get_session` para que lo use el UoW (CHG-04).

## Decisions

### D1 · `Settings` de pydantic-settings con nombres de variable fijos
`class Settings(BaseSettings)` en `app/core/config.py`, con `model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)` (nombres sin distinguir mayúsculas, que es el comportamiento por defecto).

| Variable | Campo | Tipo / regla | Por defecto |
|---|---|---|---|
| `POSTGRES_USER` | `postgres_user` | `str`, no vacío | — (obligatoria) |
| `POSTGRES_PASSWORD` | `postgres_password` | `SecretStr`, no vacío | — (obligatoria, consigna) |
| `POSTGRES_DB` | `postgres_db` | `str`, no vacío | — (obligatoria) |
| `POSTGRES_HOST` | `postgres_host` | `str` | `localhost` |
| `POSTGRES_PORT` | `postgres_port` | `int` 1–65535 | `5432` |
| `JWT_SECRET` | `jwt_secret` | `SecretStr`, ≥ 32 caracteres | — (obligatoria, consigna) |
| `JWT_EXPIRE_MINUTES` | `jwt_expire_minutes` | `int` ≥ 1 | `60` |
| `BCRYPT_COST` | `bcrypt_cost` | `int` 4–31 (rango que acepta bcrypt) | `12` |
| `BCRYPT_MAX_CONCURRENTES` | `bcrypt_max_concurrentes` | `int` ≥ 1 | `4` |
| `COOKIE_SECURE` | `cookie_secure` | `bool` | `False` (en local se sirve por http) |
| `DB_POOL_SIZE` | `db_pool_size` | `int` ≥ 1 | `5` |
| `DB_MAX_OVERFLOW` | `db_max_overflow` | `int` ≥ 0 | `10` |
| `SQL_ECHO` | `sql_echo` | `bool` | `False` |

- **`extra="ignore"`**: sin esto, un `.env` viejo con `DATABASE_URL`/`DB_ECHO` o con `REQUIRE_TEST_DB` rompe el arranque (verificado). **Alternativa descartada:** el `extra="forbid"` por defecto, que convierte una migración de `.env` en un error de arranque para cada integrante.
- **`SecretStr`** para los dos secretos: no salen en `repr`, logs ni tracebacks; CHG-10 usa `settings.jwt_secret.get_secret_value()`. **Alternativa descartada:** `str`, que se imprime entero en cualquier `print(settings)`.
- **`min_length=32` en `JWT_SECRET`** y no vacío en `POSTGRES_PASSWORD`: una línea `JWT_SECRET=` en `.env` llega como `""` y pasaría la regla «sin valor por defecto»; el mínimo cierra ese hueco y rechaza claves débiles (`secrets.token_urlsafe(48)` da 64).
- `POSTGRES_USER`/`POSTGRES_DB` también obligatorias: no hay un valor razonable que no sea adivinar el entorno, y `docker-compose.yml` ya las exige. Host y puerto sí tienen valor por defecto.
- **`BCRYPT_MAX_CONCURRENTES`** (tamaño del semáforo que limita cuántas llamadas a bcrypt corren a la vez, consigna Ej4): lo declara CHG-03 para que CHG-10 no reabra `config.py`; CHG-10 crea el semáforo con ese valor. **Alternativa descartada:** que lo agregue CHG-10, que obligaría a otra revisión del archivo compartido.
- **Nombres frente a la consigna** (cruce con `Parcial_Cap1a6_Consigna.pdf`): la consigna nombra sólo `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT` (pág. 4, Ej1) y `SQL_ECHO` (págs. 15 y 20); todas coinciden. `JWT_SECRET`, `JWT_EXPIRE_MINUTES`, `BCRYPT_COST`, `BCRYPT_MAX_CONCURRENTES`, `COOKIE_SECURE`, `DB_POOL_SIZE` y `DB_MAX_OVERFLOW` son nombres del grupo (la consigna no fija ninguno). El `DATABASE_URL` que aparece en el env-file de Ej9/Ej10 (págs. 14–15) y en los casos D-05/D-06 (págs. 22–23) es del contenedor del **TP 1–4** (carpeta de despliegue aparte, pág. 9: «El despliegue no forma parte de esta estructura»), no de esta aplicación: no hay conflicto.
- `env_file=".env"` relativo: pydantic-settings lo resuelve contra el directorio actual; todos los comandos (`uvicorn`, `alembic`, `pytest`, seed) se corren desde la raíz, y los tests lo aíslan con `monkeypatch.chdir(tmp_path)` o `_env_file=None`. **Alternativa descartada:** ruta absoluta anclada al paquete, que impide aislar los tests del `.env` real del desarrollador.

### D2 · `database_url` como `@computed_field` armado con `sqlalchemy.engine.URL.create`
`@computed_field(repr=False)` `database_url -> str` = `URL.create("postgresql+asyncpg", username=..., password=postgres_password.get_secret_value(), host=..., port=..., database=...).render_as_string(hide_password=False)` (con `from sqlalchemy.engine import URL`). **Nunca** un f-string. Se conserva el **nombre** `database_url` para que `migrations/env.py` y `tests/conftest.py` no cambien de forma. `repr=False` porque la URL lleva la contraseña. **Alternativa descartada:** f-string, que rompe con `@`, `/` o `%` en la contraseña (escenario de la spec con los tres a la vez); `URL.create` escapa.
- El `.replace("%", "%%")` de `migrations/env.py` **se conserva**: la URL ya escapada lleva `%40`, `%2F`, `%25`, y ConfigParser interpreta `%` como interpolación.

### D3 · `get_settings()` sin caché, que traduce el error
`get_settings() -> Settings` construye `Settings()` y, ante `ValidationError`, lanza `RuntimeError` en español con las variables en mayúsculas tomadas de `e.errors()[i]["loc"]` (p. ej. «Configuración incompleta o inválida: JWT_SECRET, POSTGRES_PASSWORD. Copiá env.example a .env y completalo.»), con `from None`. Sigue siendo `RuntimeError`, así el `except RuntimeError` de `tests/conftest.py` no cambia. Se quita `load_dotenv()` del módulo: pydantic-settings lee `.env` por su cuenta y el módulo deja de tener efectos al importarse.
- **Una sola instancia por proceso de la app**: el lifespan la guarda en `app.state.settings`; quien la necesite dentro de una petición la lee de ahí. Alembic y el seed llaman a `get_settings()` una vez.
- **Alternativa descartada:** `@lru_cache` sobre `get_settings` (patrón de la documentación de FastAPI): estado global oculto que sobrevive entre tests y obliga a `cache_clear()`; el lifespan ya da el «una vez».

### D4 · `DB_ECHO` se abandona, sin alias
Sólo se lee `SQL_ECHO` (nombre de la consigna). Con `extra="ignore"`, un `DB_ECHO=true` viejo se ignora en silencio (el eco queda apagado): se avisa en el PR y en `env.example`. **Alternativa descartada:** `validation_alias=AliasChoices("SQL_ECHO", "DB_ECHO")`, que perpetúa dos nombres para lo mismo cuando sólo afecta a la consola local. La carpeta `despliegue/` es otro proyecto y no se ve afectada.

### D5 · `database.py`: dos funciones de construcción
- `crear_motor(settings) -> AsyncEngine`: `create_async_engine(settings.database_url, echo=settings.sql_echo, pool_size=settings.db_pool_size, max_overflow=settings.db_max_overflow, connect_args={"timeout": 5})`. `DB_POOL_SIZE` (por defecto 5) **debe** llegar a `pool_size=` (consigna Ej1: «el motor, con el tamaño del pool declarado en la configuración»); un test lo verifica con un espía sobre `create_async_engine` y otro con `engine.pool.size()` para el valor por defecto y uno explícito. El timeout de conexión queda como constante del módulo (no es algo que se ajuste por entorno).
- `crear_fabrica_sesiones(motor) -> async_sessionmaker[AsyncSession]` con `expire_on_commit=False`.
- `get_session(request)` no cambia (ya cumple; la spec lo fija con tests de cierre).
- Se elimina `crear_engine_y_sessionmaker` y se migran sus dos llamadores (`scripts/seed.py::main()` y el lifespan de `app/main.py`) **en el mismo paso**, para que `import app.main` no se rompa entre tareas; el lifespan se reescribe del todo después (D6). **Alternativa descartada:** conservarla como envoltorio: dos caminos para crear el motor, y la consigna (pág. 8) habla de «las funciones que crean el motor y la fábrica».
- Los nombres de `app.state` se mantienen (`engine`, `sessionmaker`) para no tocar a quien ya los lee; se agregan `settings` y `hash_ficticio`.

### D6 · Orden del lifespan
1. `settings = get_settings()` — si falla, no se creó nada (falla rápido, sin recursos colgados).
2. `hash_ficticio = await asyncio.to_thread(calcular_hash_ficticio, settings.bcrypt_cost)` — fuera del bucle (obligatorio: bcrypt bloquea ~300 ms con costo 12) y con el **mismo** `BCRYPT_COST` que los hashes reales; sin semáforo porque es una única llamada antes de atender peticiones (el semáforo es de CHG-10).
3. `engine = crear_motor(settings)`; `sessionmaker = crear_fabrica_sesiones(engine)`.
4. Se asignan `app.state.settings`, `.engine`, `.sessionmaker`, `.hash_ficticio`.
5. `try: yield` / `finally: await engine.dispose()` — el motor se cierra también si el apagado viene por una excepción.

El motor de SQLAlchemy no conecta al crearse: el arranque no depende de que la base esté arriba (eso lo informa `/health/ready`).

### D7 · Hash ficticio en `app/core/security.py` (archivo nuevo, mínimo)
`calcular_hash_ficticio(costo: int) -> str`: función pura y síncrona que hace `bcrypt.hashpw(secrets.token_urlsafe(32).encode(), bcrypt.gensalt(rounds=costo)).decode()`; es lo **único** que contiene `security.py` en este change. La contraseña es aleatoria y se descarta, así que nada verifica contra el hash. El lifespan la llama con `settings.bcrypt_cost`, el **mismo costo** que los hashes reales: si el costo difiriera, verificar contra el hash ficticio tardaría distinto que contra uno real y el tiempo de respuesta del login revelaría si el correo existe (rompe RN-08). Se testea que el costo del hash resultante es el de `BCRYPT_COST` y que la llamada corre en un hilo distinto del bucle (`asyncio.to_thread`). Devuelve `str` (formato `$2b$NN$...`), igual a como se guardaría `password_hash`. `token_urlsafe` da 43 bytes ASCII: por debajo de 72 y sin bytes nulos.
- **Por qué acá:** la consigna pone el hash ficticio en el lifespan (Ej1, CHG-03) y CHG-10 depende de CHG-03, así que no se puede esperar a CHG-10. `security.py` es su lugar natural (pág. 8: «hash con bcrypt»). CHG-10 completa el archivo (hash, verificación, semáforo, JWT) sin cambiar esta firma.
- **Alternativas descartadas:** (a) función privada en `main.py` — CHG-10/11 tendrían que importarla de `main` o duplicarla; (b) generar el hash con la futura `hashear_password` de CHG-10 — no existe todavía; cuando exista, CHG-10 puede reimplementar `calcular_hash_ficticio` encima de ella.

### D8 · `health` sólo con `router.py`
`LiveRead` y `ReadyRead` pasan a `app/modules/health/router.py` y se borra `schemas.py` (pág. 9: «El módulo health sólo tiene router.py»). La lógica de `/ready` no cambia: sigue con `Depends(get_session)`, `SELECT 1`, `except Exception` → log + 503 fijo.

### D9 · Migración de cada consumidor
| Consumidor | Cambio |
|---|---|
| `migrations/env.py` | Ninguno de código (`get_settings().database_url` sigue valiendo y el `.replace("%", "%%")` se conserva, D2); se actualiza el comentario. Alembic pasa a requerir `JWT_SECRET` (D10). |
| `alembic.ini`, `migrations/README` | Comentario/línea que nombraba `DATABASE_URL` → variables `POSTGRES_*`. |
| `README.md` | Sólo las 4 líneas que nombran `DATABASE_URL`/`DB_ECHO` (setup del `.env`, puerto 5433, base de test y diagnóstico con eco de SQL) pasan a `POSTGRES_*`/`SQL_ECHO`/`JWT_SECRET`. El resto del README es de CHG-20. |
| `AGENTS.md` | **No se toca** (lo corrige Matias). |
| `docs/evidencia_c07.md` y demás evidencia del TP 1–4 | **No se tocan** (históricos). |
| `scripts/seed.py` | Sólo `main()`: `settings = get_settings(); engine = crear_motor(settings); sessionmaker = crear_fabrica_sesiones(engine)`. El archivo es de Lauti (lo mueve CHG-17): se le avisa en el PR. |
| `tests/conftest.py` | `_url_test()` igual (mensaje de skip actualizado). `_alembic_upgrade_head`: pasa `POSTGRES_DB=libreria_test` en el entorno del subproceso en vez de `DATABASE_URL` (en pydantic-settings el entorno pisa a `.env`, D1). Al inicio: `os.environ.setdefault("JWT_SECRET", secrets.token_urlsafe(48))`, generada en cada corrida (ningún literal en el repo), para que la suite no dependa de la clave real del desarrollador. Docstring actualizado. **Se adapta en el mismo paso en que `Settings` deja de leer `DATABASE_URL`**: si no, el subproceso de Alembic ignoraría la URL de test y migraría la base de desarrollo. |
| `tests/test_config.py` | Se reescribe sobre `Settings`/`get_settings` con `monkeypatch.setenv/delenv` y `monkeypatch.chdir(tmp_path)` (o `_env_file=None`). Los casos de booleanos se conservan para `SQL_ECHO`. |
| `tests/test_database.py` | Test de naming convention sin cambios; los de echo/`expire_on_commit`/timeout pasan a `crear_motor` y `crear_fabrica_sesiones` + uno de pool. |
| `tests/test_health.py` | Sin cambios (sobrescribe `get_session`; `ASGITransport` no corre el lifespan). |
| `tests/test_lifespan.py` (nuevo) | Arranque, estado, hash ficticio (una vez, mismo costo, fuera del bucle), `dispose()`, falta de clave y `/ready` → 503 con la app arrancada contra un puerto cerrado (los dos últimos son el DoD de CHG-03). |
| `env.example` | Todas las variables de D1 con valores de ejemplo no secretos, `JWT_SECRET=` vacío con el comando para generarla, sin `DATABASE_URL`/`DB_ECHO`; `REQUIRE_TEST_DB` se documenta como variable de la línea de comandos (ya no se carga desde `.env`, D3). |

### D10 · Una sola clase `Settings` también para Alembic y el seed
Alembic y el seed construyen el `Settings` completo, así que exigen `JWT_SECRET` aunque no lo usen. Se acepta: el `.env` local y el env-file del servidor tienen todas las variables, y una sola clase evita dos fuentes de verdad. **Alternativa descartada:** `DatabaseSettings` aparte para Alembic — más superficie, y el seed de CHG-17 igual va a necesitar el costo de bcrypt.

### D11 · Estrategia de tests (Strict TDD, sin base real)
- Lifespan: se ejecuta con `async with lifespan(app)` (o `app.router.lifespan_context(app)`) con el entorno armado por `monkeypatch`, `monkeypatch.chdir(tmp_path)` para no leer el `.env` real y `BCRYPT_COST=4` para que tarde milisegundos. Un fixture limpia `app.state` al terminar para no contaminar `test_health.py`.
- `dispose()`: espía sobre el motor creado (envolviendo `crear_motor` con `monkeypatch` en `app.main`) que cuenta las llamadas.
- «Una sola vez»: contador sobre `calcular_hash_ficticio` monkeypatcheado en `app.main`, más dos peticiones a `/health/live` dentro del ciclo.
- «Fuera del bucle»: el doble de `calcular_hash_ficticio` registra `threading.get_ident()`; debe diferir del hilo del bucle del test.
- «Mismo costo»: con `BCRYPT_COST=5` el hash guardado empieza con `$2b$05$` (triangula el caso de costo 4).
- `/ready` → 503 real: `POSTGRES_HOST=127.0.0.1` y un puerto libre (se abre y cierra un socket para obtenerlo); petición con `ASGITransport` dentro del lifespan, sin override de `get_session`. El timeout de 5 s acota el peor caso en Windows.
- Ningún test nuevo lleva la marca `db`.

### D12 · Un commit
`feat(core): Settings con pydantic-settings y recursos en el lifespan` (plan, CHG-03). Los ciclos RED/GREEN se verifican en `tasks.md`; se commitea al final con la suite verde.

## Risks / Trade-offs

- [Cada `.env` local queda desactualizado: falta `JWT_SECRET` y la app no arranca] → el `RuntimeError` nombra la variable y dice qué hacer; `env.example` trae el comando para generarla; aviso en la descripción del PR.
- [`DB_ECHO=true` viejo se ignora en silencio y la evidencia de consultas no aparece] → `env.example` y el PR lo dicen; los `.http` que nombran `DB_ECHO` se reescriben en CHG-18.
- [`REQUIRE_TEST_DB=1` puesto en `.env` deja de tener efecto al quitar `load_dotenv`] → `env.example` lo documenta como variable de línea de comandos (`REQUIRE_TEST_DB=1 pytest`, como ya dice el README).
- [El test del 503 real depende de la red local (puerto cerrado) y puede tardar ~2 s en Windows] → puerto obtenido dinámicamente; timeout de conexión de 5 s; si resulta inestable, queda la cobertura de `test_health.py` con sesión rota.
- [Conflicto con CHG-10 sobre `app/core/security.py`] → este change crea sólo `calcular_hash_ficticio`; CHG-10 agrega el resto en el mismo archivo sin tocar esa función. Se coordina en la revisión.
- [Tocar archivos que el plan no lista en «Archivos» de CHG-03 (`migrations/env.py`, `tests/conftest.py`, `alembic.ini`, `migrations/README`, `scripts/seed.py` de Lauti, `README.md`)] → aprobados por Matias; cambios de pocas líneas, imprescindibles para no romper la suite; la descripción del PR los lista uno por uno y se avisa a Lauti del cambio en el seed.
- [`computed_field` aparece en `model_dump()` con la contraseña] → un `@model_serializer(mode="wrap")` quita `database_url` de `model_dump()`/`model_dump_json()` (hallazgo del advisor: `app.state.settings` queda a mano de CHG-10/11); `repr=False` cubre logs y tracebacks. Test: `test_serializar_no_muestra_los_secretos`.

## Migration Plan

1. Merge del PR (revisa Matias).
2. Cada integrante actualiza su `.env` desde `env.example`: agrega `POSTGRES_HOST`, `POSTGRES_PORT` (si usaba 5433, el mismo valor que ya tenía para Docker), `JWT_SECRET` generada con `python -c "import secrets; print(secrets.token_urlsafe(48))"`, y renombra `DB_ECHO` → `SQL_ECHO`. `DATABASE_URL` puede quedar o borrarse (se ignora).
3. `alembic upgrade head`, `uvicorn app.main:app` y `REQUIRE_TEST_DB=1 pytest` como verificación.
4. Rollback: revertir el commit; el `.env` nuevo sigue sirviendo al código viejo si conserva `DATABASE_URL`.

## Decisiones confirmadas

Confirmadas por Matias (2026-11-03), gobernanza HIGH:

1. **Nombres para CHG-10/11** — `JWT_SECRET` (`SecretStr`), `JWT_EXPIRE_MINUTES` (minutos, defecto 60, ≥ 1), `BCRYPT_COST` (defecto 12, 4–31), `COOKIE_SECURE` (defecto `false`). Se **agrega** `BCRYPT_MAX_CONCURRENTES` (defecto 4, ≥ 1) en este change. El algoritmo del JWT queda fuera de `Settings` (constante `HS256` de CHG-10). `DB_POOL_SIZE` (defecto 5) llega a `create_async_engine(pool_size=...)`; `DB_MAX_OVERFLOW` se mantiene (D1, D5).
2. **Hash ficticio** — `app/core/security.py` sólo con `calcular_hash_ficticio(costo)`, con `bcrypt.gensalt(rounds=costo)` y el mismo `BCRYPT_COST` que los hashes reales (RN-08); el lifespan lo llama con `await asyncio.to_thread(...)` y lo guarda en `app.state.hash_ficticio` (D6, D7).
3. **`DB_ECHO` → `SQL_ECHO`** sin alias y sin `load_dotenv()` (D3, D4). `tests/conftest.py` pasa `POSTGRES_DB=libreria_test` al subproceso de Alembic. `docs/evidencia_c07.md` y la evidencia del TP 1–4 no se tocan.
4. **Alembic y seed** usan el `Settings` completo (D10); `tests/conftest.py` fija una `JWT_SECRET` de prueba generada en cada corrida, así la suite no depende de `.env` (D9).
5. **Validaciones** — `JWT_SECRET` `min_length=32`; `POSTGRES_USER`/`PASSWORD`/`DB` obligatorias, host y puerto con defecto; `JWT_EXPIRE_MINUTES` ≥ 1. URL con `sqlalchemy.engine.URL.create(...).render_as_string(hide_password=False)`, nunca f-string; escenario con `@`, `/` y `%` juntos; `.replace("%", "%%")` de `migrations/env.py` se conserva (D2).
6. **Documentación** — este change corrige las 4 líneas de `README.md` que nombran `DATABASE_URL`/`DB_ECHO`; `AGENTS.md` no se toca (lo corrige Matias); `PLAN_PARCIAL.md` sí (estado de CHG-03).
7. **Archivos extra aprobados** — `migrations/env.py`, `tests/conftest.py`, `alembic.ini`, `migrations/README`, `scripts/seed.py`: la descripción del PR los lista y se avisa a Lauti del cambio en el seed.

### Aviso fuera de este change (para CHG-01, Lauti)
El env-file del contenedor que pide la consigna (Ej9, pág. 15) trae `SQL_ECHO=false`, pero el TP 1–4 que se despliega lee `DB_ECHO`: ahí `SQL_ECHO` se ignora (el eco queda en su valor por defecto, apagado, así que el efecto es el pedido). No afecta a CHG-03; se menciona para que CHG-01 lo tenga presente.

## Open Questions

Ninguna pendiente para CHG-03.
