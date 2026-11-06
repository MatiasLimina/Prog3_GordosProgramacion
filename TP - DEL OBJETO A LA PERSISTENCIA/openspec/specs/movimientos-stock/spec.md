# movimientos-stock Specification

## Purpose
Registra cada cambio del stock de un libro como un movimiento con cantidad, motivo, momento, usuario responsable y, si corresponde, la venta que lo originó, de modo que el stock de cada libro pueda reconstruirse como la suma de sus movimientos.

## Requirements

### Requirement: Estructura de movimiento_stock
La tabla `movimiento_stock` SHALL tener las columnas `id` (clave primaria), `libro_id` (obligatoria), `venta_id` (admite nulo), `usuario_id` (obligatoria), `cantidad` (entero, obligatoria), `motivo` (texto de hasta 255 caracteres, obligatorio) y `cuando` (`timestamptz`, obligatoria).

#### Scenario: Columnas y nulabilidad
- **WHEN** se inspecciona la definición de `movimiento_stock`
- **THEN** tiene exactamente `id`, `libro_id`, `venta_id`, `usuario_id`, `cantidad`, `motivo` y `cuando`, y sólo `venta_id` admite nulo

#### Scenario: Momento con zona horaria
- **WHEN** se inspecciona la columna `cuando`
- **THEN** es `timestamptz`

### Requirement: Momento del movimiento lo fija la base
Si al insertar un movimiento no se indica `cuando`, la base SHALL completarlo con el momento actual (`now()`).

#### Scenario: Alta sin cuando
- **WHEN** se inserta un movimiento sin valor para `cuando`
- **THEN** la fila queda con `cuando` igual al momento de la transacción, no nulo

### Requirement: Cantidad distinta de cero
La base SHALL rechazar un movimiento con `cantidad = 0` mediante la restricción `ck_movimiento_stock_cantidad_no_cero`. Las cantidades positivas (entradas) y negativas (salidas) MUST aceptarse.

#### Scenario: Movimiento de cantidad cero
- **WHEN** se intenta guardar un movimiento con `cantidad` 0
- **THEN** la base lo rechaza por `ck_movimiento_stock_cantidad_no_cero`

#### Scenario: Entrada y salida
- **WHEN** se guardan movimientos con `cantidad` 4 y `cantidad` -2 para un libro existente
- **THEN** la base acepta los dos

### Requirement: Referencias del movimiento
Cada movimiento SHALL referenciar un libro existente (`fk_movimiento_stock_libro_id_libro`) y un usuario existente (`fk_movimiento_stock_usuario_id_usuario`), y puede referenciar una venta existente (`fk_movimiento_stock_venta_id_venta`). Ninguna de esas claves foráneas MUST propagar borrados ni poner nulos (sin `ON DELETE`).

#### Scenario: Libro inexistente
- **WHEN** se intenta guardar un movimiento con un `libro_id` que no existe
- **THEN** la base lo rechaza por `fk_movimiento_stock_libro_id_libro`

#### Scenario: Movimiento sin venta
- **WHEN** se guarda un movimiento de reposición con `venta_id` nulo
- **THEN** la base lo acepta

#### Scenario: Borrar una fila referenciada
- **WHEN** se intenta borrar físicamente un libro, una venta o un usuario que tiene movimientos
- **THEN** la base rechaza el borrado y el movimiento no cambia

### Requirement: Índice en cada clave foránea del movimiento
`movimiento_stock` SHALL tener los índices `ix_movimiento_stock_libro_id`, `ix_movimiento_stock_venta_id` e `ix_movimiento_stock_usuario_id`.

#### Scenario: Índices presentes
- **WHEN** se inspeccionan los índices de `movimiento_stock`
- **THEN** existen los tres índices sobre `libro_id`, `venta_id` y `usuario_id`

### Requirement: Navegación entre movimiento, libro, venta y usuario
El modelo SHALL permitir navegar en los dos extremos: de un movimiento a su libro, su venta (o ninguna) y su usuario; de un libro, de una venta y de un usuario a la colección de sus movimientos. Navegar o dar de baja un padre MUST NOT modificar ni borrar movimientos desde la aplicación.

#### Scenario: Relaciones recíprocas
- **WHEN** se configuran los mapeos de todos los modelos
- **THEN** `movimiento.libro`, `movimiento.venta` y `movimiento.usuario` devuelven un objeto y `libro.movimientos`, `venta.movimientos` y `usuario.movimientos` devuelven colecciones, emparejadas entre sí

#### Scenario: Borrar el padre no toca los movimientos desde el ORM
- **WHEN** la aplicación marca para borrar un libro que tiene movimientos cargados
- **THEN** el ORM no emite UPDATE ni DELETE sobre `movimiento_stock` y la base decide (rechazo por clave foránea)

### Requirement: Sólo agregado garantizado por la base
La base SHALL rechazar cualquier `UPDATE` o `DELETE` sobre una fila de `movimiento_stock`, venga de la aplicación, del ORM o de una consola SQL (RN-12). El rechazo MUST dejar la fila sin cambios y la transacción que lo intentó MUST fallar.

#### Scenario: UPDATE de un movimiento
- **WHEN** se ejecuta un `UPDATE` sobre un movimiento existente
- **THEN** la base lo rechaza y el movimiento conserva su `cantidad`, `motivo` y `cuando`

#### Scenario: DELETE de un movimiento
- **WHEN** se ejecuta un `DELETE` sobre un movimiento existente
- **THEN** la base lo rechaza y el movimiento sigue en la tabla

