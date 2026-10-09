# Reparto del TP "Del objeto a la persistencia" — Librería (FastAPI + PostgreSQL)

## Contexto
La carpeta del TP sólo tiene la consigna (`TP_Cap1a4_Consigna.pdf`); el proyecto arranca de cero.
Hay que repartir el trabajo entre 3 integrantes de forma que:
- cada uno sea dueño de un **módulo vertical** completo (models → schemas → service → router → .http), así se evalúa todo el temario en cada persona y se minimizan los conflictos de merge;
- las piezas compartidas (core, Alembic, helpers) tengan **un solo dueño**;
- las dependencias entre modelos (relaciones con `back_populates` cruzadas) y las **2 migraciones obligatorias** se resuelvan con un orden de entregas claro.



---

## Roles

### Integrante A — Infra, catálogo base e integración (dueño del esqueleto)
| Entregable | Ejercicio |
|---|---|
| Estructura obligatoria, `requirements.txt`, `env.example`, `.gitignore` (con `.env`) | Ej1 |
| `app/core/config.py` (DATABASE_URL + `DB_ECHO` configurable), `app/core/database.py` (engine/sessionmaker en lifespan → `app.state`, `get_session` con `expire_on_commit=False`), `app/main.py` | Ej1, Ej7 |
| Módulo `health`: `/health/live` (sin DB) y `/health/ready` (`SELECT 1`) | Ej1 |
| Helpers compartidos: `app/core/pagination.py` (`limit` 1–100 def. 20, `offset` ≥0 vía `Query`) y `app/core/errors.py` (traducir `IntegrityError` → 409 con mensaje propio, RN12) | Ej4 |
| Módulos `editoriales` y `generos` completos (CRUD, PATCH con `exclude_unset`, `/{id}/libros` con precarga) | Ej2, Ej4, Ej6 |
| **Alembic** con plantilla async (`alembic init -t async`), `env.py` lee `.env`, sin credenciales en `alembic.ini` | Ej3 |
| Migración 1 (todo menos `genero`) y migración 2 (`genero` + `libro.genero_id`), leídas y corregidas con comentarios; probar `upgrade head` / `downgrade -1` / `upgrade head` | Ej3 |
| Script de seed (estado inicial conocido) + `README.md` (pasos desde cero) | Entrega |
| Casos `.http`: C-01 | Tests |

### Integrante B — Catálogo: autores y libros
| Entregable | Ejercicio |
|---|---|
| Módulo `autores`: modelo, CRUD, `GET /autores/{id}/libros` (libros con rol y orden) | Ej2, Ej4 |
| Módulo `libros`: modelos `Libro` y `LibroAutor` (objeto de asociación, PK compuesta, CHECK `orden>=1`, CHECK de `rol`), `isbn` UNIQUE, CHECK `precio>0`/`stock>=0`, `Numeric(10,2)` + `Decimal`, índices en FKs | Ej2 |
| `POST /libros/` con `editorial_id`, `genero_id`, lista `autores` (`autor_id`, `rol`, `orden`); **sin consultar antes** si los ids existen → FK rechazada = 409 | Ej5 |
| `GET /libros/` paginado con filtro `titulo` (`ilike` con parámetro ligado, RN11) y `genero_id`; `GET /libros/{id}` con `joinedload(editorial, genero)` + `selectinload(autorias).joinedload(autor)`; `PATCH /libros/{id}` | Ej4, Ej6 |
| Casos `.http`: C-02 (ISBN), C-04, C-07 (detalle libro + evidencia de consola), C-08 (`' OR '1'='1`) | Tests |

### Integrante C — Clientes y ventas
| Entregable | Ejercicio |
|---|---|
| Módulo `clientes`: `Cliente` (email UNIQUE), `PerfilCliente` (`cliente_id` UNIQUE, `Cliente.perfil` con `uselist=False`), `POST/GET/PATCH /clientes`, `POST /clientes/{id}/perfil` (2º perfil → 409), `GET /clientes/{id}/ventas` | Ej2, Ej4 |
| Módulo `ventas`: `Venta` (`fecha` timezone-aware, `total Numeric(12,2)`, CHECK `total>=0`) y `RenglonVenta` (CHECK `cantidad>0`, `precio_unitario>0`), cascade de composición | Ej2 |
| `POST /ventas/` con DTO anidado (RN04), validación ≥1 renglón y sin libros repetidos → 422 (RN05), precio copiado del libro (RN06), total calculado (RN07), sin PATCH (RN08) | Ej5 |
| `GET /ventas/` y `GET /ventas/{id}` con `joinedload(cliente)` + `selectinload(renglones).joinedload(libro)` (para `titulo` y `subtotal`) | Ej6 |
| `BackgroundTasks` con aviso de comprobante (`await asyncio.sleep(0.5)` + log) | Ej7 |
| Casos `.http`: C-02 (email), C-03, C-05, C-06, C-07 (detalle venta + evidencia de consola) | Tests |

