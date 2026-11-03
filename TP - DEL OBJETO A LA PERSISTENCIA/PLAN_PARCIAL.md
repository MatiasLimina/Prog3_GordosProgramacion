# PLAN_PARCIAL.md — Backlog de changes del Parcial Cap 1–6

Plan de ejecución del parcial «La librería con acceso, transacciones y despliegue en el VPS».
**Fuente de verdad:** `Parcial_Cap1a6_Consigna.pdf`. Si este plan la contradice, gana la consigna y se corrige este archivo por PR.

> **Para agentes de IA:** antes de trabajar en un change, buscá su ID acá (`CHG-XX`), leé su sección completa
> (entregables, DoD, "Leer antes" y dependencias) y verificá que sus dependencias estén mergeadas.
> No toques archivos de otro change sin avisar. Al terminar, marcá el estado en la tabla de seguimiento.

---

## 0. Contexto rápido

- **Dos proyectos distintos**, que van en dos carpetas del zip:
  - `parcial/` ← esta carpeta (`TP - DEL OBJETO A LA PERSISTENCIA`): el TP ampliado con usuarios, roles, repositorios + Unit of Work, stock por movimientos.
  - `despliegue/` ← `TP - DEL OBJETO A LA PERSISTENCIA (despliegue)`: el TP de los capítulos 1–4 **tal como se entregó**, más `Dockerfile`, `.dockerignore`, `env.example`, `DEPLOY.md` y `evidencia/`. **No lleva ningún cambio del parcial.**
- **Capas obligatorias:** Router → Service → UoW → Repository → Model.
  - El router construye el UoW con una dependencia y se lo pasa al servicio **sin abrirlo**.
  - El servicio lo abre con `async with` y **nunca lo construye**.
  - Los repositorios hacen `flush()`, **nunca** `commit()`.
  - El UoW confirma al salir, revierte si hay una excepción y **no cierra la sesión**.
- **Integrantes:** Matias (lead), Nico (persistencia y APIs), Lauti (tareas acotadas, commits constantes).

### Gotchas conocidos (leer antes de empezar)

1. `AGENTS.md` todavía describe el TP 1–4 (limit/offset, `DB_ECHO`, servicios que reciben la sesión, `DATABASE_URL`). **Hasta que se cierre CHG-00, ante la duda gana este plan y la consigna.**
2. La consigna usa `python seed.py` **en la raíz**; el TP lo tiene en `scripts/seed.py` (CHG-17).
3. Despliegue: el TP lee `DB_ECHO`, mientras que la consigna menciona `SQL_ECHO=false` en el env-file. No rompe nada (por defecto queda en false), pero hay que anotarlo en `DEPLOY.md`. D-05 ya pasa: `get_settings()` lanza un error si falta `DATABASE_URL`.
4. En el contenedor, el seed se corre con `docker exec libreria python -m scripts.seed`.
5. `--autogenerate` puede manejar mal el paso de `uq_libro_isbn` (UNIQUE) al índice único parcial, y no ve funciones ni disparadores. La migración 0003 se lee línea por línea y la 0004 se escribe a mano.
6. Healthcheck en Alpine: usar `wget` contra `http://127.0.0.1:8000/...`, **nunca `localhost`**, porque resuelve primero a `::1` y uvicorn escucha sólo IPv4.
7. La base del VPS **no está en `localhost`** desde el contenedor: usar `host.docker.internal` con `--add-host=host.docker.internal:host-gateway`, o la dirección que entregue la cátedra.
8. `intento_acceso` es la **única** escritura con sesión y transacción propias (Ej7). Todo lo demás comparte el UoW de la petición.

---

## 1. Fases y peso en la nota

