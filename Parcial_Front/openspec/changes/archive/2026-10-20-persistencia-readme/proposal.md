# Proposal

## Why

C-05 dejó la venta funcionando en memoria: al recargar o navegar se pierden libros, clientes y ventas dados de alta, y el Historial vuelve al seed. El Ejercicio 6 (10 pts) exige persistir libros, clientes y ventas en `localStorage`, recuperarlos sin duplicar el seed ni las ventas, documentar claves y estructura, y entregar un `README.md` con la verificación manual real. Es el cierre del proyecto.

## What Changes

- Se crea `js/persistencia.js` (IIFE, `defer`) que:
  - define claves documentadas: `libreria:libros`, `libreria:clientes`, `libreria:ventas` (JSON).
  - al cargar, si no existe la clave, carga el seed correspondiente; si existe, parsea y reemplaza el array en memoria.
  - expone `window.Persistencia.guardarTodo()` (y por colección) que serializa los arrays actuales.
  - se carga **antes** que `datos.js`? No: `datos.js` define los arrays; `persistencia.js` debe leer/escribir esos arrays. Se carga después de `datos.js` y antes de las vistas, invocando la carga inicial al inicializar.
- Se modifican `js/datos.js`, `js/altas.js`, `js/ventas.js` para llamar a `Persistencia.guardar...` tras cada mutación (alta de libro/cliente/venta). Los arrays siguen siendo los mismos por referencia.
- Se modifican `js/catalogo.js`? No; solo lee `Datos.libros`.
- Se quitan los avisos de maqueta de `index.html`, `libros.html`, `clientes.html` (C-06 es dueño de la revisión final).
- Se crea `README.md` en la raíz con: integrantes, cómo abrir `index.html` sin npm, navegación, funcionalidades implementadas, ubicación de datos iniciales, claves/estructura de `localStorage` (para la prueba del precio histórico), funcionamiento y límites de `localStorage`, procedencia de imágenes (no se usan imágenes ajenas), y la tabla de resultados reales observados de la verificación manual.
- Se registra el resultado real de los casos manuales (07 §Verificación) en el README y en tasks.md.

## Capabilities

### New Capabilities
Ninguna.

### Modified Capabilities
- `datos-locales`: persistencia en `localStorage`, primer inicio carga ejemplos, reaperturas recuperan sin duplicar.

## Impact

- **Archivos nuevos**: `js/persistencia.js`, `README.md`.
- **Archivos modificados**: `js/datos.js` (integración con persistencia), `js/altas.js`, `js/ventas.js`, `index.html`, `libros.html`, `clientes.html` (quitar aviso de maqueta y cargar persistencia).
- **Sin cambios**: `css/estilos.css`.
- **Datos**: `localStorage` con claves `libreria:libros`, `libreria:clientes`, `libreria:ventas`.
- **Restricciones**: HTML/CSS/JS nativos, sin librerías, sin npm ni build. Sin `innerHTML`.
- **Verificación**: casos manuales de F6 + tabla de verificación de 07 + W3C + teclado + 320/1280 px.