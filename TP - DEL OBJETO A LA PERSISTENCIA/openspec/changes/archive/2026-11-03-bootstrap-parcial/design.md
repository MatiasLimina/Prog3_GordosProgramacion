# Design

## Context

Ver `proposal.md` (Why). Estado observado en la rama `chore/bootstrap-parcial`:

- `openspec/` y `.claude/` (comandos `opsx` y skills `openspec-*`) existen pero no están versionados. `openspec list` responde.
- En el árbol de trabajo, `TP_Cap1a4_Consigna.pdf` figura borrado y `Parcial_Cap1a6_Consigna.pdf` sin versionar; `AGENTS.md` y `REPARTO.md` siguen citando el primero.
- `requirements.txt` declara seis paquetes con piso mínimo (`paquete>=X.Y`); `requirements-dev.txt` lo incluye con `-r` y suma pytest, pytest-asyncio y httpx.
- `pytest.ini` marca con `db` los tests que usan `libreria_test` y los saltea si la base no responde; `REQUIRE_TEST_DB=1` convierte ese salto en fallo.
- El código sigue el patrón del TP 1–4: servicios que reciben `AsyncSession`, `app/core/pagination.py` con `limit/offset`, `DATABASE_URL` + `DB_ECHO` en `app/core/config.py`, seed en `scripts/seed.py`, `health` con `router.py` y `schemas.py`.
- `AGENTS.md` usa numeraciones del TP 1–4 (RN-10 = paginación, RN-12 = `IntegrityError`, casos C-01 a C-08) que el parcial reasigna (RN-10 = venta con stock, RN-12 = sólo agregado, casos C-01 a C-16).

## Goals / Non-Goals

**Goals:**
- Que `AGENTS.md` sea, después del merge, una guía que ningún agente pueda leer como contraria a la consigna del parcial, y que diga explícitamente qué partes del código todavía no la cumplen.
- Dejar instaladas las dependencias de CHG-03/10/11 sin que cambie ningún comportamiento observable de la app.
- Una línea base de `pytest` medida con la base levantada, comparable antes y después.

**Non-Goals:**
- Fijar firmas o nombres que deciden otros changes (la firma de `registrar_movimiento` es de CHG-13 con Matias; los nombres de los índices únicos parciales, de CHG-06/07). `AGENTS.md` enuncia la regla y remite al change.
- Escribir tests nuevos: no hay comportamiento nuevo que diseñar. Strict TDD aplica desde CHG-03.

## Decisions

### D1 · `skip_specs: true`
El change sólo toca documentación de trabajo, dependencias y herramientas. Inventar una capability «reglas del proyecto» crearía specs que describen archivos `.md` y no comportamiento del sistema, y que cada change siguiente tendría que mantener. **Alternativa descartada:** una capability `convenciones-proyecto` con requisitos sobre el contenido de `AGENTS.md`.

### D2 · `AGENTS.md` describe el estado objetivo, con una nota de transición
Las reglas se escriben como deben quedar al final del parcial. Una sección corta «Transición» lista lo que el código todavía hace a la manera del TP 1–4 (servicios con sesión, `pagination.py`, `DATABASE_URL`/`DB_ECHO`, `scripts/seed.py`) y el change que lo migra, con la regla: *código nuevo sigue las reglas del parcial; un módulo existente se migra sólo dentro de su change*. **Alternativas descartadas:** (a) describir sólo el estado actual y actualizar `AGENTS.md` en cada change — cada PR tocaría un archivo compartido y se pisarían; (b) dos documentos (TP y parcial) — duplica reglas que siguen vigentes y obliga a elegir cuál leer.

### D3 · Misma estructura de secciones, renumeración explícita
Se conservan las secciones 1–8 (stack, comandos, estructura, dueños, convenciones, reglas duras, git, terminado) para que el diff se pueda revisar, y se agregan dos: **Capas y transacciones** (UoW: quién construye, abre, confirma y cierra; `intento_acceso` como excepción con su comentario de tres partes) y **Acceso** (Settings sin secretos por defecto, cookie, 401/403, bcrypt fuera del bucle y con semáforo, hash antes de abrir la transacción, 72 bytes, roles vigentes consultados en la base, dos grupos de rutas). Las reglas del TP que siguen vigentes se mantienen (naming convention, `Decimal`, carga anticipada, `IntegrityError` → 409, nada de `create_all`, nada de consultar antes «para validar»). Toda referencia a RN-xx y C-xx usa la numeración del parcial; ninguna conserva la del TP.