| Fase | Hito | Changes | Ejercicios (peso) |
|---|---|---|---|
| **F0 · Setup e infraestructura** | Base lista, reglas al día y despliegue andando | CHG-00 a 03 | Ej1 (6 %), Ej9 (11 %), Ej10 (7 %) |
| **F1 · Dominio central** | Modelos, migraciones, capas base y contratos | CHG-04 a 09b | Ej2 (10 %), Ej3 (8 %), Ej6 base |
| **F2 · Capa externa / API** | Auth, autorización y módulos pasados a UoW | CHG-10 a 16 | Ej4 (14 %), Ej5 (12 %), Ej6 (16 %), Ej7 (10 %), Ej8 (6 %) |
| **F3 · Pruebas y documentación** | Seed, casos C, evidencia y zip | CHG-17 a 20 | Casos C-01 a C-16, entrega |

---

## 2. Seguimiento

Estados: `pendiente` · `en curso` · `en PR` · `mergeado`

| ID | Change (nombre openspec) | Responsable | Depende de | Estado |
|---|---|---|---|---|
| CHG-00 | `bootstrap-parcial` | Matias | — | pendiente |
| CHG-01 | `deploy-imagen` | Lauti | — | pendiente |
| CHG-02 | `deploy-vps` | Lauti (+Matias) | CHG-01, accesos al VPS | pendiente |
| CHG-03 | `settings-lifespan` | Matias | CHG-00 | pendiente |
| CHG-04 | `core-repository-uow` | Matias | CHG-03 | pendiente |
| CHG-05 | `paginacion-envoltorio` | Lauti | CHG-00 | pendiente |
| CHG-06 | `modelos-usuarios` | Lauti | CHG-00 | pendiente |
| CHG-07 | `modelos-libro-cliente-stock` | Nico | CHG-00 | pendiente |
| CHG-08 | `migraciones-3-4` | Nico | CHG-06, CHG-07 | pendiente |
| CHG-09a | `schemas-auth-usuarios` | Lauti | CHG-00 | pendiente |
| CHG-09b | `schemas-catalogo-ventas` | Lauti | CHG-00 | pendiente |
| CHG-10 | `security-core` | Matias | CHG-03 | pendiente |
| CHG-11 | `auth-endpoints` | Matias | CHG-04, 08, 09a, 10 | pendiente |
| CHG-12 | `autorizacion-grupos-rutas` | Matias | CHG-11 | pendiente |
| CHG-13 | `catalogo-repos-uow` | Nico | CHG-04, 05, 08, 09b | pendiente |
| CHG-14 | `usuarios-admin` | Nico | CHG-12 | pendiente |
| CHG-15 | `clientes-repos-uow` | Nico | CHG-04, 05, 08 | pendiente |
| CHG-16 | `ventas-transaccional` | Matias | CHG-12, 13, 15 | pendiente |
| CHG-17 | `seed-parcial` | Lauti | CHG-08, CHG-10 | pendiente |
| CHG-18 | `casos-http` | Lauti (Nico revisa) | CHG-17 y el change de cada caso | pendiente |
| CHG-19 | `pytest-integracion` | Nico | CHG-13, 16 | pendiente |
| CHG-20 | `entrega-zip` | Lauti + Matias | todo | pendiente |

---

## 3. Backlog detallado

### F0 · Setup e infraestructura

#### CHG-00 · `bootstrap-parcial` — Matias
- **Entregables:**
  - `openspec init` en esta carpeta.
  - Reescribir `AGENTS.md` con las reglas del parcial: UoW, Settings, envoltorio `{items, total, page, size, pages}`, cookie, 401/403, stock con una sola vía de escritura.
  - Agregar `pydantic-settings`, `bcrypt` y `PyJWT` a `requirements.txt`.
  - Definir ramas por integrante.
- **Leer antes:** consigna págs. 2 («Qué cambia»), 4 (Requisitos técnicos) y 8–9 (Estructura obligatoria).
- **DoD:** `openspec list` funciona. `AGENTS.md` no contradice la consigna. `pytest` en verde como línea base.
- **Commits:** `chore(parcial): inicializar openspec y dependencias de auth` · `docs(agents): actualizar reglas al parcial cap 1-6`

