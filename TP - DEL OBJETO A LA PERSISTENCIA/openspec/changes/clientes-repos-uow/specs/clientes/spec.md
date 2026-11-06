# Spec Delta

## ADDED Requirements

### Requirement: Alta de cliente
`POST /clientes` con `nombre` y `email` válidos SHALL crear el cliente sin usuario vinculado y responder 201 con `id`, `nombre` y `email`. Un correo ya usado por otro cliente MUST responder 409 con «Ya existe un cliente con ese correo.», decidido por la base y no por una consulta previa, sin dejar fila nueva.

#### Scenario: Alta válida
- **WHEN** el personal envía `POST /clientes` con `{"nombre": "Ana Pérez", "email": "ana@example.com"}`
- **THEN** la respuesta es 201 con `id`, `nombre` y `email`, y el cliente queda confirmado con `usuario_id` nulo

#### Scenario: Correo repetido
- **WHEN** ya existe un cliente con `ana@example.com` y se envía otro con el mismo correo
- **THEN** la respuesta es 409 con `{"detail": "Ya existe un cliente con ese correo."}` y la cantidad de clientes no cambia

#### Scenario: Mismo mensaje que el registro
- **WHEN** se compara el 409 de `POST /clientes` por correo repetido con el de `POST /auth/registro` por correo de cliente existente
- **THEN** los dos cuerpos son `{"detail": "Ya existe un cliente con ese correo."}`

### Requirement: Entradas de cliente sin campos no declarados
Las entradas de alta y edición de cliente y de alta de perfil MUST responder 422 sin escribir nada si traen un campo no declarado (por ejemplo `id` o `usuario_id`), un correo inválido o un texto obligatorio vacío.

#### Scenario: Vincular un usuario por la API
- **WHEN** se envía `POST /clientes` o `PATCH /clientes/{id}` con el campo `usuario_id`
- **THEN** la respuesta es 422 y ningún cliente cambia ni se crea

#### Scenario: Correo inválido
- **WHEN** se envía `POST /clientes` con `"email": "no-es-email"`
- **THEN** la respuesta es 422 y no se crea ningún cliente

### Requirement: Detalle de cliente con su perfil
`GET /clientes/{id}` SHALL responder 200 con `id`, `nombre`, `email` y `perfil` (`id`, `cliente_id`, `telefono`, `direccion`, o nulo si no tiene), leído con un número fijo de consultas. Un id sin cliente MUST responder 404 con «El cliente no existe.».

#### Scenario: Cliente con perfil
- **WHEN** se pide el detalle de un cliente que tiene perfil
- **THEN** la respuesta es 200 e incluye el perfil con `telefono` y `direccion`

#### Scenario: Cliente sin perfil
- **WHEN** se pide el detalle de un cliente sin perfil
- **THEN** la respuesta es 200 con `"perfil": null`

#### Scenario: Cliente inexistente
- **WHEN** se pide `GET /clientes/999` y no existe ese cliente
- **THEN** la respuesta es 404 con `{"detail": "El cliente no existe."}`

### Requirement: Listado paginado de clientes
`GET /clientes` SHALL responder el envoltorio `{items, total, page, size, pages}` con `page` y `size`, ordenado por `id`, con `total` igual a la cantidad de clientes. Los parámetros `limit` y `offset` MUST NOT paginar.

#### Scenario: Segunda página
- **WHEN** hay 5 clientes y se pide `GET /clientes?size=2&page=2`
- **THEN** la respuesta es 200 con los clientes 3 y 4 en `items`, `total` 5 y `pages` 3

#### Scenario: Página fuera de rango
- **WHEN** hay 5 clientes y se pide `GET /clientes?size=2&page=4`
- **THEN** la respuesta es 422 con `{"detail": "La página 4 no existe: hay 3"}`

#### Scenario: Sin clientes
- **WHEN** no hay clientes y se pide `GET /clientes`
- **THEN** la respuesta es 200 con `items` vacío, `total` 0 y `pages` 1

### Requirement: Edición parcial de cliente
`PATCH /clientes/{id}` SHALL aplicar sólo los campos enviados (`nombre`, `email`) y responder 200 con el detalle del cliente y su perfil. Un cliente inexistente MUST responder 404; un correo de otro cliente MUST responder 409 con «Ya existe un cliente con ese correo.» sin cambiar nada. El correo de un cliente con cuenta tiene su propio requisito.

#### Scenario: Sólo cambia lo enviado
- **WHEN** se envía `PATCH /clientes/{id}` con sólo `nombre`
- **THEN** la respuesta es 200 con el nombre nuevo, el mismo `email` y el perfil que tenía

#### Scenario: Cuerpo vacío
- **WHEN** se envía `PATCH /clientes/{id}` con `{}`
- **THEN** la respuesta es 200 y el cliente no cambia

#### Scenario: Correo de otro cliente
- **WHEN** se edita el correo de un cliente con el de otro cliente existente
- **THEN** la respuesta es 409 con `{"detail": "Ya existe un cliente con ese correo."}` y los dos clientes siguen como estaban

