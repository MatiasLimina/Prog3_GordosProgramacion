# migraciones-esquema Specification

## Purpose
Define cómo se crea y evoluciona el esquema de la base: sólo con migraciones de Alembic encadenadas, reversibles sobre una base vacía, aplicables sobre una base con datos del TP y siempre coincidentes con los modelos.

## Requirements

### Requirement: El esquema se crea sólo con migraciones
El esquema de la base SHALL crearse y modificarse exclusivamente con `alembic upgrade`; ningún camino de la aplicación, del seed ni de los tests MUST crear tablas con `create_all`.

#### Scenario: Base vacía hasta la última revisión
- **WHEN** se corre `alembic upgrade head` sobre una base vacía
- **THEN** termina sin error y la base queda con las catorce tablas de la consigna (`editorial`, `genero`, `autor`, `libro`, `libro_autor`, `cliente`, `perfil_cliente`, `venta`, `renglon_venta`, `usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad`, `movimiento_stock`) y `alembic_version` en la cuarta revisión

### Requirement: Cadena de cuatro revisiones
La historia de migraciones SHALL ser una cadena lineal de cuatro revisiones con una sola cabeza: las dos del TP, una tercera generada con `--autogenerate` (tablas de acceso, movimiento de stock y cambios de `cliente` y `libro`) y una cuarta escrita a mano (disparador de sólo agregado).

#### Scenario: Historia lineal
- **WHEN** se consulta la historia de Alembic
- **THEN** hay una sola cabeza y la tercera revisión desciende de la segunda del TP y la cuarta de la tercera

#### Scenario: Cada migración nueva declara que se leyó
- **WHEN** se abre la tercera o la cuarta migración
- **THEN** su cabecera dice que se leyó antes de aplicarla y cada corrección manual de la versión generada lleva un comentario que la explica

### Requirement: Reversibilidad sobre una base vacía
Sobre una base vacía, `alembic upgrade head`, después `alembic downgrade base` y otra vez `alembic upgrade head` SHALL terminar sin error. Tras `downgrade base` no MUST quedar ninguna tabla, función ni disparador del proyecto.

#### Scenario: Ida, vuelta e ida
- **WHEN** sobre una base vacía se corren en orden `upgrade head`, `downgrade base` y `upgrade head`
- **THEN** los tres terminan sin error y al final el esquema es el mismo que después del primer `upgrade head`

#### Scenario: Nada queda después de bajar a base
- **WHEN** se corre `alembic downgrade base`
- **THEN** en el esquema `public` sólo queda `alembic_version` (vacía) y no existen la función ni el disparador de sólo agregado

### Requirement: La tercera migración se aplica sobre una base con datos del TP
La tercera migración SHALL aplicarse sobre una base en la segunda revisión que ya tiene editoriales, libros y clientes, sin pedir valores para las filas existentes y sin modificar sus datos.

#### Scenario: Filas existentes de libro y cliente
- **WHEN** una base en la segunda revisión con libros y clientes se lleva a `head`
- **THEN** la migración termina sin error, esas filas conservan sus datos, `libro.borrado_en` y `cliente.usuario_id` quedan nulos y no se crea ningún usuario ni movimiento

### Requirement: Unicidad de ISBN tras la migración
Después de la tercera migración `libro` SHALL no tener la constraint `uq_libro_isbn` y SHALL tener el índice único parcial `uq_libro_isbn_vigente` sobre `isbn` con `WHERE borrado_en IS NULL`. El 409 de un ISBN repetido MUST seguir saliendo con el mensaje propio «Ya existe un libro con ese ISBN.».

#### Scenario: ISBN repetido entre vigentes
- **WHEN** se guardan dos libros vigentes con el mismo ISBN en la base migrada
- **THEN** la base rechaza el segundo por `uq_libro_isbn_vigente` y la API responde 409 «Ya existe un libro con ese ISBN.»

#### Scenario: ISBN de un libro dado de baja
- **WHEN** un libro tiene `borrado_en` con fecha y se guarda otro vigente con el mismo ISBN
- **THEN** la base acepta el segundo

### Requirement: Esquema migrado igual a los modelos
Con la base en `head`, la comparación automática de Alembic entre el esquema y los modelos SHALL no encontrar diferencias.

#### Scenario: Comparación sin diferencias
- **WHEN** se corre `alembic check` contra una base en `head`
- **THEN** termina sin error e informa que no hay operaciones nuevas

### Requirement: Restricciones de la base migrada
La base migrada SHALL aplicar las restricciones con nombre de los modelos de acceso, cliente y movimiento de stock, de modo que una escritura inválida se rechace en la base y se pueda traducir a 409 por su nombre.

#### Scenario: Rol fuera de la lista
- **WHEN** se guarda una asignación con un rol que no es ADMIN, VENDEDOR ni CLIENTE
- **THEN** la base la rechaza por `ck_asignacion_rol_rol_valido`

#### Scenario: Dos asignaciones vigentes del mismo rol
- **WHEN** un usuario tiene una asignación de un rol sin `revocada_en` y se guarda otra del mismo rol sin `revocada_en`
- **THEN** la base rechaza la segunda por `uq_asignacion_rol_usuario_rol_vigente`; si la primera tiene `revocada_en`, la acepta

#### Scenario: Dos clientes con el mismo usuario
- **WHEN** dos clientes apuntan al mismo `usuario_id`
- **THEN** la base rechaza el segundo por `uq_cliente_usuario_id`; varios clientes con `usuario_id` nulo se aceptan

#### Scenario: Movimiento de cantidad cero
- **WHEN** se guarda un movimiento con `cantidad` 0
- **THEN** la base lo rechaza por `ck_movimiento_stock_cantidad_no_cero`

#### Scenario: Borrar un padre con movimientos
- **WHEN** se intenta borrar un libro, una venta o un usuario que tiene movimientos
- **THEN** la base rechaza el borrado por la clave foránea correspondiente y el movimiento sigue igual

#### Scenario: Momento por defecto del movimiento
- **WHEN** se inserta un movimiento sin `cuando`
- **THEN** la fila queda con `cuando` con zona horaria igual al momento de la transacción
