# Tasks

> ⚠️ **Pendiente de decisión antes del apply** (ver `design.md` § Open Questions): (1) nombre de la librería — supuesto "Librería Papel y Tinta"; (2) formato del id y la fecha de venta en la maqueta — supuesto ids numéricos y `DD/MM/AAAA`.

> Sin tests automáticos (regla dura 1): cada tarea se verifica a mano o con el W3C Nu HTML Checker (https://validator.w3.org/nu/, subiendo el archivo). Contrato de ids/`name`/`data-*`: `design.md` §D2. Datos de ejemplo: `design.md` §D4. Ninguna página incluye `<script>`.

## 1. Base compartida

- [ ] 1.1 Crear `css/estilos.css` con las reglas mínimas de `design.md` §D5 (incluye `[hidden]`, `.visualmente-oculto`, `.salto`, `.tabla-contenedor`, `.mensaje--ok/--error`) y verificar que no define colores de marca ni tipografías propias y que no anula el `outline` de foco
- [ ] 1.2 Crear `index.html` con el esqueleto compartido de §D3 (head, `data-vista="catalogo"`, "Saltar al contenido", header con marca, `<nav aria-label="Principal">` con las 5 vistas, `<main id="contenido">`, `<h1>` con el nombre de la librería, aviso `#aviso-maqueta`, footer) y verificar en el navegador que se ve la marca, el nav con "Catálogo" marcado con `aria-current="page"` y el aviso

## 2. Vista Catálogo (`index.html`)

- [ ] 2.1 Agregar el formulario `#catalogo-busqueda` (`role="search"`, label "Buscar por título" → `#catalogo-buscar` `name="busqueda"`, botón "Buscar") y verificar que clic en la etiqueta enfoca el campo
- [ ] 2.2 Agregar la sección "Catálogo de libros" con `<ul id="catalogo-lista">` y los 4 libros de §D4 como `<li data-libro-id><article>` con `<h3>` y `<dl>` de ISBN, editorial, género, autores y precio (`data-campo`), y verificar que el libro 3 muestra «Sin clasificar» y los libros 2 y 4 muestran sus dos autores
- [ ] 2.3 Agregar los mensajes `#catalogo-mensaje-vacio` y `#catalogo-mensaje-sin-resultados` (`hidden`, `role="status"`, `data-estado`) y la plantilla `#plantilla-tarjeta-libro`, y verificar quitando `hidden` desde DevTools que ambos mensajes se leen
- [ ] 2.4 Validar `index.html` en el W3C Nu HTML Checker y verificar 0 errores

## 3. Vista Libros (`libros.html`)

- [ ] 3.1 Crear `libros.html` copiando el esqueleto de `index.html` (`data-vista="libros"`, `<title>` y `<h1>` "Libros", `aria-current` en "Libros") y verificar que el nav es idéntico salvo `aria-current`
- [ ] 3.2 Agregar `#form-libro` (`novalidate`) con título, ISBN, precio, editorial (opción inicial vacía + 2 editoriales), género (primera opción «Sin clasificar» `value=""` + 2 géneros), `<fieldset id="libro-autores">` con leyenda "Autores (elegí al menos uno)" y 3 casillas `name="autorIds"`, mensajes `#libros-mensaje-ok` / `#libros-mensaje-error` + `<ul id="libros-errores">` y botón "Registrar libro"; verificar ids y `name` contra §D2 y que cada etiqueta enfoca su control
- [ ] 3.3 Agregar la tabla de libros registrados (`.tabla-contenedor`, `caption`, `thead` con `th scope="col"`, `<tbody id="libros-lista">` con los 4 libros y `data-libro-id`), `#libros-mensaje-vacio` y `#plantilla-fila-libro`, y verificar que los datos coinciden con el catálogo
- [ ] 3.4 Validar `libros.html` en el W3C Nu HTML Checker y verificar 0 errores

## 4. Vista Clientes (`clientes.html`)

- [ ] 4.1 Crear `clientes.html` desde el esqueleto (`data-vista="clientes"`, `aria-current` en "Clientes") con `#form-cliente` (`novalidate`): "Nombre completo" (`name="nombreCompleto"`), "Email" (`type="email"`, `name="email"`), mensajes ok/error + `#clientes-errores` y botón "Registrar cliente"; verificar ids/`name` contra §D2
- [ ] 4.2 Agregar la tabla de clientes (`<tbody id="clientes-lista">` con los 3 clientes de §D4 y `data-cliente-id`), `#clientes-mensaje-vacio` y `#plantilla-fila-cliente`, y verificar `caption`/`thead`/`th scope`
- [ ] 4.3 Validar `clientes.html` en el W3C Nu HTML Checker y verificar 0 errores

## 5. Vista Ventas (`ventas.html`)

- [ ] 5.1 Crear `ventas.html` desde el esqueleto (`data-vista="ventas"`, `<h1>` "Nueva venta") con `#form-venta` (`novalidate`) y el fieldset "Cliente" (`#venta-cliente`, opción inicial vacía + 3 clientes); verificar que el nav marca "Ventas"
- [ ] 5.2 Agregar el fieldset "Agregar renglón": `#venta-libro` (opción inicial vacía + 4 libros "Título — precio"), `#venta-cantidad` (`type="number" min="1" step="1" value="1"`) y botón `type="button"` "Agregar renglón" (`data-accion="agregar-renglon"`); verificar que se alcanzan con Tab en ese orden
- [ ] 5.3 Agregar la tabla de renglones (`<tbody id="venta-renglones">`) con la venta de ejemplo (libro 1 × 2 = 3000.00, libro 2 × 1 = 2000.00): cantidad editable con label oculta "Cantidad de «título»", botón "Quitar renglón" con texto oculto del título, y `<tfoot>` con `<output id="venta-total">5000.00</output>`; verificar los importes a mano y que el lector/inspector de accesibilidad nombra cada botón con su libro
- [ ] 5.4 Agregar `#venta-mensaje-vacio`, `#venta-mensaje-ok`, `#venta-mensaje-error` + `#venta-errores`, el botón "Confirmar venta" (`type="submit"`, último control del form) y `#plantilla-fila-renglon`; verificar que todos los mensajes tienen `hidden` y su `role`
- [ ] 5.5 Validar `ventas.html` en el W3C Nu HTML Checker y verificar 0 errores

## 6. Vista Historial (`historial.html`)

- [ ] 6.1 Crear `historial.html` desde el esqueleto (`data-vista="historial"`, `<h1>` "Historial de ventas") con la sección `#historial-listado`: tabla con `<tbody id="historial-lista">` y las 2 ventas de §D4 (identificador, `<time>`, cliente, total) y un enlace "Ver detalle" por fila (`href="#detalle-venta-{id}"`, texto oculto "de la venta {id}"); verificar `caption`/`thead`/`th scope`
- [ ] 6.2 Agregar `#historial-detalles` con un `<article id="detalle-venta-{id}" data-venta-id>` por venta (`<dl>` id/fecha/cliente, tabla de renglones con `tfoot` de total, enlace "Volver al listado") y verificar con JS deshabilitado que cada "Ver detalle" salta a su detalle y que el de la venta 1 muestra 3000.00 + 2000.00 = 5000.00
- [ ] 6.3 Agregar `#historial-mensaje-vacio` y las plantillas `#plantilla-fila-venta`, `#plantilla-detalle-venta`, `#plantilla-fila-renglon-detalle`, y verificar que la vista no tiene controles para editar ni eliminar ventas
- [ ] 6.4 Validar `historial.html` en el W3C Nu HTML Checker y verificar 0 errores

## 7. Verificación integral manual

- [ ] 7.1 Recorrer las 5 vistas solo con los enlaces del nav (con JS deshabilitado) partiendo de `index.html` abierto con doble clic, y verificar que todas abren, que `aria-current="page"` marca solo la vista actual y que los 5 nav son idénticos
- [ ] 7.2 Recorrer cada vista solo con teclado (Tab/Shift+Tab/Enter/Espacio) y verificar que el primer Tab cae en "Saltar al contenido", que el foco es siempre visible y que se alcanzan todos los campos, casillas y botones
- [ ] 7.3 Revisión de accesibilidad: cada control con `<label for>` coincidente (o `fieldset`/`legend`), cada tabla con `caption` + `thead` + `th scope`, cada botón/enlace de acción con texto descriptivo; verificar además con búsqueda en los 5 HTML que no hay `style=`, `<style`, `<script` ni `innerHTML`
- [ ] 7.4 Revisar los hooks contra la tabla de `design.md` §D2 (ids únicos por página, `name` en camelCase, `data-*` en filas e ítems, todos los mensajes con `hidden` + `role` + `data-estado`) y anotar al pie de este archivo el resultado observado de 7.1–7.4 (sin marcar como aprobado lo no ejecutado)

## Workflow follow-up

- Tras la revisión, archivar con `/opsx:archive estructura-pantallas-html` y marcar C-01 como `[x]` en `CHANGES.md`.
- C-02 (estilos) y C-03 (datos y catálogo) pueden arrancar en paralelo sobre este contrato de hooks.
