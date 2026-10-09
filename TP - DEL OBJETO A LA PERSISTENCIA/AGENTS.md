# AGENTS.md — Librería (FastAPI + PostgreSQL)

Guía canónica del proyecto para los integrantes del grupo y para cualquier agente de IA.
Fuente de verdad del enunciado: `TP_Cap1a4_Consigna.pdf`. Reparto de tareas: `REPARTO.md`.
Si algo de este archivo contradice la consigna, **gana la consigna** y se corrige este archivo por PR.

---

## 1. Proyecto y stack

API para una librería: catálogo (editoriales, géneros, autores, libros), clientes y ventas.

| Componente | Versión mínima | Notas |
|---|---|---|
| Python | 3.12 | |
| FastAPI | 0.111 | `fastapi[standard]` (trae uvicorn) |
| SQLModel | 0.0.24 | Modelos de tabla y DTO |
| SQLAlchemy | 2.0 (async) | Motor, sesión, carga anticipada |
| asyncpg | 0.30 | Driver async de PostgreSQL |
| PostgreSQL | 16 | Corre en Docker (`docker-compose.yml`) |
| Alembic | 1.13 | Plantilla async (`alembic init -t async`) |
| python-dotenv | 1.0 | Lee `.env` |
| pytest / pytest-asyncio / httpx | — | Tests automatizados (dev) |

## 2. Comandos

```bash
docker compose up -d                 # levanta PostgreSQL 16
python -m venv .venv                 # entorno virtual
pip install -r requirements.txt      # dependencias
cp env.example .env                  # completar con valores locales
alembic upgrade head                 # crea el esquema (única forma permitida)
python -m scripts.seed               # deja la base en estado inicial conocido
uvicorn app.main:app --reload        # servidor
pytest                               # tests automatizados
```

Si el puerto 5432 está ocupado (p. ej. un PostgreSQL instalado en Windows), usar `POSTGRES_PORT=5433` en `.env` y el mismo puerto en `DATABASE_URL`.
`DB_ECHO=true` en `.env` muestra en consola las consultas emitidas (evidencia del caso C-07).

## 3. Estructura obligatoria

```
app/
├── main.py                 # app, lifespan y registro de routers
├── models.py               # importa TODOS los modelos (metadata completo para Alembic)
├── core/
│   ├── config.py           # DATABASE_URL y DB_ECHO desde el entorno
│   ├── database.py         # motor, sessionmaker, get_session, naming convention
│   ├── pagination.py       # dependencia limit/offset (RN-10)
│   └── errors.py           # IntegrityError -> 409 con mensaje propio (RN-12)
└── modules/<módulo>/
    ├── models.py           # tablas, restricciones y relaciones
    ├── schemas.py          # DTO: XCreate, XUpdate, XRead
    ├── service.py          # lógica, traducción de errores, lecturas con precarga
    └── router.py           # rutas HTTP: reciben, delegan, declaran la respuesta
migrations/                 # Alembic (env.py + versions/)
scripts/seed.py             # carga inicial
test/*.http                 # casos de prueba C-01 a C-08
tests/                      # pytest
```

Módulos: `health`, `editoriales`, `generos`, `autores`, `libros`, `clientes`, `ventas`.
`LibroAutor` vive en `libros`, `PerfilCliente` en `clientes`, `RenglonVenta` en `ventas`.

## 4. Dueños

| Integrante | Módulos / archivos |
|---|---|
| A | `core/`, `main.py`, `app/models.py`, `health`, `editoriales`, `generos`, `migrations/`, `requirements.txt`, `scripts/seed.py`, `README.md`, `AGENTS.md`, C-01 |
| B | `autores`, `libros` (`Libro`, `LibroAutor`), C-02 (ISBN), C-04, C-07 (libro), C-08 |
| C | `clientes` (`Cliente`, `PerfilCliente`), `ventas` (`Venta`, `RenglonVenta`), BackgroundTasks, C-02 (email), C-03, C-05, C-06, C-07 (venta) |

**Archivos compartidos** (`main.py`, `app/models.py`, `requirements.txt`, `core/`, `migrations/env.py`, `AGENTS.md`): sólo los modifica A. B y C piden el cambio en su PR.

## 5. Convenciones

- **Nombres de tablas y columnas**: los de la consigna. Se pueden agregar columnas; nunca quitar ni renombrar.
  Tablas: `editorial`, `genero`, `autor`, `libro`, `libro_autor`, `cliente`, `perfil_cliente`, `venta`, `renglon_venta`.
- **DTO**: `XCreate` (sin `id`), `XUpdate` (todo opcional), `XRead`. Los modelos de tabla nunca se usan como contrato de entrada.
- **Routers**: un `APIRouter(prefix="/<módulo>", tags=[...])` por módulo; declaran `response_model` y `status_code`; no tienen lógica.
- **Services**: funciones `async` que reciben `session: AsyncSession` como parámetro. Toda la lógica y las consultas viven acá.
- **Sesión**: siempre con `Depends(get_session)`; una por petición; `expire_on_commit=False`.
- **Constraints con nombre**: `SQLModel.metadata` usa una naming convention (en `app/core/database.py`); los mensajes de 409 se eligen por nombre de constraint.
- **Mensajes de error** propios y en español.
- **Columnas únicas**: `Field(unique=True)` **sin** `index=True`. El UNIQUE ya crea su índice; con `unique=True, index=True` SQLAlchemy genera un índice `ix_...` en vez de la constraint `uq_...` y el 409 cae en el mensaje genérico.
- **CHECK con nombre**: todo `CheckConstraint` lleva `name="..."` corto (p. ej. `CheckConstraint("precio > 0", name="precio_positivo")`). La naming convention lo exige; sin `name` falla al definir la tabla.
- **Nombres de constraints** (son las claves del dict de mensajes):