#### CHG-01 · `deploy-imagen` — Lauti (Ej9)
- **Dónde:** `TP - DEL OBJETO A LA PERSISTENCIA (despliegue)/`. **No tocar la lógica del TP.**
- **Entregables:**
  - `Dockerfile` que:
    - parte de `python:3.12-alpine`;
    - instala `requirements.txt` antes de copiar el código, con `--no-cache-dir`;
    - crea un usuario sin privilegios y lo activa con `USER`;
    - al arrancar corre `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000`;
    - declara un `HEALTHCHECK` con `wget -qO- http://127.0.0.1:8000/health/ready`.
  - `.dockerignore` (`.env`, `.venv`, `.git`, `__pycache__`).
  - `env.example` con la forma de `DATABASE_URL` (`postgresql+asyncpg://...`), sin valores reales.
- **Leer antes:** consigna págs. 14–15 (Ej9).
- **DoD:** se cumplen en local D-01, D-05, D-06 y D-07; `docker ps` muestra `healthy`.
- **Commits (uno por punto):** `build(docker): Dockerfile sobre python:3.12-alpine` · `build(docker): usuario sin privilegios` · `build(docker): healthcheck sobre /health/ready` · `build(docker): .dockerignore sin secretos`

#### CHG-02 · `deploy-vps` — Lauti, con apoyo de Matias (Ej10)
- **Entregables:**
  - Contenedor corriendo en el VPS con `docker run -d --name libreria -p <puerto>:8000 --restart unless-stopped --env-file <archivo> --add-host=host.docker.internal:host-gateway libreria`.
  - Seed cargado con `docker exec libreria python -m scripts.seed`.
  - `DEPLOY.md` con la URL pública, la fecha y hora, los comandos `build` y `run` completos (el nombre del env-file, nunca su contenido), los cambios hechos al TP y cómo actualizar la app.
  - `evidencia/` con la salida de D-01 a D-08.
- **Leer antes:** consigna págs. 15–16 y 22–23 (casos D).
- **DoD:** la URL pública responde a D-03. D-04 pasa: después de `rm -f` y un nuevo `run`, los datos siguen ahí y las migraciones no se repiten. **Tiene que seguir en línea hasta que se publiquen las notas.**
- **Commits:** `docs(deploy): DEPLOY.md con URL y comandos` · `docs(deploy): evidencia D-0X` (uno por caso)

#### CHG-03 · `settings-lifespan` — Matias (Ej1)
- **Archivos:** `app/core/config.py`, `app/core/database.py`, `app/main.py`, `app/modules/health/router.py`, `env.example`.
- **Entregables:**
  - `Settings` (pydantic-settings) que arma la URL con `@computed_field` desde `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` y `POSTGRES_PORT`, con el driver `postgresql+asyncpg`.
  - Sin valor por defecto para la contraseña de la base ni para la clave JWT.
  - Costo de bcrypt, tamaño del pool, `COOKIE_SECURE`, duración del token y `SQL_ECHO` salen de la configuración.
  - El lifespan crea el motor y la fábrica de sesiones en `app.state`, calcula el hash ficticio una sola vez y llama a `dispose()` al apagar.
  - `get_session` toma la fábrica de `app.state` y usa `expire_on_commit=False`.
  - `/health/ready` ejecuta `SELECT 1` y responde 503 si la base no contesta.
- **DoD:** tests de que la app no arranca sin la clave y de que `ready` da 503 con la base caída.
- **Commit:** `feat(core): Settings con pydantic-settings y recursos en el lifespan`

### F1 · Dominio central

#### CHG-04 · `core-repository-uow` — Matias (Ej6, base)
- **Archivos:** `app/core/repository.py`, `app/core/unit_of_work.py`.
- **Entregables:**
  - `BaseRepository[T]`: recibe `session` y la **clase del modelo** en el constructor, y ofrece `get_by_id`, `get_all`, `count`, `add`, `update` y `delete`. `add` y `update` hacen `flush()`.
  - `SoftDeleteRepository[T](BaseRepository[T])`: filtra los dados de baja y agrega `get_by_id_including_deleted` y `soft_delete`.
  - `UnitOfWork` base como gestor de contexto asincrónico: confirma al salir, revierte si hay una excepción y no cierra la sesión.
  - El patrón de dependencia con el que el router construye el UoW de cada módulo.
