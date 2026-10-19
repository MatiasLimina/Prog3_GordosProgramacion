# Spec Delta

## ADDED Requirements

### Requirement: Validación de campos obligatorios del libro

El alta de libro MUST rechazarse si el título o el ISBN están vacíos, considerando vacío un valor que solo contiene espacios. La comprobación MUST hacerse en JavaScript al enviar el formulario.

#### Scenario: Título vacío
- **WHEN** se envía el formulario con el título vacío o solo con espacios y el resto de los datos válidos
- **THEN** el alta se rechaza y se muestra un error que indica que el título es obligatorio

#### Scenario: ISBN vacío
- **WHEN** se envía el formulario con el ISBN vacío o solo con espacios y el resto de los datos válidos
- **THEN** el alta se rechaza y se muestra un error que indica que el ISBN es obligatorio

### Requirement: Unicidad del ISBN

El ISBN MUST ser único dentro de los libros existentes. La comparación MUST eliminar los espacios y los guiones del valor ingresado y de cada ISBN existente, y MUST NOT distinguir mayúsculas de minúsculas. No se valida el dígito de control.

#### Scenario: ISBN duplicado con otro formato
- **WHEN** se envía un ISBN que, quitando espacios y guiones, coincide con el de un libro existente
- **THEN** el alta se rechaza y se muestra un error que indica que el ISBN ya existe

#### Scenario: ISBN nuevo
- **WHEN** se envía un ISBN que no coincide con ningún libro existente
- **THEN** la validación del ISBN no produce errores

### Requirement: Validación del precio

El precio MUST ser un número mayor que cero. Un valor vacío MUST rechazarse como error de precio y MUST NOT interpretarse como cero.

#### Scenario: Precio vacío
- **WHEN** se envía el formulario con el precio vacío
- **THEN** el alta se rechaza y se muestra un error que indica que el precio es obligatorio

#### Scenario: Precio no numérico
- **WHEN** se envía un precio que no representa un número
- **THEN** el alta se rechaza y se muestra un error que indica que el precio debe ser un número

#### Scenario: Precio menor o igual que cero
- **WHEN** se envía un precio numérico igual o menor que cero
- **THEN** el alta se rechaza y se muestra un error que indica que el precio debe ser mayor que cero

#### Scenario: Precio válido
- **WHEN** se envía un precio numérico mayor que cero
- **THEN** la validación del precio no produce errores

### Requirement: Validación de editorial y autores

El libro MUST referenciar una editorial existente y al menos un autor, y todos los autores seleccionados MUST existir en los datos locales. La ausencia de editorial, la ausencia de autores y cualquier referencia inexistente MUST rechazar el alta.

#### Scenario: Editorial sin elegir
- **WHEN** se envía el formulario sin elegir editorial
- **THEN** el alta se rechaza y se muestra un error que indica que se debe elegir una editorial

#### Scenario: Editorial inexistente
- **WHEN** el valor de editorial enviado no corresponde a ninguna editorial de los datos locales
- **THEN** el alta se rechaza y se muestra un error que indica que la editorial no existe

#### Scenario: Sin autores seleccionados
- **WHEN** se envía el formulario sin ninguna casilla de autor marcada
- **THEN** el alta se rechaza y se muestra un error que indica que se debe elegir al menos un autor

#### Scenario: Autor inexistente
- **WHEN** alguno de los autores enviados no corresponde a un autor de los datos locales
- **THEN** el alta se rechaza y se muestra un error que indica que el autor no existe

### Requirement: Validación del género opcional

El género MUST ser opcional. Cuando no se elige ninguno MUST interpretarse como «Sin clasificar» y MUST registrarse como ausencia de género. Cuando se elige uno, MUST corresponder a un género existente.

#### Scenario: Género sin clasificar
- **WHEN** se envía el formulario con la opción «Sin clasificar» y el resto de los datos válidos
- **THEN** el alta se acepta y el libro guardado no tiene género asignado

#### Scenario: Género inexistente
- **WHEN** el valor de género enviado no corresponde a ningún género de los datos locales
- **THEN** el alta se rechaza y se muestra un error que indica que el género no existe

### Requirement: Alta efectiva de libro

Solo un alta que supera todas las validaciones MUST incorporar el libro a los datos locales. El libro MUST guardarse con un identificador único, el título y el ISBN normalizados, el precio como número, la editorial, el género asignado si lo hay y todos los autores seleccionados.

#### Scenario: Alta correcta
- **WHEN** se envían datos válidos de un libro nuevo
- **THEN** el libro se agrega a los datos locales con un identificador único y aparece en el listado

#### Scenario: Alta rechazada
- **WHEN** se envían datos que incumplen al menos una validación
- **THEN** ningún libro se agrega a los datos locales y el listado no cambia

### Requirement: Actualización del listado y de los selectores sin recargar

Tras un alta correcta, la página MUST NOT recargarse y el listado de libros MUST reflejar el nuevo registro sin recargar. Los selectores relacionados presentes en la misma página MUST regenerarse desde los datos locales.

#### Scenario: Listado actualizado
- **WHEN** se registra un libro válido
- **THEN** el listado muestra el libro nuevo en la misma página, sin recargar ni navegar

#### Scenario: Formulario limpio
- **WHEN** se registra un libro válido
- **THEN** el formulario vuelve a mostrar la editorial y el género sin elegir, ninguna casilla de autor marcada y los campos de texto vacíos

