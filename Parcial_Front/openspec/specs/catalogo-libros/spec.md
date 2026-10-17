# catalogo-libros Specification

## Purpose

Presenta el catálogo de la librería: el listado de libros con sus datos descriptivos y un buscador por título, junto con los estados de lista vacía y de búsqueda sin resultados.

## Requirements

### Requirement: Buscador por título
La vista Catálogo MUST incluir un formulario de búsqueda con `role="search"`, un campo de texto etiquetado para buscar por título y un botón "Buscar".

#### Scenario: Buscador accesible
- **WHEN** se abre la vista Catálogo
- **THEN** se ve un campo "Buscar por título" con su etiqueta y un botón "Buscar", alcanzables con Tab

### Requirement: Datos de cada libro del catálogo
Cada libro del catálogo MUST mostrar título, ISBN, editorial, género, autores y precio con dos decimales. Un libro con varios autores MUST mostrarlos todos.

#### Scenario: Libro completo
- **WHEN** se observa un libro del catálogo
- **THEN** se leen su título, ISBN, editorial, género, autores y precio con dos decimales, cada dato con su rótulo

#### Scenario: Libro con varios autores
- **WHEN** se observa un libro de ejemplo con más de un autor
- **THEN** se leen todos sus autores

### Requirement: Libro sin género
Un libro sin género asignado MUST mostrar «Sin clasificar» en el lugar del género.

#### Scenario: Libro sin clasificar
- **WHEN** se observa el libro de ejemplo que no tiene género
- **THEN** su género se muestra como «Sin clasificar»

### Requirement: Datos de ejemplo del catálogo
En la etapa 1 el catálogo MUST mostrar datos estáticos de ejemplo que incluyan al menos un libro sin género y al menos un libro con varios autores.

#### Scenario: Ejemplos mínimos
- **WHEN** se abre la vista Catálogo
- **THEN** se listan libros de ejemplo, al menos uno «Sin clasificar» y al menos uno con varios autores

### Requirement: Estados del catálogo
La vista Catálogo MUST incluir, ocultos por defecto, un mensaje de catálogo vacío y un mensaje de búsqueda sin resultados, ambos con `role="status"`.

#### Scenario: Mensajes del catálogo
- **WHEN** se inspecciona el HTML de la vista Catálogo
- **THEN** existen un mensaje de catálogo vacío y uno de búsqueda sin resultados, con `hidden` y `role="status"`
