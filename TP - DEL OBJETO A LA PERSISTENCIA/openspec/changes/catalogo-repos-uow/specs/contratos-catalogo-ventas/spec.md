# Spec Delta

## ADDED Requirements

### Requirement: Entradas de editoriales, géneros y autores sin campos no declarados
Los contratos de alta y de edición de editorial, de alta de género y de alta y edición de autor MUST rechazar con 422 cualquier campo que no declaran, igual que el resto de los contratos de entrada.

#### Scenario: Campo extra en el alta de editorial
- **WHEN** se envía `POST /editoriales` con `nombre`, `pais` y un campo `id`
- **THEN** la respuesta es 422 y no se crea la editorial

#### Scenario: Campo extra en la edición de autor
- **WHEN** se envía `PATCH /autores/{id}` con `nombre` y un campo `libros`
- **THEN** la respuesta es 422 y el autor no cambia

### Requirement: Contrato de salida de un movimiento de stock
El contrato de salida de un movimiento SHALL incluir `id`, `libro_id`, `venta_id` (o nulo), `usuario_id`, `cantidad`, `motivo` y `cuando` con zona horaria, y ningún dato del usuario más allá de su id.

#### Scenario: Movimiento serializado
- **WHEN** se serializa un movimiento de reposición
- **THEN** la salida tiene exactamente `id`, `libro_id`, `venta_id`, `usuario_id`, `cantidad`, `motivo` y `cuando`, con `cuando` en ISO 8601 con desplazamiento horario

### Requirement: Contrato de salida de la reposición
La respuesta de la reposición SHALL incluir el `libro_id`, el `stock` resultante y el movimiento creado con el contrato de salida de movimiento.

#### Scenario: Reposición serializada
- **WHEN** se serializa el resultado de reponer 3 unidades de un libro que queda con stock 13
- **THEN** la salida tiene `libro_id`, `stock` 13 y `movimiento` con `cantidad` 3
