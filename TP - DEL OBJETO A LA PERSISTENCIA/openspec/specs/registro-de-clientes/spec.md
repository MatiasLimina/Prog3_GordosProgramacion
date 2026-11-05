# registro-de-clientes Specification

## Purpose
Permite que una persona se registre por su cuenta como cliente: en una sola operación atómica se crean su usuario, su rol `CLIENTE` y su ficha de cliente (RN-02), sin apropiarse nunca de una ficha que ya existía.

## Requirements

### Requirement: Registro atómico
`POST /auth/registro` con `{email, nombre, password}` válidos SHALL crear, en una sola transacción, un usuario activo sin cambio de contraseña pendiente, una asignación `CLIENTE` vigente sin vencimiento ni otorgante, y una ficha de `cliente` con el mismo nombre y correo vinculada a ese usuario. MUST responder 201 con el usuario creado sin `password_hash`.

#### Scenario: Registro exitoso (C-02)
- **WHEN** se registra `lucia@example.com` con nombre «Lucía» y una contraseña válida
- **THEN** la respuesta es 201 con `id`, `email`, `nombre`, `activo` verdadero y `debe_cambiar_password` falso, sin `password_hash`, y en la base hay un usuario, una asignación `CLIENTE` vigente y un cliente con ese correo cuyo `usuario_id` es el del usuario

#### Scenario: El registrado puede iniciar sesión
- **WHEN** después de registrarse, la persona inicia sesión con el mismo correo y contraseña
- **THEN** el login responde 200 y el token lleva `roles` `["CLIENTE"]`

### Requirement: Contraseña guardada como hash
El registro SHALL guardar sólo el hash bcrypt de la contraseña, calculado con el costo de la configuración antes de abrir la transacción de escritura. La contraseña en claro MUST NOT guardarse ni aparecer en la respuesta.

#### Scenario: Hash fuera de la transacción
- **WHEN** se registra un usuario
- **THEN** el hash se calcula cuando todavía no hay un bloque de escritura abierto, y el `password_hash` guardado verifica contra la contraseña enviada y es distinto de ella

### Requirement: Correo de usuario repetido
Si ya existe un usuario con ese correo, el registro SHALL responder 409 con `{"detail": "Ya existe un usuario con ese correo."}` y MUST NOT dejar ninguna fila nueva en `usuario`, `asignacion_rol` ni `cliente`.

#### Scenario: Usuario repetido (C-02)
- **WHEN** se registra dos veces el mismo correo
- **THEN** el segundo registro responde 409 con ese mensaje y la cantidad de filas de `usuario`, `asignacion_rol` y `cliente` no cambia

### Requirement: Correo de cliente existente
Si ya existe una ficha de cliente con ese correo (con o sin usuario), el registro SHALL responder 409 con `{"detail": "Ya existe un cliente con ese correo."}`, MUST NOT dejar ninguna fila nueva y MUST NOT vincular ni modificar la ficha existente.

#### Scenario: Cliente previo sin usuario (C-02)
- **WHEN** existe el cliente «Tomás Ríos» con `tomas@example.com` y sin usuario, y alguien se registra con `tomas@example.com`
- **THEN** la respuesta es 409 con ese mensaje, no queda ningún usuario ni asignación nuevos y el cliente existente sigue con `usuario_id` nulo y sus datos sin cambios

### Requirement: Entradas inválidas del registro
El registro MUST responder 422 sin escribir nada si el cuerpo trae campos de más (por ejemplo `rol`), un correo inválido, un nombre vacío o una contraseña de más de 72 bytes.

#### Scenario: Registrarse con un rol
- **WHEN** se envía un registro con el campo adicional `"rol": "ADMIN"`
- **THEN** la respuesta es 422 y no se crea ninguna fila

#### Scenario: Contraseña de más de 72 bytes
- **WHEN** se envía un registro con una contraseña de 37 «ñ» (74 bytes)
- **THEN** la respuesta es 422 y no se crea ninguna fila
