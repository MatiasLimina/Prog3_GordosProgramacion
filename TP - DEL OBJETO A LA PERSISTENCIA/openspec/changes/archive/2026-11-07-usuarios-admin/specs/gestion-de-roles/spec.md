# Spec Delta

## Purpose

Permite que un administrador consulte, asigne con vigencia y revoque los roles de un usuario sin borrar nunca una asignación, de modo que quede el historial de quién tuvo qué rol y hasta cuándo, y sin que el sistema pueda quedarse sin administradores vigentes.

## ADDED Requirements

### Requirement: Historial de asignaciones de un usuario
`GET /usuarios/{id}/roles` SHALL responder 200 con todas las asignaciones del usuario (vigentes, vencidas y revocadas), ordenadas de la más vieja a la más nueva, cada una con `id`, `usuario_id`, `rol`, `desde`, `vence_en`, `revocada_en` y `otorgada_por`. Si el usuario no existe MUST responder 404 con `{"detail": "El usuario no existe."}`.

#### Scenario: Historial con una revocada
- **WHEN** a un vendedor se le revocó `VENDEDOR` y un ADMIN pide `GET /usuarios/{id}/roles` de ese vendedor
- **THEN** la respuesta es 200 y la asignación revocada aparece con `revocada_en` no nulo

#### Scenario: Usuario inexistente
- **WHEN** un ADMIN pide `GET /usuarios/9999/roles`
- **THEN** la respuesta es 404 con `{"detail": "El usuario no existe."}`

### Requirement: Asignar un rol con vencimiento opcional
`POST /usuarios/{id}/roles` con `{"rol": ..., "vence_en": ...}` SHALL crear una asignación abierta de ese rol, con `vence_en` nulo si no se envía y `otorgada_por` igual al id del ADMIN de la petición, y MUST responder 201 con la asignación creada, incluido `desde`.

#### Scenario: Rol sin vencimiento
- **WHEN** un ADMIN asigna `VENDEDOR` sin `vence_en` a un usuario sin roles
- **THEN** la respuesta es 201 con `vence_en` nulo, `revocada_en` nulo y `otorgada_por` igual al id del ADMIN, y el usuario tiene `VENDEDOR` vigente en su petición siguiente

#### Scenario: Rol con vencimiento futuro
- **WHEN** un ADMIN asigna `VENDEDOR` con `vence_en` dentro de un día y con zona horaria
- **THEN** la respuesta es 201 con ese `vence_en`

### Requirement: Vencimiento inválido es 422
La asignación MUST responder 422, sin crear ninguna fila ni evento, si `vence_en` no tiene zona horaria o no está en el futuro, si el rol no es `ADMIN`, `VENDEDOR` ni `CLIENTE`, o si el cuerpo trae campos no declarados. Un vencimiento inválido nunca es 409.

#### Scenario: Vencimiento en el pasado (C-07)
- **WHEN** un ADMIN asigna un rol con `vence_en` de ayer con zona horaria
- **THEN** la respuesta es 422 y no se crea ninguna asignación ni evento

#### Scenario: Vencimiento sin zona horaria (C-07)
- **WHEN** un ADMIN asigna un rol con `vence_en` `"2030-01-01T10:00:00"`
- **THEN** la respuesta es 422 y no se crea ninguna asignación ni evento

### Requirement: ADMIN no lleva vencimiento
Asignar `ADMIN` con `vence_en` no nulo MUST responder 422 con `{"detail": "El rol ADMIN no puede tener vencimiento."}` sin crear ninguna fila ni evento, de modo que el sistema no pueda quedarse sin administradores por vencimiento (RN-05). Asignar `ADMIN` sin `vence_en` y cualquier otro rol con `vence_en` válido siguen permitidos.

#### Scenario: ADMIN con vencimiento
- **WHEN** un ADMIN asigna `ADMIN` con `vence_en` dentro de un día y con zona horaria
- **THEN** la respuesta es 422 con el mensaje propio y no se crea ninguna asignación ni evento

#### Scenario: Otro rol con el mismo vencimiento
- **WHEN** un ADMIN asigna `VENDEDOR` con ese mismo `vence_en`
- **THEN** la respuesta es 201 con ese `vence_en`

#### Scenario: ADMIN sin vencimiento
- **WHEN** un ADMIN asigna `ADMIN` sin `vence_en` a un usuario sin ese rol
- **THEN** la respuesta es 201 con `vence_en` nulo

