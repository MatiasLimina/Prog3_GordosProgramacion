# autenticacion Specification

## Purpose
Define cómo un usuario inicia y cierra sesión con una cookie que lleva un token firmado, cómo la aplicación lo identifica en cada petición a partir de esa cookie, y qué devuelve la consulta de la sesión propia (`/auth/yo`).

## Requirements

### Requirement: Orden del inicio de sesión
`POST /auth/login` SHALL aplicar primero el límite de intentos (capacidad `limite-de-intentos`) y sólo si no se superó SHALL verificar la contraseña. Ningún hash MUST calcularse ni verificarse en un intento rechazado por el límite.

#### Scenario: Límite antes que verificación
- **WHEN** el correo y la IP ya acumulan 5 fallos en los últimos 60 s y llega un sexto intento con la contraseña correcta
- **THEN** la respuesta es 429 y no se verificó ninguna contraseña

#### Scenario: Sin límite superado se verifica
- **WHEN** llega un login para un correo e IP sin fallos recientes
- **THEN** se verifica la contraseña una sola vez y el resultado decide la respuesta

### Requirement: Credenciales correctas
Un login con correo existente, usuario activo y contraseña correcta SHALL responder 200 con `{"mensaje": "Sesión iniciada", "debe_cambiar_password": <valor del usuario>, "expira_en_segundos": <JWT_EXPIRE_MINUTES × 60>}`. El cuerpo MUST NOT contener el token.

#### Scenario: Login correcto
- **WHEN** `ana@example.com` inicia sesión con su contraseña y la duración del token es 30 minutos
- **THEN** la respuesta es 200 con `mensaje` «Sesión iniciada», `debe_cambiar_password` falso y `expira_en_segundos` 1800, y el texto del cuerpo no incluye el token

#### Scenario: Usuario con cambio de contraseña pendiente
- **WHEN** inicia sesión un usuario con `debe_cambiar_password` verdadero y la contraseña correcta
- **THEN** la respuesta es 200 con `debe_cambiar_password` verdadero y la cookie de sesión

### Requirement: Credenciales incorrectas indistinguibles
Un login con correo inexistente, contraseña incorrecta o usuario inactivo SHALL responder 401 con exactamente el mismo cuerpo (`{"detail": "Correo o contraseña incorrectos."}`) y sin cookie. Cuando el correo no existe, la contraseña MUST verificarse contra el hash ficticio del arranque, de modo que los tres casos hagan una verificación bcrypt (RN-08).

#### Scenario: Contraseña incorrecta y correo inexistente
- **WHEN** se intenta un login con un correo existente y una contraseña incorrecta, y otro con un correo que no existe
- **THEN** ambos responden 401 con cuerpos idénticos y ninguno trae `Set-Cookie`

#### Scenario: Correo inexistente usa el hash ficticio
- **WHEN** se intenta un login con un correo que no existe
- **THEN** se hace exactamente una verificación de contraseña y es contra el hash ficticio del arranque

#### Scenario: Usuario inactivo
- **WHEN** un usuario con `activo` falso inicia sesión con su contraseña correcta
- **THEN** la respuesta es 401 con el mismo cuerpo que una contraseña incorrecta

### Requirement: Cookie de sesión
Un login correcto SHALL entregar el token sólo en la cookie `access_token` con `HttpOnly`, `SameSite=Lax`, `Path=/`, `Max-Age` igual a la duración del token en segundos y `Secure` si y sólo si `COOKIE_SECURE` es verdadero.

#### Scenario: Atributos de la cookie
- **WHEN** un login correcto responde con `COOKIE_SECURE` falso y una duración de 60 minutos
- **THEN** `Set-Cookie` trae `access_token` con `HttpOnly`, `SameSite=Lax`, `Path=/` y `Max-Age=3600`, y sin `Secure`

#### Scenario: Cookie segura por configuración
- **WHEN** un login correcto responde con `COOKIE_SECURE` verdadero
- **THEN** la cookie `access_token` trae además el atributo `Secure`

