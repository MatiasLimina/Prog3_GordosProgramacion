# Spec Delta

## ADDED Requirements

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
