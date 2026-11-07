# alta-de-personal Specification

## Purpose
Permite que un administrador dé de alta a un usuario del personal con una contraseña provisoria que el nuevo usuario debe cambiar antes de usar las rutas protegidas, dejando constancia en el historial de seguridad.

## Requirements

### Requirement: Alta de personal con contraseña provisoria
`POST /usuarios/` SHALL crear un usuario activo con el correo, el nombre y la contraseña provisoria recibidos, y con el cambio de contraseña obligatorio pendiente. MUST responder 201 con el usuario creado (`id`, `email`, `nombre`, `activo`, `debe_cambiar_password`) y MUST NOT incluir `password_hash` ni la contraseña en la respuesta.

#### Scenario: Alta correcta
- **WHEN** un ADMIN pide `POST /usuarios/` con `{"email": "caja@example.com", "nombre": "Caja", "password": "provisoria-1"}`
- **THEN** la respuesta es 201 con `activo` verdadero y `debe_cambiar_password` verdadero, y el cuerpo no contiene `password_hash` ni `provisoria-1`

#### Scenario: La contraseña provisoria sirve para iniciar sesión
- **WHEN** el usuario recién creado inicia sesión con la contraseña provisoria
- **THEN** el login responde 200 con `debe_cambiar_password` verdadero y una ruta protegida le responde 403 hasta que cambie la contraseña

#### Scenario: La contraseña se guarda hasheada
- **WHEN** se lee la fila del usuario creado
- **THEN** `password_hash` no es la contraseña provisoria y la verifica con bcrypt

### Requirement: El alta no asigna roles
El alta de personal MUST NOT crear ninguna asignación de rol: los roles del nuevo usuario se otorgan después con la asignación de roles, de modo que cada rol queda con su vencimiento, quién lo otorgó y su propia línea de historial.

#### Scenario: Usuario nuevo sin roles
- **WHEN** un ADMIN da de alta un usuario y pide `GET /usuarios/{id}/roles` de ese usuario
- **THEN** la respuesta es 200 con una lista vacía

#### Scenario: Usuario nuevo sin rol en lo protegido
- **WHEN** el usuario recién creado ya cambió la contraseña provisoria y todavía no tiene ningún rol, y pide una ruta protegida (por ejemplo `POST /clientes/` o `GET /eventos/`)
- **THEN** la respuesta es 403 y no se escribe nada

### Requirement: Correo de usuario repetido
Si ya existe un usuario con ese correo, el alta MUST responder 409 con `{"detail": "Ya existe un usuario con ese correo."}` y no dejar ninguna fila nueva, ni en `usuario` ni en `evento_seguridad`. La decisión MUST tomarla la restricción única de la base, sin una consulta previa.

#### Scenario: Correo de un usuario existente
- **WHEN** un ADMIN pide `POST /usuarios/` con el correo de `vendedor@example.com`
- **THEN** la respuesta es 409 con el mensaje propio y las cantidades de filas de `usuario` y `evento_seguridad` no cambian

#### Scenario: Correo de un cliente sin cuenta
- **WHEN** un ADMIN da de alta un usuario con el correo de un cliente que no tiene usuario vinculado
- **THEN** la respuesta es 201 y la ficha de ese cliente no queda vinculada al usuario nuevo

### Requirement: Contrato de alta estricto
El alta MUST responder 422 sin escribir nada si el cuerpo trae campos no declarados (por ejemplo `rol`, `activo` o `debe_cambiar_password`), si el correo no es válido, si el nombre está vacío o si la contraseña supera los 72 bytes UTF-8.

#### Scenario: Campo no declarado
- **WHEN** un ADMIN pide `POST /usuarios/` con un campo `debe_cambiar_password: false`
- **THEN** la respuesta es 422 y no se crea ningún usuario

#### Scenario: Contraseña de más de 72 bytes
- **WHEN** la contraseña provisoria tiene 73 bytes UTF-8
- **THEN** la respuesta es 422 y no se crea ningún usuario

### Requirement: Hash fuera de la transacción
El hash bcrypt de la contraseña provisoria MUST calcularse fuera del bucle de eventos y bajo el límite de concurrencia de bcrypt, y MUST terminar antes de que se abra la transacción del alta: ninguna conexión de la base queda tomada mientras se calcula.

#### Scenario: Hash antes de abrir la transacción
- **WHEN** se registra el orden de los pasos del alta
- **THEN** el cálculo del hash termina antes de que se abra la unidad de trabajo, y durante el cálculo no hay ninguna unidad de trabajo abierta sobre la sesión

#### Scenario: Contrato inválido sin hash
- **WHEN** el cuerpo del alta no cumple el contrato
- **THEN** la respuesta es 422 y bcrypt no se llama

### Requirement: Evento del alta en la misma transacción
Cada alta de personal SHALL dejar una línea en `evento_seguridad` con el correo del ADMIN que la hizo como `actor` y una `accion` que nombra el alta y el id del usuario creado, en la misma transacción que el usuario: quedan las dos filas o ninguna (RN-16).

#### Scenario: Línea del alta
- **WHEN** `admin@example.com` da de alta al usuario con id 6
- **THEN** existe una línea nueva con `actor` `admin@example.com` y `accion` «Alta de personal: usuario 6»

#### Scenario: Falla al escribir el evento
- **WHEN** la escritura del evento falla después de insertar el usuario
- **THEN** no queda ni el usuario ni el evento

### Requirement: Sólo un ADMIN da de alta personal
`POST /usuarios/` SHALL exigir `ADMIN` vigente: sin sesión responde 401, con otro rol o con el cambio de contraseña pendiente responde 403, y en ningún caso crea el usuario.

#### Scenario: Vendedor intenta dar de alta
- **WHEN** un usuario con sólo `VENDEDOR` vigente pide `POST /usuarios/` con un cuerpo válido
- **THEN** la respuesta es 403 y no se crea ningún usuario
