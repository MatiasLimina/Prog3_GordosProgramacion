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

El catálogo MUST generarse desde el conjunto de datos local e incluir al menos 6 libros, con al menos uno sin género y al menos uno con varios autores. El contenido estático del HTML SHALL ser reemplazado por el render, sin duplicar en la lista los libros ya presentes en el marcado.

#### Scenario: Ejemplos mínimos
- **WHEN** se abre la vista Catálogo
- **THEN** se listan al menos 6 libros, al menos uno «Sin clasificar» y al menos uno con varios autores

#### Scenario: Reemplazo sin duplicados
- **WHEN** se cuentan las tarjetas visibles con el buscador vacío
- **THEN** hay exactamente una tarjeta por libro del conjunto de datos local, sin repetir los libros de ejemplo que ya estaban escritos en el HTML

### Requirement: Estados del catálogo

La vista Catálogo MUST conservar un mensaje de catálogo vacío y uno de búsqueda sin resultados, ambos con `role="status"` y ocultos por defecto. MUST mostrarse como máximo un mensaje a la vez: el de vacío cuando no hay ningún libro en los datos, el de sin resultados cuando el filtro no coincide con ningún libro, y ninguno cuando hay resultados. La lista MUST ocultarse cuando se muestra un mensaje y mostrarse cuando hay resultados.

#### Scenario: Mensajes del catálogo
- **WHEN** se inspecciona el HTML de la vista Catálogo
- **THEN** existen un mensaje de catálogo vacío y uno de búsqueda sin resultados, con `hidden` y `role="status"`

#### Scenario: Búsqueda sin coincidencias
- **WHEN** se escribe `zzz` en el buscador
- **THEN** se muestra el mensaje de búsqueda sin resultados, la lista queda oculta y el mensaje de catálogo vacío permanece oculto

#### Scenario: Búsqueda vacía
- **WHEN** el buscador está vacío o solo contiene espacios
- **THEN** se muestran todos los libros y ambos mensajes quedan ocultos

#### Scenario: Limpiar una búsqueda sin coincidencias
- **WHEN** se borra el texto de una búsqueda que no tenía resultados
- **THEN** la lista vuelve a mostrar todos los libros y ambos mensajes quedan ocultos

#### Scenario: Catálogo sin libros
- **WHEN** el conjunto de datos local no tiene ningún libro
- **THEN** se muestra el mensaje de catálogo vacío, el de sin resultados permanece oculto y la lista queda oculta

### Requirement: Catálogo generado desde los datos locales

Al abrir la vista Catálogo, JavaScript MUST generar el listado de libros a partir del conjunto de datos local, una tarjeta por libro y en el orden de los datos, reutilizando el molde de tarjeta ya presente en el HTML.

#### Scenario: Generación del listado
- **WHEN** se abre `index.html` con JavaScript habilitado
- **THEN** la lista del catálogo contiene una tarjeta por cada libro del conjunto de datos local

#### Scenario: Molde único de tarjeta
- **WHEN** se inspecciona el marcado de cualquier tarjeta generada
- **THEN** tiene la misma estructura que la plantilla de tarjeta del HTML: título, ISBN, editorial, género, autores y precio, cada dato con su rótulo

### Requirement: Filtro por título

El buscador MUST filtrar por título con coincidencia parcial, sin distinguir mayúsculas y minúsculas, y eliminando los espacios de los extremos de la búsqueda. El filtro MUST aplicarse al escribir y al enviar el formulario, y el envío MUST controlarse con `preventDefault` para no recargar la página.

#### Scenario: Mayúsculas y coincidencia parcial
- **WHEN** se escribe `JARDÍN` en el buscador
- **THEN** se muestra el libro cuyo título contiene «jardín», sin importar las mayúsculas

#### Scenario: Espacios en los extremos
- **WHEN** se escribe `  mapas  ` en el buscador
- **THEN** el resultado es el mismo que con `mapas`: el libro cuyo título contiene «Mapas»

#### Scenario: Envío del formulario
- **WHEN** se envía el buscador con el botón "Buscar" o con Enter
- **THEN** la página no se recarga y el filtro se aplica igual

### Requirement: Inserción segura de texto

Todo valor proveniente de los datos locales MUST insertarse en el DOM como texto. La implementación MUST NOT usar `innerHTML` para insertar datos.

#### Scenario: Texto con caracteres especiales
- **WHEN** un título contiene `<`, `&` o comillas
- **THEN** el carácter se muestra literalmente como texto y no se interpreta como marcado

### Requirement: Responsabilidades reconocibles en el código del catálogo

El código de la vista Catálogo MUST separar los datos, el renderizado del listado y los manejadores de eventos en unidades claramente identificables, de modo que un revisor pueda ubicar cada responsabilidad sin recorrer todo el archivo.

#### Scenario: Revisión de responsabilidades
- **WHEN** se revisa el código JavaScript de la vista Catálogo
- **THEN** se identifican por separado la definición o consulta de datos, la construcción del listado y sus mensajes, y la suscripción a los eventos del buscador
