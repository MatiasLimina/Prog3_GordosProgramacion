# Proposal

## Why

Desde CHG-11 la API sabe **quién** pide (cookie → `get_usuario_actual`, 401), pero no decide **qué puede hacer**: hoy cualquiera, sin sesión, crea editoriales y libros, edita clientes o registra ventas, y un usuario con el cambio de contraseña pendiente usa toda la API. CHG-12 cubre el Ejercicio 5 de la consigna (Autorización, 12 %): roles vigentes leídos de la base en cada petición (RN-04), control del cambio obligatorio de contraseña (RN-06) y los dos grupos de rutas de `main.py`. Es P1 del camino crítico: destraba CHG-14 (administración de usuarios) y CHG-16 (ventas), que necesitan `requiere_rol` y el usuario actual autorizado.

## What Changes

- **`requiere_rol(*roles)`** en `app/core/dependencies.py`: reutiliza `get_usuario_actual` (401) y consulta los roles **vigentes en la base** (no revocados y sin vencer) en cada petición, con la misma sesión de la petición; si ninguno coincide responde **403**. Los roles del token son informativos y no dan permiso. Devuelve el `UsuarioActual`, así los handlers que necesitan al usuario (CHG-13, 14, 16) lo reciben de la misma dependencia. Se exportan dependencias únicas reutilizables (`SOLO_ADMIN`, `PERSONAL` = VENDEDOR o ADMIN) para que FastAPI las cachee por petición.
- **Control del cambio obligatorio de contraseña (RN-06)**: dependencia que responde **403** con un mensaje propio si el usuario actual tiene `debe_cambiar_password`; se monta **una sola vez**, en el grupo protegido.
- **Dos grupos de rutas en `app/main.py`**: uno **abierto** (salud, todo `/auth` —incluidos `/auth/yo` y `/auth/cambiar-password`, que piden sesión pero no pasan por el control—, y los GET del catálogo público) y uno **protegido** con el control RN-06 montado en el router del grupo. Toda ruta protegida responde 401 sin sesión y 403 con el cambio pendiente.
- **Clasificación de las rutas existentes** según la tabla «Endpoints de referencia» de la consigna: los `router.py` de editoriales, géneros, autores, libros, clientes y ventas se dividen en un router abierto (GET públicos) y uno protegido, con el rol por ruta (`ADMIN` para escrituras del catálogo; `VENDEDOR` o `ADMIN` para clientes y ventas). **Sólo** cambia el montaje y la dependencia de rol de cada ruta: servicios, firmas y contratos quedan como están (su migración a UoW es de CHG-13/15/16).
- **Nueva excepción de dominio `SinPermiso`** en `app/core/errors.py` y su handler en `app/main.py` (403 `{"detail": mensaje}`): el código de negocio sigue sin lanzar `HTTPException`. CHG-16 la reutiliza para el 403 del dueño de la venta.
- **Matriz de acceso como test**: un test recorre todas las rutas de la app y exige que cada una esté clasificada (grupo y roles); una ruta nueva sin clasificar hace fallar la suite. Así CHG-13, 14 y 16 no pueden olvidar montar sus rutas.
- **Tests existentes del catálogo, clientes y ventas**: pasan a correr con una sesión de ADMIN (fixture local por módulo), porque sus POST/PATCH quedan en el grupo protegido.
- **BREAKING** (API): las escrituras del catálogo, todo `/clientes` y todo `/ventas` exigen sesión y rol; sin cookie responden 401. Nadie externo consume todavía la API del parcial; los `.http` del TP se reescriben en CHG-18.

Fuera de alcance: alta de personal y gestión de roles por API (`/usuarios`, `/eventos`, RN-05; CHG-14); decisión de dueño en `GET /ventas/{id}` y `GET /mis-ventas` (RN-14; CHG-16); `DELETE /libros/{id}`, reponer y movimientos (CHG-13); migrar servicios a UoW (CHG-13/15/16); casos `.http` (CHG-18).

## Capabilities

### New Capabilities
- `autorizacion`: decisión de permisos por rol con los roles vigentes en la base en cada petición (RN-04), 401 antes que 403, roles del token sólo informativos, mensaje fijo de 403 y dependencias que comparten la sesión de la petición.
- `grupos-de-rutas`: grupo abierto y grupo protegido en `main.py`, control del cambio obligatorio de contraseña montado una sola vez (RN-06), clasificación de cada ruta (grupo y roles) y validación de parámetros de ruta con sesión (C-01).

### Modified Capabilities
(ninguna: `autenticacion` —usuario actual por cookie, `/auth/yo`— y `cambio-de-contrasena` se usan tal cual; sus requisitos no cambian)

## Impact

- **Archivos compartidos** (lead: Matias): `app/core/dependencies.py` (`requiere_rol`, `SOLO_ADMIN`, `PERSONAL`, control RN-06), `app/core/errors.py` (`SinPermiso`), `app/main.py` (dos grupos y handler 403), `tests/conftest.py` / `tests/auxiliares_auth.py` (ayuda para iniciar sesión con un rol).
- **Routers de otros changes** (sólo montaje y rol, sin tocar servicios): `app/modules/{editoriales,generos,autores,libros,clientes,ventas}/router.py`. Requiere coordinar con Nico (CHG-13/15) para que sus PRs conserven la división (ver design, «Decisiones a confirmar»).
- **Tests existentes** adaptados con una sesión de ADMIN: `test_editoriales.py`, `test_generos.py`, `test_libros_crud_db.py`, `test_libros_por_editorial_genero.py`, `test_libros_validaciones.py`, `test_clientes_db.py`, `test_ventas_db.py`.
- **Base**: sin migraciones; usa `asignacion_rol` y `usuario` tal como están.
- **Dependencias Python**: ninguna nueva.
- **Documentación**: `PLAN_PARCIAL.md` (fila CHG-12 y archivos/DoD de la sección CHG-12), `AGENTS.md` §9 (filas de transición).
- **Casos de la consigna**: C-01, C-06 (401 y vendedor → 403; la parte «la cliente ve su venta y no la ajena» queda para CHG-16), C-07 (403 en la petición siguiente y diferencia en `/auth/yo`; la revocación por API es de CHG-14) y C-09.
- **Gobernanza**: dominio **CRITICAL** (autorización). Ningún código se escribe sin la aprobación explícita de Matias de las «Decisiones a confirmar» de `design.md`.
