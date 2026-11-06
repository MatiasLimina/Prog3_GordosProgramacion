# AGENTS.md — Librería (FastAPI + PostgreSQL) · Parcial Cap 1–6

Guía canónica del proyecto para los integrantes del grupo y para cualquier agente de IA.
Fuente de verdad del enunciado: `Parcial_Cap1a6_Consigna.pdf`. Backlog de changes y reparto: [`PLAN_PARCIAL.md`](PLAN_PARCIAL.md)
(antes de trabajar en un change, leé su sección `CHG-XX`). `REPARTO.md` es el registro histórico del TP 1–4.
Si algo de este archivo contradice la consigna, **gana la consigna** y se corrige este archivo por PR.

Este archivo describe el **estado objetivo** al terminar el parcial. Qué partes del código todavía siguen el patrón del TP 1–4 y qué change las migra: ver «Transición» (sección 9).

---

## 1. Proyecto y stack

API para una librería: catálogo (editoriales, géneros, autores, libros), clientes, ventas, y ahora acceso con usuarios y roles, stock por movimientos y repositorios con Unit of Work (UoW).
El despliegue en el VPS (Docker) es **otro proyecto**: el TP 1–4 tal como se entregó, en la carpeta hermana `Despliegue`, que en el zip se llama `despliegue/`. No lleva ningún cambio del parcial y **nada del despliegue se crea dentro de este repositorio**.

| Componente | Versión mínima | Notas |
|---|---|---|
| Python | 3.12 | |
| FastAPI | 0.111 | `fastapi[standard]` (trae uvicorn); todos los handlers `async def` |
| SQLModel | 0.0.24 | Modelos de tabla |
| SQLAlchemy | 2.0 (async) | Motor, sesión, carga anticipada |
| asyncpg | 0.30 | Driver async de PostgreSQL |
| PostgreSQL | 16 | Corre en Docker (`docker-compose.yml`) |
| Alembic | 1.13 | Plantilla async (`alembic init -t async`) |
| pydantic-settings | 2.0 | Clase `Settings`, lee el entorno y `.env` |
| bcrypt | 4.0 | Hash de contraseñas (la versión 5 rechaza más de 72 bytes: se valida en el contrato) |
| PyJWT | 2.15 | Token firmado. El paquete se llama `PyJWT`, no `jwt`. Mínimo = versión con la que corre la suite |
| python-dotenv | 1.0 | Lee `.env` |
| pytest / pytest-asyncio / httpx | — | Tests automatizados (dev) |

## 2. Comandos

```bash
cp env.example .env                  # completar con valores locales (antes de levantar Docker)
docker compose up -d                 # levanta PostgreSQL 16 con las credenciales de .env
python -m venv .venv                 # entorno virtual
source .venv/Scripts/activate        # activarlo (Linux/macOS: source .venv/bin/activate)
pip install -r requirements-dev.txt  # app + pytest, pytest-asyncio y httpx
alembic upgrade head                 # crea el esquema (única forma permitida)
python seed.py                       # deja la base en estado inicial conocido (vacía y recarga; atómico e idempotente)
uvicorn app.main:app --reload        # servidor
pytest                               # tests automatizados
```

Todos los comandos se corren **desde esta carpeta** (`TP - DEL OBJETO A LA PERSISTENCIA/`), no desde la raíz del repositorio: `Settings` busca el `.env` en el directorio actual y, desde otra carpeta, no lo encuentra (la app no arranca por falta de variables obligatorias).
`POSTGRES_PASSWORD` y `JWT_SECRET` vienen vacías en `env.example` a propósito: hay que completarlas antes de `docker compose up -d` (Postgres no arranca sin contraseña) y antes de levantar la app (`Settings` exige ambas). Cambio respecto del TP 1–4: un `.env` copiado sin completar ya no sirve.
Si el puerto 5432 está ocupado (p. ej. un PostgreSQL instalado en Windows), usar `POSTGRES_PORT=5433` en `.env` (lo toman Docker y la app; la URL de la base se arma sola con las variables `POSTGRES_*`).
La verificación de reversibilidad (sobre base vacía: `alembic downgrade base` y otra vez `alembic upgrade head`) no forma parte del arranque: está en la sección 11.
`SQL_ECHO=true` en `.env` muestra en consola las consultas emitidas (evidencia de C-15; `DB_ECHO` ya no se lee). La clave de firma del token (`JWT_SECRET`, mínimo 32 caracteres) se genera con `python -c "import secrets; print(secrets.token_urlsafe(48))"` y vive sólo en `.env`.

