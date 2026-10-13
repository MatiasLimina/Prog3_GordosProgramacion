# 07 — Flujos principales

## F1 — Consultar catálogo con filtro
1. Se abre `index.html`; JS genera el catálogo desde el array de libros.
2. El operador escribe en el buscador → `trim` + minúsculas + `includes` sobre el título.
3. Vacío: catálogo completo. Sin coincidencias: mensaje «sin resultados».

## F2 — Alta de libro
1. Completa título, ISBN, precio, editorial, género (o «Sin clasificar»), ≥ 1 autor.
2. Submit → `preventDefault` → validaciones RN-05..09.
3. Error: mensaje cerca del formulario, no se agrega. Éxito: se agrega, mensaje correcto, se actualizan listado, catálogo y selector de ventas.

## F3 — Alta de cliente
Igual que F2 con RN-10..12 (nombre, email válido y único sin importar mayúsculas/espacios); actualiza listado y selector de clientes.

## F4 — Venta simulada
1. Elige cliente.
2. Agrega renglón (libro + cantidad entera > 0); si el libro ya está, se actualiza la cantidad o se informa duplicado.
3. Puede cambiar cantidades o quitar renglones; ve subtotales y total (2 decimales).
4. «Confirmar venta»: valida cliente/renglones/cantidades → registra id, fecha, cliente, renglones con precio histórico, total → limpia el formulario → mensaje.

## F5 — Historial
Lista id, fecha, cliente, total; «Ver detalle» muestra renglones con los valores confirmados. Sin editar ni eliminar.

## F6 — Persistencia
Primer inicio: carga ejemplos a localStorage. Reaperturas: recupera datos sin duplicar.

## Verificación manual (tabla del Ej. 6, resultado real al README)
| Caso | Esperado |
|------|----------|
| Búsqueda en mayúsculas parcial; vacía; inexistente | Coincidencias sin distinguir caso; catálogo completo; mensaje sin resultados |
| Libro con ISBN existente y luego nuevo | Duplicado rechazado; válido en catálogo y selección de venta |
| Cliente con email inválido, existente en mayúsculas, nuevo | Se rechazan los dos primeros; el nuevo aparece |
| Venta sin cliente, cantidad 0/negativa/decimal; libro repetido | No se confirma; no se crea otro renglón |
| Venta 2 × 1500 y 1 × 2000 | Subtotales 3000 y 2000; total 5000; detalle en historial |
| Cambio solo del precio de catálogo en localStorage (copia de prueba, guiado por el docente) y recarga | La venta conserva precio unitario, subtotales y total |
| Recarga tras altas y venta | Datos recuperados sin duplicar ejemplos ni ventas |
| Teclado y anchos 320/1280 px | Foco visible, controles usables, tabla con scroll propio |