- **DoD:** tests que muestran un rollback cuando hay una excepción y la sesión abierta después del bloque.
- **Commit:** `feat(core): BaseRepository, SoftDeleteRepository y UnitOfWork`

#### CHG-05 · `paginacion-envoltorio` — Lauti
- **Archivos:** `app/core/paginacion.py`, más su test.
- **Entregables:**
  - `Page[T]` con `{items, total, page, size, pages}`.
  - `page` ≥ 1; `size` de 1 a 100, por defecto 20.
  - Con cero resultados, `pages = 1` y la página va vacía.
  - Pedir una página de más da 422 con el mensaje «La página 4 no existe: hay 3».
- **Leer antes:** consigna pág. 10 (Ej3) y pág. 19 (ejemplo de listado).
- **DoD:** tests unitarios con 0 resultados, 1, un múltiplo exacto y un sobrante.
- **Commit:** `feat(core): envoltorio de paginación page/size`

#### CHG-06 · `modelos-usuarios` — Lauti
- **Archivos:** `app/modules/usuarios/models.py`, `app/models.py` (registro).
- **Entregables:**
  - `Usuario`: `email` UNIQUE, sin columna `rol`.
  - `AsignacionRol`: CHECK de rol dentro de ADMIN, VENDEDOR y CLIENTE; índice único parcial `(usuario_id, rol) WHERE revocada_en IS NULL` (`postgresql_where`).
  - `IntentoAcceso`: índice `(email, ip, cuando)`.
  - `EventoSeguridad`: `actor` es texto.
  - Todas las fechas son `timestamptz`. `Usuario.cliente` se declara con un string bajo `TYPE_CHECKING`.
- **Leer antes:** consigna págs. 4–6 (Modelo de dominio).
- **DoD:** test de nombres de constraints; los modelos importan sin errores.
- **Commit:** `feat(usuarios): modelos de acceso y seguridad`

#### CHG-07 · `modelos-libro-cliente-stock` — Nico
- **Archivos:** `app/modules/libros/models.py`, `app/modules/clientes/models.py`.
- **Entregables:**
  - `Libro.borrado_en` (timestamptz, nullable) con índice único parcial de `isbn` `WHERE borrado_en IS NULL`, **en lugar del UNIQUE**. Siguen los CHECK de precio y stock.
  - `MovimientoStock` (en `libros`): `libro_id`, `venta_id` (nullable), `usuario_id`, `cantidad` con CHECK `<> 0`, `motivo` y `cuando`. Un índice en cada FK.
  - `Cliente.usuario_id` UNIQUE y nullable; `Cliente.usuario` con `uselist=False`.
  - Navegación declarada en los dos extremos.
- **DoD:** tests de metadata.
- **Commit:** `feat(libros): borrado lógico, movimiento_stock y acceso del cliente`

#### CHG-08 · `migraciones-3-4` — Nico (Ej2 + Ej7)
- **Entregables:**
  - Migración 0003 con `--autogenerate`: tablas de acceso, `movimiento_stock` y los cambios en `cliente` y `libro`. Se lee antes de aplicarla y lleva un comentario que lo dice; cada corrección manual lleva un comentario que la explica.
  - Migración 0004 escrita a mano: función y disparador `BEFORE UPDATE OR DELETE` sobre `movimiento_stock`, con su `downgrade`.
  - `test/solo_agregado.sql` (C-14).
- **DoD:** sobre una base vacía funcionan `upgrade head`, `downgrade base` y otra vez `upgrade head`. C-14 rechaza los dos intentos.
- **Commits:** `feat(migrations): 0003 acceso y stock (autogenerada, revisada)` · `feat(migrations): 0004 disparador de sólo agregado`