## 3. Estructura obligatoria

```
app/
├── main.py                 # app, lifespan y los dos grupos de rutas (abierto / protegido)
├── core/
│   ├── config.py           # Settings (pydantic-settings)
│   ├── database.py         # funciones que crean motor y fábrica de sesiones (las llama el lifespan) y get_session
│   ├── security.py         # hash bcrypt fuera del bucle; emisión y verificación del token
│   ├── dependencies.py     # proveedor_uow (construye el UoW); usuario actual, roles vigentes, control del cambio obligatorio, requiere_rol
│   ├── repository.py       # BaseRepository[T] y SoftDeleteRepository[T]
│   ├── paginacion.py       # envoltorio de listados y cálculo de páginas
│   ├── unit_of_work.py     # UnitOfWork base: confirma o revierte al salir del bloque
│   ├── base.py             # (propio del grupo) naming convention de constraints; se importa antes que los modelos
│   ├── tipos.py            # (propio del grupo) tipos int32 para ids, stock y cantidades
│   └── errors.py           # (propio del grupo) excepciones de dominio: Conflicto -> 409, PeticionInvalida -> 422; IntegrityError -> 409 con mensaje propio
├── models.py               # importa TODOS los modelos (metadata completo para Alembic)
└── modules/<módulo>/
    ├── models.py           # tablas, restricciones y relaciones
    ├── schemas.py          # contratos de entrada y de salida
    ├── repository.py       # repositorios de cada entidad del módulo (precarga dentro de cada método)
    ├── unit_of_work.py     # UoW del módulo: compone los repositorios que sus operaciones necesitan
    ├── service.py          # reglas de negocio; recibe el UoW y lo abre
    └── router.py           # rutas HTTP: construyen el UoW, llaman al servicio y traducen errores
migrations/                 # Alembic (env.py + versions/)
seed.py                     # carga inicial, en la raíz
test/*.http                 # casos C-01 a C-16 y solo_agregado.sql (C-14)
tests/                      # pytest
evidencia/                  # captura de psql (C-14) y consola (C-15)
```

Módulos mínimos: `health`, `usuarios`, `editoriales`, `generos`, `autores`, `libros`, `clientes`, `ventas`.
`AsignacionRol`, `IntentoAcceso` y `EventoSeguridad` viven en `usuarios`; `MovimientoStock` y `LibroAutor` en `libros`; `PerfilCliente` en `clientes`; `RenglonVenta` en `ventas`.
`health` **sólo tiene `router.py`**.
`main.py` va en `app/` (lo que arranca `uvicorn app.main:app`); la consigna lo lista sin prefijo, pendiente de confirmar con la cátedra antes de CHG-20.

## 4. Dueños

Se reparte por **change** (ver tabla de seguimiento de `PLAN_PARCIAL.md`), no por módulo.

| Integrante | Áreas |
|---|---|
| Matias (lead) | core (`config`, `database`, `repository`, `unit_of_work`, `security`, `dependencies`), `app/main.py`, auth y autorización, ventas, `AGENTS.md`, `requirements.txt`, `migrations/env.py` |
| Nico | modelos de libro/cliente/stock, la tercera y la cuarta migración, catálogo y clientes con repositorios + UoW, administración de usuarios, pytest de integración |
| Lauti | carpeta hermana `Despliegue` (`despliegue/` en el zip), `core/paginacion.py`, modelos de usuarios, contratos (`schemas.py`), seed, casos `.http`, zip |