> Puntos aproximados por persona (sobre 100): A ≈ 10 + 10 + parte de 2/4/6; B ≈ mitad de 2/4/5/6; C ≈ mitad de 2/4/5/6 + 10 de Ej7. A tiene menos lógica de negocio pero carga la integración, migraciones, seed y README.

---

## Orden de trabajo (dependencias)

**Fase 0 — Kickoff (todos, 1 reunión corta)**
- Acordar convenciones: nombres de tablas/columnas de la consigna (no negociables), `Decimal` para dinero, un `APIRouter` por módulo con `prefix`, todos los handlers `async def`, nombres de DTO `XCreate/XUpdate/XRead`.
- Acordar los `back_populates` cruzados (tabla abajo) para que cada uno los escriba igual.

| Relación | Lado A | Lado B | Dueño FK |
|---|---|---|---|
| Libro → Editorial | `Libro.editorial` | `Editorial.libros` | B (en `libro`) |
| Libro → Genero (opcional) | `Libro.genero` | `Genero.libros` | B |
| Libro ↔ Autor vía LibroAutor | `Libro.autorias` / `LibroAutor.libro` | `Autor.autorias` / `LibroAutor.autor` | B |
| Cliente – Perfil (1:1) | `Cliente.perfil` | `PerfilCliente.cliente` | C |
| Venta → Cliente | `Venta.cliente` | `Cliente.ventas` | C |
| Venta ◆ Renglón | `Venta.renglones` | `RenglonVenta.venta` | C |
| Renglón → Libro | `RenglonVenta.libro` | `Libro.renglones` | C (FK) / B agrega el lado `Libro.renglones` |

**Fase 1 — Esqueleto (A, primero; bloquea al resto)**
- A sube `main`, `core/`, `health`, helpers de paginación/errores y Alembic inicializado. B y C pueden ir escribiendo modelos en sus ramas mientras tanto.

**Fase 2 — Modelos (B y C en paralelo, A con editorial/genero)**
- Cada uno entrega su `models.py` primero (PR chico). Todos los modelos se importan en un único lugar (p. ej. `app/models.py` o `migrations/env.py`) que mantiene A.

**Fase 3 — Migraciones (A, cuando estén mergeados todos los modelos)**
- Migración 1: autogenerar con `Genero` y `Libro.genero_id` temporalmente fuera del metadata.
- Migración 2: reincorporarlos y autogenerar. Revisar ambas (CHECKs, índices, nombres de constraints que autogenerate no detecta) y comentar las correcciones.

**Fase 4 — Services y routers (los 3 en paralelo)**
- C depende de `Libro` (B) para leer precios; puede avanzar con el seed de A.

**Fase 5 — Cierre (todos)**
- Cada uno completa sus `.http` con el resultado esperado comentado; B y C capturan la evidencia de C-07; A integra README, corre el flujo completo desde base vacía y revisa que no haya credenciales.

---

## Flujo de Git
- `main` protegida; ramas `feat/core-infra`, `feat/catalogo-libros`, `feat/clientes-ventas`; PRs chicos con revisión de al menos otro integrante.
- Archivos compartidos (`main.py`, registro de routers, import de modelos, `requirements.txt`) sólo los toca A; B y C piden cambios en el PR.

## Verificación (criterio de "terminado")
1. Base vacía → `alembic upgrade head` OK; `alembic downgrade -1` + `upgrade head` OK.
2. Seed + `uvicorn` levanta; `/health/live` y `/health/ready` responden 200.
3. Todos los `.http` de `test/` (C-01 a C-08) dan el código esperado.
4. Con `echo=True`, el detalle de libro y de venta emite la misma cantidad de consultas con 1 o N autores/renglones.
5. `grep` sin contraseñas en repo; `.env` ignorado; `env.example` presente.