#### CHG-09a · `schemas-auth-usuarios` — Lauti
- **Archivos:** `app/modules/usuarios/schemas.py` (y los contratos de auth).
- **Entregables:**
  - Una base `extra="forbid"` para todos los contratos de entrada.
  - Validador de contraseña de hasta **72 bytes** (`len(s.encode())`, no caracteres), aplicado a todo campo que llega a bcrypt: registro, login, alta de personal, contraseña actual y nueva.
  - `vence_en` con zona horaria y en el futuro; si no, 422.
  - Ningún contrato de salida incluye `password_hash`.
- **DoD:** un test por validador, incluido un caso con «ñ» que cruza el límite.
- **Commit:** `feat(schemas): contratos de auth y usuarios`

#### CHG-09b · `schemas-catalogo-ventas` — Lauti
- **Entregables:** `LibroCreate` con `stock_inicial` y `autores`; `LibroUpdate` sólo con título y precio, sin stock; `ReponerIn`; `extra="forbid"` en clientes y ventas. `VentaCreate` no lleva precio, total ni fecha.
- **DoD:** un `PATCH` con `stock` da 422 (C-16).
- **Commit:** `feat(schemas): stock_inicial y reposición; stock fuera del PATCH`

### F2 · Capa externa / API

#### CHG-10 · `security-core` — Matias (Ej4)
- **Archivos:** `app/core/security.py`.
- **Entregables:** hash y verificación con bcrypt dentro de `asyncio.to_thread` y bajo un `asyncio.Semaphore`, con el costo de la configuración. Emisión y verificación del JWT (PyJWT) con `sub`, `exp` y `roles`.
- **DoD:** tests de hash y verificación, token vencido y token alterado.
- **Commit:** `feat(core): hash bcrypt fuera del bucle y JWT`

#### CHG-11 · `auth-endpoints` — Matias (Ej4 + Ej7)
- **Entregables:**
  - Login en este orden: (1) contar fallos en `intento_acceso` (5 en 60 s por email e IP → 429 con `Retry-After`, sin calcular ningún hash); (2) verificar contra el hash real o contra el ficticio (RN-08).
  - `intento_acceso` se escribe desde una **sesión y transacción propias**, con un comentario que dice qué hace distinto, por qué no comparte la transacción y cuál es su costo.
  - Cookie `access_token` con `HttpOnly`, `SameSite=Lax`, `Max-Age` y `Secure` configurable. El cuerpo no trae el token.
  - `/auth/registro`: RN-02 en un solo UoW; el hash se calcula **antes** de abrir la transacción.
  - `/auth/logout` borra la cookie. `/auth/yo` devuelve el usuario, sus roles vigentes y los del token.
  - `/auth/cambiar-password` deja un evento (RN-16).
- **DoD:** C-02, C-03, C-04 y C-05.
- **Commits:** uno por endpoint, por ejemplo `feat(auth): login con límite de intentos y hash ficticio`

#### CHG-12 · `autorizacion-grupos-rutas` — Matias (Ej5)
- **Archivos:** `app/core/dependencies.py`, `app/main.py`.
- **Entregables:**
  - `get_usuario_actual` responde 401 si no hay cookie, si el token es inválido o venció, o si el usuario no existe o está inactivo.
  - `requiere_rol` responde 403 y consulta los roles vigentes **en la base** en cada petición.
  - Control del cambio obligatorio de contraseña.
  - Dos routers en `main.py`: uno abierto y uno protegido, con el control montado una sola vez.
  - Las dependencias usan **la misma sesión** que el UoW.
- **DoD:** C-01, C-06, C-07 (diferencia en `/auth/yo`) y C-09.
- **Commit:** `feat(auth): grupos abierto/protegido y requiere_rol contra la base`