Contenido que no puede faltar, con su fuente:

| Regla | Fuente |
|---|---|
| Router → Service → UoW → Repository → Model; router construye el UoW por dependencia y lo pasa sin abrir; servicio abre con `async with` y nunca construye; repos `flush()` y nunca `commit()`; UoW confirma, revierte y no cierra la sesión; dependencias de usuario/rol usan la misma sesión | Ej6, req. no funcionales |
| Un solo bloque `async with` para RN-02, RN-10 y RN-16 | Ej6 |
| `Settings` (pydantic-settings), `@computed_field` desde `POSTGRES_*`, sin default para contraseña de la base ni clave JWT; costo bcrypt, pool, `COOKIE_SECURE`, duración del token y `SQL_ECHO` en la configuración; motor y fábrica en el lifespan (`app.state`) | pág. 4, Ej1 |
| Envoltorio `{items, total, page, size, pages}`: `page` ≥ 1, `size` 1–100 (20), página de más → 422, cero resultados → una página vacía, `total` con los mismos filtros | Ej3 |
| `extra="forbid"` en contratos de entrada; nada de `password_hash` en salidas; `PATCH` con `exclude_unset`; 201/204/404/409/422 | Ej3 |
| Cookie `access_token` `HttpOnly`, `SameSite=Lax`, `Max-Age`, `Secure` configurable; leída de `request.cookies`; nunca en el cuerpo ni en `Authorization` | Ej4, req. no funcionales |
| 401 (sin cookie, token inválido/vencido, usuario inexistente/inactivo) vs 403 (rol no vigente, cambio de contraseña pendiente, no dueño); 429 con `Retry-After`; 503 en `/health/ready` | Ej4, Ej5, Ej1 |
| Stock: única vía de escritura (alta con `stock_inicial`, reposición, venta), `movimiento_stock` de sólo agregado por disparador, `stock` = suma de movimientos | RN-11, RN-12, pág. 6 |
| `intento_acceso`: única escritura con sesión y transacción propias, siempre confirmada, con comentario (qué hace distinto, por qué, costo) | Ej7 |
| Borrado lógico de `libro` con índice único parcial de ISBN entre vigentes; los índices únicos parciales llevan nombre y entran en el diccionario de mensajes de 409 | pág. 5–6, RN-01 |
| Estructura: `app/core/{config,database,security,dependencies,repository,paginacion,unit_of_work}.py`; por módulo `models, schemas, repository, unit_of_work, service, router`; `health` sólo `router.py`; módulo `usuarios`; `seed.py` en la raíz | págs. 8–9 |
| Terminado: `upgrade head` / `downgrade base` / `upgrade head` sobre base vacía; `python seed.py`; C-01 a C-16 en `test/`; `evidencia/` con C-14 y C-15 | Ej2, entrega |

`app/core/base.py`, `tipos.py` y `errors.py` se mantienen como archivos propios del grupo (la consigna permite agregar).

### D4 · Dueños por change, no por módulo
`PLAN_PARCIAL.md` reparte por change y asigna archivos compartidos a quien no es el lead (Lauti: `app/core/paginacion.py` y el registro en `app/models.py`; Nico: migraciones 0003/0004). La regla del TP («sólo A toca los compartidos») chocaría. Nueva regla: **los archivos compartidos los modifica el lead (Matias) o el responsable del change que los nombra en su sección «Archivos» del plan, siempre con revisión del lead.** La tabla de dueños pasa a ser: Matias — core (config, database, repository, unit_of_work, security, dependencies), `app/main.py`, auth, autorización, ventas, `AGENTS.md`, `requirements.txt`, `migrations/env.py`; Nico — modelos de libro/cliente/stock, migraciones 0003/0004, catálogo y clientes con repos + UoW, usuarios admin, pytest de integración; Lauti — `despliegue/`, `paginacion.py`, modelos de usuarios, contratos, seed, casos `.http`, zip. **Alternativa descartada:** mantener dueños por módulo como en `REPARTO.md` — no coincide con el plan vigente.

