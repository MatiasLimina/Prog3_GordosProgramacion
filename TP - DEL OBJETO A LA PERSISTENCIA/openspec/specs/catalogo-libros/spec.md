# catalogo-libros Specification

## Purpose
Define la identidad y la vigencia de un libro del catálogo: cómo se marca la baja lógica sin perder la fila y cómo la unicidad del ISBN se limita a los libros vigentes, con su rechazo propio.

## Requirements

### Requirement: Marca de baja lógica del libro
La tabla `libro` SHALL tener la columna `borrado_en` de tipo fecha y hora con zona horaria (`timestamptz`), que admite nulo. Un libro con `borrado_en` nulo MUST considerarse vigente; uno con `borrado_en` no nulo, dado de baja. La baja lógica MUST conservar la fila (no la borra).

#### Scenario: Libro recién cargado es vigente
- **WHEN** se inserta un libro sin indicar `borrado_en`
- **THEN** la fila queda con `borrado_en` nulo

#### Scenario: Tipo con zona horaria
- **WHEN** se inspecciona la definición de la columna `libro.borrado_en`
- **THEN** es `timestamptz` y admite nulo

### Requirement: ISBN único sólo entre los libros vigentes
La unicidad del ISBN SHALL garantizarla la base con un índice único parcial llamado `uq_libro_isbn_vigente` sobre `libro (isbn) WHERE borrado_en IS NULL`, en lugar de una restricción UNIQUE común. MUST NOT existir una restricción UNIQUE común sobre `libro.isbn`.

#### Scenario: Dos libros vigentes con el mismo ISBN
- **WHEN** ya existe un libro vigente con un ISBN y se intenta guardar otro vigente con el mismo ISBN
- **THEN** la base rechaza la escritura por el índice `uq_libro_isbn_vigente`

#### Scenario: Reutilizar el ISBN de un libro dado de baja
- **WHEN** el único libro con un ISBN tiene `borrado_en` no nulo y se guarda un libro vigente con ese ISBN
- **THEN** la base acepta la escritura y las dos filas conviven

#### Scenario: Sin UNIQUE común sobre isbn
- **WHEN** se inspeccionan las restricciones de la tabla `libro`
- **THEN** no hay una restricción `uq_libro_isbn` y sí el índice único parcial `uq_libro_isbn_vigente` con la condición `borrado_en IS NULL`

### Requirement: Mensaje propio para ISBN repetido
Cuando la base rechace un alta o una modificación de libro por el índice `uq_libro_isbn_vigente`, la API SHALL responder 409 con el mensaje «Ya existe un libro con ese ISBN.», sin exponer el nombre del índice ni texto interno de la base.

#### Scenario: Rechazo por el índice parcial traducido a 409
- **WHEN** una escritura de libro falla con una violación de unicidad cuyo nombre de restricción es `uq_libro_isbn_vigente`
- **THEN** la respuesta es 409 con el detalle «Ya existe un libro con ese ISBN.»

### Requirement: Restricciones de precio y stock del libro se mantienen
La tabla `libro` SHALL conservar `ck_libro_precio_positivo` (`precio > 0`) y `ck_libro_stock_no_negativo` (`stock >= 0`), y la columna `stock` como valor acumulado del libro.

#### Scenario: Restricciones presentes tras el cambio
- **WHEN** se inspeccionan las restricciones de la tabla `libro`
- **THEN** siguen `ck_libro_precio_positivo` y `ck_libro_stock_no_negativo`, y existe la columna `stock`
