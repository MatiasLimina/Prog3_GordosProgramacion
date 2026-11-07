# grupos-de-rutas Specification

## Purpose
Separa la API en un grupo abierto y uno protegido, con el control del cambio obligatorio de contraseña (RN-06) aplicado una sola vez a todo el grupo protegido, y fija qué grupo y qué roles corresponden a cada ruta.

## Requirements

### Requirement: Toda ruta está clasificada
Cada ruta de la API SHALL pertenecer a exactamente uno de los dos grupos, abierto o protegido, con los roles que fija la tabla «Endpoints de referencia» de la consigna y los requisitos siguientes. Una ruta que no figure en la clasificación MUST hacer fallar la suite de tests.

#### Scenario: Clasificación completa
- **WHEN** se recorren las rutas de la aplicación
- **THEN** cada una figura en la clasificación con su grupo y sus roles, y la clasificación no nombra rutas inexistentes

#### Scenario: Ruta nueva sin clasificar
- **WHEN** se agrega una ruta a la aplicación sin agregarla a la clasificación
- **THEN** el test de la clasificación falla nombrando esa ruta

### Requirement: Rutas del grupo abierto
El grupo abierto SHALL contener la salud (`GET /health/live`, `GET /health/ready`), todo `/auth` y los GET del catálogo: `GET /libros/`, `GET /libros/{id}`, `GET /editoriales/`, `GET /editoriales/{id}`, `GET /editoriales/{id}/libros`, `GET /generos/`, `GET /generos/{id}/libros`, `GET /autores/`, `GET /autores/{id}` y `GET /autores/{id}/libros`.

#### Scenario: GET del catálogo en el abierto
- **WHEN** se inspecciona el grupo de `GET /autores/{id}`
- **THEN** pertenece al grupo abierto y no exige ningún rol

### Requirement: Rutas protegidas de administración
El grupo protegido SHALL exigir `ADMIN` en `POST /editoriales/`, `PATCH /editoriales/{id}`, `POST /generos/`, `POST /autores/`, `PATCH /autores/{id}`, `POST /libros/`, `PATCH /libros/{id}`, `DELETE /libros/{id}`, `POST /libros/{id}/reponer`, `GET /libros/{id}/movimientos`, `POST /usuarios/`, `GET /usuarios/{id}/roles`, `POST /usuarios/{id}/roles`, `DELETE /usuarios/{id}/roles/{rol}` y `GET /eventos/`.

#### Scenario: Vendedor en una escritura del catálogo
- **WHEN** un usuario con sólo `VENDEDOR` vigente pide cada una de esas rutas
- **THEN** todas responden 403

#### Scenario: El historial de movimientos no es catálogo público
- **WHEN** se inspecciona el grupo de `GET /libros/{id}/movimientos`
- **THEN** pertenece al grupo protegido y exige `ADMIN`, y sin cookie responde 401

#### Scenario: Administración de usuarios en el protegido
- **WHEN** se inspecciona el grupo de cada ruta de `/usuarios` y de `GET /eventos/`
- **THEN** todas pertenecen al grupo protegido y exigen `ADMIN`; sin cookie responden 401 y un ADMIN con el cambio de contraseña pendiente recibe 403

### Requirement: Rutas protegidas del personal
El grupo protegido SHALL exigir `VENDEDOR` o `ADMIN` en `POST /clientes/`, `GET /clientes/`, `GET /clientes/{id}`, `PATCH /clientes/{id}`, `POST /clientes/{id}/perfil`, `GET /clientes/{id}/ventas`, `POST /ventas/` y `GET /ventas/`.

#### Scenario: Cliente en una ruta del personal
- **WHEN** un usuario con sólo `CLIENTE` vigente pide cada una de esas rutas
- **THEN** todas responden 403

### Requirement: El grupo abierto no pide sesión
Las rutas del grupo abierto marcadas «Cualquiera» SHALL responder sin cookie con su código normal, y MUST NOT responder 401 ni 403 por falta de sesión o por el cambio de contraseña pendiente.

#### Scenario: Catálogo público sin sesión
- **WHEN** se pide `GET /libros/`, `GET /editoriales/` y `GET /generos/` sin cookie
- **THEN** las tres responden 200

#### Scenario: Catálogo con el cambio pendiente
- **WHEN** un usuario con `debe_cambiar_password` verdadero pide `GET /libros/` con su cookie
- **THEN** la respuesta es 200

### Requirement: /auth no pasa por el control del cambio obligatorio
Las rutas `/auth` que piden estar autenticado (`GET /auth/yo`, `POST /auth/cambiar-password`) SHALL responder 401 sin sesión y MUST atender a un usuario con el cambio de contraseña pendiente (RN-06: con el cambio pendiente sólo puede usar `/auth` y las rutas que no piden sesión).

#### Scenario: Cambiar la contraseña con el cambio pendiente (C-09)
- **WHEN** un usuario con `debe_cambiar_password` verdadero pide `POST /auth/cambiar-password` con su contraseña actual correcta
- **THEN** la respuesta es 200

