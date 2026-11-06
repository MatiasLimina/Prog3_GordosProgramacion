# Spec Delta

## ADDED Requirements

### Requirement: Punto único de escritura del stock
El stock de un libro SHALL cambiar sólo por un único punto de la aplicación que, en la misma transacción, suma la cantidad al stock y agrega el movimiento con esa cantidad, su motivo, el usuario y la venta (si hay). Devuelve el stock resultante y el movimiento creado. Lo usan el alta con stock inicial, la reposición y, desde el registro transaccional de ventas, cada renglón. Ninguna otra ruta MUST escribir `libro.stock`.

#### Scenario: Escritura de stock con su movimiento
- **WHEN** se registra una entrada de 3 unidades en un libro vigente con stock 2
- **THEN** el stock queda en 5, hay un movimiento nuevo con `cantidad` 3, y el punto devuelve el stock 5 junto con ese movimiento (con `id` y `cuando` ya cargados)

#### Scenario: Salida con venta
- **WHEN** se registra una salida de 2 unidades de un libro con stock 5 indicando una venta
- **THEN** el stock queda en 3 y el movimiento lleva `cantidad` -2 y el `venta_id` de esa venta

#### Scenario: Sin confirmación propia
- **WHEN** se registra un movimiento y la unidad de trabajo que lo contiene revierte
- **THEN** ni el cambio de stock ni el movimiento quedan en la base

### Requirement: Escritura atómica del stock
El cambio de stock SHALL hacerse en una sola sentencia condicionada que exige que el libro esté vigente y que el resultado quede entre 0 y el máximo entero de la columna, sin leer el stock antes. Dos escrituras concurrentes sobre el mismo libro MUST NOT perder ninguna actualización ni dejar el stock negativo.

#### Scenario: Dos salidas concurrentes por la última unidad
- **WHEN** dos transacciones concurrentes intentan sacar 1 unidad de un libro con stock 1
- **THEN** exactamente una lo logra; la otra recibe el rechazo por stock insuficiente, y el stock final es 0 con un solo movimiento de salida

#### Scenario: Objeto ya cargado en la sesión
- **WHEN** el libro ya estaba cargado en la sesión y se registra un movimiento sobre él
- **THEN** el objeto en memoria muestra el stock resultante sin necesidad de volver a leerlo de la base

### Requirement: Rechazos del punto único de stock
Si la escritura no alcanza ninguna fila, el punto único SHALL leer el libro una sola vez (incluidos los dados de baja) e informar el motivo con el estado actual de la base: libro inexistente; dado de baja (409); y, según el signo de la cantidad, stock insuficiente en una salida (409) o máximo excedido en una entrada (409), con los mensajes de los escenarios. Ningún rechazo MUST dejar escrituras.

#### Scenario: Libro dado de baja
- **WHEN** se registra un movimiento sobre el libro 3, dado de baja
- **THEN** se rechaza con 409 «El libro 3 está dado de baja.» y el stock y los movimientos no cambian

#### Scenario: Stock insuficiente
- **WHEN** se intenta sacar 5 unidades del libro 3, que tiene stock 2
- **THEN** se rechaza con 409 «Stock insuficiente para el libro 3: hay 2, se pidieron 5.» y no queda movimiento

#### Scenario: Libro inexistente
- **WHEN** se registra un movimiento sobre un id de libro que no existe
- **THEN** se informa «libro inexistente», distinto de un conflicto, y no queda movimiento

#### Scenario: Máximo excedido
- **WHEN** se reponen unidades que llevarían el stock por encima del máximo entero de la columna
- **THEN** se rechaza con 409 «El stock del libro {id} superaría el máximo permitido.», sin texto interno de la base ni error 500

#### Scenario: Mensaje con el stock real de la base
- **WHEN** el libro estaba cargado en la sesión con un stock viejo y la salida se rechaza por stock insuficiente
- **THEN** el mensaje informa el stock que tiene la base, no el valor viejo en memoria

### Requirement: Cantidad del movimiento nunca cero
El punto único SHALL rechazar una cantidad 0 como error de programación, antes de escribir; los callers MUST no llamarlo con 0 (el alta con `stock_inicial` 0 no lo llama y la reposición exige `cantidad` >= 1 en el contrato).