#### Scenario: Cliente inexistente en la edición
- **WHEN** se envía `PATCH /clientes/999` con un cuerpo válido
- **THEN** la respuesta es 404 con `{"detail": "El cliente no existe."}`

### Requirement: Correo de un cliente con cuenta
`PATCH /clientes/{id}` que cambia el correo de un cliente con usuario vinculado (`usuario_id` no nulo) MUST responder 409 con «El correo de un cliente con cuenta no se puede cambiar.» sin cambiar nada del cliente ni del usuario. El cambio se decide comparando el correo enviado con el guardado: reenviar el mismo correo o editar sólo el `nombre` SHALL aceptarse, y un cliente sin usuario vinculado SHALL poder cambiar su correo.

#### Scenario: Cambiar el correo de un cliente con cuenta
- **WHEN** el cliente se registró por `POST /auth/registro` con `ana@example.com` y se envía `PATCH /clientes/{id}` con `{"nombre": "Ana P.", "email": "otra@example.com"}`
- **THEN** la respuesta es 409 con `{"detail": "El correo de un cliente con cuenta no se puede cambiar."}`, el cliente conserva su nombre y su correo, y el usuario sigue con `ana@example.com`

#### Scenario: Mismo correo de un cliente con cuenta
- **WHEN** se envía `PATCH /clientes/{id}` de un cliente con cuenta con `{"email": "ana@example.com"}`, el correo que ya tiene
- **THEN** la respuesta es 200 y el cliente no cambia

#### Scenario: Sólo el nombre de un cliente con cuenta
- **WHEN** se envía `PATCH /clientes/{id}` de un cliente con cuenta con sólo `nombre`
- **THEN** la respuesta es 200 con el nombre nuevo y el mismo correo

#### Scenario: Cliente sin cuenta cambia su correo
- **WHEN** se envía `PATCH /clientes/{id}` de un cliente sin usuario vinculado con un correo libre
- **THEN** la respuesta es 200 con el correo nuevo

### Requirement: Alta del perfil de un cliente
`POST /clientes/{id}/perfil` con `telefono` y `direccion` SHALL crear el único perfil del cliente y responder 201 con `id`, `cliente_id`, `telefono` y `direccion`. Un cliente inexistente MUST responder 404 «El cliente no existe.»; un segundo perfil, 409 «El cliente ya tiene un perfil.»; los dos los decide la base al escribir.

#### Scenario: Primer perfil
- **WHEN** se envía el perfil de un cliente que no tiene
- **THEN** la respuesta es 201 y el detalle del cliente muestra ese perfil

#### Scenario: Segundo perfil
- **WHEN** se envía otro perfil para un cliente que ya tiene uno
- **THEN** la respuesta es 409 con `{"detail": "El cliente ya tiene un perfil."}` y el perfil original no cambia

#### Scenario: Perfil de un cliente inexistente
- **WHEN** se envía `POST /clientes/999/perfil` con un cuerpo válido
- **THEN** la respuesta es 404 con `{"detail": "El cliente no existe."}` y no queda ningún perfil nuevo

### Requirement: Ventas de un cliente
`GET /clientes/{id}/ventas` SHALL responder el envoltorio con sólo las ventas de ese cliente, ordenadas por `id`, cada una con su cliente, fecha, total y renglones (con el título del libro aunque esté dado de baja). Un cliente inexistente MUST responder 404 «El cliente no existe.» antes de validar la página.

#### Scenario: Sólo las suyas
- **WHEN** el cliente 1 tiene las ventas 1, 2 y 4 y el cliente 2 la venta 3, y se pide `GET /clientes/1/ventas`
- **THEN** `items` trae las ventas 1, 2 y 4 en ese orden, todas con `cliente.id` 1, y `total` es 3

#### Scenario: Paginadas
- **WHEN** el cliente 1 tiene tres ventas y se pide `GET /clientes/1/ventas?size=2&page=2`
- **THEN** `items` trae sólo la tercera, con `total` 3 y `pages` 2

#### Scenario: Cliente sin ventas
- **WHEN** se piden las ventas de un cliente que no compró nada
- **THEN** la respuesta es 200 con `items` vacío, `total` 0 y `pages` 1

#### Scenario: Cliente inexistente en sus ventas
- **WHEN** se pide `GET /clientes/999/ventas?page=5`
- **THEN** la respuesta es 404 con `{"detail": "El cliente no existe."}`, no 422

#### Scenario: Libro dado de baja en una venta vieja
- **WHEN** un libro vendido al cliente se da de baja y después se piden las ventas del cliente
- **THEN** el renglón de esa venta sigue mostrando el título del libro

### Requirement: Ventas de un cliente sin N+1
La lectura de las ventas de un cliente SHALL emitir la misma cantidad de consultas sin importar cuántas ventas tenga la página ni cuántos renglones tenga cada venta.

#### Scenario: Más ventas y renglones, mismas consultas
- **WHEN** se cuentan las consultas de `GET /clientes/{id}/ventas` para un cliente con una venta de un renglón y para otro con tres ventas de dos renglones
- **THEN** las dos cantidades son iguales