### Requirement: Estados del formulario de alta de libro

El formulario MUST mostrar como máximo un mensaje de resultado a la vez: el de alta correcta o el de alta rechazada. El mensaje de error MUST listar un ítem por cada error detectado y la lista de errores MUST vaciarse antes de cada intento. Los mensajes MUST conservar sus roles de estado y alerta y su visibilidad MUST controlarse con el atributo `hidden`.

#### Scenario: Errores listados
- **WHEN** se envía un formulario con varios datos inválidos
- **THEN** el mensaje de error queda visible con un ítem por cada error y el mensaje de alta correcta queda oculto

#### Scenario: Reintento
- **WHEN** se vuelve a enviar el formulario después de un intento fallido
- **THEN** la lista de errores anterior se vacía antes de mostrar el resultado del nuevo intento

#### Scenario: Éxito sin errores visibles
- **WHEN** se registra un libro válido
- **THEN** el mensaje de alta correcta queda visible, el de error queda oculto y la lista de errores queda vacía

## MODIFIED Requirements

### Requirement: Selección de editorial

El formulario de libro MUST ofrecer la editorial mediante un selector cuyas opciones MUST generarse desde los datos locales. La primera opción MUST invitar a elegir y MUST NOT seleccionar ninguna editorial.

#### Scenario: Editorial sin elegir
- **WHEN** se abre la vista Libros
- **THEN** el selector "Editorial" muestra una opción inicial que invita a elegir, seguida de las editoriales de los datos locales

#### Scenario: Editoriales generadas desde los datos
- **WHEN** se inspeccionan las opciones del selector "Editorial"
- **THEN** hay una opción por cada editorial de los datos locales, con su nombre como texto y su identificador como valor

### Requirement: Selección de género opcional

El formulario de libro MUST ofrecer el género mediante un selector cuyas opciones MUST generarse desde los datos locales e incluir la opción «Sin clasificar», que representa la ausencia de género y es la opción inicial con valor vacío.

#### Scenario: Opción Sin clasificar
- **WHEN** se despliega el selector "Género"
- **THEN** la primera opción es «Sin clasificar», con valor vacío, seguida de los géneros de los datos locales

#### Scenario: Géneros generados desde los datos
- **WHEN** se inspeccionan las opciones del selector "Género"
- **THEN** hay una opción por cada género de los datos locales, con su nombre como texto y su identificador como valor

### Requirement: Selección de uno o más autores

El formulario de libro MUST permitir elegir uno o más autores mediante casillas de verificación agrupadas en un `<fieldset>` cuya leyenda indique que se requiere al menos uno. Las casillas MUST generarse desde los datos locales, cada una con su etiqueta asociada al nombre del autor.

#### Scenario: Varios autores
- **WHEN** se marcan dos casillas del grupo "Autores"
- **THEN** ambas quedan marcadas a la vez y cada casilla tiene su etiqueta con el nombre del autor

#### Scenario: Autores generados desde los datos
- **WHEN** se inspecciona el grupo "Autores"
- **THEN** hay una casilla por cada autor de los datos locales, identificada de forma única y con el identificador del autor como valor

### Requirement: Listado de libros registrados

La vista Libros MUST mostrar una tabla de libros registrados con columnas título, ISBN, editorial, género, autores y precio. El listado MUST generarse desde los datos locales, una fila por libro, y MUST reemplazar el contenido estático del HTML.

#### Scenario: Tabla de libros
- **WHEN** se abre la vista Libros
- **THEN** la tabla lista los libros de los datos locales, incluido uno con género «Sin clasificar» y uno con varios autores

#### Scenario: Listado generado desde los datos
- **WHEN** se cuentan las filas visibles al abrir la vista Libros
- **THEN** hay exactamente una fila por cada libro de los datos locales, sin repetir las filas de ejemplo del HTML

#### Scenario: Presentación de los campos
- **WHEN** se revisa una fila del listado
- **THEN** el género ausente se muestra como «Sin clasificar», los autores se muestran separados por coma y el precio se muestra con dos decimales

#### Scenario: Listado vacío
- **WHEN** los datos locales no tienen ningún libro
- **THEN** se muestra el mensaje de listado vacío y la tabla no muestra filas

### Requirement: Mensajes de la vista Libros

La vista Libros MUST incluir, ocultos por defecto, un mensaje de listado vacío y uno de alta correcta con `role="status"`, y un mensaje de alta rechazada con `role="alert"` ubicado junto al formulario y capaz de listar los errores.

#### Scenario: Mensajes presentes
- **WHEN** se inspecciona el HTML de la vista Libros
- **THEN** existen los mensajes de listado vacío, alta correcta y alta rechazada, todos con `hidden`

#### Scenario: Mensaje de alta correcta
- **WHEN** se registra un libro válido
- **THEN** el mensaje de alta correcta se muestra y el de alta rechazada permanece oculto

#### Scenario: Mensaje de alta rechazada
- **WHEN** se envía el formulario con datos inválidos
- **THEN** el mensaje de alta rechazada se muestra junto al formulario y el de alta correcta permanece oculto

#### Scenario: Errores como texto
- **WHEN** el mensaje de alta rechazada lista los errores
- **THEN** cada error se muestra como texto literal en un ítem propio, sin interpretarse como marcado
