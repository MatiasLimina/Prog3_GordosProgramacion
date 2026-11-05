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