#### CHG-13 · `catalogo-repos-uow` — Nico (Ej3 + Ej6)
- **Entregables:**
  - editoriales, géneros, autores y libros con `repository.py`, `unit_of_work.py` y servicios que reciben el UoW. Listados con el envoltorio.
  - `LibroRepository` hereda de `SoftDeleteRepository`; la precarga se declara dentro de cada método.
  - **Un único punto de escritura del stock** (por ejemplo `registrar_movimiento(libro_id, cantidad, motivo, usuario_id, venta_id=None)`), que usan el alta del libro, la reposición y las ventas. **Acordar la firma con Matias antes de CHG-16.**
  - `POST /libros` con `stock_inicial`, que deja el movimiento «Stock inicial».
  - `POST /libros/{id}/reponer`, `GET /libros/{id}/movimientos`, `DELETE /libros/{id}` → 204.
  - Un libro dado de baja no se vende ni se repone (409).
- **DoD:** C-13 y C-16; el stock coincide con la suma de movimientos.
- **Commits:** un módulo por commit, por ejemplo `refactor(libros): repositorio con borrado lógico y UoW`

#### CHG-14 · `usuarios-admin` — Nico (Ej5 + RN-16)
- **Entregables:**
  - `POST /usuarios`: alta de personal con contraseña provisoria y `debe_cambiar_password=true`.
  - `GET`, `POST` y `DELETE` de `/usuarios/{id}/roles`. Revocar escribe `revocada_en`; reasignar un rol vencido cierra la fila anterior y abre una nueva.
  - RN-05: nadie se revoca su propio ADMIN y nunca quedan cero administradores vigentes (409).
  - `GET /eventos` paginado. Cada alta y cada cambio de rol deja un evento en la misma transacción.
- **DoD:** C-07 (revocación) y C-08.
- **Commit:** `feat(usuarios): alta de personal y gestión de roles con vigencia`

#### CHG-15 · `clientes-repos-uow` — Nico
- **Entregables:** clientes y perfil pasados a repositorios + UoW; `GET /clientes/{id}/ventas`.
- **Commit:** `refactor(clientes): repositorios y Unit of Work`

#### CHG-16 · `ventas-transaccional` — Matias (Ej6 + Ej8)
- **Entregables:**
  - RN-09 y RN-10 en **un solo bloque `async with uow`**: venta, renglones con el precio copiado, total calculado, descuento de stock y un movimiento por renglón, todo por el punto único de CHG-13.
  - 409 si no alcanza el stock, si el libro está dado de baja o si el cliente o el libro no existen. No queda ninguna escritura.
  - `BackgroundTasks` con `await asyncio.sleep(0.5)` y un log visible con el arranque normal de uvicorn (logger `uvicorn.error` o uno configurado); corre sólo si la venta se confirmó.
  - `GET /ventas/{id}` sin `requiere_rol`: lo puede ver el personal o el cliente dueño; si no, 403.
  - `GET /mis-ventas`.
  - El detalle de una venta (cliente, renglones y libro de cada renglón, aunque esté dado de baja) se resuelve con un número fijo de consultas.
- **DoD:** C-10, C-11, C-12 y C-15.
- **Commit:** `feat(ventas): registro atómico con stock y aviso en segundo plano`

### F3 · Pruebas y documentación

#### CHG-17 · `seed-parcial` — Lauti
- **Entregables:** `seed.py` **en la raíz**. Vacía las tablas y carga:
  - Usuarios: admin y admin2 (ADMIN), vendedor (VENDEDOR), ana (CLIENTE) y nuevo (VENDEDOR con cambio de contraseña obligatorio).
  - 3 editoriales, 3 géneros, 6 autores y los 5 libros.
  - Clientes: Lucía (con perfil), Tomás y Ana (vinculada al usuario ana).
  - La venta 1: Lucía, 1 Rayuela y 2 Ficciones, total 69000.00.
  - Movimientos: «Stock inicial» de cada libro (Rayuela 11, Ficciones 10) más las salidas −1 y −2.
  - El evento de `SISTEMA` «Carga de los datos iniciales».
  - Las contraseñas de mentira viven sólo en este archivo.