| Tipo | Patrón | Ejemplo |
|---|---|---|
| UNIQUE | `uq_<tabla>_<columna>` | `uq_libro_isbn`, `uq_cliente_email`, `uq_perfil_cliente_cliente_id` |
| FK | `fk_<tabla>_<columna>_<tabla_ref>` | `fk_libro_editorial_id_editorial`, `fk_renglon_venta_libro_id_libro` |
| CHECK | `ck_<tabla>_<name>` | `ck_libro_precio_positivo` |
| Índice | `ix_<tabla>_<columna>` | `ix_libro_editorial_id` |

- **Traducir `IntegrityError`** (`app/core/errors.py`):

```python
MENSAJES = {
    "uq_libro_isbn": "Ya existe un libro con ese ISBN.",
    "fk_libro_editorial_id_editorial": "La editorial indicada no existe.",
}

# Caso simple: sólo commit
await commit_or_409(session, MENSAJES)

# Si hay flush() o lecturas (autoflush) antes del commit, envolver todo el bloque:
async with traducir_integrity(session, MENSAJES):
    session.add(venta)
    await session.flush()
    ...
    await session.commit()
```

  Si un `IntegrityError` escapa sin envolver, el handler global de `app/main.py` responde 409 con un mensaje genérico (red de seguridad, no reemplaza los mensajes propios).
- **Registro de modelos**: cada modelo nuevo se importa en `app/models.py` (con `# noqa: F401`); ese archivo importa primero `app.core.database` para fijar la naming convention.
- **Relaciones entre módulos**: type hints cruzados bajo `if TYPE_CHECKING:` y `Relationship` con el nombre de la clase como string (`list["RenglonVenta"]`), para evitar imports circulares.
- **Navegación en los dos extremos** con `Relationship(back_populates=...)`, según esta tabla:

| Relación | Lado A | Lado B | FK en |
|---|---|---|---|
| Libro → Editorial | `Libro.editorial` | `Editorial.libros` | `libro.editorial_id` |
| Libro → Genero (opcional) | `Libro.genero` | `Genero.libros` | `libro.genero_id` (nullable) |
| Libro ↔ Autor vía LibroAutor | `Libro.autorias` / `LibroAutor.libro` | `Autor.autorias` / `LibroAutor.autor` | `libro_autor` |
| Cliente – Perfil (1:1) | `Cliente.perfil` (`uselist=False`) | `PerfilCliente.cliente` | `perfil_cliente.cliente_id` UNIQUE |
| Venta → Cliente | `Venta.cliente` | `Cliente.ventas` | `venta.cliente_id` |
| Venta ◆ Renglón (composición) | `Venta.renglones` (cascade) | `RenglonVenta.venta` | `renglon_venta.venta_id` |
| Renglón → Libro | `RenglonVenta.libro` | `Libro.renglones` | `renglon_venta.libro_id` |

## 6. Reglas duras

**SIEMPRE**
- Handlers `async def`. Nada bloqueante adentro (`time.sleep`, `requests`, sesión síncrona).
- Dinero con `Decimal` y `Numeric(10,2)` / `Numeric(12,2)`. `venta.fecha` con zona horaria.
- Toda relación que se lee se precarga en la misma consulta: `joinedload` para relaciones a uno, `selectinload` para colecciones. El detalle de libro y de venta emite un número fijo de consultas.
- Cada clave foránea lleva índice.
- Listados paginados con la dependencia de `app/core/pagination.py` (`limit` 1–100, default 20; `offset` ≥ 0).
- `PATCH` aplica sólo lo enviado: `model_dump(exclude_unset=True)`.
- Códigos HTTP: **201** al crear, **404** si no existe, **409** si la base rechaza la escritura, **422** si no se cumple el contrato.
- `IntegrityError` se traduce con `app/core/errors.py` a 409 con mensaje propio.
- Cada migración autogenerada se **lee** antes de aplicarla; si se corrige a mano, se explica con un comentario en el archivo.

**NUNCA**
- `float` para dinero.
- Carga perezosa (lazy loading) en una lectura.
- SQL armado concatenando texto del usuario. Los filtros (`ilike` por título) usan parámetros ligados.
- Consultar antes si un id o un valor único existe "para validar": se escribe y la base decide (FK/UNIQUE → 409).
- Devolver al cliente texto interno de la base, nombres de constraints o trazas.
- `SQLModel.metadata.create_all`: el esquema se crea sólo con `alembic upgrade head`.
- `PATCH` de ventas. Precio unitario, total o fecha de una venta en el DTO de entrada (los calcula el servidor).
- Alta de renglones por separado: viajan dentro del `POST /ventas/`.
- Credenciales en el código, en `alembic.ini` o en el repositorio. `.env` no se commitea; sólo `env.example`.

## 7. Git

- `main` protegida. Ramas: `feat/core-infra` (A), `feat/catalogo-libros` (B), `feat/clientes-ventas` (C).
- PRs chicos, revisados por al menos otro integrante. Los `models.py` se entregan primero en un PR propio.

## 8. Definición de terminado

1. Base vacía → `alembic upgrade head` OK; `alembic downgrade -1` + `alembic upgrade head` OK.
2. Seed + `uvicorn` levanta; `/health/live` y `/health/ready` responden 200.
3. Todos los `.http` de `test/` (C-01 a C-08) dan el código esperado, indicado en un comentario; `pytest` pasa.
4. Con `DB_ECHO=true`, el detalle de libro y de venta emite la misma cantidad de consultas con 1 o N autores/renglones.
5. Sin contraseñas en el repo; `.env` ignorado; `env.example` presente; `alembic.ini` sin URL.
