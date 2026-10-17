# Consigna — Parcial_Front (TPI: frontend de una librería)

Fuente: `Repaso Primer Parcial.pdf` (Programación III, Prof. Matías Torres) + pedido del equipo.

## Restricciones del proyecto

- Solo HTML, CSS y JavaScript nativos. Sin librerías, frameworks, CDNs, npm ni herramientas de build.
- **Sin suite de tests ni test runners.** La verificación es manual (casos reproducibles) + validación W3C del HTML.
- Datos ficticios, simulados en el navegador. Sin API, backend, base de datos ni login real.
- Estructura de entrega: `index.html`, demás HTML, carpetas `css/`, `js/`, recursos locales y `README.md`.

## Ejercicio 1 — Estructura y pantallas HTML (alcance del change `estructura-pantallas-html`)

`index.html` como entrada. Puede ser multipágina o secciones de una sola página, con navegación clara entre las 5 vistas:

- **Catálogo**: título de la librería, buscador por título, listado de libros. Cada libro muestra título, ISBN, editorial, género, autores y precio. Sin género → «Sin clasificar».
- **Libros**: formulario de alta + listado de libros registrados.
- **Clientes**: formulario de alta + listado de clientes registrados.
- **Ventas**: selección de cliente, composición de renglones (libro, cantidad, precio, subtotal) y resumen de la venta (total).
- **Historial**: listado de ventas y acceso al detalle de cada una.

Requisitos:

- `<header>`, `<nav>`, `<main>` (y `<section>`/`<article>`/`<footer>` donde corresponda).
- Cada campo con `<label for>` asociado; botones con texto que describe la acción ("Registrar libro", "Agregar renglón", "Confirmar venta", "Ver detalle"…).
- Tablas con `<thead>`/`<th scope>`.
- Mensajes para: lista vacía, búsqueda sin resultados, operación correcta y operación rechazada (presentes en el HTML, p. ej. con `hidden` y `role="status"`/`role="alert"`).
- Datos estáticos de ejemplo en listados e historial (al menos un libro sin género → «Sin clasificar» y un libro con varios autores).
- Solo estructura HTML semántica + CSS mínimo. Nada de lógica JS de negocio; el HTML deja preparados ids, `name`, `data-*` y contenedores de estado que luego usará JavaScript.

## Campos que el HTML debe anticipar (de los Ejercicios 2–6)

- **Libro**: título, ISBN, precio, editorial (select), género (select con opción «Sin clasificar» = sin género), autores (selección múltiple o checkboxes; al menos uno).
- **Cliente**: nombre completo, email.
- **Venta**: cliente; renglones con libro, cantidad (entero > 0), precio unitario histórico, subtotal; total (dos decimales). Al confirmar: identificador, fecha, cliente, renglones, total. Se pueden cambiar cantidades y quitar renglones antes de confirmar.
- **Historial**: identificador, fecha, cliente y total; consulta de renglones. Ventas confirmadas no se editan ni eliminan.
- CSS (Ej. 2): archivos externos, Flexbox/Grid, 320 px y 1280 px sin scroll horizontal de página, tablas con scroll propio, foco visible, errores no solo por color.

## Texto completo del PDF (referencia)

