# Design

## Context

- Desde CHG-03, el lifespan deja `app.state.sessionmaker` (`expire_on_commit=False`) y `get_session` entrega una sesión por petición y la cierra al terminar (`async with sessionmaker() as session: yield session`). FastAPI cachea las dependencias por petición: todo `Depends(get_session)` de una misma petición recibe el mismo objeto.
- Hoy cada servicio recibe la `AsyncSession` y confirma con `commit_or_409(session, MENSAJES)` (`app/core/errors.py`), que hace `commit`, y ante `IntegrityError` hace `rollback` y lanza `HTTPException(409, mensaje_para(...)) from None`. `ventas/service.py` usa `traducir_integrity` y `_buscar_atributo` directamente. `main.py` tiene, en `registrar_handlers`, un handler global de `IntegrityError` → `JSONResponse(409, {"detail": mensaje_para(exc, {})})` como red de seguridad: es la forma de cuerpo (`{"detail": ...}`) que también da `HTTPException`.
- `mensaje_para(error, mensajes, default)` ya resuelve el nombre de la constraint con asyncpg (busca en `orig` y en `orig.__cause__`) y cae en el mensaje por SQLSTATE: es reutilizable tal cual.
- No existe `Libro.borrado_en` (lo agrega CHG-07, sin mergear) y el esquema sólo se crea con Alembic. `tests/conftest.py` hace `TRUNCATE` de **todas** las tablas de `SQLModel.metadata` antes de cada test `db`: un modelo de test registrado en ese metadata rompería el `TRUNCATE` (la tabla no existe en la base).
- Ninguna ruta hace hoy una baja física; la única baja prevista es la lógica de libros (CHG-13).
- Suite actual: 373 tests (210 sin base + 163 con la marca `db`).

## Goals / Non-Goals

**Goals:**
- API mínima y estable de `BaseRepository[T]`, `SoftDeleteRepository[T]` y `UnitOfWork` que CHG-11, 13, 15 y 16 puedan usar sin tocar `core/`.
- Que el 409 con mensaje propio funcione igual con UoW que hoy con `commit_or_409`, sin romper los módulos que siguen con la sesión.
- Tests que no dependan de CHG-05, 06, 07 ni 08.

**Non-Goals:**
- Migrar módulos, routers o servicios; borrar `commit_or_409`/`traducir_integrity` (se borran cuando el último consumidor migre, en CHG-16).
- Reglas de negocio de paginación (página fuera de rango → 422): son de CHG-05 y de cada servicio.
- Tocar `app/core/database.py`; en `app/core/errors.py` y `app/main.py`, cualquier cosa fuera de la clase `Conflicto` y su handler.
- Que los servicios lancen `Conflicto`/`NoEncontrado`/`Prohibido`: empieza con CHG-13 al migrar cada módulo.

## Decisions

### D1. Genéricos con la sintaxis de Python 3.12 y la clase del modelo en el constructor

```python
class BaseRepository[T: SQLModel]:
    def __init__(self, session: AsyncSession, model: type[T]) -> None: ...

class SoftDeleteRepository[T: SQLModel](BaseRepository[T]): ...

# CHG-13 (ejemplo):
class EditorialRepository(BaseRepository[Editorial]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Editorial)
```

El `T` sirve al editor y al lector; en tiempo de ejecución el repositorio usa `self.model` (la consigna lo pide porque los genéricos se borran). Alternativa descartada: `TypeVar` + `Generic[T]`, equivalente pero más ruidosa; el proyecto apunta a 3.12.

### D2. Contrato de los métodos genéricos