#### Scenario: /auth/yo sin sesión
- **WHEN** se pide `GET /auth/yo` sin cookie
- **THEN** la respuesta es 401

### Requirement: El grupo protegido exige sesión
Toda ruta del grupo protegido MUST responder 401 sin una sesión válida (sin cookie, token inválido o vencido, usuario inexistente o inactivo), con el mismo cuerpo que el resto de los 401 de sesión, antes de evaluar el cambio pendiente o el rol.

#### Scenario: Sin cookie en cada ruta protegida (C-06)
- **WHEN** se pide cada ruta del grupo protegido sin cookie
- **THEN** todas responden 401

### Requirement: Control del cambio obligatorio de contraseña
Mientras el usuario actual tenga `debe_cambiar_password` verdadero, toda ruta del grupo protegido MUST responder 403 con `{"detail": "Tenés que cambiar la contraseña antes de continuar."}`, aunque tenga el rol que la ruta exige, y sin ejecutar la operación.

#### Scenario: Bloqueado salvo /auth (C-09)
- **WHEN** un vendedor con `debe_cambiar_password` verdadero pide `POST /clientes/` con un cuerpo válido
- **THEN** la respuesta es 403 con el mensaje del cambio pendiente y no se crea ningún cliente

#### Scenario: El cambio pendiente gana sobre la falta de rol
- **WHEN** un vendedor con `debe_cambiar_password` verdadero pide `POST /libros/` (exige `ADMIN`)
- **THEN** la respuesta es 403 con el mensaje del cambio pendiente

#### Scenario: Misma cookie después del cambio (C-09)
- **WHEN** ese vendedor cambia su contraseña con `POST /auth/cambiar-password` y vuelve a pedir `POST /clientes/` con la misma cookie, sin iniciar sesión de nuevo
- **THEN** la respuesta es 201

### Requirement: Control montado una sola vez
El control del cambio obligatorio SHALL declararse una única vez, en el grupo protegido, y aplicarse a todas sus rutas; MUST NOT declararse en ninguna ruta individual ni en el grupo abierto.

#### Scenario: Inspección de las rutas
- **WHEN** se inspeccionan las dependencias de cada ruta de la aplicación
- **THEN** cada ruta del grupo protegido tiene el control exactamente una vez, heredado del grupo, y ninguna ruta del grupo abierto lo tiene

### Requirement: Parámetro de ruta inválido con sesión
Un parámetro de ruta que no es un entero válido SHALL responder 422 sin ejecutar la operación de la ruta, también con una sesión iniciada que tiene permiso para la ruta (C-01).

#### Scenario: Ruta abierta con sesión
- **WHEN** un administrador con sesión pide `GET /libros/abc`
- **THEN** la respuesta es 422 y el servicio de libros no se ejecuta

#### Scenario: Ruta protegida con sesión
- **WHEN** un administrador con sesión pide `PATCH /editoriales/abc` con un cuerpo válido
- **THEN** la respuesta es 422 y no se modifica ninguna editorial

### Requirement: Detalle de venta protegido sin rol
`GET /ventas/{id}` SHALL pertenecer al grupo protegido sin exigir ningún rol en la ruta: responde 401 sin sesión y 403 con el cambio de contraseña pendiente, y quién puede ver cada venta (personal o cliente dueño) lo decide la operación, no la ruta.

#### Scenario: Clasificación del detalle de venta
- **WHEN** se inspecciona el grupo de `GET /ventas/{id}`
- **THEN** pertenece al grupo protegido, figura como «autenticado» en la clasificación y no declara ningún rol

#### Scenario: Cliente dueño sin rol de personal
- **WHEN** un usuario con sólo CLIENTE vigente pide el detalle de una venta de su cliente vinculado
- **THEN** la respuesta es 200, no 403

#### Scenario: Detalle sin sesión
- **WHEN** se pide `GET /ventas/1` sin cookie
- **THEN** la respuesta es 401

### Requirement: Mis ventas sólo autenticada
`GET /mis-ventas` SHALL pertenecer al grupo protegido y pedir sólo una sesión válida (RN-14): sin cookie responde 401, con el cambio de contraseña pendiente 403, y cualquier usuario autenticado sin el cambio pendiente es atendido, tenga o no un rol.

#### Scenario: Clasificación de mis ventas
- **WHEN** se inspecciona el grupo de `GET /mis-ventas`
- **THEN** pertenece al grupo protegido, figura como «autenticado» y no declara ningún rol

#### Scenario: Mis ventas con el cambio pendiente
- **WHEN** un usuario con `debe_cambiar_password` verdadero pide `GET /mis-ventas` con su cookie
- **THEN** la respuesta es 403

#### Scenario: Mis ventas sin sesión
- **WHEN** se pide `GET /mis-ventas` sin cookie
- **THEN** la respuesta es 401
