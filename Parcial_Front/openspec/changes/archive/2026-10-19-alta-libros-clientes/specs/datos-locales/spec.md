# Spec Delta

## ADDED Requirements

### Requirement: Identificador de los registros dados de alta

Cada alta de libro o de cliente MUST recibir un identificador calculado a partir del mayor identificador existente en su colección, de modo que sea único y numérico. El identificador MUST NOT repetir ninguno de los ya presentes en esa colección.

#### Scenario: Libro nuevo
- **WHEN** se da de alta un libro en una colección cuyos identificadores van de 1 a 6
- **THEN** el libro recibe el identificador 7 y ningún libro existente cambia de identificador

#### Scenario: Cliente nuevo
- **WHEN** se da de alta un cliente en una colección cuyos identificadores van de 1 a 3
- **THEN** el cliente recibe el identificador 4 y ningún cliente existente cambia de identificador

#### Scenario: Altas consecutivas
- **WHEN** se dan de alta dos registros seguidos en la misma colección
- **THEN** cada uno recibe un identificador distinto y mayor que el del anterior

### Requirement: Inserción de las altas en los datos locales

Un alta validada MUST incorporarse a la colección correspondiente de los datos locales y MUST quedar disponible para el resto de las vistas que consultan esa colección en la misma página. La inserción MUST preservar las referencias válidas de los libros a editoriales, géneros y autores.

#### Scenario: Libro disponible tras el alta
- **WHEN** se da de alta un libro válido
- **THEN** el libro forma parte de la colección de libros y puede consultarse por su identificador

#### Scenario: Cliente disponible tras el alta
- **WHEN** se da de alta un cliente válido
- **THEN** el cliente forma parte de la colección de clientes y puede consultarse por su identificador

#### Scenario: Referencias válidas del libro dado de alta
- **WHEN** se revisa un libro dado de alta
- **THEN** su editorial y todos sus autores existen en las colecciones correspondientes, y su género, si está asignado, también existe

#### Scenario: Género ausente en el libro dado de alta
- **WHEN** se da de alta un libro sin género
- **THEN** el libro no presenta referencia a ningún género y se interpreta como «Sin clasificar»
