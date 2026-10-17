# 02 — Descripción general

## Stack
- **HTML5** semántico, **CSS3** (Flexbox/Grid, archivos externos), **JavaScript nativo** (ES modules opcional, sin dependencias).
- Prohibido: librerías, frameworks, CDNs de CSS/JS, npm, build tools.
- Persistencia: `localStorage` del navegador (Ej. 6).
- Recursos (estilos, scripts, imágenes) incluidos localmente.

## Arquitectura general
Aplicación web estática, 100 % cliente. Se abre `index.html` directamente en el navegador, sin servidor ni instalación. Puede ser multipágina o secciones de una sola página. Estructura / estilos / comportamiento separados (HTML / `css/` / `js/`).

## Integraciones externas
Ninguna. Se toma como contexto el TP backend de otro docente, pero no hay conexión con él.

## Verificación (sin tests automáticos)
**El proyecto NO tiene suite de tests ni test runners.** La verificación es:
1. Casos manuales reproducibles (tabla del Ej. 6, ver 07/09), con el resultado real registrado en el README.
2. Validación W3C del HTML.
3. Comprobación manual de teclado y anchos 320 px / 1280 px.
Nunca se marca un caso como aprobado sin ejecutarlo.

## Entrega
`index.html`, demás HTML, `css/`, `js/`, recursos locales y `README.md` (autores, cómo abrir sin npm, navegación, funcionalidades implementadas/pendientes, ubicación de datos iniciales, límites de localStorage, casos manuales, procedencia de imágenes ajenas).