### Requirement: Contenido del token emitido
El token del login SHALL identificar al usuario (`sub`) y llevar como `roles` los roles vigentes del usuario en la base al momento de emitirlo. Vigente MUST significar no revocada y sin vencer (sin `vence_en` o con `vence_en` posterior al momento de la consulta).

#### Scenario: Sólo roles vigentes
- **WHEN** inicia sesión un usuario con `VENDEDOR` vigente, `ADMIN` revocado y `CLIENTE` vencido
- **THEN** el token de su cookie lleva `sub` igual a su id y `roles` igual a `["VENDEDOR"]`

#### Scenario: Usuario sin roles vigentes
- **WHEN** inicia sesión un usuario sin ninguna asignación vigente
- **THEN** el login responde 200 y el token lleva `roles` vacío

### Requirement: Usuario actual desde la cookie
Toda ruta que pide estar autenticado SHALL identificar al usuario sólo con la cookie `access_token`, y MUST responder 401 con un mismo mensaje fijo si no hay cookie, si el token es inválido o venció, o si el usuario no existe o está inactivo. La cabecera `Authorization` MUST ignorarse.

#### Scenario: Sin cookie
- **WHEN** se pide `GET /auth/yo` sin cookie
- **THEN** la respuesta es 401

#### Scenario: Token en Authorization y no en cookie
- **WHEN** se pide `GET /auth/yo` sin cookie y con `Authorization: Bearer <token válido>`
- **THEN** la respuesta es 401

#### Scenario: Token vencido o alterado
- **WHEN** la cookie lleva un token vencido, o uno con la firma alterada
- **THEN** la respuesta es 401 y el cuerpo no menciona la clave ni el token

#### Scenario: Usuario inexistente o inactivo
- **WHEN** la cookie lleva un token válido de un usuario que no existe, o de uno con `activo` falso
- **THEN** la respuesta es 401

### Requirement: Consulta de la sesión propia
`GET /auth/yo` SHALL responder 200, para cualquier usuario autenticado y aunque tenga el cambio de contraseña pendiente, con `{usuario, roles_vigentes, roles_token}`: `usuario` sin `password_hash`, `roles_vigentes` leídos de la base en esa petición y `roles_token` tal como los trae el token.

#### Scenario: Roles iguales
- **WHEN** un vendedor recién logueado pide `GET /auth/yo`
- **THEN** la respuesta es 200 con su `usuario` (sin `password_hash`), `roles_vigentes` `["VENDEDOR"]` y `roles_token` `["VENDEDOR"]`

#### Scenario: Rol revocado después del login
- **WHEN** a un vendedor con sesión abierta se le revoca `VENDEDOR` en la base y pide `GET /auth/yo` con la misma cookie
- **THEN** la respuesta es 200 con `roles_vigentes` vacío y `roles_token` `["VENDEDOR"]`

#### Scenario: Cambio de contraseña pendiente
- **WHEN** un usuario con `debe_cambiar_password` verdadero pide `GET /auth/yo` con su cookie
- **THEN** la respuesta es 200 y `usuario.debe_cambiar_password` es verdadero

### Requirement: Cierre de sesión
`POST /auth/logout` SHALL responder 200 con `{"mensaje": "Sesión cerrada"}` y una cabecera `Set-Cookie` que borra `access_token` (mismo nombre y `Path=/`, `Max-Age=0`). MUST NOT requerir sesión.

#### Scenario: Logout con sesión
- **WHEN** un usuario logueado pide `POST /auth/logout` y después `GET /auth/yo` con el mismo cliente
- **THEN** el logout responde 200 borrando la cookie y `/auth/yo` responde 401

#### Scenario: Logout sin sesión
- **WHEN** se pide `POST /auth/logout` sin cookie
- **THEN** la respuesta es 200 con la cabecera que borra la cookie

### Requirement: Entradas inválidas del login
El login MUST responder 422, sin verificar ninguna contraseña ni anotar ningún intento, si el cuerpo no cumple el contrato: campos de más, correo inválido o contraseña de más de 72 bytes.

#### Scenario: Contraseña de más de 72 bytes
- **WHEN** se intenta un login con una contraseña de 37 «ñ» (74 bytes)
- **THEN** la respuesta es 422 y no se agrega ninguna fila a `intento_acceso`