| Método | Firma | Comportamiento |
|---|---|---|
| `get_by_id` | `(id: int) -> T \| None` | `session.get(model, id)` en la base; en `SoftDelete`, `select` con `borrado_en IS NULL`. `None` si no está: el 404 lo decide el servicio. |
| `get_all` | `(*, offset: int = 0, limit: int \| None = None) -> list[T]` | `self._consulta_base()` ordenada por la clave primaria, con `offset`/`limit`. |
| `count` | `() -> int` | `self._contar(self._consulta_base())`. |
| `add` | `(entity: T) -> T` | `session.add` + `flush` (asigna el id); devuelve la misma entidad. |
| `update` | `(entity: T, datos: Mapping[str, Any]) -> T` | `entity.sqlmodel_update(datos)` + `flush`. El servicio pasa `model_dump(exclude_unset=True)`, como hoy. |
| `delete` | `(entity: T) -> None` | `await session.delete(entity)` + `flush`. En `SoftDelete`, sobrescrito: `NotImplementedError("Usá soft_delete")`. |

- **`offset`/`limit` y no `page`/`size`**: el repositorio no depende de CHG-05. El servicio traduce: `offset=(page-1)*size, limit=size`, y calcula `total` con `count()` antes, para poder dar el 422 de página inexistente sin pedir la página.
- **Orden por clave primaria** (tomada del mapper, no de un atributo `id` fijo): sin `ORDER BY`, `OFFSET` no es determinista.
- **`delete(entity)` y no `delete(id)`**: el servicio ya trajo la entidad para dar el 404, igual que en `update`; es simétrico y no consulta de más. Ver riesgo R2.
- **Sin validar `offset`/`limit`** en el repositorio: los contratos de entrada ya lo hacen (422); el repositorio no es frontera de entrada.

### D3. Punto de extensión: consulta base + helpers protegidos

```python
def _consulta_base(self) -> Select[tuple[T]]          # select(model); SoftDelete agrega borrado_en IS NULL
async def _listar(self, consulta, *, offset=0, limit=None) -> list[T]   # orden por PK + offset/limit + scalars().unique()
async def _contar(self, consulta) -> int              # select(func.count()).select_from(consulta.order_by(None).subquery())
```

Los repositorios de cada módulo escriben métodos nombrados por lo que traen (`buscar_por_titulo`, `get_detalle`) partiendo de `self._consulta_base()`, le agregan `where(...)` y `options(joinedload/selectinload)` **dentro del método**, y usan `_listar`/`_contar` con la misma consulta filtrada: así `total` cuenta con los mismos filtros que la página y el filtro de bajas de `SoftDelete` no se puede olvidar. `.unique()` en `_listar` evita duplicados cuando la precarga usa `joinedload` sobre colecciones. Alternativa descartada: `get_all(*condiciones)` que recibe expresiones SQL desde el servicio (filtra SQL hacia la capa de negocio).

### D4. Borrado lógico

- El constructor de `SoftDeleteRepository` verifica que el modelo tenga la columna `borrado_en`; si no, `TypeError` (el error aparece al construir, no en la primera consulta).
- `soft_delete(entity) -> T`: si `borrado_en` es `None`, lo fija con `datetime.now(UTC)` (con zona); si ya tenía fecha, la conserva. `session.add` + `flush`.
- **Fecha calculada en Python, no `func.now()`**: asignar una expresión SQL deja el atributo expirado después del `flush`, y leerlo dispararía un refresh implícito (carga perezosa) que en async falla con `MissingGreenlet`. Ver riesgo R3.
- `get_by_id_including_deleted(id)` usa `session.get` sin filtro: lo necesitan el detalle de una venta vieja y las reglas «dado de baja → 409» de CHG-13/16.
- `delete` (baja física) se **sobrescribe** para lanzar `NotImplementedError("Usá soft_delete")` sin tocar la sesión: una entidad con borrado lógico nunca se borra físicamente por error (decisión 3).
- `get_by_id` se sobrescribe con `select(model).where(borrado_en IS NULL, pk == id)` (vía `_consulta_base`); la base usa `session.get` (decisión 6).

### D5. Unit of Work base

```python
class UnitOfWork:
    MENSAJES: ClassVar[Mapping[str, str]] = {}   # el UoW del módulo lo redefine
    def __init__(self, session: AsyncSession) -> None: ...
    async def __aenter__(self) -> Self: ...
    async def __aexit__(self, exc_type, exc, tb) -> None: ...   # nunca suprime
```

