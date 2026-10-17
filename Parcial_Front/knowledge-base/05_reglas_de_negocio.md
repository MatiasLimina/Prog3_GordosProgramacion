# 05 — Reglas de negocio

## Catálogo (Ej. 3)
- **RN-01** Libro sin género se muestra «Sin clasificar».
- **RN-02** Filtro por título: sin distinguir mayúsculas/minúsculas, coincidencia parcial, `trim` de la búsqueda.
- **RN-03** Búsqueda vacía muestra todo el catálogo; sin coincidencias muestra un mensaje claro.
- **RN-04** Datos escritos por usuarios se insertan como texto en el DOM (`textContent`, nunca HTML).

## Alta de libros (Ej. 4)
- **RN-05** Título e ISBN no vacíos.
- **RN-06** ISBN único; se compara sin espacios ni guiones. No se valida dígito de control.
- **RN-07** Precio numérico y > 0.
- **RN-08** Editorial y todos los autores seleccionados existen; al menos un autor.
- **RN-09** Género opcional («Sin clasificar» = ausencia); si se asigna, debe existir.

## Alta de clientes (Ej. 4)
- **RN-10** Nombre completo y email no vacíos (un solo campo de nombre).
- **RN-11** Email con formato válido.
- **RN-12** Email único, comparado sin espacios exteriores y sin distinguir mayúsculas.

## Formularios (Ej. 4)
- **RN-13** Envío controlado con `preventDefault`; errores cerca del formulario; solo se agrega el registro si todo pasa.
- **RN-14** Tras alta correcta, listados y selectores se actualizan sin recargar.

## Ventas (Ej. 5)
- **RN-15** Requiere cliente existente y ≥ 1 renglón con libro existente.
- **RN-16** Cantidad entera > 0 (rechaza 0, negativos, decimales).
- **RN-17** Sin libros repetidos en la misma venta: se modifica la cantidad del renglón o se informa el duplicado.
- **RN-18** Antes de confirmar se pueden cambiar cantidades y quitar renglones.
- **RN-19** subtotal = cantidad × precio; total = suma de subtotales; importes con dos decimales.
- **RN-20** No se confirma sin cliente, sin renglones o con cantidades inválidas.
- **RN-21** Al confirmar se registra id, fecha, cliente, renglones y total; se limpia el formulario y se muestra mensaje de resultado.
- **RN-22** El precio unitario es **histórico**: se copia al renglón y no se relee del catálogo.
- **RN-23** Ventas confirmadas inmutables: no se editan ni eliminan desde la interfaz.

## Persistencia (Ej. 6)
- **RN-24** Primer inicio carga ejemplos; reaperturas recuperan lo guardado sin duplicar ejemplos ni ventas.
