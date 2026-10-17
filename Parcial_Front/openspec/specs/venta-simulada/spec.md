# venta-simulada Specification

## Purpose

Permite componer una venta simulada: elegir un cliente, agregar renglones de libros con cantidades, revisar subtotales y total, y confirmarla.

## Requirements

### Requirement: Selección de cliente
La vista Ventas MUST incluir un selector etiquetado "Cliente" cuya opción inicial no seleccione ningún cliente.

#### Scenario: Cliente sin elegir
- **WHEN** se abre la vista Ventas
- **THEN** el selector "Cliente" muestra una opción inicial que invita a elegir, seguida de los clientes de ejemplo

### Requirement: Alta de renglón
La vista Ventas MUST incluir un selector etiquetado "Libro", un campo numérico etiquetado "Cantidad" que declare como esperados los enteros desde 1, con valor inicial 1, y un botón "Agregar renglón".

#### Scenario: Controles de renglón
- **WHEN** se abre la vista Ventas
- **THEN** se ven el selector "Libro", el campo "Cantidad" y el botón "Agregar renglón", alcanzables con Tab

### Requirement: Tabla de renglones
La vista Ventas MUST mostrar los renglones en una tabla con columnas libro, cantidad, precio unitario, subtotal y acciones; cada renglón MUST tener la cantidad editable con etiqueta propia y un botón "Quitar renglón".

#### Scenario: Renglón editable
- **WHEN** se observa un renglón de la venta de ejemplo
- **THEN** su cantidad está en un campo editable etiquetado con el título del libro y tiene un botón "Quitar renglón"

### Requirement: Resumen y total de la venta
La vista Ventas MUST mostrar el total de la venta con dos decimales al pie de la tabla de renglones, y los subtotales de cada renglón también con dos decimales.

#### Scenario: Venta de ejemplo
- **WHEN** se abre la vista Ventas con la venta de ejemplo de 2 unidades a 1500.00 y 1 unidad a 2000.00
- **THEN** los subtotales son 3000.00 y 2000.00 y el total es 5000.00

### Requirement: Confirmación de la venta
La vista Ventas MUST incluir un botón de envío "Confirmar venta".

#### Scenario: Botón de confirmación
- **WHEN** se recorre el formulario de venta con Tab
- **THEN** el último control del formulario es el botón "Confirmar venta"

### Requirement: Mensajes de la vista Ventas
La vista Ventas MUST incluir, ocultos por defecto, un mensaje de venta sin renglones y uno de venta confirmada con `role="status"`, y uno de venta rechazada con `role="alert"` capaz de listar los errores.

#### Scenario: Mensajes presentes
- **WHEN** se inspecciona el HTML de la vista Ventas
- **THEN** existen los mensajes de venta sin renglones, venta confirmada y venta rechazada, todos con `hidden`
