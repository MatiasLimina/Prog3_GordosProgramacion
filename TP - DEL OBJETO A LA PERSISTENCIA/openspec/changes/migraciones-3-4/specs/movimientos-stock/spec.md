# Spec Delta

## ADDED Requirements

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