### Requirement: Un rol vigente no se asigna dos veces
Si el usuario ya tiene una asignación vigente (no revocada y sin vencer) de ese rol, la asignación MUST responder 409 con `{"detail": "El usuario ya tiene ese rol vigente."}` sin escribir nada. La decisión MUST tomarla el índice único parcial de la base, también cuando dos asignaciones iguales llegan a la vez.

#### Scenario: Rol ya vigente
- **WHEN** un ADMIN asigna `VENDEDOR` a `vendedor@example.com`
- **THEN** la respuesta es 409 con el mensaje propio y las filas de `asignacion_rol` y `evento_seguridad` no cambian

#### Scenario: Dos asignaciones simultáneas
- **WHEN** dos peticiones asignan a la vez el mismo rol al mismo usuario sin ese rol
- **THEN** una responde 201, la otra 409, y queda una sola asignación abierta de ese rol

### Requirement: Reasignar un rol vencido
Si la asignación abierta de ese rol está vencida, la asignación SHALL cerrarla escribiendo `revocada_en` igual a su propio `vence_en` (nadie la revocó: dejó de valer al vencer) y abrir una nueva, en la misma transacción. La fila vencida MUST conservarse con su `vence_en` original. Una asignación abierta todavía vigente MUST NOT tocarse: la asignación responde 409 como en «Un rol vigente no se asigna dos veces».

#### Scenario: Reasignación de un rol vencido
- **WHEN** un usuario tiene `VENDEDOR` con `vence_en` en el pasado y `revocada_en` nulo, y un ADMIN le asigna `VENDEDOR`
- **THEN** la respuesta es 201, la fila vieja queda con `revocada_en` igual a su `vence_en` y su `vence_en` sin cambios, y hay una sola asignación abierta de `VENDEDOR`, la nueva

#### Scenario: Una vigente con vencimiento futuro no se cierra
- **WHEN** un usuario tiene `VENDEDOR` con `vence_en` dentro de un día y un ADMIN le asigna `VENDEDOR`
- **THEN** la respuesta es 409 con «El usuario ya tiene ese rol vigente.» y la fila sigue con `revocada_en` nulo

#### Scenario: Falla al abrir la nueva
- **WHEN** la inserción de la asignación nueva falla después de cerrar la vencida
- **THEN** la fila vencida sigue con `revocada_en` nulo

### Requirement: Asignar a un usuario inexistente
Si el usuario de la ruta no existe, la asignación MUST responder 404 con `{"detail": "El usuario no existe."}` sin crear filas. La decisión MUST tomarla la clave foránea de la base, sin una consulta previa.

#### Scenario: Usuario inexistente
- **WHEN** un ADMIN pide `POST /usuarios/9999/roles` con un cuerpo válido
- **THEN** la respuesta es 404 con `{"detail": "El usuario no existe."}` y no se crea ningún evento

### Requirement: Revocar sin borrar
`DELETE /usuarios/{id}/roles/{rol}` SHALL escribir `revocada_en` en la asignación vigente de ese rol, sin borrar la fila, y responder 200 con la asignación revocada. El permiso se pierde en la petición siguiente del usuario, con la misma cookie.

#### Scenario: Revocación con la sesión abierta (C-07)
- **WHEN** un vendedor con sesión abierta crea un cliente (201), un ADMIN pide `DELETE /usuarios/{id}/roles/VENDEDOR` de ese vendedor (200) y el vendedor vuelve a pedir `POST /clientes/` con la misma cookie
- **THEN** la segunda petición del vendedor responde 403, `GET /auth/yo` con su cookie muestra `roles_vigentes` sin `VENDEDOR` y `roles_token` con `VENDEDOR`, y la fila revocada sigue en `asignacion_rol` con `revocada_en` no nulo

#### Scenario: Rol que se puede volver a dar
- **WHEN** se revoca `VENDEDOR` a un usuario y después un ADMIN se lo asigna de nuevo
- **THEN** la asignación responde 201 y el historial muestra las dos filas

### Requirement: Revocar lo que no está vigente
Si el usuario no existe, la revocación MUST responder 404 con `{"detail": "El usuario no existe."}`; si existe pero no tiene ese rol vigente (nunca lo tuvo, ya fue revocado o está vencido), MUST responder 404 con `{"detail": "El usuario no tiene ese rol vigente."}`. En ningún caso escribe filas. Un rol fuera de `ADMIN`, `VENDEDOR` y `CLIENTE` en la ruta es 422.

#### Scenario: Rol ya revocado
- **WHEN** un ADMIN revoca dos veces seguidas `VENDEDOR` al mismo usuario
- **THEN** la primera responde 200 y la segunda 404 con «El usuario no tiene ese rol vigente.»

