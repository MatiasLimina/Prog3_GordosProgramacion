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
