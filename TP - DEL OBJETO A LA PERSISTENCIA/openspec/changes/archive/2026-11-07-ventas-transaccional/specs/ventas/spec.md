# Spec Delta

## Purpose

Define el registro transaccional de una venta (renglones, precio copiado, total, descuento de stock y un movimiento por renglón, todo o nada), sus conflictos, el aviso del comprobante en segundo plano y las lecturas de ventas: el detalle con control de dueño, el listado del personal y `/mis-ventas`, siempre con una cantidad fija de consultas.

## ADDED Requirements

### Requirement: Registro de una venta válida
`POST /ventas/` con `cliente_id` y al menos un renglón SHALL crear la venta y responder 201 con `id`, `fecha` (con zona), `total`, el cliente (`id`, `nombre`, `email`) y los renglones en el orden de entrada, cada uno con `libro_id`, `titulo`, `cantidad`, `precio_unitario` copiado del precio vigente del libro y `subtotal`. El total MUST ser la suma de los subtotales, calculada por el servidor.

#### Scenario: Venta con dos renglones (C-10)
- **WHEN** el personal registra una venta de 2 ejemplares de un libro de 25000.00 y 1 de otro de 27000.00
- **THEN** la respuesta es 201 con los renglones en ese orden, `precio_unitario` "25000.00" y "27000.00", subtotales "50000.00" y "27000.00" y `total` "77000.00"

#### Scenario: Decimales exactos
- **WHEN** se venden 3 ejemplares de un libro de 100.50 y 1 de uno de 25000.00
- **THEN** los subtotales son "301.50" y "25000.00" y el total "25301.50"

#### Scenario: El precio queda copiado
- **WHEN** después de la venta se cambia el precio del libro y se pide el detalle de la venta
- **THEN** el renglón conserva el precio de la venta y el total no cambia; una venta nueva toma el precio nuevo

### Requirement: Cada renglón descuenta stock y deja su movimiento
Registrar una venta SHALL descontar del stock de cada libro la cantidad del renglón y dejar, por renglón, un movimiento de stock con la cantidad negativa, el motivo «Venta», el usuario que registró la venta y el id de la venta. Después de cada venta, el stock de cada libro MUST seguir siendo igual a la suma de sus movimientos.

#### Scenario: Stock y movimientos tras la venta (C-10)
- **WHEN** se venden 2 ejemplares de un libro con stock 10 y 1 de otro con stock 6
- **THEN** los stocks quedan en 8 y 5, hay dos movimientos nuevos con cantidades -2 y -1, motivo «Venta», el `venta_id` de la venta y el usuario de la sesión, y en cada libro el stock es igual a la suma de sus movimientos

#### Scenario: Agotar el stock exacto
- **WHEN** se vende exactamente el stock disponible de un libro
- **THEN** la respuesta es 201 y el stock del libro queda en 0

### Requirement: Venta atómica
La venta, sus renglones, los descuentos de stock y los movimientos SHALL confirmarse juntos o no confirmarse. Si cualquier renglón o el cliente hace fallar la venta, MUST NOT quedar ninguna de esas escrituras, incluidos los descuentos ya hechos de los renglones anteriores.

#### Scenario: Un libro no alcanza (C-11)
- **WHEN** se registra una venta con 1 Rayuela (alcanza) y 2 Bestiario (hay 1)
- **THEN** la respuesta es 409, no hay venta ni renglones nuevos, el stock de Rayuela sigue igual, no hay movimientos nuevos y en los cinco libros el stock coincide con la suma de movimientos

#### Scenario: Falla el último renglón
- **WHEN** el primer renglón es válido y el segundo pide un libro inexistente
- **THEN** la respuesta es 409 y ningún stock ni movimiento cambió

#### Scenario: El servicio sigue usable
- **WHEN** después de una venta rechazada con 409 se registra una venta válida
- **THEN** la venta válida responde 201

### Requirement: Conflictos de la venta
La venta SHALL responder 409 con un mensaje propio, sin texto interno de la base, cuando el cliente no existe («El cliente indicado no existe.»), un libro no existe («El libro indicado no existe.»), un libro está dado de baja («El libro {id} está dado de baja.») o un libro no tiene stock suficiente («Stock insuficiente para el libro {id}: hay {n}, se pidieron {m}.»). La existencia MUST decidirla la escritura, sin consultas previas.