- **Leer antes:** consigna págs. 19–20.
- **DoD:** en los 5 libros, el stock es igual a la suma de sus movimientos.
- **Commit:** `feat(seed): datos iniciales del parcial`

#### CHG-18 · `casos-http` — Lauti (Nico revisa)
- **Entregables:** archivos `.http` en `test/` para C-01 a C-16, cada uno con la respuesta esperada en un comentario. Las sesiones múltiples usan `# @name` y `# @no-cookie-jar` con `Cookie: {{loginX.response.headers.Set-Cookie}}`.
- **Leer antes:** consigna págs. 21–23.
- **Commits:** uno por caso, por ejemplo `test(http): C-05 límite de intentos`

#### CHG-19 · `pytest-integracion` — Nico
- **Entregables:** tests de que el stock coincide con la suma de movimientos después de cada venta, de la atomicidad de RN-02 y RN-10, y del conteo de consultas de C-15 (2 contra 4 renglones).
- **Commit:** `test(integracion): invariantes de stock y atomicidad`

#### CHG-20 · `entrega-zip` — Lauti + Matias
- **Entregables:**
  - `README.md` con los nombres y apellidos de los integrantes y los pasos desde cero: venv, dependencias, `.env` y cómo generar la clave de firma, `alembic upgrade head`, `python seed.py` y uvicorn.
  - `evidencia/` con C-14 (psql) y C-15 (consola).
  - Script que arma `Parcial_Cap1a6_<Grupo>.zip` con `parcial/` y `despliegue/`, sin `.venv`, `__pycache__` ni `.env`.
  - Revisión del historial de git en busca de secretos.
  - Revisión final del diff con el advisor.
- **Commit:** `chore(entrega): README, evidencia y armado del zip`

---

## 4. Mapa de dependencias

```
Lauti:  CHG-01 ─► CHG-02 (VPS)          CHG-05   CHG-06   CHG-09a/b ─────► CHG-17 ─► CHG-18 ─► CHG-20
                                          │        │          │              ▲
Matias: CHG-00 ─► CHG-03 ─► CHG-04 ──────┼────────┼──► CHG-10 ─► CHG-11 ─► CHG-12 ─► CHG-16 ──┤
                              │           │        │                          │        ▲        │
Nico:                         └─► CHG-07 ─┴────────┴─► CHG-08 ─► CHG-13 ───────┼────────┘        │
                                                                  CHG-14 ◄─────┘ (necesita 12)    │
                                                                  CHG-15 ─► CHG-19 ──────────────┘
```

- **Paralelo desde el día 1:** CHG-01/02 (Lauti, independiente) y CHG-00/03 (Matias).
- **Cuello de botella 1:** CHG-04 (repo/UoW base). Entregarlo chico y rápido: Nico no puede pasar módulos a UoW sin él.
- **Cuello de botella 2:** CHG-08 (migraciones). Necesita los dos lotes de modelos (CHG-06 y CHG-07). Los `models.py` van en PRs propios y primero.
- **Punto de integración:** CHG-16 usa el punto único de stock de CHG-13. La firma se acuerda apenas termina CHG-07.
- **Riesgo:** el 18 % de la nota (despliegue) depende de Lauti. Checkpoint con Matias después de CHG-01 y otro con el VPS ya arriba.

## 5. Reglas de trabajo para todos los agentes

- Un change = una rama = uno o más PRs chicos, revisados por otro integrante.
- Commits convencionales en español (`feat`, `fix`, `refactor`, `test`, `docs`, `build`, `chore`), con el scope del módulo.
- Strict TDD: un test que falla primero, después el mínimo código que lo hace pasar.
- No consultar antes si algo existe «para validar»: se escribe y la base decide (FK, UNIQUE o índice parcial → 409 con mensaje propio).
- Nunca `create_all`, nunca `float` para dinero, nunca carga perezosa, nunca secretos en el repo ni en la imagen.
