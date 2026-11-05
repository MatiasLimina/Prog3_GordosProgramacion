# Proposal

## Why

El Ejercicio 6 del parcial (16 puntos) exige la capa Router → Service → UoW → Repository → Model: `BaseRepository[T]` y `SoftDeleteRepository[T]` que hacen `flush()` y nunca `commit()`, y un `UnitOfWork` base que confirma al salir del bloque, revierte si sale con una excepción y no cierra la sesión porque no la creó. Hoy no existe ninguna de las dos piezas: cada servicio recibe la `AsyncSession` y confirma con `commit_or_409`. CHG-04 es el cuello de botella 1 del plan: CHG-11 (registro de RN-02 en un solo UoW), CHG-13 y CHG-15 no arrancan sin esta base, así que se entrega chica, sin migrar ningún módulo y fácil de revisar en el día.

## What Changes

- `app/core/repository.py` (nuevo):
  - `BaseRepository[T]` (genérico de Python 3.12) que recibe en el constructor la sesión **y la clase del modelo** y ofrece `get_by_id`, `get_all` (con `offset`/`limit` y orden estable por clave primaria), `count`, `add`, `update` (aplica sólo los campos recibidos) y `delete`. `add`, `update` y `delete` hacen `flush()`; ningún método confirma ni precarga relaciones.
  - Un punto de extensión protegido (consulta base + helpers de paginar y contar) para que los repositorios de cada módulo armen métodos nombrados por lo que traen, con su precarga adentro, y cuenten con los mismos filtros que la página.
  - `SoftDeleteRepository[T](BaseRepository[T])`: exige una columna `borrado_en`, filtra los dados de baja en `get_by_id`, `get_all` y `count`, agrega `get_by_id_including_deleted` y `soft_delete` (fecha con zona, sin pisar una baja anterior) y sobrescribe `delete` para que lance `NotImplementedError("Usá soft_delete")`: una entidad con borrado lógico no se borra físicamente.
  - Ni `repository.py` ni `unit_of_work.py` importan nada de FastAPI.
- `app/core/unit_of_work.py` (nuevo):
  - `UnitOfWork` base, gestor de contexto asincrónico: confirma al salir sin error, revierte si sale con **cualquier** excepción (no sólo de integridad; p. ej. «stock insuficiente» de CHG-16) y la deja seguir sin cambios, y **nunca** cierra la sesión. Sin `commit()`/`rollback()` públicos; no admite anidarse sobre sí mismo (`RuntimeError`); sí reusarse en bloques sucesivos. Su docstring advierte que `rollback()` expira los objetos de la sesión aunque `expire_on_commit=False`: los ids que se necesiten después se guardan como valores simples antes de abrir el bloque.
  - Integración con la traducción de `IntegrityError`: el UoW de cada módulo declara su diccionario `MENSAJES` por nombre de constraint y el UoW base, ante un `IntegrityError` (del `flush` adentro del bloque o del `commit` al salir), revierte y lanza la excepción de dominio `Conflicto(mensaje_para(e, self.MENSAJES))`, sin encadenar el error de la base. No lanza `HTTPException`.
