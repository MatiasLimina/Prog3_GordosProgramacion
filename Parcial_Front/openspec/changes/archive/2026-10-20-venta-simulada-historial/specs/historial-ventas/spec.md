# Spec Delta

## MODIFIED Requirements

### Requirement: Listado de ventas

La vista Historial MUST mostrar una tabla de ventas generada desde los datos locales, con columnas identificador, fecha, cliente, total y acciones, y MUST reemplazar el contenido estático del HTML. El total MUST mostrarse con dos decimales.

#### Scenario: Tabla de ventas
- **WHEN** se abre la vista Historial
- **THEN** la tabla lista las ventas de los datos locales con identificador, fecha, cliente y total con dos decimales

#### Scenario: Listado generado desde los datos
- **WHEN** se cuentan las filas visibles al abrir la vista Historial
- **THEN** hay exactamente una fila por cada venta de los datos locales, sin repetir las filas de ejemplo del HTML

### Requirement: Acceso al detalle de una venta

Cada venta del listado MUST tener un control "Ver detalle" que lleve al detalle de esa venta. El detalle MUST mostrar identificador, fecha, cliente y una tabla de renglones con libro, cantidad, precio unitario y subtotal, más el total, usando los valores confirmados (precio unitario histórico).

#### Scenario: Ver detalle
- **WHEN** se activa "Ver detalle" de una venta
- **THEN** se muestra el detalle con los renglones confirmados y el total

#### Scenario: Detalle con precio histórico
- **WHEN** se consulta el detalle de una venta
- **THEN** cada renglón muestra el precio unitario copiado al confirmar, independientemente del precio actual del catálogo

### Requirement: Contenido del detalle de venta

El detalle de cada venta MUST mostrar identificador, fecha, cliente y una tabla de renglones con libro, cantidad, precio unitario y subtotal, más el total con dos decimales.

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