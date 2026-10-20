# Proposal

## Why

`ventas.html` e `historial.html` son todavía maquetas estáticas: la venta de ejemplo está escrita a mano en el HTML, los selects listan 4 libros y 3 clientes fijos y «Confirmar venta» no hace nada. El Ejercicio 5 de la consigna (20 pts) exige componer una venta real sobre los datos locales, calcular subtotales y total, confirmarla con precio unitario histórico y consultarla en el Historial. Es el paso previo obligatorio de C-06, que persiste ventas, libros y clientes.

## What Changes

- Se crea `js/validaciones.js` extendiendo `window.Validaciones` con `validarVenta(entrada, clientes, libros)` (RN-15, RN-16, RN-20), pura, que valida cliente existente, al menos un renglón, libro existente por renglón y cantidad entera > 0.
- Se extiende `js/datos.js` con el seed de las dos ventas de la maqueta (id 1: María Gómez 2×1500 + 1×2000 = 5000; id 2: Juan Pérez 1×3200.50 = 3200.50), `agregarVenta(venta)` y `siguienteId` ya existente. El renglón copia `precioUnitario` y `titulo` históricos al confirmar.
- Se crea `js/ventas.js` (IIFE, `defer`, guardas por hooks) que:
  - reconstruye `#venta-cliente` y `#venta-libro` desde los datos locales, preservando la primera opción literal (`value=""`);
  - implementa «Agregar renglón» (libro + cantidad > 0): si el libro ya está en la venta, **suma la cantidad al renglón existente** (decisión documentada, KB 10 #4);
  - permite cambiar cantidades y quitar renglones; recalcula subtotal (cantidad × precio) y total con 2 decimales;
  - valida y confirma la venta (cliente, renglones, cantidades), registra id entero incremental, fecha ISO 8601 mostrada `dd/mm/aaaa`, cliente (+ nombre), renglones con precio histórico y total; limpia el formulario y muestra el mensaje de resultado.
- Se crea `js/historial.js` que renderiza el listado y los detalles dinámicamente con las `<template>` existentes, sin editar ni eliminar.
- `ventas.html` y `historial.html` cargan los scripts (`datos.js` → `validaciones.js` → `ventas.js`/`historial.js`) y dejan de mostrar las filas estáticas y el aviso de maqueta (las operaciones de venta sí se guardan en memoria en esta etapa).
- Se agregan a `index.html` los scripts de catálogo ya existentes (sin cambios en esta etapa) — sin tocar datos; el aviso de maqueta de `index.html`/`libros.html`/`clientes.html` se elimina en C-06.
- **Fuera de alcance**: persistencia (`localStorage`) y README (C-06); edición/borrado de ventas (RN-23).

## Capabilities

### New Capabilities
Ninguna. Extiende capacidades ya existentes.

### Modified Capabilities
- `venta-simulada`: composición real, cálculos, confirmación y mensajes con comportamiento.
- `historial-ventas`: listado y detalle generados desde los datos locales.
- `datos-locales`: seed de ventas y operación de alta de venta con precio histórico.

## Impact

- **Archivos nuevos**: `js/ventas.js`, `js/historial.js`.
- **Archivos modificados**: `js/datos.js` (seed de ventas + `agregarVenta`), `js/validaciones.js` (validación de venta), `ventas.html`, `historial.html` (scripts y re-render).
- **Sin cambios**: `index.html`, `libros.html`, `clientes.html`, `css/estilos.css` (salvo la carga de scripts ya existente).
- **Datos**: en memoria; sin persistencia hasta C-06.
- **Restricciones**: HTML/CSS/JS nativos, sin librerías, sin npm ni build, sin CDNs. Scripts clásicos con `defer`. Todo texto con `textContent`. Sin `innerHTML`.
- **Verificación**: casos manuales de F4/F5 de `knowledge-base/07_flujos_principales.md` + W3C de `ventas.html` y `historial.html`.

## Preguntas abiertas resueltas en este change
- KB 10 #2: id de venta entero incremental; fecha ISO 8601 mostrada `dd/mm/aaaa` con `<time datetime>`.
- KB 10 #4: libro repetido en una venta **suma la cantidad** al renglón existente.