```text
Tecnicatura Universitaria en
Programación a Distancia
Página 1 de 7Programación III
Materia: Programación III
UNIDAD HTML, CSS Y JAVASCRIPT · REPASO PARA EL PARCIAL 1
TRABAJO PRÁCTICO
TPI: frontend de una librería
Revisor de la unidad: Prof. Matías Torres
Objetivos
Construir interfaces con HTML semántico y CSS propio para un sistema de librería.
Relacionar formularios, listados y navegación con las entidades del proyecto.
Aplicar JavaScript nativo para representar datos locales, modificar el DOM y responder a
eventos.
Validar entradas y comprobar el comportamiento mediante casos manuales reproducibles.
Contexto y alcance
El proyecto representa una librería que presenta su catálogo y registra libros, clientes y ventas.
Se toma como contexto el TP backend de Programación III del otro docente. Esta consigna
desarrolla exclusivamente el frontend: los datos y las operaciones se simulan en el navegador.
Se utilizan únicamente HTML, CSS y JavaScript nativos. Los estilos, scripts, imágenes y demás
recursos se incluyen en el proyecto. No se utilizan librerías, frameworks ni CDNs de CSS o
JavaScript. No se requiere API, base de datos, servidor ni conexión con el backend. Tampoco se
requiere un inicio de sesión real.
Los datos son ficticios. Las validaciones y el almacenamiento del navegador sirven para la
práctica; no representan seguridad ni integridad garantizada por un servidor. La venta registra
cantidades y precios para obtener un total simulado, sin gestionar stock, cobros ni facturación
fiscal.
Organización del trabajo
Etapa 1: inicio durante la semana de repaso. Se priorizan las pantallas del ejercicio 1 y su
presentación del ejercicio 2: navegación, catálogo, alta y listado de libros, alta y listado de
clientes, formulario de venta e historial. Se usan ejemplos estáticos para definir su aspecto. Se
incorpora una interacción básica, como el filtro por título o una validación de formulario. Los
controles pendientes se identifican como parte de la maqueta; no se presentan como
operaciones completas.
Tecnicatura Universitaria en
Programación a Distancia
Página 2 de 7Programación III
20 puntos
Etapa 2: desarrollo del TPI completo. Se conectan las pantallas con datos locales y se
completan los ejercicios 3 a 6, incluidas las validaciones, las ventas y la persistencia.
Los puntajes siguientes corresponden al TPI completo. Esta organización permite comenzar por
la maquetación y no establece contenidos adicionales, fecha ni modalidad de evaluación del
parcial 1.
Consignas
Ejercicio 1 · 1. Estructura y pantallas HTML
Se organiza el proyecto con index.html como entrada. Se permite usar varias páginas o
secciones de una misma página, siempre que exista navegación clara entre las siguientes
vistas:
Catálogo: título de la librería, buscador por título y listado de libros. Cada libro muestra
título, ISBN, editorial, género, autores y precio. Si no tiene género asignado, se muestra
«Sin clasificar».
Libros: formulario de alta y listado de libros registrados.
Clientes: formulario de alta y listado de clientes registrados.
Ventas: selección de cliente, composición de renglones y resumen de la venta.
Historial: listado de ventas y acceso a sus detalles.
Se incluyen encabezado, navegación y contenido principal con etiquetas semánticas.
Cada campo posee una etiqueta asociada; los botones tienen textos que describen su
acción. Las tablas incluyen encabezados. Se incorporan mensajes para listas vacías,
búsquedas sin resultados y operaciones correctas o rechazadas.
Para la primera etapa, los listados y el historial pueden mostrar datos estáticos de ejemplo.
La estructura contempla los campos y estados que luego utiliza JavaScript.
Tecnicatura Universitaria en
Programación a Distancia
Página 3 de 7Programación III
20 puntos
15 puntos
Ejercicio 2 · 2. Presentación con CSS y uso adaptable
Se define una identidad visual propia y coherente: colores, tipografía, espaciado, tarjetas,
formularios y botones. El CSS se mantiene en archivos externos y se reutilizan clases para
elementos equivalentes.
Se utiliza Flexbox o Grid para organizar el contenido. La interfaz se comprueba con un
ancho de 320 px y otro de 1280 px: los textos y controles resultan legibles y el contenido
no provoca desplazamiento horizontal de toda la página. Si una tabla necesita más
espacio, se desplaza dentro de su propio contenedor.
Los controles conservan un foco visible y se recorren con el teclado. Los mensajes de
error se expresan con texto y no dependen únicamente de un color. Las imágenes
informativas tienen texto alternativo; las decorativas no repiten información innecesaria.
Ejercicio 3 · 3. Datos locales, catálogo y filtro
Se representan libros, editoriales, géneros, autores y clientes mediante arrays y objetos
con identificadores estables. El conjunto inicial incluye al menos seis libros, dos
editoriales, dos géneros, tres autores y tres clientes ficticios. Cada libro se relaciona con
una editorial existente y uno o más autores existentes. El género es opcional; si se asigna,
corresponde a un género existente.
JavaScript genera el catálogo a partir del array de libros. El filtro por título ignora
diferencias entre mayúsculas y minúsculas, busca coincidencias parciales y elimina
espacios sobrantes en los extremos de la búsqueda. Una búsqueda vacía muestra todo el
catálogo; una búsqueda sin coincidencias muestra un mensaje claro.
Se utilizan eventos y funciones con responsabilidades reconocibles. Los datos escritos por
usuarios se insertan como texto en el DOM. No se requiere traer datos con fetch ni
administrar altas, bajas y modificaciones de editoriales, géneros o autores.
Tecnicatura Universitaria en
Programación a Distancia
Página 4 de 7Programación III
15 puntosEjercicio 4 · 4. Alta de libros y clientes
El formulario de libros permite registrar título, ISBN, precio y las relaciones con editorial,
género y autores. Las opciones se generan a partir de los datos locales: editorial y género
mediante selectores, y autores mediante un selector múltiple o controles de selección
equivalentes. El selector de género incluye la opción «Sin clasificar», que representa la
ausencia de género.
Se comprueba que el título y el ISBN no estén vacíos, que el ISBN no exista en el conjunto
local, que el precio sea numérico y mayor que cero y que la editorial y todos los autores
seleccionados existan en los datos locales. Se selecciona al menos un autor. El género
puede quedar sin asignar; si se asigna, se verifica que exista en los datos locales. Para
este TPI, el ISBN se compara sin espacios ni guiones; no se requiere implementar su dígito
de control.
El formulario de clientes permite registrar nombre completo y email. No se requiere un
campo de apellido separado. Se comprueba que el nombre completo y el email no estén
vacíos, que el email tenga un formato válido y que no exista otro cliente con el mismo
email, comparado sin espacios exteriores y sin distinguir mayúsculas de minúsculas.
Se controla el envío con preventDefault, se muestran errores cerca del formulario y solo
se agrega el registro si todas las comprobaciones pasan. Tras un alta correcta, el listado y
las opciones relacionadas se actualizan sin recargar la página. No se exige editar ni
eliminar registros.
Tecnicatura Universitaria en
Programación a Distancia
Página 5 de 7Programación III
20 puntosEjercicio 5 · 5. Venta simulada e historial
Se selecciona un cliente existente y se agrega al menos un renglón con un libro existente y
una cantidad entera mayor que cero. No se admiten libros repetidos dentro de la misma
venta: se modifica la cantidad del renglón existente o se informa el duplicado. Antes de
confirmar, se permite cambiar cantidades y quitar renglones.
Cada renglón muestra libro, cantidad, precio unitario y subtotal. Se calcula subtotal como
cantidad por precio y total como suma de subtotales; los importes se presentan con dos
decimales. Se impide confirmar una venta sin cliente, sin renglones o con cantidades
inválidas.
Al confirmar, se registra un identificador, fecha, cliente, renglones y total. El precio unitario
se copia al renglón como valor histórico, de modo que no se obtiene nuevamente desde el
precio actual del catálogo al consultar el historial. Se conservan también los datos
descriptivos necesarios para leer esa venta.
El historial muestra identificador, fecha, cliente y total, y permite consultar los renglones.
Las ventas confirmadas no se editan ni eliminan desde la interfaz. La confirmación limpia
el formulario para una nueva venta y muestra un mensaje de resultado.
Tecnicatura Universitaria en
Programación a Distancia
Página 6 de 7Programación III
10 puntosEjercicio 6 · 6. Persistencia, verificación y documentación
En la etapa final se utiliza localStorage para conservar libros, clientes y ventas. En el
primer inicio se cargan los ejemplos; al volver a abrir se recuperan los registros guardados
sin duplicar los datos iniciales. El README explica que el almacenamiento depende del
navegador, del perfil y de la ubicación de apertura, y que no comparte información entre
usuarios.
Se registra en el README el resultado observado de estos casos manuales:
Caso Resultado esperado
Búsqueda con una parte del título en
mayúsculas; luego búsqueda vacía y
texto inexistente
Coincidencias sin distinguir mayúsculas; catálogo
completo; mensaje sin resultados.
Alta de libro con ISBN existente y luego
con ISBN nuevo
El duplicado se rechaza; el válido aparece en
catálogo y selección de venta.
Alta de cliente con email inválido, email
existente en mayúsculas y email nuevo
Se rechazan los dos primeros; el nuevo aparece en
listado y selección.
Venta sin cliente, cantidad cero,
negativa o decimal; libro repetido
No se confirma; el duplicado no crea otro renglón.
Venta válida: dos unidades a 1500 y una
a 2000
Subtotales 3000 y 2000; total 5000; detalle
conservado en el historial.
Venta confirmada y cambio exclusivo
del precio de catálogo guardado, en
una copia de prueba del proyecto
Al consultar nuevamente el historial después de
recargar, el precio unitario, los subtotales y el total de
esa venta conservan los valores confirmados.
Recarga después de altas y venta Se recuperan datos sin duplicar ejemplos ni ventas.
Navegación por teclado y anchos de
320 px y 1280 px
Foco visible, controles utilizables y tabla con
desplazamiento propio si lo necesita.
La comprobación del precio histórico se realiza de forma guiada por el docente en una
copia del proyecto y con datos de prueba. Se confirma una venta y se anotan sus
importes. Con las herramientas de almacenamiento del navegador, se modifica únicamente
el precio del libro dentro del catálogo guardado en localStorage, sin modificar ni borrar
las ventas guardadas. Se recarga la página y se consulta el detalle de la venta anterior. No
se exige una pantalla para editar precios. La ubicación y estructura del catálogo guardado
se identifican en el README para reproducir esta comprobación.
Si un caso falla o una funcionalidad queda pendiente, se registra el comportamiento real.
No se indica una prueba como aprobada sin ejecutarla.
Tecnicatura Universitaria en
Programación a Distancia
Página 7 de 7Programación III
Criterios de evaluación
La evaluación considera el funcionamiento observado y la correspondencia entre interfaz, datos
y documentación. La maqueta debe facilitar el uso de las operaciones; el diseño no reemplaza
las validaciones.
Ejercicio Distribución de puntos
1. HTML: 20 Vistas y navegación: 10; semántica, formularios y estados: 10.
2. CSS: 20 Coherencia y organización: 8; adaptación: 8; accesibilidad básica: 4.
3. Datos y catálogo:
15
Modelo y ejemplos: 5; renderizado: 5; filtro y estados: 5.
4. Altas: 15 Libros y selectores: 6; clientes: 4; validación y actualización: 5.
5. Ventas: 20 Composición y validaciones: 8; cálculos: 5; confirmación e historial inmutable:
7.
6. Cierre: 10 Persistencia: 4; pruebas manuales registradas: 3; documentación y entrega: 3.
Total 100 puntos
Se valora código legible, nombres comprensibles, funciones acotadas y separación entre
estructura, estilos y comportamiento. El uso de librerías o frameworks incumple el alcance
técnico y se informa en la evaluación; esta consigna no fija penalizaciones adicionales ni un
mínimo de aprobación.
Formato de entrega
Se entrega una carpeta o archivo comprimido con index.html, los demás HTML si
corresponden, carpetas de CSS, JavaScript y recursos locales, y un README.md. No se incluyen
dependencias instaladas ni herramientas de compilación.
El README identifica a quienes realizan el trabajo y contiene: pasos para abrir index.html en el
navegador sin npm; navegación entre vistas; funcionalidades implementadas y pendientes;
ubicación de los datos iniciales; funcionamiento y límites de localStorage; resultados de los
casos manuales y procedencia de imágenes ajenas, si existen.
En un avance de la etapa 1 se identifica expresamente qué pantallas son maquetas y qué
interacciones ya funcionan. La entrega final reúne el alcance completo. El docente comunica por
separado las fechas, el canal de entrega y la modalidad de trabajo.```
