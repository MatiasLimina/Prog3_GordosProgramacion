# autorizacion Specification

## Purpose
Decide si un usuario autenticado puede usar una ruta que exige un rol, con los roles vigentes leídos de la base en cada petición (RN-04), y distingue «no hay sesión» (401) de «no tenés permiso» (403).

## Requirements

### Requirement: Permiso por rol vigente en la base
Toda ruta que exige uno o más roles SHALL permitir la petición sólo si el usuario actual tiene, en la base y en el momento de esa petición, al menos una asignación vigente (no revocada y sin vencer) de alguno de esos roles. Si no la tiene, MUST responder 403 sin ejecutar la operación.

#### Scenario: Rol exigido vigente
- **WHEN** un usuario con `ADMIN` vigente pide `POST /editoriales/` con un cuerpo válido
- **THEN** la respuesta es 201

#### Scenario: Otro rol (C-06)
- **WHEN** un usuario con sólo `VENDEDOR` vigente pide `POST /libros/` con un cuerpo válido
- **THEN** la respuesta es 403 y no se crea ningún libro

#### Scenario: Cualquiera de varios roles
- **WHEN** una ruta exige `VENDEDOR` o `ADMIN` y la pide un usuario con sólo `VENDEDOR` vigente
- **THEN** la petición se atiende (no responde 403)

#### Scenario: Usuario sin roles
- **WHEN** un usuario autenticado sin ninguna asignación vigente pide `POST /clientes/`
- **THEN** la respuesta es 403

### Requirement: Revocar o vencer un rol quita el permiso en la sesión abierta
El permiso MUST decidirse con la base en cada petición y no con lo que se leyó al iniciar sesión: un rol revocado (`revocada_en` no nulo) o vencido (`vence_en` en el pasado) después del login deja de dar permiso en la petición siguiente con la misma cookie, sin esperar a que el token venza.

#### Scenario: Revocación con la sesión abierta (C-07)
- **WHEN** un vendedor con sesión abierta crea un cliente (201), se le revoca `VENDEDOR` en la base y vuelve a pedir `POST /clientes/` con la misma cookie
- **THEN** la segunda petición responde 403, y `GET /auth/yo` con esa cookie muestra `roles_vigentes` sin `VENDEDOR` y `roles_token` con `VENDEDOR`

#### Scenario: Rol vencido después del login
- **WHEN** a un vendedor con sesión abierta se le pone `vence_en` en el pasado y pide `POST /clientes/`
- **THEN** la respuesta es 403

#### Scenario: La fila revocada se conserva
- **WHEN** se revoca un rol y la petición siguiente responde 403
- **THEN** la fila de `asignacion_rol` sigue en la tabla con `revocada_en` no nulo

#### Scenario: Rol otorgado después del login
- **WHEN** a un usuario que inició sesión sin roles se le asigna `ADMIN` en la base y pide `POST /editoriales/` con la misma cookie
- **THEN** la respuesta es 201

### Requirement: Los roles del token no dan permiso
Los roles que trae el token SHALL ser sólo informativos: una ruta que exige un rol MUST responder 403 si ese rol no está vigente en la base, aunque el token lo incluya.

#### Scenario: Token con ADMIN y base sin ADMIN
- **WHEN** la cookie lleva un token válido con `roles` `["ADMIN"]` de un usuario que en la base no tiene ninguna asignación vigente, y pide `POST /editoriales/`
- **THEN** la respuesta es 403

### Requirement: 401 antes que 403
Una ruta que exige un rol MUST responder 401 (y no 403) cuando no hay una sesión válida: sin cookie, token inválido o vencido, usuario inexistente o inactivo. El 403 por rol sólo se evalúa con un usuario identificado.

#### Scenario: Sin sesión en una ruta con rol (C-06)
- **WHEN** se pide `POST /libros/` sin cookie
- **THEN** la respuesta es 401 con el mismo cuerpo que el resto de los 401 de sesión

#### Scenario: Usuario inactivo con rol vigente
- **WHEN** un usuario con `ADMIN` vigente pero `activo` falso pide `POST /editoriales/` con una cookie válida
- **THEN** la respuesta es 401

### Requirement: Respuesta 403 sin detalles internos
Todo 403 por falta de rol SHALL responder `{"detail": "No tenés permiso para esta operación."}`. MUST NOT revelar qué roles exige la ruta, qué roles tiene el usuario, el token ni texto interno.

#### Scenario: Cuerpo del 403
- **WHEN** un vendedor pide `POST /libros/`
- **THEN** el cuerpo es exactamente `{"detail": "No tenés permiso para esta operación."}` y no contiene `ADMIN` ni `VENDEDOR`

### Requirement: Una sola conexión por petición autorizada
La identificación del usuario, la consulta de sus roles vigentes y la operación de la ruta MUST usar la misma sesión de base de datos de la petición: una petición autorizada no abre una segunda sesión ni toma una segunda conexión del pool.

#### Scenario: Una sesión por petición
- **WHEN** un administrador pide `POST /editoriales/` y se cuentan las sesiones que entrega la dependencia de sesión durante esa petición
- **THEN** se entregó exactamente una