#### Scenario: Rol desconocido en la ruta
- **WHEN** un ADMIN pide `DELETE /usuarios/3/roles/GERENTE`
- **THEN** la respuesta es 422

### Requirement: Nadie se revoca su propio ADMIN
Un ADMIN que pide revocar su propio rol `ADMIN` MUST recibir 409 con `{"detail": "No podés revocarte tu propio rol de administrador."}` y la asignación MUST seguir vigente (RN-05). Revocarse otro rol propio sí está permitido.

#### Scenario: Autoprotección (C-08)
- **WHEN** `admin@example.com` pide `DELETE /usuarios/{su id}/roles/ADMIN`
- **THEN** la respuesta es 409 con el mensaje propio, su `ADMIN` sigue vigente y no se crea ningún evento

#### Scenario: No es un 403
- **WHEN** se compara la respuesta de la autoprotección con la de una ruta sin permiso
- **THEN** la autoprotección es 409 y nunca 403

### Requirement: Nunca quedan cero administradores vigentes
Una revocación de `ADMIN` que dejaría al sistema sin ninguna asignación `ADMIN` vigente MUST responder 409 con `{"detail": "No se puede revocar: el sistema quedaría sin administradores vigentes."}` sin escribir nada (RN-05). La regla MUST cumplirse también cuando dos revocaciones de `ADMIN` corren a la vez.

#### Scenario: Revocar a otro administrador
- **WHEN** hay dos ADMIN vigentes y uno revoca el `ADMIN` del otro
- **THEN** la respuesta es 200 y queda un ADMIN vigente

#### Scenario: Revocaciones cruzadas simultáneas
- **WHEN** hay exactamente dos ADMIN vigentes y cada uno revoca a la vez el `ADMIN` del otro
- **THEN** una revocación responde 200, la otra 403 (su actor ya no es ADMIN cuando obtiene el bloqueo) sin escribir nada, y queda exactamente un ADMIN vigente

#### Scenario: Último administrador vigente
- **WHEN** el único usuario con `ADMIN` vigente pide revocarse el `ADMIN`
- **THEN** la respuesta es 409 con el mensaje de la autoprotección y su asignación sigue vigente (el conteo final «cero ADMIN» queda como defensa en profundidad: con el actor comprobado no puede darse)

### Requirement: Quien ya no es administrador no revoca
Una revocación de `ADMIN` MUST responder 403 con `{"detail": "No tenés permiso para esta operación."}` y no escribir nada si el actor dejó de tener `ADMIN` vigente mientras esperaba el bloqueo de otra revocación: la sesión se autorizó antes de esa espera y quien ya no es administrador no puede administrar.

#### Scenario: Un ADMIN revocado no revoca a otro
- **WHEN** hay tres ADMIN vigentes (A, B y C), A revoca el `ADMIN` de B y a la vez B revoca el de C
- **THEN** la revocación de A responde 200, la de B responde 403 sin escribir nada ni dejar evento, y A y C siguen siendo ADMIN vigentes

### Requirement: Evento de cada cambio de rol en la misma transacción
Cada asignación y cada revocación SHALL dejar una línea en `evento_seguridad` con el correo del ADMIN como `actor` y una `accion` que nombra la operación, el rol y el id del usuario, en la misma transacción que el cambio: quedan las dos cosas o ninguna (RN-16). Una operación rechazada no deja evento.

#### Scenario: Línea de una asignación
- **WHEN** `admin@example.com` asigna `VENDEDOR` al usuario 6
- **THEN** existe una línea nueva con `actor` `admin@example.com` y `accion` «Asignación del rol VENDEDOR al usuario 6»

#### Scenario: Línea de una revocación
- **WHEN** `admin@example.com` revoca `VENDEDOR` al usuario 3
- **THEN** existe una línea nueva con `actor` `admin@example.com` y `accion` «Revocación del rol VENDEDOR al usuario 3»

#### Scenario: Falla al escribir el evento de una revocación
- **WHEN** la escritura del evento falla después de escribir `revocada_en`
- **THEN** la asignación sigue vigente y no queda ningún evento

### Requirement: Sólo un ADMIN administra roles
Las tres rutas de roles SHALL exigir `ADMIN` vigente: sin sesión responden 401 y con otro rol o con el cambio de contraseña pendiente responden 403, sin leer ni escribir asignaciones.

#### Scenario: Vendedor intenta revocar
- **WHEN** un usuario con sólo `VENDEDOR` vigente pide `DELETE /usuarios/1/roles/ADMIN`
- **THEN** la respuesta es 403 y el `ADMIN` del usuario 1 sigue vigente
