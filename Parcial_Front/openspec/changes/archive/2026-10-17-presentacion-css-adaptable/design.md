# Design

## Context

Las 5 páginas HTML (`index.html`, `libros.html`, `clientes.html`, `ventas.html`, `historial.html`) ya fueron construidas y validadas en `C-01` con una hoja `css/estilos.css` mínima de estructura. Ver `proposal.md` para la motivación y `specs/presentacion-adaptable/spec.md` para los requisitos.

Restricciones de diseño (`AGENTS.md`, KB 08):
- Prohibido usar frameworks CSS, CDNs (incluyendo Google Fonts), preprocesadores, `<style>` o atributos `style=""`.
- El contrato de hooks DOM de `C-01` (`id`, `name`, `data-*`, `<template>`, `hidden`) es inmutable: `C-03` puede ejecutarse en paralelo con `C-02` sin conflictos si `C-02` trabaja sobre `css/estilos.css` y las clases existentes.

## Goals / Non-Goals

**Goals:**
- Dotar a «Librería Papel y Tinta» de una identidad visual editorial cálida, legible y consistente mediante tokens CSS en `:root`.
- Resolver la maquetación adaptable entre 320 px y 1280 px usando Flexbox y CSS Grid sin media queries innecesarias cuando las primitivas intrínsecas (`auto-fill` + `minmax(min(100%, …), 1fr)`, `flex-wrap`, `clamp()`) lo resuelven de forma más robusta.
- Garantizar 0 px de desborde horizontal de página a 320 px y 1280 px, aislando el scroll horizontal en `.tabla-contenedor`.
- Asegurar contraste WCAG AA (≥ 4.5:1 en texto normal, ≥ 3:1 en bordes de controles e indicadores `:focus-visible`) y diferenciación no cromática en estados.

**Non-Goals:**
- Agregar modo oscuro o conmutadores de tema (no requerido por la consigna).
- Modificar `id`, `name`, `data-*` o la estructura de `<template>` fijada en `C-01`.
- Incorporar JavaScript (corresponde a `C-03..C-06`).

## Decisions

### D1. Sistema de tokens en `:root` (identidad «Librería Papel y Tinta»)

Se organiza `:root` en dos niveles simples (paleta base + tokens semánticos de interfaz) dentro de `css/estilos.css`, inspirados en papel editorial cálido y tinta azul-pizarra/terracota de alto contraste:

- **Superficies y fondos**:
  - `--color-fondo`: `#faf6f0` (papel cálido claro para el fondo de página)
  - `--color-superficie`: `#ffffff` (tarjetas, tablas, paneles de formulario)
  - `--color-superficie-alt`: `#f2ebe1` (encabezados de tabla, bloques secundarios, hover suave)
- **Texto**:
  - `--color-texto`: `#1f1c18` (tinta carbón; contraste > 14:1 sobre `--color-fondo` y `--color-superficie`)
  - `--color-texto-secundario`: `#524a40` (rótulos `<dt>`, metadatos, pie de página; contraste > 7:1)
- **Marca y acentos**:
  - `--color-primario`: `#7c2d12` (terracota/borgoña editorial para botones primarios, enlaces activos y acentos; contraste > 8:1 con texto `#ffffff`)
  - `--color-primario-hover`: `#5c1f0b`
  - `--color-secundario`: `#1e3a5f` (azul tinta para enlaces e indicadores informativos)
  - `--color-foco`: `#0f4c81` (contorno `:focus-visible` de 3 px con `outline-offset: 2px`)
- **Bordes y sombras**:
  - `--color-borde`: `#cfc5b7`
  - `--color-borde-fuerte`: `#786f63` (bordes de `input`, `select`, `button` con contraste ≥ 3:1)
  - `--radio-borde`: `0.375rem`
  - `--sombra-tarjeta`: `0 1px 3px rgba(31, 28, 24, 0.08)`
- **Estados semánticos (fondo + borde + texto de alto contraste)**:
  - Info / aviso: `--color-info-fondo: #eef4fa`, `--color-info-borde: #1e3a5f`, `--color-info-texto: #142842`
  - Éxito (`ok`): `--color-ok-fondo: #edf7ed`, `--color-ok-borde: #1b5e20`, `--color-ok-texto: #134217`
  - Error (`error`): `--color-error-fondo: #fdf0ef`, `--color-error-borde: #991b1b`, `--color-error-texto: #6b1111`
