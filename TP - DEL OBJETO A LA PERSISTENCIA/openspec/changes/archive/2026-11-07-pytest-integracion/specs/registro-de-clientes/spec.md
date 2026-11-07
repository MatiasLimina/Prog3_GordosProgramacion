# Spec Delta

## MODIFIED Requirements

### Requirement: Registro atómico
`POST /auth/registro` con `{email, nombre, password}` válidos SHALL crear, en una sola transacción, un usuario activo sin cambio de contraseña pendiente, una asignación `CLIENTE` vigente sin vencimiento ni otorgante, y una ficha de `cliente` con el mismo nombre y correo vinculada a ese usuario. MUST responder 201 con el usuario creado sin `password_hash`. Si el registro falla en cualquier punto, haya o no escrito ya alguna de las tres filas y venga o no la falla de la base, MUST NOT quedar ninguna de ellas.

#### Scenario: Registro exitoso (C-02)
- **WHEN** se registra `lucia@example.com` con nombre «Lucía» y una contraseña válida
- **THEN** la respuesta es 201 con `id`, `email`, `nombre`, `activo` verdadero y `debe_cambiar_password` falso, sin `password_hash`, y en la base hay un usuario, una asignación `CLIENTE` vigente y un cliente con ese correo cuyo `usuario_id` es el del usuario

#### Scenario: El registrado puede iniciar sesión
- **WHEN** después de registrarse, la persona inicia sesión con el mismo correo y contraseña
- **THEN** el login responde 200 y el token lleva `roles` `["CLIENTE"]`

#### Scenario: Falla a mitad del registro
- **WHEN** el registro falla por un error que no viene de la base después de haber escrito el usuario, después de haber escrito el usuario y la asignación, o después de las tres escrituras y antes de confirmar
- **THEN** no queda ninguna fila nueva en `usuario`, `asignacion_rol` ni `cliente`

#### Scenario: El correo queda libre tras una falla
- **WHEN** un registro falla a mitad del bloque y después se registra el mismo correo sin fallas
- **THEN** el segundo registro responde 201 y en la base hay exactamente un usuario, una asignación y un cliente con ese correo

### Requirement: Correo de cliente existente
Si ya existe una ficha de cliente con ese correo (con o sin usuario), el registro SHALL responder 409 con `{"detail": "Ya existe un cliente con ese correo."}`, MUST NOT dejar ninguna fila nueva y MUST NOT vincular ni modificar la ficha existente.

#### Scenario: Cliente previo sin usuario (C-02)
- **WHEN** existe el cliente «Tomás Ríos» con `tomas@example.com` y sin usuario, y alguien se registra con `tomas@example.com`
- **THEN** la respuesta es 409 con ese mensaje, no queda ningún usuario ni asignación nuevos y el cliente existente sigue con `usuario_id` nulo y sus datos sin cambios

#### Scenario: Cliente previo con usuario
- **WHEN** existe un cliente con `vero@example.com` vinculado a otro usuario, y alguien se registra con `vero@example.com`
- **THEN** la respuesta es 409 con ese mensaje, no queda ningún usuario ni asignación nuevos y el cliente existente sigue vinculado a su usuario original con sus datos sin cambios