**Archivos compartidos** (`app/main.py`, `app/models.py`, `requirements.txt`, `core/` (incluidos `base.py`, `tipos.py`, `errors.py`), `migrations/env.py`, `AGENTS.md`): los modifica el lead (Matias) o el responsable del change que los nombra en su sección «Archivos» del plan, siempre con revisión del lead.

## 5. Capas y transacciones

Flujo obligatorio: **Router → Service → UoW → Repository → Model**. Cada capa sabe lo suyo y nada más.

| Capa | Quién construye / abre / confirma / cierra |
|---|---|
| Router | **Construye** el UoW con una dependencia y se lo pasa al servicio **sin abrirlo**. Traduce errores a HTTP. Sin lógica. |
| Service | **Abre** el UoW con `async with` y **nunca lo construye**. Contiene las reglas de negocio. |
| UoW base | Gestor de contexto asincrónico: **confirma** al salir del bloque, **revierte** si sale con una excepción y **no cierra la sesión** porque no la creó. |
| UoW de módulo | Compone los repositorios que sus operaciones necesitan, todos con **la misma sesión**. |
| Repository | `add` y `update` hacen `flush()`, **nunca `commit()`**. Cada entidad tiene el suyo, con métodos nombrados por lo que traen; la precarga (`joinedload` / `selectinload`) se declara **dentro del método** que la necesita. |
| `get_session` | Toma la fábrica de `app.state`, entrega una sesión por petición (`expire_on_commit=False`) y la **cierra** al terminar. |

Jerarquías: `BaseRepository[T]` recibe en el constructor la sesión **y la clase del modelo** (ofrece al menos `get_by_id`, `get_all`, `count`, `add`, `update`, `delete`); `SoftDeleteRepository[T]` hereda de él, lo usa `Libro`, filtra los dados de baja y agrega `get_by_id_including_deleted` y `soft_delete`.

**Operaciones de varias escrituras, cada una en un solo bloque `async with uow`:**
- RN-02 · auto-registro: usuario, rol CLIENTE y ficha de cliente (las tres filas o ninguna; correo de cliente existente → 409, no se apropia de la ficha).
- RN-10 · venta: venta, renglones con el precio copiado, total calculado, descuento de stock y un movimiento por renglón. Si un libro no alcanza, no queda ninguna escritura.
- RN-16 · alta de personal, cambio de rol y cambio de contraseña dejan su línea en `evento_seguridad` **en la misma transacción** que el cambio.

**Dependencias de usuario y de rol** (`dependencies.py`) reciben **la misma sesión** que el UoW: sin eso, cada petición autenticada tomaría dos conexiones del pool.

**Stock:** una sola vía de escritura (RN-11), un único punto de código que usan el alta del libro (`stock_inicial`), la reposición y las ventas; cada uno deja un `movimiento_stock`. Nadie escribe `libro.stock` por otro camino ni por `PATCH`. Siempre: `libro.stock` = suma de `cantidad` de sus movimientos. `movimiento_stock` es de sólo agregado (RN-12): lo garantiza un disparador instalado por la cuarta migración; los errores se compensan con otro movimiento. La firma del punto único la fija CHG-13 con Matias; acá no se fija.

**`intento_acceso` es la única escritura con sesión y transacción propias** (se confirma siempre, aunque la petición falle). El código lo declara en un comentario con tres partes: qué hace distinto, por qué no puede compartir la transacción (el fallo que se cuenta es el mismo que la revierte) y cuál es su costo (deja filas aunque la petición falle). Todo lo demás comparte el UoW de la petición.

## 6. Acceso

Se implementa en CHG-03 (Settings), CHG-10 (seguridad), CHG-11 (auth), CHG-12 (autorización) y CHG-14 (administración de usuarios). Estas son las reglas que esos changes deben cumplir.

