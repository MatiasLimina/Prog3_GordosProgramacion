# datos-locales Specification

## Purpose

Define el modelo de datos local de la librería (libros, editoriales, géneros, autores y clientes) con identificadores estables y relaciones válidas, que alimenta el catálogo, las altas y las ventas sin depender de red ni de un backend.

## Requirements

### Requirement: Conjunto de datos inicial

El sistema MUST disponer de un conjunto de datos local en memoria con al menos 6 libros, 2 editoriales, 2 géneros, 3 autores y 3 clientes ficticios, disponible desde la primera apertura de la aplicación.

#### Scenario: Cantidad mínima de registros
- **WHEN** se abre `index.html` con JavaScript habilitado
- **THEN** existen al menos 6 libros, 2 editoriales, 2 géneros, 3 autores y 3 clientes en los datos locales

#### Scenario: Clientes disponibles aunque el catálogo no los muestre
- **WHEN** se consultan los datos locales desde la vista Catálogo
- **THEN** los 3 clientes del conjunto inicial están presentes y completos (nombre completo y email)

### Requirement: Referencias válidas de los libros

Cada libro MUST referenciar una editorial existente y uno o más autores existentes. El género SHALL ser opcional; cuando está asignado MUST corresponder a un género existente.

#### Scenario: Editorial y autores existentes
- **WHEN** se recorre cualquier libro del conjunto inicial
- **THEN** su editorial y todos sus autores existen en las colecciones de editoriales y autores

#### Scenario: Género ausente
- **WHEN** un libro no tiene género asignado
- **THEN** no presenta referencia a un género inexistente y se interpreta como «Sin clasificar»

#### Scenario: Género asignado existente
- **WHEN** un libro tiene género asignado
- **THEN** ese género existe en la colección de géneros

### Requirement: Cobertura mínima de casos del conjunto inicial

El conjunto inicial MUST incluir al menos un libro sin género y al menos un libro con dos o más autores, para que la presentación de esos casos pueda verificarse sin cargar datos.

#### Scenario: Libro sin género disponible
- **WHEN** se revisan los libros del conjunto inicial
- **THEN** al menos uno no tiene género asignado

#### Scenario: Libro con varios autores disponible
- **WHEN** se revisan los libros del conjunto inicial
- **THEN** al menos uno tiene dos o más autores

#### Scenario: Precios válidos
- **WHEN** se revisan los libros del conjunto inicial
- **THEN** todos tienen un precio numérico mayor que cero

### Requirement: Identificadores estables y únicos

Cada registro MUST tener un identificador único dentro de su colección (libros, editoriales, géneros, autores y clientes), y ese identificador MUST mantenerse estable durante toda la sesión y entre renderizados.

#### Scenario: Sin identificadores repetidos
- **WHEN** se recorren los libros, editoriales, géneros, autores y clientes
- **THEN** no hay identificadores repetidos dentro de cada colección

#### Scenario: Identificador estable entre renderizados
- **WHEN** el catálogo se vuelve a renderizar tras filtrar o limpiar la búsqueda
- **THEN** cada libro conserva el mismo identificador y sus referencias no cambian

### Requirement: Datos locales sin red ni persistencia

La aplicación MUST obtener los datos de estructuras locales en memoria. En esta etapa MUST NOT depender de peticiones de red ni de `localStorage` para mostrar el catálogo.

#### Scenario: Apertura sin conexión
- **WHEN** se abre `index.html` sin conexión a la red
- **THEN** el catálogo se genera con los libros del conjunto inicial

#### Scenario: Perfil de navegador sin datos guardados
- **WHEN** se abre la aplicación en un perfil de navegador que nunca almacenó datos del proyecto
- **THEN** se listan los libros del conjunto inicial sin configuración previa

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
