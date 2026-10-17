# Tasks

> Sin tests automáticos (regla dura 1): cada tarea se verifica manualmente en el navegador (320 px, 1280 px, teclado y contraste) y con el W3C Nu HTML Checker si se toca algún archivo HTML. El contrato de hooks (`id`, `name`, `data-*`, `<template>`, `hidden`) fijado en `C-01` debe permanecer intacto.

## 1. Tokens de diseño y base tipográfica en `css/estilos.css`

- [x] 1.1 Definir en `:root` de `css/estilos.css` las variables de identidad visual de `design.md` §D1 (superficies `--color-fondo`, `--color-superficie`, `--color-superficie-alt`; texto `--color-texto`, `--color-texto-secundario`; marca `--color-primario`, `--color-primario-hover`, `--color-secundario`, `--color-foco`; bordes y sombras; colores de estado info/ok/error; pilas tipográficas `--fuente-cuerpo`, `--fuente-titulos`, `--fuente-mono`) y verificar en DevTools que todas se resuelven sin errores ni peticiones externas
- [x] 1.2 Actualizar las reglas base de `body`, encabezados (`h1`, `h2`, `h3` con `clamp()`), enlaces, utilidades `[hidden]`, `.visualmente-oculto`, `.salto` y el indicador `:focus-visible` (`outline: 3px solid var(--color-foco); outline-offset: 2px;`) y verificar con la tecla Tab en `index.html` que el enlace "Saltar al contenido" y todos los controles muestran un foco de alto contraste

## 2. Layout general, cabecera y navegación con Flexbox

- [x] 2.1 Configurar `body` como columna Flex (`min-height: 100dvh`) con `main { flex: 1; width: 100%; }` y contenedores centrados (`max-width: 72rem; padding-inline: clamp(0.75rem, 3vw, 1.5rem)`) y verificar que el `.pie` queda al fondo de la ventana sin generar scroll horizontal en 320 px ni en 1280 px
- [x] 2.2 Estilizar `.encabezado`, `.encabezado__marca` y `<nav aria-label="Principal"><ul>` con Flexbox (`flex-wrap: wrap`), distinguiendo el enlace activo `a[aria-current="page"]` con fondo `--color-primario`, texto claro, `font-weight: 700` y subrayado grueso (no solo color), y verificar en las 5 páginas a 320 px y 1280 px que la navegación se envuelve limpiamente sin truncarse

## 3. Componentes reutilizables: tarjetas, grillas CSS Grid, formularios y botones

- [x] 3.1 Estilizar la grilla `.catalogo-lista` con CSS Grid (`grid-template-columns: repeat(auto-fill, minmax(min(100%, 17.5rem), 1fr)); gap: 1.25rem;`) y las tarjetas `.tarjeta-libro` y `.detalle-venta` (borde superior de acento, sombra sutil, `<dl>` en grilla adaptable con `overflow-wrap: break-word` y precios/ISBN en `--fuente-mono` con `tabular-nums`), verificando en `index.html` y `historial.html` que a 320 px se apilan en 1 columna y a 1280 px forman múltiples columnas
- [x] 3.2 Estilizar los formularios (`#catalogo-busqueda` con Flexbox en línea adaptable, paneles `#form-libro`, `#form-cliente`, `#form-venta`, `fieldset` con `min-width: 0`, `.campo`, `input`, `select`, grupo `.opcion-casilla` con Flexbox) y los botones (`button[type="submit"]` primario y `button[type="button"]` secundario con `:hover:not(:disabled)`), verificando en `libros.html`, `clientes.html` y `ventas.html` que ningún control desborda a 320 px
- [x] 3.3 Estilizar `.aviso-maqueta` y las variantes `.mensaje--info`, `.mensaje--ok` y `.mensaje--error` con fondo, borde izquierdo acentuado y diferenciación por estilo de borde (`solid` vs `dashed`) y texto (no solo color), verificando en DevTools al quitar `hidden` que cada estado se distingue incluso en escala de grises

## 4. Tablas con desplazamiento horizontal propio

- [x] 4.1 Refinar `.tabla-contenedor` (`position: relative; width: 100%; max-width: 100%; overflow-x: auto; border: 1px solid var(--color-borde); border-radius: var(--radio-borde);`) y las reglas de `table`, `caption`, `thead th`, `tbody tr`, `tfoot` e importes (`tabular-nums`, `white-space: nowrap`), verificando en `libros.html`, `clientes.html`, `ventas.html` e `historial.html` a 320 px que la tabla desplaza dentro de `.tabla-contenedor` mientras `document.documentElement.scrollWidth <= document.documentElement.clientWidth`

## 5. Verificación integral manual (320 px, 1280 px, teclado, W3C y contrato de hooks)