- **`Settings`** (pydantic-settings) lee el entorno o `.env`. La URL de la base se arma con `@computed_field` desde `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` y `POSTGRES_PORT` con el driver `postgresql+asyncpg`. **Sin valor por defecto** para la contraseña de la base ni para la clave JWT: si faltan, la app no arranca. Costo de bcrypt, tamaño del pool, `COOKIE_SECURE`, duración del token y `SQL_ECHO` salen de la configuración, no del código.
- **Lifespan:** crea el motor y la fábrica de sesiones y los guarda en `app.state` (nunca al importar un módulo); calcula una sola vez el hash ficticio del login; llama a `dispose()` al apagar.
- **Salud:** `GET /health/live` no toca la base; `GET /health/ready` ejecuta `SELECT 1` y responde 503 si la base no contesta.
- **bcrypt:** toda llamada corre fuera del bucle (`asyncio.to_thread`) y bajo un `asyncio.Semaphore`. El hash se calcula **antes** de abrir la transacción. Todo campo que termina en bcrypt (registro, login, alta de personal, contraseña actual y nueva) acepta **máximo 72 bytes** (`len(s.encode())`, no caracteres) y da 422 si pasa.
- **Login** (orden fijo): (1) límite de intentos, RN-07: con 5 fallos con el mismo correo desde la misma IP en 60 s, el sexto intento recibe 429 (C-05) con `Retry-After`, sin calcular ningún hash; un login correcto reinicia la cuenta; (2) verificación contra el hash del usuario o contra el hash ficticio si el correo no existe, RN-08 (misma respuesta y mismo tiempo aproximado). Cada intento se anota en `intento_acceso` (ver sección 5).
- **Token:** JWT con `sub`, `exp` y los roles vigentes al emitirlo. Viaja **sólo** en la cookie `access_token` con `HttpOnly`, `SameSite=Lax`, `Max-Age` igual a la duración del token y `Secure` configurable. **Nunca** en el cuerpo ni leído de `Authorization`; se lee de `request.cookies`. Cambiar la contraseña no invalida sesiones ni emite un token nuevo. `/auth/logout` borra la cookie.
- **401 vs 403:** 401 si no hay cookie, el token es inválido o venció, o el usuario no existe o está inactivo. 403 si falta el rol vigente, si hay cambio de contraseña pendiente o si no es dueño del recurso.
- **Roles vigentes** (RN-04): `requiere_rol` los consulta **en la base en cada petición**; los roles del token son informativos (`/auth/yo` devuelve ambos). Vigente = no revocada y sin vencer. Revocar escribe `revocada_en` y la fila no se borra; reasignar un rol vencido cierra la fila anterior y abre una nueva. El vencimiento llega con zona horaria y en el futuro (si no, 422, no 409). RN-05: nadie se revoca su propio ADMIN y nunca quedan cero administradores vigentes (409).
- **Dos grupos de rutas** en `main.py`: uno abierto (health, `/auth`, catálogo público en GET) y uno protegido con el control del cambio obligatorio de contraseña (RN-06) montado **una sola vez**, porque FastAPI suma dependencias y no las resta. Lo propio (`/mis-ventas`) sólo pide estar autenticado (RN-14), pero igual vive en el grupo protegido (401 sin sesión, 403 con el cambio de contraseña pendiente). Todo `/auth`, incluidos `/auth/yo` y `/auth/cambiar-password`, vive en el grupo **abierto**: piden estar autenticados (401 sin sesión) pero **no** pasan por el control del cambio obligatorio (consigna: tabla de endpoints, RN-06 y C-09). `GET /ventas/{id}` no lleva `requiere_rol`: decide el servicio (personal o cliente dueño; si no, 403).
- **Errores:** nunca texto interno de la base, nombres de constraints ni trazas; ninguna entrada inválida termina en 500 (RN-15). Las excepciones de dominio son `Conflicto` (409) y `PeticionInvalida` (422), declaradas en `app/core/errors.py` y traducidas por los handlers de `app/main.py`; el código de negocio nunca lanza `HTTPException`.

## 7. Convenciones

- **Nombres de tablas y columnas**: los de la consigna. Se pueden agregar columnas; nunca quitar ni renombrar.
  Tablas: `editorial`, `genero`, `autor`, `libro`, `libro_autor`, `cliente`, `perfil_cliente`, `venta`, `renglon_venta`, `usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad`, `movimiento_stock`.
