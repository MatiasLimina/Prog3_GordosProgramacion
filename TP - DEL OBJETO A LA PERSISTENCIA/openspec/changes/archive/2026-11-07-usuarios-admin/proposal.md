# Proposal

## Why

Desde CHG-12 la API decide permisos con los roles vigentes en la base (RN-04), pero nadie puede **administrarlos** por API: el personal y sus roles sólo existen si los carga el seed o se tocan a mano en `asignacion_rol`. CHG-14 cubre el resto del Ejercicio 5 de la consigna (alta de personal con contraseña provisoria; asignar con vencimiento opcional, revocar sin borrar y reasignar un rol vencido; autoprotección RN-05) y la parte de RN-16 que falta (alta de personal y cambio de rol dejan su evento en la misma transacción), más el historial `GET /eventos`. Lo necesitan los casos C-07 (revocación por API) y C-08 (autoprotección).

## What Changes

- **`POST /usuarios/`** (ADMIN): alta de personal con contraseña provisoria y `debe_cambiar_password = true`. El hash bcrypt se calcula **antes** de abrir el UoW (indicación de Matias, 2026-11-04). Correo repetido → 409 por `uq_usuario_email`; 201 con `UsuarioRead` (sin `password_hash`). Deja el evento «Alta de personal» en la misma transacción. El alta **no** asigna rol (confirmado por Matias y Lauti, 2026-11-07): el rol se da después con `POST /usuarios/{id}/roles`, y mientras tanto el usuario nuevo recibe 403 en todo lo protegido (design D1).
- **`GET /usuarios/{id}/roles`** (ADMIN): historial completo de asignaciones del usuario (vigentes, vencidas y revocadas); 404 si el usuario no existe.
- **`POST /usuarios/{id}/roles`** (ADMIN): asigna un rol con `vence_en` opcional (con zona y en el futuro; si no, 422, ya en el contrato) y `otorgada_por` = el ADMIN de la petición. Si la asignación abierta de ese rol está **vencida**, la cierra con `revocada_en = vence_en` (nadie la revocó: venció) y abre una nueva; si está **vigente**, no se toca y el índice único parcial da 409 (sin consulta previa). `ADMIN` con `vence_en` → 422 «El rol ADMIN no puede tener vencimiento.» (validado en el servicio). Usuario inexistente → 404 (la FK lo decide; excepción explícita a AGENTS §8, gana la consigna). Deja el evento en la misma transacción.
- **`DELETE /usuarios/{id}/roles/{rol}`** (ADMIN): revoca la asignación vigente escribiendo `revocada_en` (la fila no se borra); 200 con la asignación revocada; 404 si el usuario no existe o no tiene ese rol vigente. **RN-05**: nadie se revoca su propio `ADMIN` y nunca quedan cero administradores vigentes → 409, también con dos revocaciones simultáneas (`SELECT … FOR UPDATE ORDER BY id` de las filas `ADMIN` vigentes y conteo después de revocar). Deja el evento en la misma transacción.
- **`GET /eventos/`** (ADMIN): historial de seguridad paginado con el envoltorio `{items, total, page, size, pages}`, del más reciente al más viejo.
- **Excepciones de dominio** nuevas en `app/core/errors.py`: `UsuarioNoEncontrado` y `RolNoVigente` (404), `AutoRevocacionAdmin` y `SinAdministradores` (409), `AdminConVencimiento` (422, subclase de `PeticionInvalida`). RN-05 es 409, nunca `SinPermiso` (403).
- **Montaje**: `/usuarios` y `/eventos` en el grupo **protegido** de `app/main.py` con `SOLO_ADMIN`; las cinco rutas se suman a `tests/matriz_acceso.py`.
- **Contratos** en `app/modules/usuarios/schemas.py` (archivo de Lauti; cambio chico aprobado por él, 2026-11-07): nuevo `EventoSeguridadRead` (`id`, `cuando`, `actor`, `accion`, `from_attributes=True`) y un solo tipo público `Rol`, que pasan a usar `AsignacionRolCreate`, `AsignacionRolRead` y `AuthYoRead` y el `{rol}` de la ruta (422 por el tipo). Su comportamiento no cambia; `UsuarioCreate` y `UsuarioRead` se usan tal cual.
- Sin cambios **BREAKING**: sólo se agregan rutas; ninguna ruta, contrato (salvo el nombre del tipo de rol, que acepta los mismos valores) ni tabla existente cambia.

Fuera de alcance: desactivar usuarios o editar sus datos; normalizar mayúsculas del correo (anotado desde CHG-11); casos `.http` (CHG-18: C-07 y C-08 ya se pueden escribir por API). El vencimiento de `ADMIN` ya no es un riesgo: la API lo rechaza (design D3b).

## Capabilities

### New Capabilities
- `alta-de-personal`: alta de un usuario del personal por un ADMIN, con contraseña provisoria, cambio obligatorio pendiente, hash fuera de la transacción y evento de seguridad en la misma transacción.
- `gestion-de-roles`: consulta, asignación con vigencia, reasignación de un rol vencido y revocación sin borrar de las asignaciones de rol, con la autoprotección RN-05 y el evento de cada cambio en la misma transacción.
- `historial-de-seguridad`: listado paginado de `evento_seguridad` para el ADMIN y convención de actor y acción de cada línea.

### Modified Capabilities
- `grupos-de-rutas`: «Rutas protegidas de administración» suma `POST /usuarios/`, `GET`/`POST /usuarios/{id}/roles`, `DELETE /usuarios/{id}/roles/{rol}` y `GET /eventos/` con `ADMIN`.
- `contratos-auth-usuarios`: nuevo contrato de salida del historial de seguridad (`id`, `cuando`, `actor`, `accion`).

## Impact

- **Módulo `usuarios`** (Nico, con revisión de Matias porque `service.py` y `router.py` tienen el auth de CHG-11): `repository.py` (métodos de asignaciones y eventos), `service.py` (funciones de administración), `router.py` (nuevos routers `/usuarios` y `/eventos`). `unit_of_work.py` **no cambia**: `UsuariosUoW` ya compone usuarios, asignaciones y eventos y sus `MENSAJES` ya traen `uq_usuario_email` y `uq_asignacion_rol_usuario_rol_vigente`.
- **Archivos compartidos** (revisión de Matias): `app/core/errors.py` (cinco excepciones), `app/main.py` (montar el router en el protegido), `tests/matriz_acceso.py` (cinco rutas).
- **Archivo de Lauti**: `app/modules/usuarios/schemas.py` (`EventoSeguridadRead` y tipo público `Rol`; aprobado por Lauti, 2026-11-07).
- **CHG-15 (PR #58, mergeado en `main` 2f5a148)**: la rama parte de ahí; se reutiliza `constraint_violada` de `app/core/errors.py` para la FK → 404, y las excepciones nuevas van lejos de las de CHG-15 (design D8, D11).
- **Base**: sin migraciones ni cambios de modelos.
- **Dependencias Python**: ninguna nueva.
- **Documentación**: `PLAN_PARCIAL.md` (fila CHG-14 y, en el mismo PR, la ruta `DELETE /usuarios/{id}/roles/{rol}` de la consigna en su sección), `AGENTS.md` §9 (fila «Sin usuarios ni roles»).
- **Casos de la consigna**: C-07 (revocación por API con la sesión abierta; vencimientos inválidos 422) y C-08 (autoprotección 409).
- **Gobernanza**: **HIGH** (administración de roles: adyacente a autorización). Decisiones aprobadas por Matias y Lauti el 2026-11-07 (design, «Decisiones confirmadas»): se puede implementar.
