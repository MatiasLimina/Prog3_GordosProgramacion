# Proposal

## Why

En `C-01` (`estructura-pantallas-html`) se construyeron las 5 páginas HTML semánticas con un `css/estilos.css` puramente estructural, sin identidad visual propia ni grilla adaptable. El Ejercicio 2 de la consigna (20 puntos: coherencia y organización 8; adaptación 8; accesibilidad básica 4) exige definir una identidad visual coherente en archivos CSS externos (variables de color, tipografía, espaciado, tarjetas, formularios y botones reutilizando clases), organizar la maqueta con Flexbox y CSS Grid, garantizar legibilidad sin scroll horizontal de página tanto en 320 px como en 1280 px (con scroll propio en tablas) y asegurar foco visible en teclado y diferenciación visual de estados no basada solo en color.

## What Changes

- Se evoluciona `css/estilos.css` (manteniendo un único archivo externo en `css/`, sin `<style>` ni `style=""`) con una identidad visual editorial cálida para «Librería Papel y Tinta» basada en variables CSS (`:root`) para paleta de colores, escala tipográfica, espaciado, bordes y sombras sutiles.
- Se organiza el layout general y los componentes mediante **Flexbox** (encabezado, barra de navegación adaptable, buscador en línea, acciones y grupos de casillas) y **CSS Grid** (grilla adaptable de tarjetas en `#catalogo-lista`, distribución de campos en formularios y paneles de detalle de venta).
- Se estilizan de forma coherente y reutilizable las tarjetas (`.tarjeta-libro`, `.detalle-venta`), los formularios (`fieldset`, `.campo`, `input`, `select`), los botones (primarios de envío y secundarios de acción en fila como «Agregar renglón» y «Quitar renglón»), las tablas dentro de `.tabla-contenedor` y los mensajes de estado (`.aviso-maqueta`, `.mensaje--info`, `.mensaje--ok`, `.mensaje--error`).
- Se garantiza la adaptación responsiva entre **320 px** y **1280 px** sin desplazamiento horizontal en `html`/`body`, permitiendo que las tablas anchas desplacen horizontalmente dentro de su propio contenedor `.tabla-contenedor` (`overflow-x: auto`).
- Se refuerza la accesibilidad visual: indicador `:focus-visible` de alto contraste en todos los enlaces y controles interactivos, distinción de mensajes de error/éxito/información mediante texto, borde e indicador visual (no solo color) y regla explícita sobre texto alternativo en imágenes si se incorporan recursos gráficos.
- Se preserva intacto el contrato de hooks (`id`, `name`, `data-*`, `<template>`, `hidden`) establecido en `C-01` para no interferir con `C-03`, `C-04` y `C-05`.

## Capabilities

### New Capabilities
- `presentacion-adaptable`: identidad visual propia en CSS externo con variables de diseño y clases reutilizadas, diagramación con Flexbox y CSS Grid, adaptación sin scroll horizontal de página en 320 px y 1280 px, desplazamiento horizontal propio para tablas y accesibilidad visual (`:focus-visible`, estados diferenciados más allá del color y criterio de `alt` en imágenes).

### Modified Capabilities
<!-- Ninguna: los requisitos estructurales de navegacion-vistas y de las 5 vistas se mantienen intactos. -->

## Impact

- **Archivos modificados**: `css/estilos.css` (y ajustes menores de clases CSS en `index.html`, `libros.html`, `clientes.html`, `ventas.html`, `historial.html` solo si hiciera falta agregar alguna clase de presentación, sin alterar ids, `name`, `data-*` ni estructura de `<template>`).
- **Contrato con changes futuros**: `C-03`, `C-04` y `C-05` siguen seleccionando exclusivamente por `id`, `name` y `data-*`, y las plantillas `<template>` heredan automáticamente los estilos de `.tarjeta-libro`, `.detalle-venta`, tablas y botones.
- **Dependencias**: ninguna (CSS3 nativo, fuentes locales/del sistema, sin CDNs ni preprocesadores). Verificación manual a 320 px y 1280 px, recorrido con teclado y validación W3C Nu HTML Checker.
- **Governance**: BAJO.