### D5 · Una rama por change: `<tipo>/<nombre-openspec>`
`<tipo>` es el tipo de commit convencional dominante (`feat`, `refactor`, `docs`, `build`, `chore`, `test`); sale de `main` y vuelve por PR revisado por otro integrante. La rama actual `chore/bootstrap-parcial` ya cumple. «Ramas por integrante» se resuelve con la tabla de dueños: cada integrante trabaja en las ramas de sus changes. **Alternativas descartadas:** ramas personales largas (`Lautaro`, `Nicolas`, que existen en el remoto) — acumulan cambios de varios changes y producen PRs grandes; los nombres `feat/C-0X-…` existentes — confunden el ID del change con el de los casos C.

### D6 · Pisos mínimos, sin techo
`pydantic-settings>=2.0`, `bcrypt>=4.0`, `PyJWT>=2.8`, igual que el resto del archivo y que la tabla de la consigna. Se escribe `PyJWT` (el paquete `jwt` de PyPI es otro y pisaría el módulo). No se pone techo a bcrypt: la versión 5 rechaza contraseñas de más de 72 bytes con una excepción, y la consigna lo resuelve en el contrato (CHG-09a), no fijando la versión.

### D7 · Dos commits, en el orden del plan
1. `chore(parcial): inicializar openspec y dependencias de auth` — `openspec/` (incluido este change), `.claude/commands/opsx/`, `.claude/skills/openspec-*`, `requirements.txt` y el cambio de PDF de consigna (ver Open Questions).
2. `docs(agents): actualizar reglas al parcial cap 1-6` — `AGENTS.md` y el estado de CHG-00 en `PLAN_PARCIAL.md`.

Nunca entra `../Parcial1_Proyecto_Libreria.zip` (está fuera de la carpeta y es un entregable armado).

### D8 · Línea base de pytest con la base levantada
`docker compose up -d` y `REQUIRE_TEST_DB=1 pytest`, para que los tests `db` no se salteen en silencio. Se anota «N passed» antes de tocar nada y se exige el mismo resultado al final. Si el puerto 5432 está ocupado, se usa `POSTGRES_PORT=5433` como indica `AGENTS.md`.

## Risks / Trade-offs

- [Un agente lee las reglas objetivo y «corrige» módulos que todavía no le tocan] → nota de transición con la regla de migrar sólo dentro del change, y la tabla de dueños.
- [La reescritura de `AGENTS.md` (archivo compartido, gobernanza HIGH para el equipo) mezcla una decisión del lead con texto generado] → el PR no se mergea sin la revisión de Matias; el diff conserva las secciones para que se lea por partes.
- [Otro change edita `AGENTS.md` mientras este PR está abierto] → PR chico y mergeado primero; CHG-01/02 trabajan en `despliegue/` y no lo tocan.
- [Instalar bcrypt 5.x rompe algo] → nada del código lo importa todavía; la línea base de pytest lo confirma.
- [Sin Docker no hay línea base real] → con `REQUIRE_TEST_DB=1` el fallo es explícito en vez de un verde engañoso.

## Migration Plan

Después del merge, cada integrante corre `pip install -r requirements-dev.txt`. Rollback: revertir los dos commits; no hay esquema ni datos involucrados.

## Open Questions

- **PDF de consigna**: por defecto el commit 1 versiona `Parcial_Cap1a6_Consigna.pdf` y confirma el borrado de `TP_Cap1a4_Consigna.pdf` que ya está en el árbol de trabajo (la copia del TP 1–4 vive en la carpeta de despliegue). Si Matias prefiere no versionar PDFs, se quitan las dos rutas del commit y `AGENTS.md` sólo los nombra.
- **`main.py` en la tabla de estructura**: la consigna lo lista sin el prefijo `app/`. Se mantiene `app/main.py` (lo que asume el plan y lo que arranca `uvicorn app.main:app`); conviene confirmarlo con la cátedra antes de CHG-20.
- **`health/schemas.py`**: la consigna dice que `health` sólo tiene `router.py`. Se documenta la regla y se deja la limpieza a CHG-03, que ya toca ese módulo.

### Respuestas (Matias, 2026-11-03)

Se aceptan los defaults de las tres preguntas:

1. Se versiona `Parcial_Cap1a6_Consigna.pdf` y se confirma el borrado de `TP_Cap1a4_Consigna.pdf` en el commit 1.
2. Se mantiene `app/main.py`; queda pendiente confirmarlo con la cátedra antes de CHG-20.
3. Se versionan `.claude/commands/opsx/` y `.claude/skills/openspec-*` en el commit 1.
