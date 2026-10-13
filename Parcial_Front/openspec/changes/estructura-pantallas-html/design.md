# Design

## Context

Repo sin código de frontend: no existen `index.html`, `css/` ni `js/` (solo `docs/`, `knowledge-base/`, `openspec/`). Motivación y alcance en `proposal.md`; requisitos en `specs/*/spec.md`.

Restricciones que condicionan el enfoque (`CLAUDE.md`, KB 08):

- Solo HTML/CSS/JS nativos, recursos locales, sin npm/CDN/build; se abre `index.html` con doble clic (`file://`).
- Sin tests automáticos: verificación manual + W3C Nu HTML Checker.
- CSS solo en archivos externos de `css/`; JS (cuando llegue) inserta texto de usuario con `textContent`, nunca `innerHTML`.
- Este change es solo maqueta: el HTML debe servirle a C-03/C-04/C-05 sin reescrituras, y a C-02 para estilizar sin tocar estructura.

## Goals / Non-Goals

**Goals:**
- Fijar la organización de páginas (decisión 1) y un contrato de hooks estable para JS (decisión 2).
- Que cada página valide sola en W3C y se recorra completa con teclado.
- Datos de ejemplo coherentes entre las 5 vistas (mismos libros, clientes y la venta 2 × 1500 + 1 × 2000 = 5000).

