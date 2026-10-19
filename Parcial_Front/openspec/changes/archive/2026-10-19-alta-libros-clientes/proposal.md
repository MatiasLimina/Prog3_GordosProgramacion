# Proposal

## Why

Las vistas Libros y Clientes siguen siendo maquetas estáticas: los selectores de editorial, género y autores están escritos a mano, las tablas repiten 4 libros y 3 clientes fijos y los formularios no hacen nada. El Ejercicio 4 de la consigna (15 pts) exige altas reales sobre los datos locales, con opciones generadas desde esos datos, validaciones de negocio y actualización de listados sin recargar la página. Es el paso previo obligatorio de C-05, que consume los libros y clientes dados de alta.

## What Changes

- Se agrega a `js/datos.js` la capacidad de **dar de alta registros**: `agregarLibro(libro)`, `agregarCliente(cliente)` y `siguienteId(coleccion)`. El id se calcula como `max(id) + 1` y se guarda como número; la función inserta el registro y lo devuelve.
- Se crea `js/validaciones.js` con **validaciones puras** expuestas en `window.Validaciones`: `validarLibro(entrada, libros)` y `validarCliente(entrada, clientes)`, más los normalizadores de ISBN y email. Cubren RN-05..RN-09 y RN-10..RN-12 y devuelven `{ valido, errores, datosNormalizados }`.
- Se crea `js/altas.js` con las utilidades de mensajes, listados y selectores, y el cableado de eventos de cada vista (expuesto en `window.Altas`). Hace `return` si no encuentra sus hooks, igual que `catalogo.js`, para poder cargarse en ambas páginas sin errores.
- Los selects `#libro-editorial` y `#libro-genero` y los checkboxes de `#libro-autores-opciones` se **regeneran desde los datos locales** al inicializar, preservando la primera opción literal del HTML (`value=""` con «Elegí una editorial» / «Sin clasificar»).
- Los listados `#libros-lista` y `#clientes-lista` se **re-renderizan completos** desde los datos locales clonando `#plantilla-fila-libro` / `#plantilla-fila-cliente`. Al inicializar desaparecen las 4 y 3 filas estáticas y aparecen los 6 libros y 3 clientes del seed (cierra la inconsistencia 4-vs-6 documentada en C-03).
- Los formularios `#form-libro` y `#form-cliente` controlan el envío con `preventDefault()`. Si la validación falla, se listan los errores en `#libros-errores` / `#clientes-errores` (un `<li>` por error, con `textContent`) y no se agrega nada; si pasa, se agrega el registro, se re-renderiza el listado y los selectores relacionados, se muestra el mensaje de alta correcta y se limpia el formulario.
- Se agregan a `libros.html` y `clientes.html` únicamente las etiquetas `<script defer src="...">`, en el orden `datos.js` → `validaciones.js` → `altas.js`. No se agregan ni modifican estructuras, `<template>` ni textos.
- **Fuera de alcance**:
  - `ventas.html`: **no se toca**. C-04 deja los datos y las funciones de alta listas; C-05 genera y actualiza los selects de libros y clientes de esa vista. La parte de F2/F3 sobre «selector de ventas» queda diferida a C-05.
  - `index.html`, `historial.html`, `css/estilos.css` y el texto del aviso de maqueta: sin cambios. Tampoco se agregan `aria-invalid`/`aria-describedby` ni estilos nuevos.
  - **`localStorage` (C-06)**: no se adelanta persistencia.
  - Edición y borrado de registros: la consigna no los exige.
- **Limitación transitoria (explícita)**: la aplicación es multipágina y hasta C-06 no hay persistencia; `datos.js` recarga el seed en cada navegación, por lo que un alta se pierde al salir de la página. F2/F3 se cumplen y se verifican **dentro de la misma página** (el listado y las opciones relacionadas se actualizan sin recargar). La propagación entre páginas (catálogo de `index.html` y selects de `ventas.html`) queda diferida a C-05/C-06.

## Capabilities

### New Capabilities

Ninguna. El change extiende capacidades ya existentes.

### Modified Capabilities

- `registro-libros`: las opciones de editorial, género y autores se generan desde los datos locales; el listado deja de ser estático y se renderiza desde los datos; los mensajes de alta correcta y rechazada pasan a tener comportamiento. Se agregan las validaciones del alta, el alta efectiva, la actualización sin recarga y los estados del formulario.
- `registro-clientes`: el listado deja de ser estático y se renderiza desde los datos; los mensajes pasan a tener comportamiento. Se agregan las validaciones del alta, el alta efectiva, la actualización sin recarga y los estados del formulario.
- `datos-locales`: se agrega la operación de alta de libros y clientes, con id único `max(id) + 1` e integridad referencial preservada.

## Impact

- **Archivos nuevos**: `js/validaciones.js`, `js/altas.js`.
- **Archivos modificados**: `js/datos.js` (solo se agregan funciones, no se altera el seed ni la API existente), `libros.html` y `clientes.html` (solo etiquetas `<script defer>`, sin cambios estructurales ni de estilos).
- **Sin cambios**: `index.html`, `ventas.html`, `historial.html`, `css/estilos.css`.
- **Datos**: en memoria; no hay migración ni esquema persistido. El seed de C-03 se conserva intacto.
- **Restricciones**: HTML/CSS/JS nativos, sin librerías, sin npm ni build, sin CDNs. Scripts clásicos con `defer` (no `type="module"`, que rompe en `file://`). Todo dato escrito por el usuario se inserta con `textContent`; prohibido `innerHTML`. CSS solo externo; no se agregan estilos.
- **Verificación**: sin tests automatizados (regla dura 1). Casos manuales de F2/F3 de `knowledge-base/07_flujos_principales.md` y de la tabla de la consigna, más la validación W3C de `libros.html` y `clientes.html`.
- **Riesgo transitorio aceptado**: un alta no sobrevive a la navegación ni a una recarga hasta C-06; el aviso de maqueta («las operaciones todavía no se guardan») sigue siendo literalmente cierto.

## Preguntas abiertas

- No quedan preguntas de prioridad alta o media asignadas a C-04. El formato de id/fecha de venta, el tratamiento del libro repetido en una venta y las claves de `localStorage` pertenecen a C-05 y C-06 y no condicionan este change.
- La propagación de las altas al catálogo (`index.html`) y a los selectores de `ventas.html` queda diferida a C-05/C-06, según la limitación transitoria descrita arriba.
