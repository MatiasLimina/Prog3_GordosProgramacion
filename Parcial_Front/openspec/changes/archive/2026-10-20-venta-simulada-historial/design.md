# Design

## Context

C-04 dejó `js/datos.js` con seed de 6 libros, 2 editoriales, 2 géneros, 3 autores y 3 clientes, ids numéricos y helpers de consulta/escritura (`agregarLibro`, `agregarCliente`, `siguienteId`). `libros.html` y `clientes.html` cargan `datos.js` → `validaciones.js` → `altas.js`. `ventas.html` e `historial.html` **no cargan ningún script**: sus tablas tienen filas estáticas (2 ventas de ejemplo) y sus selects 4 libros y 3 clientes fijos. Los mensajes y `<template>` ya existen en el HTML.

Restricciones: HTML/CSS/JS nativo sin librerías ni build; `file://` (nada de `type="module"`); prohibido `innerHTML`; CSS solo externo; sin tests automatizados. Ver `proposal.md`.

## Goals / Non-Goals

**Goals:**
- Componer una venta real sobre los datos locales: selección de cliente, renglones, cantidades, subtotales y total.
- Confirmar la venta registrando id, fecha, cliente, renglones con precio unitario histórico y total.
- Renderizar el Historial (listado + detalle) desde los datos locales.
- Mantener el patrón de C-03/C-04 (IIFE + global, `defer`, clonado de plantilla, `textContent`, guardas por hooks).

**Non-Goals:**
- Persistencia (`localStorage`) y README: C-06.
- Edición/borrado de ventas (RN-23).
- Propagación entre páginas de altas (C-06).
- Estilos nuevos.

## Decisions

### D1. Dos archivos nuevos con responsabilidades separadas
`js/ventas.js` (composición + confirmación) y `js/historial.js` (render del historial). Cada uno se auto-inicializa y hace `return` si faltan sus hooks, igual que `catalogo.js`/`altas.js`. Orden de carga: `datos.js` → `validaciones.js` → `ventas.js`/`historial.js`.

### D2. Venta en memoria como estado de la página
La venta en curso vive en un objeto JS de `ventas.js` (`{ clienteId, renglones: [{ libroId, cantidad, precioUnitario, titulo, subtotal }] }`). No se persiste hasta confirmar; al confirmar se copia al array `ventas` de `Datos`. No se usa el DOM como fuente de verdad para los cálculos.

### D3. Libro repetido suma cantidad
Al «Agregar renglón» con un libro ya presente, se **suma la cantidad** al renglón existente y se recalcula su subtotal. Se informa con un mensaje de estado (no se rechaza). Decisión documentada (KB 10 #4).

### D4. Identificador y fecha de venta
- id: entero incremental con `siguienteId(Datos.ventas)` (max + 1).
- fecha: `new Date().toISOString()` (ISO 8601 completo). En el Historial se muestra `dd/mm/aaaa` y el elemento `<time>` lleva `datetime` con la fecha ISO (`YYYY-MM-DD`).

### D5. Precio unitario histórico
Al confirmar, cada renglón copia `precioUnitario` (número) y `titulo` del libro en ese momento. El Historial lee del renglón, nunca del catálogo. Esto permite la prueba del precio histórico del docente (C-06).

### D6. Validación de venta (pura)
`Validaciones.validarVenta(entrada, clientes, libros)`:
- entrada: `{ clienteId, renglones: [{ libroId, cantidad }] }`.
- cliente existente (RN-15); ≥ 1 renglón (RN-15); libro existente por renglón (RN-15); cantidad entera > 0 (RN-16, rechaza 0, negativos, decimales).
- Devuelve `{ valido, errores, datosNormalizados }` con los renglones normalizados (cantidad como número).
- Textos: «Elegí un cliente.», «La venta debe tener al menos un renglón.», «El libro seleccionado no existe.», «La cantidad debe ser un entero mayor que cero.».

### D7. Render de renglones y total
`ventas.js` clona `#plantilla-fila-renglon` por renglón, asigna `data-libro-id`, escribe título, cantidad (input editable con `data-accion="cambiar-cantidad"`), precio unitario y subtotal con `textContent` y 2 decimales. El total se escribe en `#venta-total` con `toFixed(2)`. Se muestra `#venta-mensaje-vacio` cuando no hay renglones.

### D8. Confirmación
Al submit de `#form-venta` con `preventDefault()`:
1. Arma la entrada desde el estado en memoria (no del DOM).
2. Valida con `validarVenta`. Si falla: lista errores en `#venta-errores`, muestra `#venta-mensaje-error`, oculta `#venta-mensaje-ok`.
3. Si pasa: `Datos.agregarVenta(ventaNormalizada)`; limpia el estado y el DOM (cliente a «Elegí un cliente», sin renglones, total 0.00, cantidad a 1, libro a «Elegí un libro»); muestra `#venta-mensaje-ok`; oculta error.

### D9. Historial dinámico
`historial.js` renderiza `#historial-lista` clonando `#plantilla-fila-venta` (id, fecha `<time datetime>`, cliente, total, enlace «Ver detalle» con `data-venta-id`). Los detalles se generan clonando `#plantilla-detalle-venta` y `#plantilla-fila-renglon-detalle` por cada venta, dentro de `#historial-detalles`. Sin controles de edición/borrado. Muestra `#historial-mensaje-vacio` si no hay ventas. Se mantiene el ancla `#detalle-venta-<id>` para navegación sin JS cuando hay filas estáticas; en modo dinámico el detalle se agrega al contenedor.

### D10. Selects regenerados
`regenerarSelectoresVenta()` reconstruye `#venta-cliente` (preservando la primera opción literal) y `#venta-libro` (con texto `título — precio` con 2 decimales) desde los datos. Se invoca al inicializar y tras altas (en la misma página no hay altas de libros/clientes, pero se deja el hook para C-06).

### D11. Verificación manual y W3C
Sin tests automatizados. Casos F4/F5 de `07_flujos_principales.md` + W3C de `ventas.html` y `historial.html`. Se registra el resultado real en tasks.md (y se consolidará en el README de C-06).

## Risks / Trade-offs
- Venta en memoria se pierde al navegar/recargar hasta C-06 (igual que altas en C-04).
- `historial.html` mantiene filas estáticas como respaldo sin JS; el JS las reemplaza al inicializar.
- El detalle dinámico usa anclas generadas; la navegación «Ver detalle» funciona con JS habilitado. Con JS deshabilitado se ven las filas estáticas de ejemplo.