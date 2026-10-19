# registro-libros Specification

## Purpose

Permite registrar libros nuevos con sus relaciones (editorial, género opcional y uno o más autores) y consultar el listado de libros registrados.

## Requirements

### Requirement: Campos del formulario de alta de libro
La vista Libros MUST incluir un formulario de alta con campos etiquetados para título, ISBN y precio, y un botón de envío "Registrar libro".

#### Scenario: Campos básicos
- **WHEN** se abre la vista Libros
- **THEN** el formulario muestra los campos "Título", "ISBN" y "Precio" con sus etiquetas y el botón "Registrar libro"

### Requirement: Selección de editorial
El formulario de libro MUST ofrecer la editorial mediante un selector cuya opción inicial no seleccione ninguna editorial.

#### Scenario: Editorial sin elegir
- **WHEN** se abre la vista Libros
- **THEN** el selector "Editorial" muestra una opción inicial que invita a elegir, seguida de las editoriales de ejemplo

### Requirement: Selección de género opcional
El formulario de libro MUST ofrecer el género mediante un selector que incluya la opción «Sin clasificar», que representa la ausencia de género y es la opción inicial.

#### Scenario: Opción Sin clasificar
- **WHEN** se despliega el selector "Género"
- **THEN** la primera opción es «Sin clasificar», con valor vacío, seguida de los géneros de ejemplo

### Requirement: Selección de uno o más autores
El formulario de libro MUST permitir elegir uno o más autores mediante casillas de verificación agrupadas en un `<fieldset>` cuya leyenda indique que se requiere al menos uno.

#### Scenario: Varios autores
- **WHEN** se marcan dos casillas del grupo "Autores"
- **THEN** ambas quedan marcadas a la vez y cada casilla tiene su etiqueta con el nombre del autor

### Requirement: Listado de libros registrados
La vista Libros MUST mostrar una tabla de libros registrados con columnas título, ISBN, editorial, género, autores y precio, con datos de ejemplo en la etapa 1.

#### Scenario: Tabla de libros
- **WHEN** se abre la vista Libros
- **THEN** la tabla lista los libros de ejemplo, incluido uno con género «Sin clasificar» y uno con varios autores

### Requirement: Mensajes de la vista Libros
La vista Libros MUST incluir, ocultos por defecto, un mensaje de listado vacío y uno de alta correcta con `role="status"`, y un mensaje de alta rechazada con `role="alert"` ubicado junto al formulario y capaz de listar los errores.

#### Scenario: Mensajes presentes
- **WHEN** se inspecciona el HTML de la vista Libros
- **THEN** existen los mensajes de listado vacío, alta correcta y alta rechazada, todos con `hidden`