- `__aenter__` **no** llama a `session.begin()`: si una dependencia ya consultó con esa sesión (usuario actual, CHG-12), la transacción ya está abierta por autobegin y `begin()` fallaría con «A transaction is already begun». Se apoya en el autobegin y marca la **sesión** como ocupada (`session.info["uow_activo"]`); si ya estaba marcada, `RuntimeError` (bloque anidado). Decisión de Matias («`RuntimeError` si anidás») aplicada **por sesión y no por instancia** (hallazgo del advisor): dos UoW distintos inyectados en un mismo handler (`UoWADep` + `UoWBDep`) comparten la sesión y por tanto la transacción, así que el interno confirmaría a medias la operación del externo. Regla: un solo UoW abierto por sesión a la vez; nunca anidar UoW, ni distintos.
- `__aexit__` sin excepción: `commit()`. Con **cualquier** excepción (de integridad, de negocio como «stock insuficiente» de CHG-16, `HTTPException` o un error de programación): `rollback()` y la misma excepción sigue, salvo `IntegrityError`, que se traduce (D6). Nunca `close()`. Siempre desmarca la sesión (también si `commit`/`rollback` fallan; bloques sucesivos permitidos, con la misma instancia o con otra).
- Docstring obligatorio (R7): si hay una transacción abierta (lo normal: cualquier consulta previa con la sesión la abre por autobegin), `rollback()` expira todos los objetos de la sesión aunque la fábrica use `expire_on_commit=False`; leer después un atributo (p. ej. `usuario_actual.id`) dispara una carga perezosa que en async falla con `MissingGreenlet`. Los valores que se necesiten tras un posible rollback se guardan como valores simples **antes** de abrir el bloque.
- `unit_of_work.py` no importa nada de FastAPI.
- La sesión queda expuesta como atributo `session` para que el UoW del módulo construya sus repositorios; los servicios no la usan.
- Sin métodos públicos `commit()`/`rollback()`: la consigna pide confirmar al salir del bloque, y un `commit()` intermedio partiría las operaciones de varias escrituras (RN-02, RN-10, RN-16). El aviso en segundo plano de CHG-16 se agenda después de salir del bloque, así sólo corre si se confirmó.

### D6. Integración con la traducción de `IntegrityError`: excepción de dominio `Conflicto`

En `__aexit__`, si el bloque salió con `IntegrityError` (de un `flush`) o el `commit` lanza `IntegrityError`: `rollback()` y `raise Conflicto(mensaje_para(e, self.MENSAJES)) from None`. El UoW del módulo declara sus mensajes:

```python
# app/core/errors.py (se agrega sólo esto)
class Conflicto(Exception):
    """Choque con lo guardado; la app lo responde como 409 con `mensaje`."""
    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje

# app/main.py, dentro de registrar_handlers
@app.exception_handler(Conflicto)
async def conflicto_handler(request: Request, exc: Conflicto):
    return JSONResponse(status_code=409, content={"detail": exc.mensaje})

# app/modules/editoriales/unit_of_work.py (CHG-13)
class EditorialesUoW(UnitOfWork):
    MENSAJES = {"uq_editorial_nombre": "Ya existe una editorial con ese nombre."}
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.editoriales = EditorialRepository(session)
```

- **Por qué excepción de dominio** (decisión 1): el núcleo transaccional no conoce HTTP (`unit_of_work.py` y `repository.py` no importan nada de FastAPI) y queda fiel a «el router traduce errores» (AGENTS §5). El cuerpo del 409 es el mismo que hoy (`{"detail": mensaje}`), así los tests y casos `.http` existentes no cambian.
- `errors.py` sólo suma la clase: `mensaje_para` se reutiliza; `commit_or_409` y `traducir_integrity` quedan para los módulos que todavía reciben la sesión (comentario en `unit_of_work.py`; se borran en CHG-16 cuando no quede consumidor). Mientras tanto `errors.py` sigue importando `HTTPException`, así que `unit_of_work.py` depende de FastAPI sólo transitivamente; desaparece con ese borrado.
- Un UoW que compone repositorios de varios módulos (ventas, registro) une los diccionarios (`{**MENSAJES_VENTAS, **MENSAJES_LIBROS}`).
- `from None`: el `Conflicto` no encadena el error de la base (RN-15). El handler global de `IntegrityError` sigue como red de seguridad.
- Desde CHG-13, los servicios migrados lanzan `Conflicto` (y más adelante `NoEncontrado`/`Prohibido`) en vez de `HTTPException`; fuera de alcance acá.
- Alternativas descartadas: `HTTPException(409)` desde el UoW (acopla `core/` a HTTP); traducir en cada servicio con `async with traducir_409(MENSAJES): async with uow:` (duplica el anidado y es fácil olvidarlo).

