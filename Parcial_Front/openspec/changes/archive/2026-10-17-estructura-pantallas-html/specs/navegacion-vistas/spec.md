# Spec Delta

## Purpose

Define la estructura común de todas las páginas de la librería: puntos de entrada, landmarks semánticos, navegación entre las cinco vistas y convenciones compartidas de accesibilidad, mensajes de estado y estilos externos.

## ADDED Requirements

### Requirement: Punto de entrada y vistas disponibles
El proyecto SHALL tener `index.html` como punto de entrada y MUST ofrecer cinco vistas: Catálogo, Libros, Clientes, Ventas e Historial, abribles directamente en el navegador sin servidor, npm ni build.

#### Scenario: Apertura del punto de entrada
- **WHEN** se abre `index.html` con doble clic desde el sistema de archivos
- **THEN** se muestra la vista Catálogo con el nombre de la librería y la navegación principal

#### Scenario: Cada vista existe
- **WHEN** se recorren los enlaces de la navegación principal
- **THEN** cada uno de los cinco enlaces abre su vista sin errores 404

### Requirement: Navegación principal entre vistas
Cada vista MUST incluir un `<nav>` con nombre accesible que enlace a las cinco vistas en el mismo orden y con los mismos textos, y SHALL marcar el enlace de la vista actual con `aria-current="page"`. La navegación MUST funcionar sin JavaScript.

#### Scenario: Vista actual identificada
- **WHEN** se abre la vista Ventas
- **THEN** solo el enlace "Ventas" de la navegación tiene `aria-current="page"`

#### Scenario: Navegación sin JavaScript
- **WHEN** se deshabilita JavaScript en el navegador y se usan los enlaces del `<nav>`
- **THEN** se puede llegar a las cinco vistas

### Requirement: Landmarks semánticos
Cada vista MUST contener exactamente un `<header>` de página, un `<nav>` principal, un `<main>` y un `<footer>` de página, y SHALL agrupar su contenido en `<section>` con encabezado. Cada página MUST declarar `lang="es"`, codificación UTF-8, viewport y un `<title>` que identifique la vista.

#### Scenario: Estructura de landmarks
- **WHEN** se inspecciona el HTML de cualquiera de las cinco vistas
- **THEN** contiene `<header>`, `<nav>`, `<main>` y `<footer>`, y cada `<section>` tiene un encabezado `h2` o inferior

#### Scenario: Título de la pestaña
- **WHEN** se abre la vista Clientes
- **THEN** el título de la pestaña menciona "Clientes" y el nombre de la librería

### Requirement: Salto al contenido principal
Cada vista MUST ofrecer como primer elemento enfocable un enlace "Saltar al contenido" que lleve al `<main>`.

#### Scenario: Primer Tab
- **WHEN** se carga una vista y se presiona Tab una vez
- **THEN** el foco queda en "Saltar al contenido" y al activarlo el foco pasa al contenido principal

### Requirement: Aviso de maqueta de la etapa 1
Cada vista MUST mostrar un aviso visible que indique que los datos son de ejemplo y que las operaciones todavía no se guardan, para no presentar controles pendientes como operaciones completas.

#### Scenario: Aviso visible
- **WHEN** se abre cualquiera de las cinco vistas
- **THEN** se lee un aviso de maqueta dentro del contenido principal

### Requirement: Campos con etiqueta asociada
Todo control de formulario MUST tener una etiqueta asociada mediante `<label for>` cuyo valor coincida con el `id` del control; los grupos de opciones MUST usar `<fieldset>` con `<legend>`.

#### Scenario: Revisión de etiquetas
- **WHEN** se hace clic sobre el texto de cualquier etiqueta de formulario
- **THEN** el foco o la selección pasa al control asociado

### Requirement: Botones con texto de acción
Todo botón y todo enlace de acción MUST tener un texto visible que describa la acción; cuando se repite en varias filas, su nombre accesible MUST identificar el elemento afectado.

#### Scenario: Botones repetidos por fila
- **WHEN** un lector de pantalla lista los botones "Quitar renglón" de la vista Ventas
- **THEN** cada uno anuncia el título del libro del renglón que quita

### Requirement: Tablas con encabezados
Toda tabla MUST tener `<caption>`, `<thead>` y celdas `<th>` con atributo `scope`, y SHALL estar envuelta en un contenedor que permita su desplazamiento horizontal propio.

#### Scenario: Revisión de tablas
- **WHEN** se inspecciona cualquier tabla del proyecto
- **THEN** tiene `caption`, `thead` y cada `th` declara `scope="col"` o `scope="row"`

### Requirement: Mensajes de estado presentes en el HTML
Cada lista y cada operación MUST tener en el HTML sus mensajes de estado ocultos con `hidden`: los informativos y de éxito con `role="status"` y los de rechazo con `role="alert"`. El texto MUST describir el estado sin depender del color.

#### Scenario: Mensajes ocultos por defecto
- **WHEN** se abre una vista con datos de ejemplo
- **THEN** sus mensajes de estado existen en el HTML pero no se muestran

#### Scenario: Mensaje revelado
- **WHEN** se quita el atributo `hidden` de un mensaje desde las herramientas del navegador
- **THEN** el mensaje se ve con su texto completo y su rol correspondiente

### Requirement: Estilos externos mínimos
La presentación MUST definirse en hojas de estilo externas dentro de `css/`, sin atributos `style` ni elementos `<style>`, y el atributo `hidden` MUST ocultar siempre el elemento.

#### Scenario: Sin estilos embebidos
- **WHEN** se buscan `style=` y `<style` en los archivos HTML
- **THEN** no hay coincidencias y cada página enlaza `css/estilos.css`

### Requirement: HTML válido
Cada archivo HTML MUST validar sin errores en el W3C Nu HTML Checker.

#### Scenario: Validación W3C
- **WHEN** se sube cada una de las cinco páginas al W3C Nu HTML Checker
- **THEN** el resultado informa 0 errores