**Non-Goals:**
- Identidad visual, Flexbox/Grid y adaptación 320/1280 px (C-02).
- Cualquier `<script>`, evento, validación, render dinámico o `localStorage` (C-03..C-06).
- Formato definitivo de id/fecha de venta y claves de `localStorage` (C-05/C-06; KB 10 #2, #3).
- README (C-06).

## Decisions

### D1. Multipágina: una página HTML por vista

| Archivo | Vista | `<h1>` |
|---------|-------|--------|
| `index.html` | Catálogo (entrada) | Nombre de la librería; la sección del listado es `h2` "Catálogo de libros" |
| `libros.html` | Libros | "Libros" |
| `clientes.html` | Clientes | "Clientes" |
| `ventas.html` | Ventas | "Nueva venta" |
| `historial.html` | Historial | "Historial de ventas" |

**Por qué multipágina:**
- La navegación funciona sin JS en esta etapa (enlaces reales); con una sola página habría que ocultar/mostrar secciones con JS o depender de `:target`, que no deja una vista "activa" por defecto ni marca el enlace actual.
- Cada página se valida, revisa y prueba de forma independiente; cada `<title>` y `<h1>` identifica la vista y `aria-current="page"` se fija en el HTML estático.
- Los changes C-03..C-05 tocan archivos distintos (menos conflictos entre Agente A y Agente B).
- La persistencia del Ej. 6 vive en `localStorage`, compartido por las páginas del mismo origen, así que no se pierde nada respecto a una SPA. El estado "en memoria" que se pierde al cambiar de página (p. ej. una venta a medio armar) es aceptable: la consigna no exige conservarlo.

**Alternativa descartada — una página con 5 `<section>`:** menos duplicación de header/nav/footer, pero sin JS todas las vistas se ven a la vez (o hay que usar `:target`, frágil y sin estado inicial), un único archivo muy largo concentra todos los cambios futuros y el foco/`aria-current` requieren JS desde el día 1.

**Costo asumido:** header/nav/footer se repiten en 5 archivos. Mitigación: bloque compartido idéntico (D5) copiado de `index.html` y verificado en la tarea de recorrido de navegación.

**Detalle del historial sin JS:** cada fila del listado tiene un enlace `<a href="#detalle-venta-{id}">Ver detalle</a>` que salta a un `<article id="detalle-venta-{id}">` dentro de la sección `#historial-detalles` (debajo del listado). Cada detalle tiene un enlace "Volver al listado" (`href="#historial-listado"`). Se descartó `<details>/<summary>` dentro de la tabla porque mete una tabla de renglones dentro de una celda (ilegible a 320 px) y complica el render de C-05. En C-05, JS puede reutilizar el mismo marcado (por ejemplo, mostrando solo el detalle seleccionado) sin cambiar ids. "Ver detalle" es un enlace (navega) y no un `<button>`: es la semántica correcta para un salto dentro de la página.

### D2. Convención de hooks para JavaScript

Reglas generales:

| Hook | Convención | Ejemplo |
|------|-----------|---------|
| Vista actual | `data-vista` en `<body>` | `<body data-vista="ventas">` |
| `id` | kebab-case, prefijo de vista o entidad; único por página | `libro-isbn`, `historial-lista` |
| `name` | nombre de la propiedad del modelo en camelCase (KB 04) | `editorialId`, `autorIds` |
| Filas / ítems | `data-{entidad}-id` con el id del modelo | `<tr data-libro-id="3">` |
| Celdas a rellenar | `data-campo` = propiedad del modelo (camelCase) | `<td data-campo="isbn">` |
| Acciones delegadas | `data-accion` en kebab-case | `data-accion="quitar-renglon"` |
| Mensajes de estado | `id="{vista}-mensaje-{estado}"` + `data-estado` + `hidden` + `role` | ver tabla de mensajes |
| Destinos de render | `id` en el `<ul>`/`<tbody>`/contenedor que JS vacía y rellena | `<tbody id="clientes-lista">` |
| Plantillas | `<template id="plantilla-{nombre}">` al final de `<main>` | `plantilla-fila-cliente` |
| Clases CSS | solo para estilo, BEM liviano en español: `bloque__elemento--modificador` | `mensaje--error` |

Reglas de uso:
- **JS selecciona por `id`, `name` y `data-*`, nunca por clase** (las clases son de C-02 y pueden cambiar).
- Mostrar/ocultar siempre con el atributo `hidden` (el CSS garantiza `[hidden] { display: none !important; }`).
- Las plantillas no llevan `id` ni `for` (deben ser únicos y validar); JS los asigna al clonar. Los textos se cargan con `textContent` sobre `[data-campo]`.
- Formularios de alta y venta con `novalidate` + atributos semánticos (`required`, `type`, `min`, `step`): la validación la hace JS (Ej. 4/5 exigen `preventDefault` y errores propios); sin JS el envío solo recarga la página.
- Los valores de los `<option>`/checkboxes de ejemplo son ids del modelo; C-04 regenera esas opciones desde los datos.

Hooks por vista:

**Comunes (las 5 páginas)**

| Elemento | id | Otros hooks |
|----------|----|-------------|
| Enlace de salto | — | `href="#contenido"` |
| `<main>` | `contenido` | — |
| Aviso de maqueta | `aviso-maqueta` | se quita/oculta cuando la vista sea funcional |
| Enlace activo del nav | — | `aria-current="page"` |

**Catálogo (`index.html`, `data-vista="catalogo"`)**

| Elemento | id | name / data-* |
|----------|----|---------------|
| Form de búsqueda (`role="search"`) | `catalogo-busqueda` | — |
| Input `type="search"` "Buscar por título" | `catalogo-buscar` | `name="busqueda"` |
| Botón "Buscar" (`type="submit"`) | — | — |
| Lista de libros `<ul>` | `catalogo-lista` | `<li data-libro-id>` con `<article>` |
| Datos de la tarjeta (`<dl>`/`<dd>`) | — | `data-campo="titulo\|isbn\|editorial\|genero\|autores\|precio"` |
| Mensaje vacío | `catalogo-mensaje-vacio` | `data-estado="vacio"`, `role="status"` |
| Mensaje sin resultados | `catalogo-mensaje-sin-resultados` | `data-estado="sin-resultados"`, `role="status"` |
| Plantilla | `plantilla-tarjeta-libro` | — |

**Libros (`libros.html`, `data-vista="libros"`)**

| Elemento | id | name / data-* |
|----------|----|---------------|
| Form | `form-libro` | `novalidate` |
| Título | `libro-titulo` | `name="titulo"` |
| ISBN | `libro-isbn` | `name="isbn"` |
| Precio (`type="number" min="0.01" step="0.01"`) | `libro-precio` | `name="precio"` |
| Editorial (select; 1.ª opción `value=""` "Elegí una editorial") | `libro-editorial` | `name="editorialId"` |
| Género (select; 1.ª opción `value=""` «Sin clasificar») | `libro-genero` | `name="generoId"` |
| Autores `<fieldset>` / contenedor de casillas | `libro-autores` / `libro-autores-opciones` | casillas `id="libro-autor-{id}"`, `name="autorIds"`, `value="{id}"` |
| Botón "Registrar libro" (`type="submit"`) | — | — |
| Mensaje ok | `libros-mensaje-ok` | `data-estado="ok"`, `role="status"` |
| Mensaje error + lista de errores | `libros-mensaje-error` / `libros-errores` | `data-estado="error"`, `role="alert"` |
| `<tbody>` de libros | `libros-lista` | `<tr data-libro-id>`, celdas `data-campo` (como catálogo) |
| Mensaje vacío | `libros-mensaje-vacio` | `data-estado="vacio"`, `role="status"` |
| Plantilla | `plantilla-fila-libro` | — |

**Clientes (`clientes.html`, `data-vista="clientes"`)**

| Elemento | id | name / data-* |
|----------|----|---------------|
| Form | `form-cliente` | `novalidate` |
| Nombre completo | `cliente-nombre-completo` | `name="nombreCompleto"`, `autocomplete="name"` |
| Email (`type="email"`) | `cliente-email` | `name="email"`, `autocomplete="email"` |
| Botón "Registrar cliente" (`type="submit"`) | — | — |
| Mensaje ok / error + lista | `clientes-mensaje-ok` / `clientes-mensaje-error` / `clientes-errores` | `data-estado="ok\|error"`, `role="status\|alert"` |
| `<tbody>` de clientes | `clientes-lista` | `<tr data-cliente-id>`, `data-campo="nombreCompleto\|email"` |
| Mensaje vacío | `clientes-mensaje-vacio` | `data-estado="vacio"`, `role="status"` |
| Plantilla | `plantilla-fila-cliente` | — |

**Ventas (`ventas.html`, `data-vista="ventas"`)** — un solo `<form id="form-venta" novalidate>` con tres `<fieldset>`: Cliente, Agregar renglón, Renglones.

| Elemento | id | name / data-* |
|----------|----|---------------|
| Cliente (select; 1.ª opción `value=""` "Elegí un cliente") | `venta-cliente` | `name="clienteId"` |
| Libro (select; 1.ª opción `value=""` "Elegí un libro"; texto "Título — precio") | `venta-libro` | `name="libroId"` |
| Cantidad (`type="number" min="1" step="1" value="1"`) | `venta-cantidad` | `name="cantidad"` |
| Botón "Agregar renglón" (`type="button"`) | `venta-agregar-renglon` | `data-accion="agregar-renglon"` |
| `<tbody>` de renglones | `venta-renglones` | `<tr data-libro-id>`; celdas `data-campo="titulo\|precioUnitario\|subtotal"` |
| Cantidad del renglón (input + `<label class="visualmente-oculto">Cantidad de «título»</label>`) | `venta-renglon-{libroId}-cantidad` | `name="cantidadRenglon"`, `data-accion="cambiar-cantidad"` |
| Botón "Quitar renglón" (`type="button"`, texto oculto "de «título»") | — | `data-accion="quitar-renglon"` |
| Total (`<output>` en `<tfoot>`) | `venta-total` | `data-campo="total"` |
| Botón "Confirmar venta" (`type="submit"`) | `venta-confirmar` | — |
| Mensaje sin renglones | `venta-mensaje-vacio` | `data-estado="vacio"`, `role="status"` |
| Mensaje ok / error + lista | `venta-mensaje-ok` / `venta-mensaje-error` / `venta-errores` | `data-estado="ok\|error"`, `role="status\|alert"` |
| Plantilla | `plantilla-fila-renglon` | — |

**Historial (`historial.html`, `data-vista="historial"`)**

| Elemento | id | name / data-* |
|----------|----|---------------|
| Sección del listado | `historial-listado` | — |
| `<tbody>` de ventas | `historial-lista` | `<tr data-venta-id>`, `data-campo="id\|fecha\|cliente\|total"` |
| Enlace "Ver detalle" (texto oculto "de la venta {id}") | — | `href="#detalle-venta-{id}"`, `data-accion="ver-detalle"`, `data-venta-id` |
| Contenedor de detalles | `historial-detalles` | — |
| Detalle de una venta `<article>` | `detalle-venta-{id}` | `data-venta-id`; `<dl>` con `data-campo="id\|fecha\|cliente"`; tabla de renglones `data-campo="titulo\|cantidad\|precioUnitario\|subtotal"`; total `data-campo="total"` |
| Mensaje vacío | `historial-mensaje-vacio` | `data-estado="vacio"`, `role="status"` |
| Plantillas | `plantilla-fila-venta`, `plantilla-detalle-venta`, `plantilla-fila-renglon-detalle` | — |

Mensajes (texto base, todos con `hidden` en la maqueta, clase `mensaje mensaje--{info|ok|error}`; los de error empiezan con la palabra "Error:" para no depender del color):

| id | Texto |
|----|-------|
| `catalogo-mensaje-vacio` | No hay libros en el catálogo. |
| `catalogo-mensaje-sin-resultados` | No se encontraron libros con ese título. |
| `libros-mensaje-vacio` / `clientes-mensaje-vacio` | Todavía no hay libros / clientes registrados. |
| `libros-mensaje-ok` / `clientes-mensaje-ok` | Libro / Cliente registrado correctamente. |
| `libros-mensaje-error` / `clientes-mensaje-error` | Error: no se pudo registrar el libro / cliente. Revisá: + `<ul>` vacía |
| `venta-mensaje-vacio` | La venta todavía no tiene renglones. |
| `venta-mensaje-ok` | Venta confirmada correctamente. |
| `venta-mensaje-error` | Error: no se pudo confirmar la venta. Revisá: + `<ul>` vacía |
| `historial-mensaje-vacio` | Todavía no hay ventas confirmadas. |

Los mensajes de alta/venta se ubican dentro del `<form>`, inmediatamente antes del botón de envío ("errores cerca del formulario", RN-13).

**Alternativa descartada:** un único contenedor por vista con `data-estado` cambiante. Un elemento por estado es más fácil de verificar en el HTML estático (la consigna pide que los mensajes estén presentes) y JS solo alterna `hidden`.

### D3. Estructura compartida de cada página (orden del DOM)

1. `<!doctype html>`, `<html lang="es">`, `<meta charset="utf-8">`, viewport, `<title>{Vista} — Librería Papel y Tinta</title>`, `<link rel="stylesheet" href="css/estilos.css">`.
2. `<body data-vista="…">` → `<a class="salto" href="#contenido">Saltar al contenido</a>`.
3. `<header class="encabezado">` con la marca `<p class="encabezado__marca"><a href="index.html">Librería Papel y Tinta</a></p>` y `<nav aria-label="Principal"><ul>` con Catálogo, Libros, Clientes, Ventas, Historial (en ese orden).
4. `<main id="contenido">` → `<h1>` → aviso de maqueta → `<section aria-labelledby>` por bloque (formulario, listado) → `<template>`s al final.
5. `<footer class="pie">`: "TPI Programación III — datos ficticios, sin backend."

Toda tabla: `<div class="tabla-contenedor">` → `<table>` con `<caption>`, `<thead>`, `<th scope="col">` y, cuando hay total, `<tfoot>` con `<th scope="row">`. El contenedor se crea ahora para que C-02 le dé scroll propio sin tocar el HTML.

Importes: texto con dos decimales y punto, sin símbolo de moneda (KB 09), igual a lo que producirá `toFixed(2)`. Fechas: `<time datetime="AAAA-MM-DD">DD/MM/AAAA</time>`.

### D4. Datos de ejemplo (coherentes en las 5 vistas)

Ilustrativos: C-03 define el seed definitivo (≥ 6 libros) y puede reutilizarlos. Nombre de la librería "Librería Papel y Tinta" (supuesto, cambiable).

- Editoriales: 1 Ediciones del Sur, 2 Editorial Faro. Géneros: 1 Novela, 2 Ensayo. Autores: 1 Ana Ríos, 2 Bruno Paz, 3 Carla Vega.
- Libros:

| id | Título | ISBN | Precio | Editorial | Género | Autores |
|----|--------|------|--------|-----------|--------|---------|
| 1 | El jardín de las horas | 978-950-000-001-1 | 1500.00 | Ediciones del Sur | Novela | Ana Ríos |
| 2 | Mapas del silencio | 978-950-000-002-8 | 2000.00 | Editorial Faro | Ensayo | Bruno Paz, Carla Vega |
| 3 | Cuentos de medianoche | 978-950-000-003-5 | 3200.50 | Ediciones del Sur | Sin clasificar | Carla Vega |
| 4 | La ciudad invisible | 978-950-000-004-2 | 2750.00 | Editorial Faro | Novela | Ana Ríos, Bruno Paz |

- Clientes: 1 María Gómez (maria.gomez@example.com), 2 Juan Pérez (juan.perez@example.com), 3 Lucía Fernández (lucia.fernandez@example.com).
- Venta en composición (`ventas.html`): libro 1 × 2 = 3000.00, libro 2 × 1 = 2000.00, total 5000.00.
- Historial: venta 1 — 01/10/2026 — María Gómez — 5000.00 (mismos renglones); venta 2 — 05/10/2026 — Juan Pérez — 1 × Cuentos de medianoche 3200.50 = 3200.50.

### D5. CSS mínimo y carpeta `js/`

`css/estilos.css` (único archivo) contiene solo lo estructural, sin paleta ni tipografías propias:
- `box-sizing: border-box`; `body` con fuente del sistema, `line-height` legible y `background`/`color` explícitos; contenedor con `max-width` y márgenes.
- `[hidden] { display: none !important; }` y `.visualmente-oculto` (patrón clip para texto solo para lectores).
- `.salto`: oculto hasta recibir foco.
- `nav ul` en fila con `flex-wrap` (sin viñetas); `[aria-current="page"]` en negrita/subrayado (no solo color).
- Campos apilados (`label` en bloque), `fieldset` con espacio.
- `.tabla-contenedor { overflow-x: auto; }`, tablas con `border-collapse` y bordes finos.
- `.mensaje--ok` / `.mensaje--error` con borde (no solo color). No se quita el `outline` de foco.

La identidad visual (colores, tipografía, tarjetas, Grid, 320/1280 px) es C-02, que extiende o reemplaza este archivo.

**`js/` no se crea**: git no versiona carpetas vacías y no hay ningún script en esta etapa; ninguna página incluye `<script>`. C-03 crea `js/` y agrega los `<script>`.

## Risks / Trade-offs

- [Header/nav duplicados en 5 archivos pueden divergir] → copiar el bloque desde `index.html` y verificar en la tarea de recorrido que los 5 nav son idénticos salvo `aria-current`.
- [Sin JS, los formularios hacen un envío GET que recarga la página con parámetros en la URL] → aceptable en la maqueta; el aviso de maqueta lo explica y C-03..C-05 interceptan con `preventDefault`.
- [Enter en "Cantidad" envía el formulario de venta (dispara "Confirmar venta")] → C-05 debe tratar Enter dentro del fieldset "Agregar renglón" como "Agregar renglón"; la validación de C-05 igual rechaza una venta incompleta.
- [`type="number"` en precio devuelve `""` ante texto no numérico] → C-04 distingue vacío/no numérico con `validity.badInput` o cambia a `type="text" inputmode="decimal"` (cambio de atributo, no de estructura).
- [Regiones `role="status"`/`role="alert"` que pasan de `hidden` a visibles pueden no anunciarse en algunos lectores] → JS debe escribir el texto después de quitar `hidden` (anotado para C-03..C-05).
- [`localStorage` con `file://`: según el navegador, páginas distintas abiertas desde disco podrían no compartir almacenamiento] → C-06 lo verifica en los navegadores usados; si falla, se documenta en el README abrir el proyecto con un servidor estático local.
- [Para C-03: `<script type="module">` no carga desde `file://` en Chrome por CORS] → usar scripts clásicos con `defer` o documentar el servidor local.
- [Datos de ejemplo distintos del seed de C-03] → al llegar JS, el render reemplaza el contenido estático; las plantillas deben reproducir exactamente el marcado de los ejemplos.

## Migration Plan

No aplica (archivos nuevos). Rollback: borrar los 5 HTML y `css/`.

## Open Questions

- Nombre definitivo de la librería ("Librería Papel y Tinta" es un supuesto; cambiarlo solo afecta textos).
- Formato definitivo del identificador y la fecha de venta (KB 10 #2): la maqueta usa ids numéricos y `DD/MM/AAAA`; lo fija C-05 sin cambiar la estructura.
