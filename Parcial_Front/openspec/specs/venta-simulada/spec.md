# venta-simulada Specification

## Purpose

Permite componer una venta simulada: elegir un cliente, agregar renglones de libros con cantidades, revisar subtotales y total, y confirmarla. Los renglones se componen sobre los datos locales y la confirmación registra la venta con precio unitario histórico.

## Requirements

### Requirement: Selección de cliente
La vista Ventas MUST incluir un selector etiquetado "Cliente" cuyas opciones MUST generarse desde los datos locales. La opción inicial MUST NOT seleccionar ningún cliente.

#### Scenario: Cliente sin elegir
- **WHEN** se abre la vista Ventas
- **THEN** el selector "Cliente" muestra una opción inicial que invita a elegir, seguida de los clientes de los datos locales

#### Scenario: Clientes generados desde los datos
- **WHEN** se inspeccionan las opciones del selector "Cliente"
- **THEN** hay una opción por cada cliente de los datos locales, con su nombre como texto y su identificador como valor

### Requirement: Alta de renglón
La vista Ventas MUST incluir un selector etiquetado "Libro", un campo numérico etiquetado "Cantidad" que declare como esperados los enteros desde 1, con valor inicial 1, y un botón "Agregar renglón". Al agregar, el renglón MUST usar el precio unitario actual del libro y MUST calcular el subtotal (cantidad × precio unitario) con dos decimales. Si el libro ya está en la venta, la cantidad MUST sumarse al renglón existente.

#### Scenario: Controles de renglón
- **WHEN** se abre la vista Ventas
- **THEN** se ven el selector "Libro", el campo "Cantidad" y el botón "Agregar renglón", alcanzables con Tab

#### Scenario: Renglón agregado
- **WHEN** se elige un libro y una cantidad válida y se activa "Agregar renglón"
- **THEN** aparece un renglón con el título, la cantidad, el precio unitario con dos decimales y el subtotal con dos decimales

#### Scenario: Libro repetido suma cantidad
- **WHEN** se agrega un renglón con un libro que ya está en la venta
- **THEN** no se crea otro renglón: la cantidad del renglón existente se incrementa y su subtotal se recalcula

#### Scenario: Cantidad inválida al agregar
- **WHEN** se intenta agregar un renglón con cantidad 0, negativa o decimal
- **THEN** no se agrega el renglón y se informa el error

### Requirement: Tabla de renglones
La vista Ventas MUST mostrar los renglones en una tabla con columnas libro, cantidad, precio unitario, subtotal y acciones; cada renglón MUST tener la cantidad editable con etiqueta propia y un botón "Quitar renglón". Al cambiar la cantidad MUST recalcularse el subtotal y el total.

#### Scenario: Renglón editable
- **WHEN** se observa un renglón de la venta
- **THEN** su cantidad está en un campo editable etiquetado con el título del libro y tiene un botón "Quitar renglón"

#### Scenario: Cambio de cantidad
- **WHEN** se modifica la cantidad de un renglón a un valor válido
- **THEN** su subtotal y el total se recalculan con dos decimales

#### Scenario: Quitar renglón
- **WHEN** se activa "Quitar renglón" de un renglón
- **THEN** el renglón desaparece y el total se recalcula

### Requirement: Resumen y total de la venta
La vista Ventas MUST mostrar el total de la venta con dos decimales al pie de la tabla de renglones, y los subtotales de cada renglón también con dos decimales. El total MUST ser la suma de los subtotales.

#### Scenario: Venta de ejemplo
- **WHEN** se compone una venta de 2 unidades a 1500.00 y 1 unidad a 2000.00
- **THEN** los subtotales son 3000.00 y 2000.00 y el total es 5000.00

### Requirement: Confirmación de la venta
La vista Ventas MUST incluir un botón de envío "Confirmar venta". Al confirmar MUST validarse cliente, renglones y cantidades; si todo es válido, la venta MUST registrarse con identificador entero incremental, fecha ISO 8601, cliente (id y nombre), renglones con precio unitario histórico (copiado al confirmar) y total; MUST limpiarse el formulario y mostrarse el mensaje de resultado.

#### Scenario: Botón de confirmación
- **WHEN** se recorre el formulario de venta con Tab
- **THEN** el último control del formulario es el botón "Confirmar venta"

#### Scenario: Confirmación válida
- **WHEN** se confirma una venta válida
- **THEN** se registra la venta con id y fecha, se limpia el formulario y se muestra el mensaje de venta confirmada

#### Scenario: Confirmación inválida
- **WHEN** se confirma sin cliente, sin renglones o con cantidades inválidas
- **THEN** no se registra ninguna venta y se listan los errores en el mensaje de venta rechazada

### Requirement: Mensajes de la vista Ventas
La vista Ventas MUST incluir, ocultos por defecto, un mensaje de venta sin renglones y uno de venta confirmada con `role="status"`, y uno de venta rechazada con `role="alert"` capaz de listar los errores.

#### Scenario: Mensajes presentes
- **WHEN** se inspecciona el HTML de la vista Ventas
- **THEN** existen los mensajes de venta sin renglones, venta confirmada y venta rechazada, todos con `hidden`

### Requirement: Validación pura de la venta
La validación de la venta MUST ser una función pura que reciba la entrada, los clientes y los libros, y devuelva `{ valido, errores, datosNormalizados }`. MUST validar cliente existente, al menos un renglón, libro existente por renglón y cantidad entera mayor que cero.

#### Scenario: Venta válida
- **WHEN** se valida una venta con cliente existente, al menos un renglón con libro existente y cantidades enteras mayores que cero
- **THEN** devuelve `valido: true` y `errores: []`

#### Scenario: Sin cliente
- **WHEN** se valida una venta sin cliente
- **THEN** devuelve un error que indica que se debe elegir un cliente

#### Scenario: Sin renglones
- **WHEN** se valida una venta sin renglones
- **THEN** devuelve un error que indica que la venta debe tener al menos un renglón

#### Scenario: Cantidad inválida
- **WHEN** se valida un renglón con cantidad 0, negativa o decimal
- **THEN** devuelve un error que indica que la cantidad debe ser un entero mayor que cero

#### Scenario: Libro inexistente
- **WHEN** se valida un renglón con un libro que no existe
- **THEN** devuelve un error que indica que el libro seleccionado no existe