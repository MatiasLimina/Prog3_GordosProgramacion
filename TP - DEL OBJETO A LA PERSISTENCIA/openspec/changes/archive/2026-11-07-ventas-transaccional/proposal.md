# Proposal

## Why

`ventas` es el último módulo que sigue el patrón del TP 1–4: su servicio recibe la sesión, escribe `libro.stock` con un `UPDATE` propio sin dejar `movimiento_stock` (viola RN-11 y la igualdad «stock = suma de movimientos»), puede vender un libro dado de baja (RN-13), lanza `HTTPException` y pagina con `limit`/`offset`. Además `GET /ventas/{id}` quedó con `PERSONAL` provisorio (CHG-12, D8) y no existe `/mis-ventas` (RN-14), así que la cliente no puede ver su venta (C-06). Es CHG-16, el de mayor peso del parcial (Ej6 + Ej8) y está en el camino crítico: CHG-19 (pytest de integración) depende de él.

## What Changes

- **Registro atómico de la venta (RN-09, RN-10, RN-11, RN-13)**: `POST /ventas/` en un solo bloque `async with uow` de un `VentasUoW` nuevo: venta, renglones con el precio copiado, total calculado por el servidor y, por cada renglón (en orden ascendente de `libro_id`), una salida de stock por el punto único `LibroRepository.registrar_movimiento(...)` con motivo `"Venta"`, el usuario que la registra y el `venta_id`. Si algo falla no queda ninguna escritura.
- **409 de la venta**: cliente inexistente (FK, decide la base), libro inexistente (`LibroNoEncontrado` se traduce a conflicto), libro dado de baja, stock insuficiente y total que no entra en `Numeric(12,2)`; todos como excepciones de dominio, sin `HTTPException`. **BREAKING**: el texto del 409 por stock insuficiente pasa a ser el del punto único («Stock insuficiente para el libro {id}: hay {n}, se pidieron {m}.») y vender un libro dado de baja, que hoy da 201, da 409.
- **Aviso del comprobante**: se conserva con `BackgroundTasks` (`await asyncio.sleep(0.5)` + log en `uvicorn.error`), agendado sólo después de que la venta se confirmó.
- **`GET /ventas/{id}` sin `requiere_rol`**: lo decide el servicio; el personal (VENDEDOR o ADMIN vigente) o el cliente dueño (el cliente vinculado al usuario) la ven; cualquier otro, 403. Se quita el `PERSONAL` provisorio.
- **`GET /mis-ventas` (RN-14)**: nueva ruta del grupo protegido, sólo autenticada, que lista con el envoltorio las ventas del cliente vinculado al usuario de la sesión.
- **Listados con envoltorio**: **BREAKING** `GET /ventas/` pasa de lista suelta con `limit`/`offset` a `{items, total, page, size, pages}` con `page`/`size`.
- **Lecturas sin N+1 (Ej8, C-15)**: el detalle de una venta (cliente, renglones y libro de cada renglón, aunque esté dado de baja) y los listados se resuelven con un número fijo de consultas, con la precarga declarada en métodos de `VentaRepository`.
- **Retiro del código viejo**: con `ventas` migrado no queda ningún usuario de `app/core/pagination.py`, `commit_or_409` ni `traducir_integrity`; se borran junto con sus tests.
- **Matriz de acceso**: `GET /ventas/{venta_id}` pasa a protegido sin rol y se agrega `GET /mis-ventas` (`AUTENTICADO`).

## Capabilities

### New Capabilities
- `ventas`: registro transaccional de una venta con su stock y sus movimientos, sus conflictos (409), el aviso en segundo plano, el detalle con control de dueño, el listado del personal y `/mis-ventas`, y las lecturas con cantidad fija de consultas.

### Modified Capabilities
- `grupos-de-rutas`: se reemplaza «Detalle de venta provisorio» por el detalle protegido sin rol (decide el servicio) y se agrega `/mis-ventas` como ruta protegida sólo autenticada.
- `movimientos-stock`: el punto único de escritura devuelve además el precio vigente del libro, leído en la misma sentencia que cambia el stock (lo usa la venta para copiar el precio; ver design, pregunta abierta Q1).
- `errores-de-dominio`: `ventas` se suma a los módulos migrados sin errores HTTP en el negocio, y el libro inexistente en una venta se responde como conflicto.

## Impact

- **Código**: `app/modules/ventas/` (`repository.py` ampliado, `unit_of_work.py` nuevo, `service.py` y `router.py` reescritos); `app/modules/clientes/repository.py` (`get_por_usuario`); `app/modules/libros/repository.py` (`ResultadoMovimiento.precio`, si se confirma Q1); `app/core/errors.py` (excepciones nuevas; se borran `commit_or_409` y `traducir_integrity`); `app/core/pagination.py` (se borra); `app/core/dependencies.py` (constante de roles del personal); `app/main.py` (monta el router de `/mis-ventas`; comentario de la red de seguridad). Archivos compartidos: los toca Matias, lead y responsable del change.
- **Tests**: `tests/test_ventas_db.py` (adaptado al envoltorio, a los textos nuevos y a la sesión del personal), tests nuevos de repositorio, UoW, dueño y `/mis-ventas`; `tests/matriz_acceso.py`; `tests/test_codigo_libros.py` (agrega `ventas`); se borran `tests/test_pagination.py` y los tests de `commit_or_409`/`traducir_integrity` de `tests/test_errors.py`.
- **API**: cambian la forma de `GET /ventas/` y textos de 409; aparece `GET /mis-ventas`. Los `.http` de ventas se ajustan en CHG-18 (Lauti).
- **Sin cambios de esquema** ni migraciones; el seed (CHG-17) ya usa el mismo punto único y el literal `"Venta"`.
- **Documentación**: `AGENTS.md` §9 «Transición» (filas de ventas → ✅) y `PLAN_PARCIAL.md` (fila CHG-16 en `mergeado (#N)`).