- **Contratos**: contratos de entrada separados de los modelos de tabla (nunca el modelo de tabla como entrada). Todos los de entrada con `extra="forbid"` (nadie se registra con un rol ni edita el stock por PATCH). Ninguna salida incluye `password_hash`. `PATCH` aplica sólo lo enviado: `model_dump(exclude_unset=True)`.
- **Listados**: devuelven el envoltorio `{items, total, page, size, pages}`. `page` ≥ 1; `size` 1–100 (por defecto 20); una página más allá de la última → 422 («La página 4 no existe: hay 3»); `total` cuenta con los mismos filtros que la página; con cero resultados hay una página (`pages = 1`) y va vacía. Búsqueda de libros por título con parámetros ligados y sin distinguir mayúsculas.
- **Códigos HTTP**: **201** al crear, **204** al dar de baja un libro, **404** si el recurso de la ruta no existe, **409** si choca con lo guardado, **422** si el cuerpo o los parámetros no cumplen el contrato, **429** con `Retry-After` por límite de intentos, **503** en `/health/ready` sin base.
- **Servicios**: funciones `async` que reciben el **UoW** (no la sesión) y lo abren con `async with`.
- **Constraints con nombre**: `SQLModel.metadata` usa una naming convention (en `app/core/base.py`); los mensajes de 409 se eligen por nombre de constraint.
- **Mensajes de error** propios y en español.
- **Columnas únicas**: `Field(unique=True)` **sin** `index=True`. El UNIQUE ya crea su índice; con `unique=True, index=True` SQLAlchemy genera un índice `ix_...` en vez de la constraint `uq_...` y el 409 cae en el mensaje genérico.
- **CHECK con nombre**: todo `CheckConstraint` lleva `name="..."` corto (p. ej. `CheckConstraint("precio > 0", name="precio_positivo")`). Sin `name` falla al definir la tabla.
- **Índices únicos parciales** (ISBN entre libros vigentes `WHERE borrado_en IS NULL`; `(usuario_id, rol) WHERE revocada_en IS NULL`): se declaran con `postgresql_where`, **llevan nombre** y entran en el diccionario de mensajes de 409 igual que un UNIQUE. Sus nombres los fijan CHG-06/07.
- **Nombres de constraints** (son las claves del dict de mensajes):

| Tipo | Patrón | Ejemplo |
|---|---|---|
| UNIQUE | `uq_<tabla>_<columna>` | `uq_cliente_email`, `uq_usuario_email`, `uq_perfil_cliente_cliente_id` |
| FK | `fk_<tabla>_<columna>_<tabla_ref>` | `fk_libro_editorial_id_editorial`, `fk_renglon_venta_libro_id_libro` |
| CHECK | `ck_<tabla>_<name>` | `ck_libro_precio_positivo` |
| Índice | `ix_<tabla>_<columna>` | `ix_libro_editorial_id` |

- **Traducir `IntegrityError`** (`app/core/errors.py`):

```python
MENSAJES = {
    "fk_libro_editorial_id_editorial": "La editorial indicada no existe.",
    "uq_cliente_email": "Ya existe un cliente con ese correo.",
}
```

  Con UoW, la traducción envuelve el bloque que escribe (el commit ocurre al salir del `async with`). Si un `IntegrityError` escapa sin traducir, el handler global de `app/main.py` responde 409 con un mensaje genérico (red de seguridad, no reemplaza los mensajes propios). Integración con el UoW (CHG-04): cada UoW de módulo declara sus `MENSAJES`; el UoW base atrapa el `IntegrityError` (en el flush o en el commit), revierte y lanza la excepción de dominio `Conflicto` (`app/core/errors.py`), que un handler de `app/main.py` traduce a 409. El core no lanza `HTTPException`; desde CHG-13, los servicios migrados lanzan excepciones de dominio en vez de `HTTPException`.
