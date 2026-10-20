# Spec Delta

## ADDED Requirements

### Requirement: Seed de ventas de ejemplo

Los datos locales MUST incluir al menos dos ventas de ejemplo con identificador, fecha, cliente, renglones (con título y precio unitario histórico) y total, para que el Historial muestre contenido al abrir.

#### Scenario: Ventas de ejemplo presentes
- **WHEN** se abren los datos locales por primera vez
- **THEN** existen al menos dos ventas con id, fecha, cliente, renglones y total

### Requirement: Alta de venta

Una venta confirmada MUST registrarse en los datos locales con identificador entero incremental, fecha ISO 8601, cliente (id y nombre descriptivo), renglones con libroId, título descriptivo, cantidad, precio unitario histórico y subtotal, y total. El renglón MUST copiar el precio unitario y el título al confirmar, sin releeerlos del catálogo.

#### Scenario: Venta registrada
- **WHEN** se confirma una venta válida
- **THEN** la venta se agrega a los datos locales con id, fecha, cliente, renglones y total

#### Scenario: Precio unitario histórico
- **WHEN** se revisa una venta confirmada
- **THEN** cada renglón conserva el precio unitario copiado al confirmar, independientemente del precio actual del libro en el catálogo

### Requirement: Inmutabilidad de las ventas confirmadas

Las ventas confirmadas MUST NOT poder editarse ni eliminarse desde la interfaz.

#### Scenario: Sin controles de edición
- **WHEN** se recorre la vista Historial con Tab
- **THEN** no hay campos editables ni botones de editar o eliminar ventas