### D7. Dependencia que construye el UoW: fábrica genérica `proveedor_uow`

```python
# app/core/dependencies.py (nuevo; CHG-12 agrega acá las dependencias de usuario y rol)
def proveedor_uow[U: UnitOfWork](clase: type[U]) -> Callable[..., Awaitable[U]]:
    async def _proveer(session: AsyncSession = Depends(get_session)) -> U:
        return clase(session)
    return _proveer

# app/modules/editoriales/unit_of_work.py (CHG-13)
EditorialesUoWDep = Annotated[EditorialesUoW, Depends(proveedor_uow(EditorialesUoW))]

# router (CHG-13)
@router.post("/", status_code=201)
async def crear(datos: EditorialCreate, uow: EditorialesUoWDep):
    return await service.crear(uow, datos)

# service (CHG-13)
async def crear(uow: EditorialesUoW, datos: EditorialCreate) -> Editorial:
    async with uow:
        return await uow.editoriales.add(Editorial(**datos.model_dump()))
```

- **Condición** (decisión 4): todo UoW de módulo se construye sólo con `(session)`; lo que necesite más se arma adentro.
- **Dónde vive**: usa `Depends`, así que no puede ir en `unit_of_work.py` (sin FastAPI). Va en `app/core/dependencies.py`, el archivo de dependencias que fija AGENTS §3; este change lo crea sólo con la fábrica y CHG-12 le suma las de usuario y rol.
- `async def`: una dependencia `def` correría en el threadpool de FastAPI sin necesidad.
- Toma la sesión de `Depends(get_session)`; FastAPI cachea `get_session` por petición, así comparte el objeto con `get_usuario_actual`/`requiere_rol` (CHG-12) y con otro UoW de la misma petición, y una petición autenticada usa una sola conexión del pool.
- Se testea con una app FastAPI mínima de test y UoW de test; ningún router se cablea en este change.

### D8. Estrategia de tests

- **Unitarios (sin base)**:
  - `tests/test_conflicto.py`: `Conflicto` guarda el mensaje; una app FastAPI de test con `registrar_handlers` y una ruta que lanza `Conflicto("X")` responde 409 `{"detail": "X"}`; la app real tiene registrado el handler.
  - `tests/test_unit_of_work.py` y `tests/test_repository.py`: sesión falsa que registra `commit`/`rollback`/`close` y puede lanzar en `commit` (mismo estilo que `SesionFalsa` de `tests/test_errors.py`). Cubren commit/rollback/no-close, `Conflicto` (no `HTTPException`) en bloque y en commit, propagación sin cambios de otras excepciones, anidado y reuso, el `TypeError` de `SoftDeleteRepository`, el `NotImplementedError` de su `delete` y que ninguno de los dos archivos importa `fastapi`.
  - `tests/test_dependencies.py`: la fábrica `proveedor_uow`.