- **Naming convention primero**: todo `app/modules/*/models.py` arranca con `import app.core.base  # noqa: F401`. Si el modelo se importa antes (p. ej. desde el seed), las constraints quedan sin nombre y el 409 cae en el mensaje genérico.
- **Registro de modelos**: cada modelo nuevo se importa en `app/models.py` (con `# noqa: F401`); ese archivo importa primero `app.core.base`.
- **Relaciones entre módulos**: type hints cruzados bajo `if TYPE_CHECKING:` y `Relationship` con el nombre de la clase como string (`list["RenglonVenta"]`), para evitar imports circulares. Navegación declarada **en los dos extremos** con `back_populates`:

| Relación | Lado A | Lado B | FK en |
|---|---|---|---|
| Libro → Editorial | `Libro.editorial` | `Editorial.libros` | `libro.editorial_id` |
| Libro → Genero (opcional) | `Libro.genero` | `Genero.libros` | `libro.genero_id` (nullable) |
| Libro ↔ Autor vía LibroAutor | `Libro.autorias` / `LibroAutor.libro` | `Autor.autorias` / `LibroAutor.autor` | `libro_autor` |
| Cliente – Perfil (1:1) | `Cliente.perfil` (`uselist=False`) | `PerfilCliente.cliente` | `perfil_cliente.cliente_id` UNIQUE |
| Cliente → Usuario (opcional) | `Cliente.usuario` (a uno: devuelve un objeto) | `Usuario.cliente` (`sa_relationship_kwargs={"uselist": False}`, escalar) | `cliente.usuario_id` UNIQUE, nullable |
| Usuario → Roles | `Usuario.asignaciones` | `AsignacionRol.usuario` | `asignacion_rol.usuario_id` |
| Libro → Movimientos | `Libro.movimientos` | `MovimientoStock.libro` | `movimiento_stock.libro_id` |
| Movimiento → Venta (opcional) | `MovimientoStock.venta` | `Venta.movimientos` | `movimiento_stock.venta_id` (nullable) |
| Movimiento → Usuario | `MovimientoStock.usuario` | `Usuario.movimientos` | `movimiento_stock.usuario_id` |
| Asignación → Usuario que la otorgó (opcional) | `AsignacionRol.otorgada_por_usuario` | — | `asignacion_rol.otorgada_por` (nullable); FK a `usuario` a confirmar con la Figura 1 en CHG-06 |
| Venta → Cliente | `Venta.cliente` | `Cliente.ventas` | `venta.cliente_id` |
| Venta ◆ Renglón (composición) | `Venta.renglones` (cascade) | `RenglonVenta.venta` | `renglon_venta.venta_id` |
| Renglón → Libro | `RenglonVenta.libro` | `Libro.renglones` | `renglon_venta.libro_id` |

  (`IntentoAcceso` y `EventoSeguridad` no se relacionan con ninguna tabla; `EventoSeguridad.actor` es texto, p. ej. `SISTEMA`.) Esta tabla no es exhaustiva: toda FK de la Figura 1 lleva índice y navegación en los dos extremos; los nombres exactos de las relaciones nuevas los fijan CHG-06/07.

## 8. Reglas duras

**SIEMPRE**
- Handlers `async def`. Nada bloqueante adentro (`time.sleep`, `requests`, sesión síncrona, bcrypt fuera de `to_thread`).
- Dinero con `Decimal` y `Numeric(10,2)` / `Numeric(12,2)`. Todas las fechas nuevas `timestamptz` (con zona).
- Toda relación que se lee se precarga **en el repositorio**: `joinedload` para relaciones a uno, `selectinload` para colecciones. El detalle de venta (cliente, renglones y libro de cada renglón, aunque el libro esté dado de baja) emite un número fijo de consultas.
- Cada clave foránea lleva índice.
- `IntegrityError` se traduce con `app/core/errors.py` a 409 con mensaje propio.
- El aviso del comprobante al registrar una venta va por `BackgroundTasks` (`await asyncio.sleep(0.5)` y un log visible con el arranque normal de uvicorn, p. ej. logger `uvicorn.error`); corre sólo si la venta se confirmó.
- Cada migración se **lee** antes de aplicarla y lleva un comentario que lo dice; si se corrige a mano, el comentario lo explica. La tercera migración se autogenera; la cuarta (disparador de sólo agregado) se escribe a mano.
- Un libro dado de baja (borrado lógico, `borrado_en`) no aparece en el catálogo y no se vende ni se repone (409), pero sus datos se conservan y las ventas viejas lo siguen mostrando.