- `app/core/errors.py` (se agrega sólo la clase): `Conflicto(Exception)` con el mensaje propio. `mensaje_para`, `commit_or_409` y `traducir_integrity` **no cambian**: siguen sirviendo a los módulos que todavía reciben la sesión hasta CHG-13/15/16.
- `app/main.py` (un handler): `registrar_handlers` agrega el handler de `Conflicto` → 409 con el mismo cuerpo que los 409 de hoy (`{"detail": mensaje}`). El handler global de `IntegrityError` sigue como red de seguridad.
- `app/core/dependencies.py` (nuevo, sólo la fábrica): `proveedor_uow(ClaseUoW)`, dependencia `async` genérica que entrega `ClaseUoW(session)` con la misma sesión de `get_session`, de modo que las dependencias de usuario y de rol (CHG-12) compartan la sesión del UoW. Condición: todo UoW de módulo se construye sólo con `(session)`. Cada módulo define su alias (`LibrosUoWDep = Annotated[LibrosUoW, Depends(proveedor_uow(LibrosUoW))]`). Vive fuera de `unit_of_work.py` porque usa `Depends` de FastAPI.
- Tests nuevos (unitarios con sesión falsa e integración con `libreria_test`), entre ellos los dos del DoD: rollback ante una excepción y sesión abierta después del bloque; además, que el UoW lanza `Conflicto` (no `HTTPException`), que el handler responde 409 con el mensaje, que una excepción de negocio no deja escrituras y que dos dependencias de la misma petición reciben la misma sesión. Para `SoftDeleteRepository` se usa un modelo **sólo de test** con registro propio y una tabla que el test crea y borra con SQL explícito, sin depender de CHG-07 ni de una migración.

**Fuera de alcance**: migrar cualquier módulo a repositorios + UoW (CHG-13, 15, 16) y sus routers; `Libro.borrado_en` y el índice único parcial del ISBN (CHG-07); el envoltorio de paginación (CHG-05); el punto único de escritura del stock (CHG-13 con Matias); las dependencias de usuario y de rol (CHG-12); la sesión propia de `intento_acceso` (CHG-11); que los servicios migrados lancen `Conflicto` (y más adelante `NoEncontrado`/`Prohibido`) en vez de `HTTPException` (desde CHG-13); el arreglo RN-12→RN-15 del docstring de `errors.py` (PR de documentación de Matias); cambios en `app/core/database.py` y cualquier otro cambio en `errors.py` o `main.py` fuera de la clase y el handler.

## Capabilities

### New Capabilities

- `repositorios`: acceso a datos por entidad sobre una sesión compartida: operaciones genéricas de lectura, conteo y escritura sin confirmar, orden estable para paginar, punto de extensión para consultas con nombre y precarga, y la variante con borrado lógico.
- `unidad-de-trabajo`: delimitación transaccional de una operación: confirmar o revertir al salir del bloque sin cerrar la sesión, traducción de violaciones de integridad a un conflicto de dominio que la app responde como 409 con mensajes propios, y construcción del Unit of Work por petición con la misma sesión que el resto de las dependencias.

### Modified Capabilities

Ninguna. `ciclo-de-vida` ya define que `get_session` entrega y cierra la sesión por petición; este change se apoya en eso sin cambiarlo.

## Impact

- **Código**: `app/core/repository.py`, `app/core/unit_of_work.py` y `app/core/dependencies.py` (nuevos); `app/core/errors.py` (agrega `Conflicto`) y `app/main.py` (agrega un handler). Todos son archivos compartidos: revisa Matias, que aprobó sumar `errors.py` y `main.py` y corrige la sección «Archivos» de CHG-04 en el plan. Sin cambios en módulos, routers ni `database.py`.
- **Tests**: `tests/test_conflicto.py`, `tests/test_repository.py`, `tests/test_unit_of_work.py`, `tests/test_dependencies.py` (unitarios) y `tests/test_repository_db.py`, `tests/test_unit_of_work_db.py` (marca `db`), más `tests/modelos_prueba.py` con el modelo sólo de test. La suite existente (373 tests) sigue igual.
- **Documentación**: fila de CHG-04 en `PLAN_PARCIAL.md` (`en PR`).
- **Dependencias**: ninguna nueva.
- **API**: sin cambios visibles (ninguna ruta lanza `Conflicto` todavía; el handler responde con la misma forma que los 409 actuales).
- **Gobernanza**: MEDIUM-HIGH (núcleo compartido y transacciones). Las decisiones las confirmó Matias el 2026-11-04 («Decisiones confirmadas» de `design.md`).
- **Desbloquea**: CHG-11, CHG-13 y CHG-15.