#### Scenario: Borrado desde el ORM
- **WHEN** la aplicación marca un movimiento para borrar o le cambia un campo y confirma
- **THEN** la confirmación falla y no queda ninguna escritura de esa transacción

#### Scenario: Rechazo dentro de una unidad de trabajo
- **WHEN** la aplicación cambia un campo de un movimiento dentro de una unidad de trabajo y sale del bloque
- **THEN** la unidad de trabajo revierte y lanza el conflicto de dominio (409), nunca un error 500

#### Scenario: El alta sigue permitida
- **WHEN** se inserta un movimiento válido
- **THEN** la base lo acepta

### Requirement: Mensaje y código del rechazo de sólo agregado
El rechazo SHALL decir en español que `movimiento_stock` es de sólo agregado, nombrar la operación rechazada (`UPDATE` o `DELETE`) y el id del movimiento, e indicar que un error se corrige con otro movimiento. Su SQLSTATE MUST ser de la clase de violación de integridad (`23001`), para que la aplicación lo trate como un conflicto y nunca como un error 500.

#### Scenario: Texto del rechazo
- **WHEN** se rechaza un `UPDATE` sobre `movimiento_stock`
- **THEN** el error dice que la tabla es de sólo agregado, menciona `UPDATE` y sugiere registrar un movimiento que compense

#### Scenario: Código del rechazo
- **WHEN** se rechaza un `DELETE` sobre `movimiento_stock`
- **THEN** el SQLSTATE del error es `23001`

### Requirement: Nombre de constraint del rechazo de sólo agregado
El rechazo SHALL llevar el nombre de constraint `movimiento_stock_solo_agregado`, para que la aplicación elija su mensaje por nombre como con cualquier otra restricción; si el diccionario de mensajes no tiene esa clave, la aplicación MUST responder con un mensaje propio para el código `23001`.

#### Scenario: Nombre de constraint del rechazo
- **WHEN** se rechaza un `UPDATE` o un `DELETE` sobre `movimiento_stock`
- **THEN** el error lleva el nombre de constraint `movimiento_stock_solo_agregado` y un diccionario de mensajes que tiene esa clave elige su mensaje

#### Scenario: Mensaje por código cuando el módulo no tiene la clave
- **WHEN** la aplicación traduce un rechazo `23001` con un diccionario de mensajes que no tiene `movimiento_stock_solo_agregado`
- **THEN** el 409 lleva un mensaje propio en español para ese código, distinto del mensaje genérico de conflicto, sin texto interno de la base

### Requirement: Acciones referenciales compatibles con el sólo agregado
Ninguna clave foránea que apunte a `movimiento_stock` SHALL tener `ON DELETE CASCADE`, y las claves foráneas de `movimiento_stock` MUST no tener `ON DELETE CASCADE` ni `ON DELETE SET NULL`: cualquiera de esas acciones haría que la base intente borrar o modificar movimientos y choque con el disparador.

#### Scenario: Metadata sin acciones incompatibles
- **WHEN** se recorren las claves foráneas del metadata de los modelos
- **THEN** ninguna que apunte a `movimiento_stock` tiene `ondelete` `CASCADE` y ninguna de `movimiento_stock` tiene `ondelete` `CASCADE` ni `SET NULL`

#### Scenario: Base migrada sin acciones incompatibles
- **WHEN** se leen las claves foráneas de o hacia `movimiento_stock` en la base migrada
- **THEN** todas tienen la acción por defecto (`NO ACTION`)

### Requirement: Vaciado completo para cargas iniciales
El sólo agregado SHALL aplicarse a `UPDATE` y `DELETE`, no a `TRUNCATE`: la carga inicial y la preparación de los tests MUST poder vaciar `movimiento_stock` con `TRUNCATE`. El comentario de la cuarta migración MUST decir que `TRUNCATE` no se bloquea a propósito porque lo usan la preparación de los tests y la carga inicial.

#### Scenario: TRUNCATE de todas las tablas
- **WHEN** se ejecuta `TRUNCATE` de todas las tablas del modelo con `RESTART IDENTITY CASCADE` y hay movimientos
- **THEN** termina sin error y `movimiento_stock` queda vacía

### Requirement: Disparador instalado y retirado por migración
El mecanismo de sólo agregado SHALL instalarlo la cuarta migración y retirarlo su `downgrade`: con la base en la tercera revisión no MUST existir, y con la base en `head` MUST existir.

#### Scenario: Bajar a la tercera revisión
- **WHEN** la base pasa de `head` a la tercera revisión
- **THEN** un `UPDATE` sobre un movimiento se acepta y no existen la función ni el disparador

#### Scenario: Volver a head
- **WHEN** la base vuelve de la tercera revisión a `head`
- **THEN** un `UPDATE` sobre un movimiento se rechaza otra vez

### Requirement: Demostración C-14 en psql
El proyecto SHALL incluir `test/solo_agregado.sql`, un script de psql que, corrido después de la carga inicial, muestra un movimiento, intenta un `UPDATE` y un `DELETE` sobre él y vuelve a mostrarlo. Cada intento MUST llevar en un comentario el resultado esperado.

#### Scenario: Los dos intentos rechazados
- **WHEN** se corre `test/solo_agregado.sql` con psql sobre la base sembrada
- **THEN** psql muestra dos errores del disparador, uno por el `UPDATE` y otro por el `DELETE`, y la fila mostrada al final es igual a la del principio

#### Scenario: Independiente de los ids sembrados
- **WHEN** se corre el script sobre una base con al menos un movimiento
- **THEN** elige el movimiento por consulta (el de menor id) y no por un id fijo

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