- **Tipografía (pilas nativas locales, 0 peticiones de red)**:
  - `--fuente-cuerpo`: `system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`
  - `--fuente-titulos`: `Georgia, "Cambria", "Times New Roman", Times, serif` (carácter editorial en `h1`, `h2`, `h3` y `.encabezado__marca`)
  - `--fuente-mono`: `ui-monospace, "Cascadia Mono", "Consolas", monospace` (para ISBN, identificadores e importes tabulares con `font-variant-numeric: tabular-nums`)
  - Escala fluida en títulos con `clamp()` combinando `rem` y `vw` (p. ej. `h1 { font-size: clamp(1.6rem, 1.35rem + 1.2vw, 2.15rem); }`).

**Alternativa descartada:** usar `@import` de Google Fonts. Viola la regla dura 2 (prohibido CDNs; todos los recursos deben ser locales). La combinación de `Georgia` para encabezados literarios y `system-ui` para controles y tablas da carácter de librería sin depender de red.

### D2. Layout con Flexbox y CSS Grid

1. **Estructura de página completa (`body`)**:
   - `display: flex; flex-direction: column; min-height: 100dvh;` con `main { flex: 1; width: 100%; }` para mantener el `.pie` al final de la ventana sin recortes en navegadores móviles (`dvh`).
2. **Cabecera y navegación (`.encabezado`, `<nav>`) — Flexbox**:
   - `.encabezado__contenido` (o `.encabezado` directo) usa `display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.75rem 1.5rem;`.
   - `nav ul` usa `display: flex; flex-wrap: wrap; gap: 0.5rem;` con enlaces tipo píldora/pestaña (`padding: 0.4rem 0.75rem; border-radius: var(--radio-borde)`).
   - El enlace activo (`a[aria-current="page"]`) se distingue por fondo `--color-primario`, texto blanco, `font-weight: 700` y subrayado grueso (`text-decoration: underline; text-underline-offset: 0.25rem`), de modo que no dependa solo del color.
3. **Grilla de tarjetas del catálogo (`.catalogo-lista`) — CSS Grid**:
   - `display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 17.5rem), 1fr)); gap: 1.25rem;`.
   - El uso de `min(100%, 17.5rem)` garantiza que en una ventana de **320 px** (donde el área útil descontando padding es ~288 px) la columna ocupe `100%` sin desbordar jamás, y en **1280 px** se formen automáticamente 3 columnas equilibradas.
4. **Tarjetas (`.tarjeta-libro`, `.detalle-venta`) y listas de definición (`<dl>`) — CSS Grid**:
   - `.tarjeta-libro` usa `display: flex; flex-direction: column; justify-content: space-between; height: 100%;` sobre fondo `--color-superficie`, borde `--color-borde`, borde superior acentuado (`border-top: 4px solid var(--color-primario)`) y sombra sutil.
   - El `<dl>` interno se diagrama con CSS Grid de dos columnas en pantallas ≥ 360 px (`grid-template-columns: minmax(5.5rem, auto) 1fr; gap: 0.35rem 0.75rem`) y se apila limpiamente cuando el espacio es menor, evitando que ISBNs largos rompan el ancho (`overflow-wrap: anywhere`).
5. **Formularios (`#catalogo-busqueda`, `#form-libro`, `#form-cliente`, `#form-venta`) — Flexbox y Grid**:
   - `#catalogo-busqueda` usa Flexbox con `flex-wrap: wrap; align-items: flex-end; gap: 0.75rem;` para que en 1280 px el campo de búsqueda y el botón "Buscar" se alineen en fila y en 320 px el botón pase debajo a ancho completo si no entra.
   - Los formularios de alta (`#form-libro`, `#form-cliente`, `#form-venta`) se presentan como paneles sobre `--color-superficie` con borde y relleno responsivo (`padding: clamp(1rem, 2.5vw, 1.5rem)`), y sus campos `.campo` usan `width: 100%; max-width: 36rem`. En `#libro-autores-opciones`, las casillas `.opcion-casilla` se disponen con Flexbox (`display: flex; flex-wrap: wrap; gap: 0.5rem 1.25rem`) y área de clic cómoda (`min-height: 2.25rem`).
   - Los estados interactivos de botones usan `button:hover:not(:disabled)` para no acoplar el orden de cascada frente a futuros botones deshabilitados.

### D3. Adaptación en 320 px y 1280 px y tablas con scroll propio