**NUNCA**
- `float` para dinero.
- Carga perezosa (lazy loading) en una lectura.
- SQL armado concatenando texto del usuario. Los filtros (`ilike` por título) usan parámetros ligados.
- Consultar antes si un id o un valor único existe «para validar»: se escribe y la base decide (FK, UNIQUE o índice parcial → 409).
- Devolver al cliente texto interno de la base, nombres de constraints o trazas.
- `SQLModel.metadata.create_all`: el esquema se crea sólo con `alembic upgrade head`.
- `PATCH` de ventas. Precio unitario, total o fecha de una venta en el contrato de entrada (los calcula el servidor). Stock en el `PATCH` de libros.
- Alta de renglones por separado: viajan dentro del `POST /ventas/`.
- Un repositorio que confirme; un servicio que construya su UoW; un UoW que cierre la sesión.
- El token en el cuerpo de una respuesta o leído de `Authorization`.
- Credenciales o clave de firma en el código (ni como valor por defecto), en `alembic.ini`, en el repositorio o en la imagen. `.env` no se commitea; sólo `env.example`.

## 9. Transición (código que todavía sigue el TP 1–4)

Regla: **el código nuevo sigue las reglas del parcial; un módulo existente se migra sólo dentro de su change, no antes.** No «corrijas» por tu cuenta lo que no es de tu change.

| Parte del código hoy | Cómo queda | Change |
|---|---|---|
| ~~`app/core/config.py` con `DATABASE_URL` y `DB_ECHO`~~ | `Settings` con `POSTGRES_*`, `SQL_ECHO` y recursos en el lifespan | CHG-03 ✅ hecho |
| ~~`health` con `router.py` y `schemas.py`~~ | sólo `router.py` | CHG-03 ✅ hecho |
| Servicios que reciben `AsyncSession` (clientes, ventas; el catálogo ya migró) | reciben el UoW; repositorios por entidad | CHG-04 (base), 13 ✅ hecho (catálogo), 15, 16 |
| `app/core/pagination.py` con `limit` / `offset` | `app/core/paginacion.py` con `{items, total, page, size, pages}` | CHG-05 ✅ hecho (el catálogo ya migró en CHG-13 ✅; el viejo queda para clientes (15) y ventas (16)) |
| `app/core/errors.py` (`commit_or_409` / `traducir_integrity` reciben la sesión) | el UoW lanza `Conflicto` (con `mensaje_para`) y `main.py` lo pasa a 409; `commit_or_409` / `traducir_integrity` quedan sólo para clientes y ventas hasta CHG-15/16 (catálogo ya migrado, CHG-13 ✅) | CHG-04, 13 ✅ (catálogo), 15, 16 |
| `test/*.http` con los casos C-01 a C-08 del TP | casos C-01 a C-16 del parcial (otra numeración y otro significado); desde CHG-13 los listados del catálogo usan el envoltorio (`page`/`size`) y las escrituras piden sesión, y los `.http` se ajustan en CHG-18 | CHG-18 |
| ~~`tests/` con un conftest que deriva `libreria_test` de `DATABASE_URL`; `env.example` con `DATABASE_URL`~~ | deriva de `Settings` / `POSTGRES_*` | CHG-03 ✅ hecho |
| `test/libros.http` y `test/ventas.http` mencionan `DB_ECHO=true` | `SQL_ECHO=true` | CHG-18 |
| ~~Semáforo de bcrypt: `BCRYPT_MAX_CONCURRENTES` ya está en `Settings`, pero el `asyncio.Semaphore` todavía no se crea~~ | el lifespan crea el semáforo y `security.py` lo usa | CHG-10 ✅ hecho |
| ~~`scripts/seed.py` (`python -m scripts.seed`)~~ | `seed.py` en la raíz (`python seed.py`) | CHG-17 ✅ hecho |
| ~~`libro.stock` editable, ISBN con UNIQUE común~~ | stock por movimientos, ISBN único entre vigentes | CHG-07, 08, 13 ✅ hecho |
| Ventas escribe `libro.stock` sin dejar movimiento y puede vender libros dados de baja | usa el punto único de stock; un libro dado de baja da 409 | CHG-16 |
| Sin usuarios ni roles | módulo `usuarios`, auth y autorización | CHG-06, 10, 11 ✅ (rutas `/auth` hechas), 12 ✅ hecho (`requiere_rol`, grupos abierto/protegido), 14 (administración de usuarios) |
| `GET /ventas/{id}` con `PERSONAL` provisorio | sin `requiere_rol`: decide el servicio (personal o cliente dueño; si no, 403) | CHG-16 |
| Routers de catálogo, clientes y ventas divididos en `router_abierto` / `router`, y rutas clasificadas en `tests/matriz_acceso.py` | CHG-13, 15 y 16 conservan la división y agregan sus rutas a la matriz (la suite falla si falta una) | CHG-13 ✅ hecho (catálogo), 15, 16 |

