# Design

## Context

CHG-09a puede implementarse sin que CHG-06/07/08 estén integrados a `main`: los schemas son contratos Pydantic y no crean tablas ni importan modelos. La rama existente `feat/modelos-usuarios` define como referencia los nombres y campos públicos de `Usuario` y `AsignacionRol`; sus commits no se incorporan a esta rama.

## Goals / Non-Goals

**Goals:**
- Definir contratos tipados que CHG-11 y CHG-14 puedan consumir.
- Hacer que las entradas inválidas se rechacen con `ValidationError` (422 en FastAPI) antes de llegar al servicio o a bcrypt.
- Mantener las salidas explícitas y sin secretos.

**Non-Goals:**
- Implementar rutas, servicios, modelos, hashing, JWT ni autorización.
- Cambiar los contratos de catálogo, clientes o ventas (CHG-09b).

## Decisions

- Todas las entradas heredan de `_Entrada`, que fija `extra="forbid"`.
- Los campos `password`, `password_actual` y `password_nueva` comparten una validación UTF-8 con límite inclusivo de 72 bytes.
- `AsignacionRolCreate.vence_en` es opcional; si se envía, debe ser una fecha con offset y estrictamente posterior al momento de validación.
- Las salidas se componen sólo de campos públicos declarados. `UsuarioRead` no declara `password_hash`; `AuthYoRead` reutiliza ese contrato.
- Los roles se restringen a `ADMIN`, `VENDEDOR` y `CLIENTE`, que son los valores admitidos por el modelo de usuario acordado.

## Risks / Trade-offs

- Los schemas se implementan antes de integrar los modelos, así que los nombres de campos deben mantenerse alineados con el contrato acordado en CHG-06/07. Los schemas no importan esos modelos para evitar una dependencia de rama.
- La validación de vigencia usa el reloj UTC del proceso al validar; no hay base de datos ni dependencia temporal externa.