- **Prevención de desborde global**:
  - En320 px, el padding lateral de `.encabezado`, `main` y `.pie` se ajusta con `padding-inline: clamp(0.75rem, 3vw, 1.5rem)`.
  - Todos los `input`, `select`, `button` y `fieldset` declaran `max-width: 100%` y `min-width: 0` (crítico en hijos de Flex/Grid, especialmente `<fieldset>`, que en los navegadores tiene un `min-width: min-content` nativo que suele causar scroll horizontal de página si contiene una tabla ancha).
- **Aislamiento del scroll en `.tabla-contenedor`**:
  - `.tabla-contenedor` define `position: relative; width: 100%; max-width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; border: 1px solid var(--color-borde); border-radius: var(--radio-borde); background-color: var(--color-superficie);`. `position: relative` es indispensable para que los elementos `.visualmente-oculto` (`position: absolute`) dentro de las celdas de acciones tengan a `.tabla-contenedor` como bloque contenedor y no escapen al viewport en 320 px.
  - `table` mantiene `width: 100%; min-width: 34rem; border-collapse: collapse;` para que sus columnas (Título, ISBN, Editorial, Género, Autores, Precio, o los renglones editables de Venta) nunca se aplasten de forma ilegible en 320 px, sino que activen limpiamente el scroll horizontal propio de `.tabla-contenedor`.
  - Las celdas de importes (`[data-campo="precio"]`, `[data-campo="precioUnitario"]`, `[data-campo="subtotal"]`, `[data-campo="total"]`) usan `font-variant-numeric: tabular-nums; white-space: nowrap;`.

### D4. Accesibilidad visual: foco, estados sin depender del color e imágenes

- **Foco visible (`:focus-visible`)**:
  - Se mantiene y mejora la regla global `:focus-visible { outline: 3px solid var(--color-foco); outline-offset: 2px; }` verificando buen contraste tanto sobre el fondo claro de la página como en los enlaces de la cabecera.
- **Mensajes de estado no dependientes solo del color**:
  - `.aviso-maqueta` y `.mensaje` comparten estructura base con `border-inline-start-width: 5px` para dar jerarquía inmediata.
  - `.mensaje--info`: borde sólido `--color-info-borde` + prefijo decorativo `::before { content: "ℹ "; font-weight: 700; }`.
  - `.mensaje--ok`: borde sólido doble o grueso `--color-ok-borde` + prefijo decorativo `::before { content: "✓ "; font-weight: 700; }`.
  - `.mensaje--error`: borde discontinuo (`border-style: dashed`, `border-inline-start-style: solid`) `--color-error-borde` + el texto HTML que ya inicia con `"Error: …"` más `::before { content: "⚠ "; font-weight: 700; }`.
- **Imágenes (`img`, `svg`)**:
  - La maqueta actual no requiere imágenes raster externas; se incluye la regla defensiva `img { max-width: 100%; height: auto; display: block; }` en `css/estilos.css` y se verifica en las 5 vistas que no existan `<img>` sin `alt` adecuado.

## Risks / Trade-offs

- [`<fieldset>` con `.tabla-contenedor` adentro en `ventas.html` expande el `<form>` más allá de 320 px por el `min-width: min-content` nativo de `<fieldset>`] → Mitigación: aplicar `min-width: 0; max-width: 100%;` explícito en `fieldset` y `.campo`.
- [Títulos o emails largos (`lucia.fernandez@example.com`) empujan el ancho de tarjeta o celda en 320 px] → Mitigación: aplicar `overflow-wrap: break-word` en tarjetas y mantener `min-width: 34rem` en tablas dentro de `.tabla-contenedor` para que el scroll ocurra dentro del contenedor de tabla y no en la página.
- [Pseudoelementos `::before` con símbolos en `.mensaje` podrían ser leídos de forma verbosa por lectores de pantalla] → Mitigación: el mensaje en el HTML ya contiene el texto semántico ("Error: …", "… correctamente"); si se usa `content` en `::before`, usar texto alternativo vacío `content: "✓ " / "";` con fallback para no ensuciar la lectura accesible, o descansar en los bordes diferenciados (`solid` vs `dashed` + grosor) y el texto existente.

## Migration Plan

El cambio se aplica íntegramente en `css/estilos.css` (sin tocar los hooks de los 5 archivos HTML). Rollback: restaurar la versión de `css/estilos.css` de `C-01`.
