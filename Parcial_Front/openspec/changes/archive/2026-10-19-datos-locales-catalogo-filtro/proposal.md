# Proposal

## Why

La vista Catálogo (C-01) muestra libros escritos a mano en el HTML y el buscador no hace nada. El Ejercicio 3 de la consigna exige un modelo de datos local con relaciones válidas, un catálogo generado por JavaScript desde ese modelo y un filtro por título funcional. Sin esta base tampoco pueden construirse C-04 (altas) ni C-05 (ventas), que dependen de los mismos arrays y de un render reutilizable.

## What Changes

- Se crea `js/datos.js` con los arrays locales de **libros, editoriales, géneros, autores y clientes**, con ids estables y relaciones válidas: ≥ 6 libros, 2 editoriales, 2 géneros, 3 autores y 3 clientes. Se garantiza al menos un libro sin género y al menos uno con varios autores.
- Se crea `js/catalogo.js` con el render del catálogo, el filtro por título y el manejo de eventos de la vista Catálogo.
- Se agregan los `<script defer>` correspondientes a `index.html`; se conserva la plantilla `#plantilla-tarjeta-libro` como único molde de tarjeta.
- El contenido estático de `#catalogo-lista` se reemplaza en tiempo de ejecución por el render de los 6 libros del seed (sin duplicar ítems). El HTML conserva los 4 libros de ejemplo como contenido de respaldo para cuando JavaScript no está disponible.
- El buscador `#catalogo-buscar` pasa a filtrar en vivo (evento `input`) por título, con `trim`, sin distinguir mayúsculas y por coincidencia parcial; el envío del formulario se controla con `preventDefault`. Búsqueda vacía = catálogo completo; sin coincidencias = mensaje visible.
- Se implementan los estados ya presentes en el HTML (`#catalogo-mensaje-vacio`, `#catalogo-mensaje-sin-resultados`): se muestra a lo sumo uno, y la lista se oculta cuando corresponde.
- Todos los valores del modelo se insertan con `textContent`; no se usa `innerHTML`.
- **Fuera de alcance**: `localStorage` (C-06), altas de libros/clientes (C-04), ventas e historial (C-05), y el render de las tablas de `libros.html` y `ventas.html` (siguen con sus datos estáticos hasta C-04/C-05).

## Capabilities

### New Capabilities
- `datos-locales`: modelo de datos local en memoria (libros, editoriales, géneros, autores y clientes) con ids estables, seed mínimo inicial y reglas de integridad referencial que reutilizarán las altas y las ventas.

### Modified Capabilities
- `catalogo-libros`: el catálogo deja de ser estático y pasa a generarse desde `datos-locales`; se agregan el filtro por título funcional, la precedencia de los estados de lista y la inserción segura de texto. Los requisitos de campos visibles, «Sin clasificar», varios autores y precio con dos decimales se conservan.

## Impact

- **Archivos nuevos**: `js/datos.js`, `js/catalogo.js`.
- **Archivos modificados**: `index.html` (etiquetas `<script defer>`; sin cambios de estructura ni de estilos).
- **Sin cambios**: `css/estilos.css`, `libros.html`, `clientes.html`, `ventas.html`, `historial.html`.
- **Restricciones**: HTML/CSS/JS nativos, sin librerías, sin build y sin tests automatizados (verificación manual + W3C). Scripts clásicos con `defer`, no `type="module"`, para que funcione abriendo `index.html` con doble clic (`file://`).
- **Riesgo transitorio**: hasta C-04, `libros.html` y `ventas.html` seguirán mostrando los 4 libros estáticos, mientras el catálogo ya muestra 6. Es una inconsistencia esperada y documentada por el orden del roadmap.