- [x] 5.1 Comprobar las 5 páginas (`index.html`, `libros.html`, `clientes.html`, `ventas.html`, `historial.html`) en un viewport de **320 px** y en uno de **1280 px**, verificando que `scrollWidth === clientWidth` en todas y que los textos y controles son legibles
- [x] 5.2 Recorrer las 5 vistas únicamente con el teclado (`Tab`, `Shift+Tab`, `Enter`, `Espacio`) y verificar foco visible en todos los enlaces y controles, ausencia de trampas de foco y correcta lectura visual de los mensajes de error sin depender del color
- [x] 5.3 Verificar que no existen atributos `style=`, etiquetas `<style`, dependencias externas ni imágenes sin `alt` válido, que el contrato de hooks de `C-01` sigue intacto (y validar en W3C Nu HTML Checker si se tocó algún HTML), y registrar el resultado real observado al pie de este archivo

## Resultado observado de la verificación (5.1–5.3) — 2026-10-17

- **5.1 Comprobación en Chromium a 320 px y 1280 px (Chrome CDP)**:
  - `index.html`: a `320 px` (`clientWidth = 305`, `scrollWidth = 305`, `noHorizontalOverflow = true`) `#catalogo-lista` forma `1` columna CSS Grid; a `1280 px` (`clientWidth = 1265`, `scrollWidth = 1265`, `noHorizontalOverflow = true`) forma `3` columnas CSS Grid.
  - `libros.html`: a `320 px` (`clientWidth = 305`, `scrollWidth = 305`, `noHorizontalOverflow = true`) `.tabla-contenedor` activa su propio scroll (`overflowX = "auto"`, `clientWidth = 279`, `scrollWidth = 544`); a `1280 px` (`clientWidth = 1265`, `scrollWidth = 1265`) la tabla entra completa (`1102 px`).
  - `clientes.html`: a `320 px` (`clientWidth = 305`, `scrollWidth = 305`, `noHorizontalOverflow = true`) `.tabla-contenedor` desplaza horizontalmente (`clientWidth = 279`, `scrollWidth = 544`); a `1280 px` (`clientWidth = 1265`, `scrollWidth = 1265`) entra completa (`1102 px`).
  - `ventas.html`: a `320 px` (`clientWidth = 305`, `scrollWidth = 305`, `noHorizontalOverflow = true`) `.tabla-contenedor` dentro de `<fieldset>` desplaza horizontalmente (`clientWidth = 218`, `scrollWidth = 544`) gracias a `fieldset { min-width: 0; }` y `.tabla-contenedor { position: relative; }` (que contiene a los `.visualmente-oculto` con `position: absolute` dentro de las celdas de acción); a `1280 px` (`clientWidth = 1265`, `scrollWidth = 1265`) entra completa (`1006 px`).
  - `historial.html`: a `320 px` (`clientWidth = 305`, `scrollWidth = 305`, `noHorizontalOverflow = true`) las 3 tablas (`.tabla-contenedor` del listado `279/544` y de los 2 detalles `248/544`) desplazan dentro de su contenedor sin ensanchar la página; a `1280 px` (`clientWidth = 1265`, `scrollWidth = 1265`) entran completas (`1102 px` y `1060 px`).
- **5.2 Teclado, foco visible y diferenciación de estados**:
  - `:focus-visible` aplica `outline: 3px solid var(--color-foco)` (`#0f4c81`) con `outline-offset: 2px` en todos los controles y enlaces, incluido `.salto` ("Saltar al contenido") que aparece al primer `Tab`.
  - Enlace activo del `<nav>` (`a[aria-current="page"]`) diferenciado por fondo `#7c2d12`, texto `#ffffff`, `font-weight: 700` y `text-decoration: underline` de `2px`.
  - Al quitar `hidden` en DevTools, `.mensaje--info` (`border-style: solid`, `border-left-width: 5px`, prefijo `ℹ`), `.mensaje--ok` (`border-style: solid`, `border-left-width: 6px`, prefijo `✓`) y `.mensaje--error` (`border-style: dashed`, `border-left-width: 6px`, prefijo `⚠` + texto `"Error: …"`) se distinguen sin depender del color.
- **5.3 Restricciones duras y contrato de hooks**:
  - Los 5 archivos HTML (`index.html`, `libros.html`, `clientes.html`, `ventas.html`, `historial.html`) no requirieron modificaciones (`git status`: `0` cambios en HTML), por lo que mantienen el 100 % del contrato de hooks de `C-01` y los `0` errores del W3C Nu HTML Checker.
  - Búsqueda de `style=`, `<style`, `<script`, `innerHTML` e imágenes sin `alt` en los 5 HTML: `0` coincidencias; `0` peticiones externas en `css/estilos.css`.