#### Scenario: Cliente inexistente (C-12)
- **WHEN** se registra una venta con un `cliente_id` que no existe
- **THEN** la respuesta es 409 con `{"detail": "El cliente indicado no existe."}` y ningún stock cambia

#### Scenario: Libro inexistente (C-12)
- **WHEN** se registra una venta con un `libro_id` que no existe
- **THEN** la respuesta es 409 (no 404) con `{"detail": "El libro indicado no existe."}` y no queda ninguna escritura

#### Scenario: Libro dado de baja (C-12)
- **WHEN** se registra una venta con un libro dado de baja que todavía tiene stock
- **THEN** la respuesta es 409 con `{"detail": "El libro {id} está dado de baja."}` y su stock no cambia

#### Scenario: Stock insuficiente
- **WHEN** se piden 7 ejemplares de un libro con stock 6
- **THEN** la respuesta es 409 con `{"detail": "Stock insuficiente para el libro {id}: hay 6, se pidieron 7."}`

### Requirement: Total fuera de rango
Si el total calculado de la venta no entra en la columna `total` (`Numeric(12,2)`), la venta SHALL responder 409 con «El total de la venta supera el máximo permitido.», sin escrituras y MUST NOT responder 500 ni texto interno de la base.

#### Scenario: Total enorme
- **WHEN** se vende 1.000.000.000 de ejemplares de un libro de 25000.00 que tiene ese stock
- **THEN** la respuesta es 409 con ese mensaje y el stock del libro no cambia

### Requirement: Aviso del comprobante en segundo plano
Al confirmarse una venta, la aplicación SHALL agendar en segundo plano el aviso del comprobante al cliente: una espera asincrónica de 0,5 s y un mensaje con el id de la venta y el correo del cliente en el registro de uvicorn, visible con su arranque normal, después de enviar la respuesta. Una venta rechazada MUST NOT agendar el aviso.

#### Scenario: Aviso tras la venta (C-10)
- **WHEN** se registra una venta válida del cliente `tomas@example.com`
- **THEN** después de la respuesta 201 hay exactamente un mensaje en el registro de uvicorn que nombra la venta y ese correo

#### Scenario: Sin aviso si falla
- **WHEN** la venta se rechaza con 409
- **THEN** no se espera ni se registra ningún aviso

### Requirement: Las ventas no se modifican
Una venta registrada MUST NOT poder modificarse ni borrarse por la API: no existen `PATCH`, `PUT` ni `DELETE` sobre `/ventas/{id}`, y los renglones sólo viajan dentro del alta.

#### Scenario: Modificar o borrar una venta
- **WHEN** se envía `PATCH`, `PUT` o `DELETE` a `/ventas/1`
- **THEN** la respuesta es 405

### Requirement: Detalle de una venta para el personal o el dueño
`GET /ventas/{id}` SHALL devolver la venta con la misma forma que el alta cuando quien la pide tiene un rol de personal vigente (VENDEDOR o ADMIN, leído en la base) o es el usuario vinculado al cliente de la venta. A cualquier otro usuario autenticado MUST responderle 403 con el mensaje fijo de falta de permiso, sin nombrar roles.

#### Scenario: La cliente ve su venta (C-06)
- **WHEN** la usuaria `ana@example.com`, vinculada a la clienta Ana, pide el detalle de una venta de Ana
- **THEN** la respuesta es 200 con la venta

#### Scenario: La cliente no ve la ajena (C-06)
- **WHEN** esa misma usuaria pide el detalle de una venta de Lucía
- **THEN** la respuesta es 403 con `{"detail": "No tenés permiso para esta operación."}`

#### Scenario: El personal ve cualquier venta
- **WHEN** un usuario con VENDEDOR vigente pide el detalle de una venta de cualquier cliente
- **THEN** la respuesta es 200 y es igual a la respuesta del alta de esa venta

#### Scenario: Personal con el rol revocado
- **WHEN** un usuario cuyo único rol VENDEDOR fue revocado pide el detalle de una venta ajena con la misma cookie
- **THEN** la respuesta es 403

