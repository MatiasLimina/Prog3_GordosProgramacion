# Tasks

> Sin tests automatizados (regla dura 1): cada tarea se verifica con comportamiento observable en el navegador, la consola de DevTools o el W3C Nu HTML Checker. Los checkboxes quedan sin marcar hasta el apply.

## 1. Capa de datos (`js/datos.js`)

- [ ] 1.1 Agregar el seed de dos ventas de ejemplo (id 1: María Gómez 2×1500 + 1×2000 = 5000, fecha `2026-10-01`; id 2: Juan Pérez 1×3200.50 = 3200.50, fecha `2026-10-05`) con renglones que copian `precioUnitario` y `titulo`; verificar en consola que `Datos.ventas.length === 2` y que `Datos.ventas[0].renglones[0].precioUnitario === 1500`.
- [ ] 1.2 Agregar `agregarVenta(venta)` a `window.Datos`: asigna id con `siguienteId(Datos.ventas)`, inserta la venta en el array y la devuelve; verificar en consola que el id es 3 tras la primera alta y que el array crece.
- [ ] 1.3 Verificar en consola que `siguienteId(Datos.ventas)` devuelve 3 con el seed y 4 tras agregar una venta, sin alterar los ids existentes.

## 2. Validación pura (`js/validaciones.js`)

- [ ] 2.1 Extender `window.Validaciones` con `validarVenta(entrada, clientes, libros)` que devuelva `{ valido, errores, datosNormalizados }`; verificar en consola que una venta válida (cliente 1, renglón libro 1 cantidad 2) devuelve `valido: true`.
- [ ] 2.2 Verificar los casos inválidos en consola: sin cliente → «Elegí un cliente.»; sin renglones → «La venta debe tener al menos un renglón.»; cantidad 0, negativa y decimal → «La cantidad debe ser un entero mayor que cero.»; libro inexistente → «El libro seleccionado no existe.».
- [ ] 2.3 Verificar que `datosNormalizados.renglones[i].cantidad` es número y que el cliente se devuelve por id.

## 3. Composición de la venta (`js/ventas.js`)

- [ ] 3.1 Crear `js/ventas.js` como IIFE con `"use strict"` que exponga `window.Ventas` y se auto-inicialice con guardas; agregar a `ventas.html` los scripts `datos.js` → `validaciones.js` → `ventas.js` en ese orden.
- [ ] 3.2 Implementar `regenerarSelectoresVenta()`: reconstruye `#venta-cliente` (preservando la primera opción literal) y `#venta-libro` (texto `título — precio` con 2 decimales) desde los datos; verificar que hay 4 opciones de libro y 4 de cliente.
- [ ] 3.3 Implementar el estado en memoria de la venta en curso (`clienteId`, `renglones`) y «Agregar renglón»: valida libro + cantidad > 0; si el libro ya está, suma la cantidad al renglón existente; renderiza la tabla clonando `#plantilla-fila-renglon` con `textContent`.
- [ ] 3.4 Implementar cambio de cantidad (input `data-accion="cambiar-cantidad"`) y «Quitar renglón» (`data-accion="quitar-renglon"`); recalcular subtotal por renglón y total con `toFixed(2)`; mostrar `#venta-mensaje-vacio` cuando no hay renglones.
- [ ] 3.5 Verificar en `ventas.html`: venta 2 × 1500 + 1 × 2000 muestra subtotales 3000.00 y 2000.00 y total 5000.00; cambiar cantidad a 3 recalcula; quitar un renglón actualiza el total.

## 4. Confirmación de la venta

- [ ] 4.1 Cablear el `submit` de `#form-venta` con `preventDefault()` incondicional; armar la entrada desde el estado en memoria; validar con `Validaciones.validarVenta`; con errores, listarlos en `#venta-errores` y mostrar `#venta-mensaje-error`.
- [ ] 4.2 En caso válido: llamar a `Datos.agregarVenta` con renglones que copien `precioUnitario` y `titulo` históricos; limpiar estado y DOM (cliente a «Elegí un cliente», sin renglones, total 0.00, cantidad 1, libro «Elegí un libro»); mostrar `#venta-mensaje-ok`.
- [ ] 4.3 Verificar: confirmar la venta de ejemplo; comprobar que `Datos.ventas` crece a 3, que el renglón conserva `precioUnitario === 1500` y que el formulario queda limpio.
- [ ] 4.4 Verificar los casos inválidos de confirmación: sin cliente, sin renglones, cantidad 0/negativa/decimal, libro repetido (suma, no duplica) → no se registra venta.

## 5. Historial dinámico (`js/historial.js`)

- [ ] 5.1 Crear `js/historial.js` como IIFE con `"use strict"` que exponga `window.Historial` y se auto-inicialice con guardas; agregar a `historial.html` los scripts `datos.js` → `historial.js` en ese orden.
- [ ] 5.2 Implementar `renderHistorial()`: clona `#plantilla-fila-venta` por venta (id, fecha con `<time datetime>` ISO, cliente, total 2 decimales, enlace «Ver detalle» con `data-venta-id`); reemplaza `#historial-lista` con `replaceChildren`; muestra `#historial-mensaje-vacio` si no hay ventas.
- [ ] 5.3 Implementar el render de detalles: por cada venta clona `#plantilla-detalle-venta` y `#plantilla-fila-renglon-detalle` (título, cantidad, precio unitario, subtotal, total); inserta en `#historial-detalles`; sin controles de edición/borrado.
- [ ] 5.4 Verificar: `historial.html` muestra 2 ventas; «Ver detalle» de la venta 1 muestra 2 × 1500.00 = 3000.00, 1 × 2000.00 = 2000.00 y total 5000.00; venta 2 muestra 1 × 3200.50 = 3200.50.
- [ ] 5.5 Verificar precio histórico: cambiar el precio del libro 1 en `Datos.libros` y re-renderizar el Historial → la venta 1 sigue mostrando 1500.00.

## 6. Limpieza de maqueta en vistas de venta

- [ ] 6.1 Quitar `#aviso-maqueta` de `ventas.html` y `historial.html` (las operaciones de venta se guardan en memoria en esta etapa) y reemplazar las filas estáticas por el render dinámico.
- [ ] 6.2 Verificar que sin JavaScript `ventas.html` sigue mostrando la venta de ejemplo y `historial.html` las 2 ventas (respaldo), y que con JS habilitado se reemplazan por los datos.

## 7. Verificación manual F4/F5 y W3C

- [ ] 7.1 Ejecutar F4 completo: elegir cliente, agregar renglón, cambiar cantidades, quitar renglón, ver subtotales/total, confirmar, limpieza y mensaje.
- [ ] 7.2 Ejecutar los casos inválidos: sin cliente, cantidad 0/negativa/decimal, libro repetido (suma), venta sin renglones → no se confirma.
- [ ] 7.3 Ejecutar F5: listado con id, fecha, cliente, total; «Ver detalle» con renglones y valores confirmados; sin editar/eliminar.
- [ ] 7.4 Ejecutar la prueba de precio histórico: cambiar el precio del catálogo en `Datos.libros` y recargar el Historial → la venta conserva precio unitario, subtotales y total.
- [ ] 7.5 Validar `ventas.html` y `historial.html` con el W3C Nu HTML Checker y confirmar 0 errores.
- [ ] 7.6 Revisar con búsqueda de texto que no se agregó `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `type="module"` ni `localStorage` en los archivos del change.
- [ ] 7.7 Registrar el resultado real de cada caso en la tabla de verificación de este change (a consolidar en el README de C-06).