- **Integración (`db`)**, `tests/test_unit_of_work_db.py` y `tests/test_repository_db.py`, con `sessionmaker_test`:
  - `BaseRepository` y UoW sobre `editorial` (tabla real, sin FK obligatoria, con `uq_editorial_nombre` para el 409).
  - `SoftDeleteRepository` sobre un modelo **sólo de test**: `class _BasePrueba(SQLModel, registry=registry())` + `class Borrable(_BasePrueba, table=True)` con `__tablename__ = "prueba_borrable"` y `borrado_en` `DateTime(timezone=True)`. El registro propio deja la tabla **fuera** de `SQLModel.metadata` (verificado con SQLModel instalado: el `TRUNCATE` del conftest y el autogenerate de Alembic no la ven). Un fixture crea la tabla con SQL explícito (`DROP TABLE IF EXISTS` + `CREATE TABLE prueba_borrable (...)`) y la borra al terminar. No es `create_all` ni una migración: es DDL de un test sobre `libreria_test`, y `esquema_test` igual rehace el esquema `public` en cada corrida.
  - «Sesión abierta después del bloque» (DoD): un espía envuelve `session.close` y verifica cero llamadas, la entidad confirmada sigue en la sesión (`entity in session`, que `close()` vaciaría) y `SELECT 1` funciona después del bloque.
  - «Rollback cuando hay una excepción» (DoD): `add` + `flush` + excepción dentro del bloque; desde otra sesión, `count` de `editorial` es 0. Se repite con una excepción de negocio propia del test (`StockInsuficiente(Exception)`) después de dos escrituras: 0 filas y el mismo objeto de excepción afuera.
  - Expiración tras rollback (R7, caracterización): una editorial confirmada antes, tras un bloque que falla, figura en `inspect(e).expired`; su id guardado antes como `int` sigue usable sin consultar.
  - Dependencia (sin base): app FastAPI de test con un endpoint que pide `Depends(get_session)` y **dos** UoW de clases distintas por `proveedor_uow` (con alias `Annotated`); `dependency_overrides[get_session]` entrega una sesión falsa nueva por petición. Se verifica que la sesión y los dos UoW comparten el mismo objeto, que el UoW llega sin bloque abierto y que dos peticiones dan sesiones distintas.

## Risks / Trade-offs

- **[R1] Dos formas de 409 conviven** (`HTTPException` de `commit_or_409` en módulos sin migrar y `Conflicto` desde el UoW) → Mismo código y mismo cuerpo `{"detail": ...}`; el cliente no las distingue. Converge cuando CHG-16 borra `commit_or_409`/`traducir_integrity`.
- **[R2] `session.delete(entity)` sobre un padre con hijos**: sin `passive_deletes`, el flush del ORM intenta poner en NULL la FK de los hijos cargados (o los carga) y el error sale como NOT NULL (`23502`, mensaje genérico) en vez de la FK con mensaje propio → Hoy no hay ninguna baja física. Si un módulo la agrega sobre un padre con hijos, declara `passive_deletes=True` en la relación (la base decide con su FK) o define su propio `delete`. Se documenta en el docstring de `delete`.
- **[R3] Expresiones SQL en atributos** (`func.now()`): dejan el atributo expirado y su lectura posterior es carga perezosa → `soft_delete` usa `datetime.now(UTC)`; el docstring del repositorio lo advierte para los módulos.
- **[R4] Lecturas fuera del bloque**: si un servicio lee antes de `async with uow`, la transacción ya empezó por autobegin; el UoW la confirma igual al salir. Si un servicio lee y **no** abre el bloque, `get_session` cierra la sesión y la transacción se descarta (correcto para lecturas). Convención para CHG-13/15/16: también las lecturas se hacen dentro de `async with uow`.
- **[R5] Un `rollback()` que falla** (conexión caída) dentro de `__aexit__` reemplazaría la excepción original → Se acepta: la nueva excepción encadena la original (`__context__`) y el handler global evita el 500 sólo para `IntegrityError`; es un escenario de infraestructura, no de entrada inválida.
- **[R7] `rollback()` expira los objetos de la sesión** aunque `expire_on_commit=False`: leer después `usuario_actual.id` (cargado por una dependencia en la misma sesión) dispara una carga perezosa → `MissingGreenlet` en async → Docstring del UoW que lo advierte y convención: guardar ids como valores simples antes del bloque; test de caracterización en `test_unit_of_work_db.py`.
- **[R6] El modelo de test usa un registro propio de SQLModel**: si una versión futura de SQLModel dejara de aceptar `registry=`, el fallback es mapear la tabla de prueba con `DeclarativeBase` de SQLAlchemy y su propio `MetaData` (el repositorio no usa nada exclusivo de SQLModel salvo `sqlmodel_update` en `update`, que no se ejercita sobre `Borrable`).