### Requirement: Detalle de una venta inexistente
Para el personal, `GET /ventas/{id}` con un id que no corresponde a ninguna venta SHALL responder 404 con «La venta no existe.». Para un usuario que no es personal MUST responder 403, exista o no la venta, de modo que la respuesta no revele qué ventas existen.

#### Scenario: Personal y venta inexistente
- **WHEN** un ADMIN pide `GET /ventas/999` y esa venta no existe
- **THEN** la respuesta es 404 con `{"detail": "La venta no existe."}`

#### Scenario: Cliente y venta inexistente
- **WHEN** un usuario con sólo CLIENTE pide `GET /ventas/999` y esa venta no existe
- **THEN** la respuesta es 403, igual que para una venta ajena

### Requirement: Listado de ventas del personal
`GET /ventas/` SHALL responder el envoltorio `{items, total, page, size, pages}` con todas las ventas, ordenadas por `id`, cada ítem con la forma del detalle, con `page` y `size` validados como en todo listado. Los parámetros `limit` y `offset` MUST NOT paginar.

#### Scenario: Página intermedia
- **WHEN** hay tres ventas y se pide `GET /ventas/?size=1&page=2`
- **THEN** `items` trae sólo la venta 2, con `total` 3 y `pages` 3

#### Scenario: Sin ventas
- **WHEN** no hay ventas y se pide `GET /ventas/`
- **THEN** la respuesta es 200 con `items` vacío, `total` 0 y `pages` 1

#### Scenario: Página inexistente
- **WHEN** hay tres ventas y se pide `GET /ventas/?size=1&page=4`
- **THEN** la respuesta es 422 con «La página 4 no existe: hay 3»

### Requirement: Mis ventas
`GET /mis-ventas` SHALL responder el envoltorio con sólo las ventas del cliente vinculado al usuario de la sesión, ordenadas por `id`, con la forma del detalle y `page`/`size` validados. Un usuario sin cliente vinculado MUST recibir 200 con el envoltorio vacío; nunca ve ventas de otro cliente.

#### Scenario: Sólo las propias (RN-14)
- **WHEN** Ana tiene dos ventas, Lucía una, y la usuaria `ana@example.com` pide `GET /mis-ventas`
- **THEN** `items` trae sólo las dos ventas de Ana y `total` es 2

#### Scenario: Usuario sin cliente vinculado
- **WHEN** un vendedor sin cliente vinculado pide `GET /mis-ventas`
- **THEN** la respuesta es 200 con `items` vacío, `total` 0 y `pages` 1

#### Scenario: Página fuera de rango
- **WHEN** Ana tiene dos ventas y pide `GET /mis-ventas?size=1&page=3`
- **THEN** la respuesta es 422

### Requirement: Ventas viejas con libros dados de baja
Toda lectura de ventas (alta, detalle, listados) SHALL mostrar en cada renglón el título del libro aunque el libro esté dado de baja.

#### Scenario: Venta vieja de un libro dado de baja (C-13)
- **WHEN** se vende un libro, después se da de baja y se pide el detalle de la venta
- **THEN** el renglón sigue mostrando el título del libro

### Requirement: Lecturas de ventas con cantidad fija de consultas
El detalle de una venta (cliente, renglones y libro de cada renglón) SHALL emitir la misma cantidad de consultas sin importar cuántos renglones tenga, y los listados de ventas la misma sin importar cuántas ventas y renglones traiga la página. Ninguna lectura MUST depender de la carga perezosa.

#### Scenario: Detalle con 2 y con 4 renglones (C-15)
- **WHEN** se cuentan las consultas de `GET /ventas/{id}` para una venta con 2 renglones y para otra con 4
- **THEN** las dos cantidades son iguales

#### Scenario: Listado con una o varias ventas
- **WHEN** se cuentan las consultas de `GET /ventas/` con una venta de un renglón y con tres ventas de hasta tres renglones
- **THEN** las dos cantidades son iguales

#### Scenario: Mis ventas sin N+1
- **WHEN** se cuentan las consultas de `GET /mis-ventas` con una venta y con tres ventas de varios renglones
- **THEN** las dos cantidades son iguales