## 10. Git

- `main` protegida. **Una rama por change**, con el nombre `<tipo>/<nombre-openspec>` (p. ej. `chore/bootstrap-parcial`); `<tipo>` es el tipo de commit convencional dominante (`feat`, `refactor`, `docs`, `build`, `chore`, `test`). Sale de `main` y vuelve por **PR chico revisado por al menos otro integrante**. Cada integrante trabaja en las ramas de sus changes (sección 4).
- Commits convencionales en español con el scope del módulo (`feat(core): ...`). Los `models.py` se entregan primero en un PR propio.
- Strict TDD: un test que falla primero, después el mínimo código que lo hace pasar.
- **El plan se actualiza en el mismo PR del change, nunca después.** Antes de pedir revisión, el último PR de un change trae, además del código:
  1. su fila de la tabla de seguimiento de `PLAN_PARCIAL.md` (sección 2) en `mergeado (#N)`, con el número del PR;
  2. el change archivado con `openspec archive <nombre>`, hecho en la misma rama;
  3. lo que el change deje desactualizado en `PLAN_PARCIAL.md` o en la «Transición» de este archivo (sección 9).

  Se marca `mergeado` antes del merge porque la tabla describe `main` y el PR sólo llega a `main` mergeado; si se cierra sin merge, no cambia nada. Si el change se entrega en varios PRs, los anteriores marcan `en curso` y sólo el último pone `mergeado`. **Quien revisa no aprueba** un PR de change que no trae estos tres puntos. Lo que está en trabajo no se anota en la tabla: lo muestran los PRs abiertos (`gh pr list`). Un PR que no es de un change (docs, arreglos sueltos) no toca la tabla.

## 11. Definición de terminado (parcial)

1. Sobre una base vacía: `alembic upgrade head` OK, `alembic downgrade base` OK y `alembic upgrade head` otra vez OK.
2. `python seed.py` + `uvicorn` levanta; `/health/live` y `/health/ready` responden 200.
3. Todos los `.http` de `test/` (C-01 a C-16) dan el código esperado, indicado en un comentario, más `test/solo_agregado.sql` (C-14); `pytest` verde. Antes de cada archivo se corre `python seed.py`.
4. Con `SQL_ECHO=true`, el detalle de una venta emite la misma cantidad de consultas con 2 o 4 renglones (C-15). `evidencia/` con la captura de psql de C-14 y la consola de C-15.
5. En los cinco libros, `stock` = suma de sus movimientos tras cada caso de venta.
6. Sin contraseñas ni clave de firma en el repo ni en el historial; `.env` ignorado; `env.example` presente; `alembic.ini` sin URL.
7. Entrega: `Parcial_Cap1a6_<Grupo>.zip` con `parcial/` (README con integrantes y pasos desde cero, `evidencia/`) y `despliegue/`, sin `.venv`, `__pycache__` ni `.env`.
