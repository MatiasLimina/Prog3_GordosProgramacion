# 06 — Funcionalidades

## Épica 1 — Estructura y navegación (Ej. 1, 20 pts)
- Como operador, navego entre Catálogo, Libros, Clientes, Ventas e Historial desde `<nav>`.
- HTML semántico (`header`, `nav`, `main`, `section`, `article`, `footer`); `<label for>` en cada campo; botones con texto de acción («Registrar libro», «Agregar renglón», «Confirmar venta», «Ver detalle»); tablas con `thead`/`th scope`.
- Mensajes presentes en el HTML (`hidden`, `role="status"`/`role="alert"`): lista vacía, sin resultados, operación correcta, operación rechazada.
- Etapa 1: datos estáticos de ejemplo; ids, `name` y `data-*` preparados para JS.

## Épica 2 — Presentación CSS (Ej. 2, 20 pts)
- Identidad visual coherente (colores, tipografía, espaciado, tarjetas, formularios, botones), clases reutilizadas, CSS externo.
- Flexbox/Grid; correcto a 320 px y 1280 px sin scroll horizontal de página; tablas con scroll propio.
- Foco visible, navegación por teclado, errores con texto (no solo color), `alt` correcto.

## Épica 3 — Datos y catálogo (Ej. 3, 15 pts)
- Modelo con arrays/objetos e ids estables; seed mínimo; catálogo generado por JS; filtro por título con estados.

## Épica 4 — Altas (Ej. 4, 15 pts)
- Alta de libro (selectores generados desde datos; autores con select múltiple o checkboxes) y de cliente, con validación y actualización sin recarga.

## Épica 5 — Ventas e historial (Ej. 5, 20 pts)
- Selección de cliente, renglones, cambio/quita de cantidades, cálculos, confirmación, historial con detalle de renglones.

## Épica 6 — Cierre (Ej. 6, 10 pts)
- localStorage (4), casos manuales registrados (3), README y entrega (3).
