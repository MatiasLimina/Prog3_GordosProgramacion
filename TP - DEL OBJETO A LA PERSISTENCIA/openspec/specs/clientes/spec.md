# clientes Specification

## Purpose
Define el vínculo opcional entre un cliente de la librería y un usuario del sistema, que le da acceso web: un cliente puede no tener usuario, y un usuario identifica a lo sumo a un cliente.

## Requirements

### Requirement: Usuario opcional y exclusivo del cliente
La tabla `cliente` SHALL tener la columna `usuario_id` que admite nulo, con clave foránea a `usuario` (`fk_cliente_usuario_id_usuario`) y restricción única `uq_cliente_usuario_id`. El UNIQUE MUST ser el índice de esa clave foránea (sin un `ix_cliente_usuario_id` adicional). `cliente.email` MUST seguir siendo único (`uq_cliente_email`).

#### Scenario: Cliente sin acceso web
- **WHEN** se guarda un cliente sin `usuario_id`
- **THEN** la base lo acepta y varios clientes pueden quedar con `usuario_id` nulo

#### Scenario: Un usuario para dos clientes
- **WHEN** un cliente ya tiene un `usuario_id` y se intenta asignar el mismo a otro cliente
- **THEN** la base lo rechaza por `uq_cliente_usuario_id`

#### Scenario: Usuario inexistente
- **WHEN** se intenta guardar un cliente con un `usuario_id` que no existe
- **THEN** la base lo rechaza por `fk_cliente_usuario_id_usuario`

#### Scenario: Restricciones presentes
- **WHEN** se inspecciona la tabla `cliente`
- **THEN** tiene `uq_cliente_usuario_id`, `fk_cliente_usuario_id_usuario` y `uq_cliente_email`, y no tiene `ix_cliente_usuario_id`

### Requirement: Navegación cliente–usuario a uno en los dos extremos
El modelo SHALL permitir navegar del cliente a su usuario y del usuario a su cliente, y los dos extremos MUST devolver un objeto (o nada), nunca una lista.

#### Scenario: Extremos escalares y emparejados
- **WHEN** se configuran los mapeos de todos los modelos
- **THEN** `cliente.usuario` y `usuario.cliente` son relaciones a uno, emparejadas entre sí

#### Scenario: Cliente sin usuario
- **WHEN** se navega `cliente.usuario` de un cliente con `usuario_id` nulo
- **THEN** devuelve nada (`None`), no una lista vacía