#### Scenario: Llamada con cantidad cero
- **WHEN** se invoca el punto único con `cantidad` 0
- **THEN** falla sin emitir ninguna escritura

### Requirement: Reposición de stock
`POST /libros/{id}/reponer` (sólo `ADMIN`) SHALL sumar `cantidad` al stock del libro vigente por el punto único, con el `motivo` enviado o «Reposición» y el administrador de la sesión como `usuario_id`, y responder 200 con el stock resultante y el movimiento que devolvió el punto único. Libro inexistente → 404; dado de baja → 409; sin sesión → 401; sin `ADMIN` → 403; cuerpo inválido → 422. Ningún rechazo MUST dejar movimiento.

#### Scenario: Reposición válida (C-13)
- **WHEN** un administrador con sesión repone 3 unidades de un libro vigente con stock 10
- **THEN** la respuesta es 200 con `stock` 13 y el movimiento (`cantidad` 3, `motivo` «Reposición», `usuario_id` de ese administrador, `venta_id` nulo, `cuando`)

#### Scenario: Reponer un libro dado de baja
- **WHEN** se repone un libro dado de baja
- **THEN** la respuesta es 409 con «El libro {id} está dado de baja.» y no queda movimiento

#### Scenario: Reponer un libro inexistente
- **WHEN** se repone el libro 999, que no existe
- **THEN** la respuesta es 404 con `{"detail": "El libro no existe."}`

#### Scenario: Reponer sin sesión
- **WHEN** se envía la reposición sin la cookie de acceso
- **THEN** la respuesta es 401 y el stock no cambia

#### Scenario: Reponer como vendedor
- **WHEN** un usuario con sólo `VENDEDOR` vigente envía una reposición válida
- **THEN** la respuesta es 403, el stock no cambia y no queda movimiento

#### Scenario: Cantidad inválida
- **WHEN** se envía `cantidad` 0 o negativa
- **THEN** la respuesta es 422 y no queda movimiento

### Requirement: Historial de movimientos de un libro
`GET /libros/{id}/movimientos` SHALL listar con el envoltorio de paginación los movimientos del libro en orden de alta (por `id`), con `id`, `libro_id`, `venta_id`, `usuario_id`, `cantidad`, `motivo` y `cuando`, también si el libro está dado de baja. Exige `ADMIN` vigente (no es parte del catálogo público). Si el libro no existe MUST responder 404 con «El libro no existe.».

#### Scenario: Historial tras alta y reposición
- **WHEN** un libro se dio de alta con `stock_inicial` 4 y se repuso 3
- **THEN** el historial trae 2 movimientos, «Stock inicial» (4) y «Reposición» (3), `total` 2

#### Scenario: Historial de un libro dado de baja
- **WHEN** se pide el historial de un libro dado de baja
- **THEN** la respuesta es 200 con sus movimientos

#### Scenario: Historial de un libro inexistente
- **WHEN** se pide `GET /libros/999/movimientos`
- **THEN** la respuesta es 404

### Requirement: Stock igual a la suma de los movimientos
Para todo libro dado de alta o repuesto por la API, `libro.stock` SHALL ser igual a la suma de `cantidad` de sus movimientos, también después de un rechazo.

#### Scenario: Invariante tras alta, reposición y rechazo
- **WHEN** se da de alta un libro con `stock_inicial` 4, se repone 3 y después falla una reposición sobre él por estar dado de baja
- **THEN** `stock` es 7 y la suma de las cantidades de sus movimientos es 7

### Requirement: Mensaje del rechazo de sólo agregado en el catálogo
Si una operación del módulo de libros choca con el disparador de sólo agregado, la respuesta SHALL ser 409 con el mensaje propio del módulo para `movimiento_stock_solo_agregado`, que indica que los movimientos no se modifican ni se borran y que un error se corrige con otro movimiento.

#### Scenario: Rechazo traducido por la unidad de trabajo de libros
- **WHEN** dentro de la unidad de trabajo de libros se intenta modificar un movimiento y el bloque termina
- **THEN** se revierte y el conflicto lleva el mensaje propio del módulo, sin el nombre de la constraint ni texto de la base
