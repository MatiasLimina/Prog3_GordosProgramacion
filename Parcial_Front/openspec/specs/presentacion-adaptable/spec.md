# presentacion-adaptable Specification

## Purpose

Define la identidad visual coherente de la librería en hojas de estilo externas, la diagramación con Flexbox y CSS Grid, el comportamiento adaptable sin desplazamiento horizontal de página entre 320 px y 1280 px (con desplazamiento propio para tablas) y las garantías de accesibilidad visual en foco, mensajes de estado e imágenes.

## Requirements

### Requirement: Identidad visual coherente y reutilización de clases
El sistema MUST definir en archivos CSS externos dentro de `css/` una identidad visual propia mediante variables CSS (`:root`) para paleta de colores, tipografía, espaciado, bordes y superficies, y SHALL reutilizar las mismas clases para tarjetas, formularios, botones, tablas y mensajes equivalentes en las cinco vistas, sin usar atributos `style` ni etiquetas `<style>`.

#### Scenario: Variables de diseño y clases compartidas
- **WHEN** se inspecciona `css/estilos.css` y las cinco vistas HTML
- **THEN** los colores, tipografías y espaciados provienen de variables CSS en `:root` y los componentes equivalentes comparten clases sin estilos en línea

### Requirement: Diagramación con Flexbox y CSS Grid
El sistema MUST utilizar Flexbox y CSS Grid para organizar el diseño de las vistas: Flexbox para la cabecera, la navegación principal, las barras de acción y las casillas de selección, y CSS Grid para el listado de tarjetas del catálogo y la disposición de metadatos y bloques de contenido.

#### Scenario: Grilla de tarjetas en el catálogo
- **WHEN** se abre la vista Catálogo en un ancho de escritorio (1280 px) y en un ancho móvil (320 px)
- **THEN** `#catalogo-lista` organiza las tarjetas `.tarjeta-libro` mediante CSS Grid en múltiples columnas a 1280 px y en una sola columna a 320 px

#### Scenario: Cabecera y navegación con Flexbox
- **WHEN** se inspecciona `.encabezado` y `<nav aria-label="Principal"><ul>`
- **THEN** sus elementos se distribuyen y envuelven mediante Flexbox manteniendo alineación y separación legibles en ambos anchos

### Requirement: Adaptación a 320 px y 1280 px sin scroll horizontal de página
Todas las vistas MUST presentarse con textos y controles legibles tanto a 320 px como a 1280 px de ancho de ventana y MUST NOT provocar desplazamiento horizontal en el documento (`document.documentElement.scrollWidth <= document.documentElement.clientWidth`).

#### Scenario: Ventana a 320 px de ancho
- **WHEN** se redimensiona el navegador a 320 px de ancho en cualquiera de las cinco vistas
- **THEN** los textos, campos y botones se leen completos sin cortarse y la página no presenta barra de desplazamiento horizontal

#### Scenario: Ventana a 1280 px de ancho
- **WHEN** se redimensiona el navegador a 1280 px de ancho en cualquiera de las cinco vistas
- **THEN** el contenido se centra con un ancho máximo legible, aprovecha el espacio disponible y la página no presenta barra de desplazamiento horizontal

### Requirement: Desplazamiento horizontal propio en tablas
Cuando una tabla requiera más ancho que el disponible en la pantalla (por ejemplo a 320 px), MUST desplazarse horizontalmente dentro de su propio contenedor `.tabla-contenedor` sin ensanchar el `<main>` ni el `<body>`.

#### Scenario: Tabla ancha en 320 px
- **WHEN** se abre `libros.html`, `ventas.html` o `historial.html` con un ancho de 320 px
- **THEN** el contenedor `.tabla-contenedor` permite desplazar horizontalmente la tabla mientras el ancho total de la página permanece en 320 px

### Requirement: Indicador de foco visible en controles interactivos
Todo enlace, botón, campo de entrada, selector y casilla de verificación MUST mostrar un indicador de foco claro y de alto contraste al navegar con el teclado (`:focus-visible`), sin que ninguna regla CSS anule el contorno de foco sin reemplazo visible.

#### Scenario: Recorrido con tecla Tab
- **WHEN** el operador recorre con Tab todos los elementos interactivos de cualquiera de las cinco vistas
- **THEN** cada control enfocado muestra un contorno visible y contrastado que permite identificar dónde está el foco en todo momento

### Requirement: Diferenciación de mensajes de estado sin depender solo del color
Los mensajes de información, éxito y error MUST distinguirse mediante texto explícito y rasgos visuales adicionales al color (grosor o estilo de borde, ícono o prefijo textual), garantizando contraste legible entre texto y fondo.

#### Scenario: Visualización de mensaje de error y de éxito
- **WHEN** se muestran un `.mensaje--error` y un `.mensaje--ok` en un formulario
- **THEN** ambos exhiben contraste suficiente y se diferencian por su texto ("Error: …" frente a confirmación), estilo/grosor de borde y marcador visual, incluso en escala de grises

### Requirement: Texto alternativo en imágenes
Si se incluyen imágenes en las vistas, las imágenes informativas MUST tener un atributo `alt` que describa su contenido o función, y las imágenes meramente decorativas MUST declarar `alt=""` (o `aria-hidden="true"` en SVG decorativos) para no repetir información innecesaria.

#### Scenario: Revisión de imágenes en las cinco vistas
- **WHEN** se inspeccionan los elementos `<img>` o `<svg>` de las cinco páginas
- **THEN** ninguna imagen carece de atributo `alt` válido ni repite textualmente el título adyacente si es decorativa
