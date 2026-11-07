# contratos-auth-usuarios Specification

## Purpose
Define los contratos de entrada y salida de autenticación, usuarios y asignaciones de rol: entradas que rechazan campos de más, contraseñas que no pasan el límite de 72 bytes de bcrypt, vencimientos de rol con zona horaria y en el futuro, y salidas que nunca exponen el hash de la contraseña.

## Requirements

### Requirement: Entradas de autenticación y usuarios estrictas
Los contratos de entrada de registro, login, cambio de contraseña, alta de usuario y asignación de rol MUST rechazar cualquier campo que no esté declarado.

#### Scenario: Campo adicional en una entrada
- **WHEN** una petición de autenticación o usuarios contiene un campo no declarado
- **THEN** la validación la rechaza antes de ejecutar el servicio

### Requirement: Contraseñas dentro del límite de bcrypt
Los campos de contraseña que llegan a bcrypt MUST aceptar como máximo 72 bytes UTF-8, sin confundir bytes con cantidad de caracteres.

#### Scenario: Contraseña de hasta 72 bytes
- **WHEN** un campo de contraseña contiene exactamente 72 bytes UTF-8 o menos
- **THEN** el contrato lo acepta

#### Scenario: Contraseña mayor a 72 bytes
- **WHEN** un campo de contraseña contiene más de 72 bytes UTF-8
- **THEN** el contrato lo rechaza antes de que llegue a bcrypt

### Requirement: Vencimiento de rol inequívoco
Una asignación de rol MUST permitir no especificar vencimiento. Si se especifica `vence_en`, MUST incluir zona horaria y ser posterior al momento de validación.

#### Scenario: Rol sin vencimiento
- **WHEN** `vence_en` se omite o es `null`
- **THEN** la asignación queda sin vencimiento

#### Scenario: Vencimiento con zona en el futuro
- **WHEN** `vence_en` tiene zona horaria y está en el futuro
- **THEN** el contrato lo acepta

#### Scenario: Vencimiento sin zona o vencido
- **WHEN** `vence_en` no tiene zona horaria o ya pasó
- **THEN** la validación rechaza la entrada

### Requirement: Salidas sin hash de contraseña
Los contratos de salida de autenticación y usuarios MUST NOT incluir `password_hash` ni devolver el token en el cuerpo de login.

#### Scenario: Respuesta de usuario
- **WHEN** se serializa una respuesta de usuario o de `/auth/yo`
- **THEN** el resultado no contiene `password_hash`

#### Scenario: Respuesta de login
- **WHEN** se serializa la respuesta de login
- **THEN** el cuerpo no contiene el token

### Requirement: Salida del historial de seguridad
El contrato de salida de una línea del historial de seguridad SHALL tener exactamente `id`, `cuando` (fecha con zona horaria), `actor` y `accion`, y MUST poder construirse desde la fila de `evento_seguridad`.

#### Scenario: Serialización de una línea
- **WHEN** se serializa una línea con `actor` `SISTEMA` y `accion` «Carga de los datos iniciales»
- **THEN** el resultado tiene sólo las claves `id`, `cuando`, `actor` y `accion`, y `cuando` incluye la zona horaria

### Requirement: Un solo tipo público de rol
Los contratos que llevan roles (entrada de asignación, salida de asignación y `/auth/yo`) y el parámetro `{rol}` de las rutas de administración SHALL usar un único tipo público de rol con exactamente `ADMIN`, `VENDEDOR` y `CLIENTE`. Un rol fuera de esa lista MUST dar 422 por la validación del tipo, sin código propio, y el comportamiento de los contratos existentes MUST NOT cambiar.

#### Scenario: Mismo tipo en los tres contratos
- **WHEN** se inspeccionan las anotaciones de `rol` en la entrada y la salida de asignación y de `roles_vigentes` y `roles_token` en la salida de `/auth/yo`
- **THEN** todas usan el mismo tipo público de rol

#### Scenario: Rol desconocido en el cuerpo
- **WHEN** se valida una asignación con `rol` `GERENTE`
- **THEN** la validación falla (422)
