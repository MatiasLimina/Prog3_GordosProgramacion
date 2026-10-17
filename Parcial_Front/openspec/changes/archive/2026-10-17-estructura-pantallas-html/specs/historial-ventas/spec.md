# Spec Delta

## Purpose

Permite consultar las ventas confirmadas, con su identificador, fecha, cliente y total, y acceder al detalle de renglones de cada una sin poder editarlas ni eliminarlas.

## ADDED Requirements

### Requirement: Listado de ventas
La vista Historial MUST mostrar una tabla de ventas con columnas identificador, fecha, cliente, total y acciones, con al menos dos ventas de ejemplo en la etapa 1.

#### Scenario: Tabla de ventas
- **WHEN** se abre la vista Historial
- **THEN** la tabla lista las ventas de ejemplo con identificador, fecha, cliente y total con dos decimales

### Requirement: Acceso al detalle de una venta
Cada venta del listado MUST tener un control "Ver detalle" que lleve, sin JavaScript, al detalle de esa venta, con un nombre accesible que identifique la venta.

#### Scenario: Ver detalle sin JavaScript
- **WHEN** se activa "Ver detalle" de una venta con JavaScript deshabilitado
- **THEN** la página se desplaza al detalle de esa venta

### Requirement: Contenido del detalle de venta
El detalle de cada venta MUST mostrar identificador, fecha, cliente y una tabla de renglones con libro, cantidad, precio unitario y subtotal, más el total.

#### Scenario: Detalle de la venta de ejemplo
- **WHEN** se consulta el detalle de la venta de ejemplo de María Gómez
- **THEN** muestra 2 × 1500.00 = 3000.00, 1 × 2000.00 = 2000.00 y total 5000.00

### Requirement: Ventas confirmadas sin edición
La vista Historial MUST NOT ofrecer controles para editar ni eliminar ventas confirmadas.

#### Scenario: Sin controles de edición
- **WHEN** se recorre la vista Historial con Tab
- **THEN** no hay campos editables ni botones de editar o eliminar ventas

### Requirement: Historial vacío
La vista Historial MUST incluir, oculto por defecto, un mensaje de historial vacío con `role="status"`.

#### Scenario: Mensaje de historial vacío
- **WHEN** se inspecciona el HTML de la vista Historial
- **THEN** existe un mensaje de historial vacío con `hidden` y `role="status"`
