# Proposal

## Why

El repositorio todavía no tiene ninguna pantalla: no existen `index.html`, `css/` ni `js/`. El Ejercicio 1 (20 pts: vistas y navegación 10; semántica, formularios y estados 10) es la base del camino crítico `C-01 → C-03 → C-04 → C-05 → C-06` y la etapa 1 de la consigna pide priorizar la maqueta con datos estáticos. Si el HTML no expone desde ahora los ids, `name`, `data-*` y contenedores de estado que usará JavaScript, los changes C-03, C-04 y C-05 tendrían que reescribir el marcado.

## What Changes

- Se crea `index.html` como entrada (vista **Catálogo**) y una página por vista restante: `libros.html`, `clientes.html`, `ventas.html`, `historial.html` (decisión multipágina, ver `design.md`).
- Estructura compartida en cada página: enlace "Saltar al contenido", `<header>` con el nombre de la librería, `<nav>` con las 5 vistas y `aria-current="page"` en la activa, `<main>`, `<footer>` y un aviso visible de que la pantalla es una maqueta de la etapa 1.
- **Catálogo**: buscador por título (`role="search"`, botón "Buscar") y listado de libros de ejemplo con título, ISBN, editorial, género (o «Sin clasificar»), autores y precio.
- **Libros**: formulario de alta (título, ISBN, precio, editorial, género con «Sin clasificar», autores con checkboxes; botón "Registrar libro") y tabla de libros registrados.
- **Clientes**: formulario de alta (nombre completo, email; botón "Registrar cliente") y tabla de clientes registrados.
- **Ventas**: selección de cliente, alta de renglón (libro + cantidad, botón "Agregar renglón"), tabla de renglones con cantidad editable y botón "Quitar renglón", total y botón "Confirmar venta". Ejemplo: 2 × 1500.00 + 1 × 2000.00 = 5000.00.
- **Historial**: tabla de ventas (identificador, fecha, cliente, total, "Ver detalle") y detalle de renglones de cada venta alcanzable sin JavaScript.
- Mensajes presentes en el HTML (ocultos con `hidden`, con `role="status"` o `role="alert"`): lista vacía, búsqueda sin resultados, operación correcta y operación rechazada.
- Convención de hooks para JS (ids, `name`, `data-*`, contenedores de estado, destinos de render y `<template>`), documentada en `design.md` como contrato para C-03..C-05.
- `css/estilos.css` con CSS mínimo de estructura y legibilidad (la identidad visual completa es C-02).
- Sin lógica JS de negocio: no se crea `js/` en este change.

## Capabilities

### New Capabilities
- `navegacion-vistas`: estructura común de todas las páginas (landmarks, navegación entre las 5 vistas, aviso de maqueta, convenciones de accesibilidad y de mensajes de estado, hoja de estilos externa).
- `catalogo-libros`: vista de catálogo con buscador por título, listado de libros y estados de lista vacía / sin resultados.
- `registro-libros`: formulario de alta de libro con sus campos y relaciones, listado de libros registrados y mensajes de resultado.
- `registro-clientes`: formulario de alta de cliente, listado de clientes registrados y mensajes de resultado.
- `venta-simulada`: composición de una venta (cliente, renglones, cantidades, subtotales, total) y su confirmación.
- `historial-ventas`: listado de ventas confirmadas y consulta del detalle de renglones de cada una.

### Modified Capabilities
<!-- Ninguna: openspec/specs/ está vacío. -->

## Impact

- **Archivos nuevos**: `index.html`, `libros.html`, `clientes.html`, `ventas.html`, `historial.html`, `css/estilos.css`.
- **Contrato con changes futuros**: C-02 estiliza sobre las clases definidas acá; C-03, C-04 y C-05 usan los hooks (ids, `name`, `data-*`, `<template>`) sin reescribir el HTML; C-06 documenta en el README qué pantallas son maqueta.
- **Dependencias**: ninguna (sin npm, sin CDN, sin build). Verificación manual + W3C Nu HTML Checker; sin tests automáticos.
- **Governance**: BAJO.
