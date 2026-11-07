# Spec Delta

## MODIFIED Requirements

### Requirement: Punto único de escritura del stock
El stock de un libro SHALL cambiar sólo por un único punto de la aplicación que, en la misma transacción, suma la cantidad al stock y agrega el movimiento con esa cantidad, su motivo, el usuario y la venta (si hay). Devuelve el stock resultante, el precio vigente del libro leído en la misma sentencia que cambia el stock, y el movimiento creado. Lo usan el alta con stock inicial, la reposición y, desde el registro transaccional de ventas, cada renglón. Ninguna otra ruta MUST escribir `libro.stock`.

#### Scenario: Escritura de stock con su movimiento
- **WHEN** se registra una entrada de 3 unidades en un libro vigente con stock 2
- **THEN** el stock queda en 5, hay un movimiento nuevo con `cantidad` 3, y el punto devuelve el stock 5 junto con ese movimiento (con `id` y `cuando` ya cargados)

#### Scenario: Salida con venta
- **WHEN** se registra una salida de 2 unidades de un libro con stock 5 indicando una venta
- **THEN** el stock queda en 3 y el movimiento lleva `cantidad` -2 y el `venta_id` de esa venta

#### Scenario: Precio vigente junto con el stock
- **WHEN** se registra una salida de 1 unidad de un libro cuyo precio es 25000.00
- **THEN** el punto devuelve el precio 25000.00 sin emitir otra consulta además de la escritura del stock y la del movimiento

#### Scenario: Sin confirmación propia
- **WHEN** se registra un movimiento y la unidad de trabajo que lo contiene revierte
- **THEN** ni el cambio de stock ni el movimiento quedan en la base
