# Design

## Context

CHG-09b puede implementarse sobre `main` con CHG-07/08 ya mergeados: los schemas son contratos Pydantic y no crean tablas ni importan modelos. El modelo `Libro` sigue teniendo la columna `stock`; `stock_inicial` es sólo el nombre del campo en el contrato de entrada (la consigna lo muestra en el ejemplo del cuerpo de `POST /libros`).

## Goals / Non-Goals

**Goals:**
- Dejar los contratos de catálogo y ventas alineados con la consigna antes de que CHG-13 migre los módulos.
- Que el stock no sea escribible por `PATCH` ni por campos no declarados (RN-11, Ej3): todo lo que no está en el contrato es 422.
- Mantener el alta de libro funcionando mientras tanto: `service.crear` traduce `stock_inicial` a la columna `stock`.

**Non-Goals:**
- Implementar `POST /libros/{id}/reponer`, `GET /libros/{id}/movimientos` ni `DELETE /libros/{id}` (CHG-13).
- Crear `movimiento_stock` ni el punto único de escritura de stock (CHG-13, con firma acordada con Matias).
- Tocar los contratos de editoriales, géneros, autores, clientes ni usuarios.

## Decisions

- `LibroCreate.stock` pasa a llamarse `stock_inicial` (`StockDto`, >= 0) y la clase fija `extra="forbid"`. El servicio excluye `autores` y `stock_inicial` del `model_dump` y construye `Libro(stock=datos.stock_inicial, ...)`: el alta sigue escribiendo la columna hasta que CHG-13 introduzca el movimiento «Stock inicial».
- `LibroUpdate` conserva sólo `titulo` y `precio`, ambos `| None` con el validador `no_null` existente; cualquier otro campo (`stock`, `isbn`, `editorial_id`, `genero_id` o uno desconocido) es 422 por `extra="forbid"` o por campo inexistente.
- `LibroAutorCreate` también fija `extra="forbid"`: un campo de más dentro de `autores[]` se rechaza igual que en el nivel raíz.
- `ReponerIn` declara `cantidad` (`int`, `ge=1`, `le=INT32_MAX`) y `motivo` (`str` opcional, `min_length=1`, `max_length=255`), con `extra="forbid"`. El motivo es opcional porque la consigna no fija el cuerpo del endpoint y el servicio de CHG-13 puede completar un motivo por defecto; si el equipo decide exigirlo, el cambio es de una línea.
- Los contratos de salida (`LibroRead`, `LibroDetalleRead`, `VentaRead`, etc.) no cambian: el listado de la consigna sigue mostrando `stock`.

## Risks / Trade-offs

- Renombrar `stock` → `stock_inicial` rompe el contrato vigente del `POST /libros`: los tests y los `.http` del TP 1–4 se actualizan en el mismo PR (CHG-18 los reescribirá con la numeración nueva).
- `PATCH /libros/{id}` deja de aceptar `editorial_id`/`genero_id`: es lo que pide la consigna ("título y precio; el stock no"); el test de identity map que los usaba se reescribe para patchear `titulo`/`precio`.
- Mientras CHG-13 no llegue, `stock_inicial` escribe `libro.stock` sin dejar movimiento: la igualdad stock = suma de movimientos no se cumple todavía en el flujo de alta. Es la transición ya declarada en AGENTS.md §9; este change no la empeora.
