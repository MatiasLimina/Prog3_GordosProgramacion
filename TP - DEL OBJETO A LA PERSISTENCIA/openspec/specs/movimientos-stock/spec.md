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