## Migration Plan

Sin migración de base ni cambios de comportamiento visibles: tres archivos nuevos en `core/` (`repository.py`, `unit_of_work.py`, `dependencies.py`), la clase `Conflicto` en `errors.py`, su handler en `main.py` y los tests. Los módulos se migran en CHG-13 (catálogo), CHG-15 (clientes) y CHG-16 (ventas) con el patrón de D6/D7; CHG-16 borra `commit_or_409`/`traducir_integrity` si ya no tienen consumidores. Rollback: revertir el PR (nadie depende todavía de estos archivos).

## Decisiones confirmadas

Confirmadas por **Matias** (revisor de `core/`) el 2026-11-04:

1. **409 por excepción de dominio** (D6): el UoW revierte y lanza `Conflicto(mensaje_para(e, self.MENSAJES))`; `Conflicto` vive en `app/core/errors.py` y `app/main.py` la traduce a 409. CHG-04 suma `errors.py` (sólo la clase) y `main.py` (un handler); Matias corrige «Archivos» del plan. `unit_of_work.py` y `repository.py` no importan FastAPI. Cada UoW de módulo declara sus `MENSAJES`. Desde CHG-13 los servicios migrados lanzan `Conflicto` (después `NoEncontrado`/`Prohibido`).
2. **API del UoW** (D5): sin `commit()`/`rollback()` públicos, `RuntimeError` en bloques anidados (por sesión, incluso con UoW distintos), bloques sucesivos permitidos. Revierte ante **cualquier** excepción y la deja seguir sin cambios. Docstring con la advertencia de R7. No llama a `session.begin()`.
3. **`SoftDeleteRepository.delete`** sobrescrito: `NotImplementedError("Usá soft_delete")` (D4).
4. **Dependencia**: fábrica genérica `proveedor_uow(Clase)` (D7), con alias `Annotated` por módulo; todo UoW de módulo se construye sólo con `(session)`.
5. **CHG-11**: registro (RN-02) en un solo UoW (usuario, asignación, cliente) con `uq_usuario_email` y `uq_cliente_email` en `MENSAJES`; `intento_acceso` con `async with app.state.sessionmaker() as s: async with IntentosUoW(s):`; alcanza el autobegin, no hace falta abrir una transacción nueva.
6. **`get_by_id`**: la base usa `session.get`; `SoftDeleteRepository` lo sobrescribe con `select ... WHERE borrado_en IS NULL`; los métodos de módulo con precarga usan `select` + `options(...)`.
7. `soft_delete` usa `datetime.now(UTC)`. El arreglo RN-12→RN-15 del docstring de `errors.py` va en el PR de documentación de Matias, no acá.

Pendiente de visto bueno de Matias en el PR: `proveedor_uow` vive en `app/core/dependencies.py` (nuevo) y no en `unit_of_work.py`, porque necesita `Depends` y el UoW no puede importar FastAPI. Es un archivo más fuera de la lista que aprobó (`errors.py`, `main.py`).

**Nota para CHG-11 (tests)**: hoy `tests/conftest.py` sólo pone `POSTGRES_DB=libreria_test` en el entorno del **subproceso** de Alembic; el fixture `client` sobrescribe `get_session` pero no `app.state.sessionmaker`, y como `ASGITransport` de httpx no ejecuta el lifespan, `app.state.sessionmaker` ni siquiera existe en esos tests. Un `intento_acceso` que use `app.state.sessionmaker` fallaría (o, si el lifespan corriera, escribiría en la base de desarrollo del `.env`). CHG-11 debe hacer que `client` fije `fastapi_app.state.sessionmaker = sessionmaker_test` (y lo restaure). No afecta a CHG-04: sus tests usan `sessionmaker_test` directo y overrides de `get_session`.

Para **Nico (CHG-07)**: `Libro.borrado_en` tiene que llamarse exactamente así y ser `DateTime(timezone=True)` nullable; `SoftDeleteRepository` lo verifica al construir.
