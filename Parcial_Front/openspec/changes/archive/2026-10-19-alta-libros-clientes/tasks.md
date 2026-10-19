# Tasks

> Sin tests automatizados (regla dura 1): cada tarea se verifica con comportamiento observable en el navegador, la consola de DevTools o el W3C Nu HTML Checker. Los checkboxes quedan sin marcar hasta el apply.

## 1. Capa de datos (`js/datos.js`)

- [x] 1.1 Agregar a `js/datos.js` la función `siguienteId(coleccion)` que devuelva `max(id) + 1` como número (1 si la colección está vacía), sin modificar el seed; verificar en consola que `Datos.siguienteId(Datos.libros) === 7`, `Datos.siguienteId(Datos.clientes) === 4` y `Datos.siguienteId([]) === 1`
- [x] 1.2 Agregar `agregarLibro(libro)` y `agregarCliente(cliente)` a `js/datos.js`, expuestas en `window.Datos`: asignan el id con `siguienteId`, insertan el registro en la colección correspondiente y lo devuelven; verificar en consola que el registro devuelto es el último del array, con id numérico y sin alterar los ids existentes (recargar la página para restaurar el seed)
- [x] 1.3 Verificar la integridad de un alta en consola: el libro agregado referencia una editorial y autores existentes y omite `generoId` cuando no se le asigna género; comprobar que `buscarLibro(nuevoId)` lo devuelve y que el total de libros pasó de 6 a 7

## 2. Validaciones puras (`js/validaciones.js`)

- [x] 2.1 Crear `js/validaciones.js` como IIFE con `"use strict"` que exponga `window.Validaciones` con `normalizarIsbn(valor)` y `normalizarEmail(valor)`; verificar en consola que `normalizarIsbn(" 978 950-000-001-1 ")` devuelve `"9789500000011"` y que `normalizarEmail("  María@Example.COM ")` devuelve `"maría@example.com"` (o el resultado exacto de `trim().toLowerCase()`)
- [x] 2.2 Implementar `validarLibro(entrada, libros)` devolviendo `{ valido, errores, datosNormalizados }` con RN-05..RN-09 y los textos exactos de `design.md` §D6; verificar en consola los casos: título vacío → `El título es obligatorio.`; ISBN vacío → `El ISBN es obligatorio.`; ISBN `978-950-000-001-1` → `El ISBN ya está registrado en otro libro.`; precio `""` → `El precio es obligatorio.` (no debe caer en «mayor que cero»); precio `0` y `-5` → `El precio debe ser mayor que cero.`; editorial `""` → `Elegí una editorial.`; sin autores → `Elegí al menos un autor.`; autores `["1","999"]` → `Uno de los autores seleccionados no existe.`; género `"99"` → `El género seleccionado no existe.`
- [x] 2.3 Verificar la normalización de la entrada válida de libro en consola: `generoId: ""` desaparece de `datosNormalizados` (sin `""` ni `0`), precio se devuelve como número, autores como números y el ISBN/título con `trim()`; un libro válido con género devuelve `valido: true` y `errores: []`
- [x] 2.4 Implementar `validarCliente(entrada, clientes)` con RN-10..RN-12 y los textos exactos de `design.md` §D6; verificar en consola: nombre vacío → `El nombre completo es obligatorio.`; email vacío → `El email es obligatorio.`; `"maria.gomez"` y `"maria@example"` → `El email no tiene un formato válido.`; `"  MARIA.GOMEZ@EXAMPLE.COM "` → `El email ya está registrado.`; email nuevo válido → `valido: true` con el email y el nombre sin espacios exteriores

## 3. Utilidades y wiring (`js/altas.js`)

- [x] 3.1 Crear `js/altas.js` como IIFE con `"use strict"` que exponga `window.Altas`; incluir helpers privados de mensajes (`mostrarExito`, `mostrarErrores`, `ocultarMensajes`) que vacíen la lista con `replaceChildren`, agreguen un `<li>` por error con `textContent`, alternen `hidden` y nunca usen `innerHTML`; verificar en consola que se puede invocar la API pública sin errores y que no hay coincidencias de `innerHTML` en el archivo
- [x] 3.2 Implementar en `js/altas.js` `regenerarSelectoresLibro()`: reconstruye las opciones de `#libro-editorial` y `#libro-genero` con `createElement("option")` + `textContent`, preservando la primera opción literal del HTML (`value=""`), y reemplaza los checkboxes de `#libro-autores-opciones` con `id="libro-autor-<id>"`, `name="autorIds"`, `value="<id>"` y su `<label for>`; verificar en `libros.html` que quedan 3 opciones en editorial (1 + 2 editoriales), 3 en género (1 + 2 géneros) y 3 checkboxes con etiqueta, sin duplicar los estáticos
- [x] 3.3 Implementar `renderLibros()` y `renderClientes()`: clonan `#plantilla-fila-libro` / `#plantilla-fila-cliente` con `plantilla.content.firstElementChild.cloneNode(true)`, asignan `data-libro-id` / `data-cliente-id`, escriben cada `[data-campo]` con `textContent` y reemplazan el cuerpo con `replaceChildren` sobre un `DocumentFragment`; mapear `cliente.nombre → data-campo="nombreCompleto"`, género ausente → «Sin clasificar», autores unidos con `", "` y precio con `toFixed(2)`; mostrar el mensaje de vacío cuando la colección esté vacía
- [x] 3.4 Implementar `inicializarAltas()` con guardas: hace `return` si no encuentra `#form-libro` ni `#form-cliente`; en la vista Libros regenera selectores y renderiza el listado; en la vista Clientes renderiza el listado; invocarla al final del archivo sin `DOMContentLoaded`; verificar en consola que `window.Altas` existe en ambas páginas y que cargar la página no produce errores

## 4. Scripts en `libros.html` y `clientes.html`

- [x] 4.1 Agregar a `libros.html`, antes de `</body>`, `<script defer src="js/datos.js"></script>`, `<script defer src="js/validaciones.js"></script>` y `<script defer src="js/altas.js"></script>` en ese orden, sin ningún otro cambio en el HTML; verificar con doble clic (`file://`) que la consola no muestra errores y que el listado muestra 6 libros
- [x] 4.2 Agregar a `clientes.html`, antes de `</body>`, las mismas tres etiquetas `<script defer src="...">` en el mismo orden, sin otro cambio; verificar con `file://` que la consola no muestra errores y que el listado muestra 3 clientes
- [x] 4.3 Verificar que `libros.html` y `clientes.html` siguen mostrando respectivamente 4 y 3 filas estáticas cuando JavaScript está deshabilitado (respaldo sin JS), y que el aviso de maqueta y la navegación no cambiaron

## 5. Integración en la vista Libros

- [x] 5.1 Cablear el `submit` de `#form-libro`: `preventDefault()` incondicional, limpieza previa de errores y mensajes, lectura de `titulo`, `isbn`, `precio`, `editorialId`, `generoId` y `input[name="autorIds"]:checked`; verificar que al enviar con Enter o con el botón la URL no cambia y la página no se recarga
- [x] 5.2 Integrar `Validaciones.validarLibro` en el submit: con errores, listar un `<li>` por error en `#libros-errores`, mostrar `#libros-mensaje-error` y ocultar `#libros-mensaje-ok`, sin agregar el libro; verificar que con título vacío, precio vacío y sin autores aparecen tres ítems y el total de libros sigue en 6
- [x] 5.3 Integrar el alta correcta: llamar a `Datos.agregarLibro`, re-renderizar el listado, regenerar los selectores de editorial/género y los checkboxes, mostrar `#libros-mensaje-ok`, ocultar el error y limpiar el formulario (editorial «Elegí una editorial», género «Sin clasificar», sin autores, campos vacíos); verificar que el libro nuevo aparece como séptima fila con su precio a dos decimales y que el formulario queda listo para otra alta
- [x] 5.4 Verificar los estados del listado: con `Datos.libros.length = 0` y un re-render manual se muestra `#libros-mensaje-vacio` y la tabla queda sin filas; recargar para restaurar el seed

## 6. Integración en la vista Clientes

- [x] 6.1 Cablear el `submit` de `#form-cliente`: `preventDefault()` incondicional, limpieza previa de errores y mensajes, lectura de `nombreCompleto` y `email`; verificar que el envío no recarga ni cambia la URL
- [x] 6.2 Integrar `Validaciones.validarCliente`: con errores, listar un `<li>` por error en `#clientes-errores`, mostrar `#clientes-mensaje-error` y ocultar `#clientes-mensaje-ok`, sin agregar el cliente; verificar con email inválido y con email existente en mayúsculas (`  MARIA.GOMEZ@EXAMPLE.COM `) que se rechazan ambos y el total sigue en 3
- [x] 6.3 Integrar el alta correcta: llamar a `Datos.agregarCliente`, re-renderizar el listado, mostrar `#clientes-mensaje-ok`, ocultar el error y vaciar los dos campos; verificar que el cliente nuevo aparece como cuarta fila con su nombre completo y email
- [x] 6.4 Verificar los estados del listado: con `Datos.clientes.length = 0` y un re-render manual se muestra `#clientes-mensaje-vacio` y la tabla queda sin filas; recargar para restaurar el seed

## 7. Verificación manual F2/F3 y W3C

> Ejecutar sobre `file://` (doble clic). Completar la columna «Resultado observado» durante el apply; no se agregan tests automatizados. Para F2/F3, la actualización de listados y selectores se verifica dentro de la misma página (ver `design.md` §D8); la propagación a `index.html` y `ventas.html` queda diferida a C-05/C-06.

- [x] 7.1 Ejecutar F2 (`knowledge-base/07_flujos_principales.md`) completo: alta válida con género y un autor; alta con «Sin clasificar» y dos autores; comprobar listado, mensaje OK, limpieza y re-render de selectores
- [x] 7.2 Ejecutar el caso de ISBN de la consigna: primero un ISBN existente (`978-950-000-001-1` y su variante con espacios) → rechazo con `El ISBN ya está registrado en otro libro.`; luego un ISBN nuevo → alta aceptada y séptima fila visible
- [x] 7.3 Ejecutar F3 completo: alta válida; email inválido (`maria.gomez`) → rechazo; email existente en mayúsculas con espacios → rechazo; email nuevo → alta aceptada y cuarta fila visible
- [x] 7.4 Verificar los estados de los formularios: errores simultáneos listados uno por ítem, mensaje OK oculto; reintento que vacía la lista anterior; éxito que oculta el error y deja la lista vacía; comprobar que los textos no se interpretan como marcado al ingresar `<b>` o `&` en el título o el nombre
- [x] 7.5 Verificar los listados iniciales: `libros.html` muestra 6 filas (no 4) y `clientes.html` 3 (no duplicadas), con género «Sin clasificar» en los libros 3 y 6, autores separados por coma y precios a dos decimales
- [x] 7.6 Validar `libros.html` y `clientes.html` con el W3C Nu HTML Checker (`Invoke-RestMethod -Method Post -Uri "https://validator.w3.org/nu/?out=json" -InFile <archivo>`) y confirmar 0 errores en ambas páginas
- [x] 7.7 Revisar con búsqueda de texto que `js/datos.js`, `js/validaciones.js`, `js/altas.js`, `libros.html` y `clientes.html` no contienen `innerHTML`, `outerHTML`, `insertAdjacentHTML` ni `document.write`, y que no se agregó `type="module"` ni `localStorage`

## Resultados observados de la verificación

| Caso | Esperado | Resultado observado |
|------|----------|---------------------|
| Carga de `libros.html` con JS | 6 filas, 3 opciones de editorial, 3 de género, 3 checkboxes; mensajes ocultos | 6 filas (ids 1–6); editorial: 3 opciones (`""` «Elegí una editorial», `1` Ediciones del Sur, `2` Editorial Faro); género: 3 (`""` «Sin clasificar», `1` Novela, `2` Ensayo); 3 checkboxes `libro-autor-1..3` (`name="autorIds"`, labels Ana Ríos, Bruno Paz, Carla Vega); ok/error/vacío con `hidden=true`. |
| Carga de `clientes.html` con JS | 3 filas; mensajes ocultos | 3 filas (ids 1–3: María Gómez, Juan Pérez, Lucía Fernández); ok/error/vacío con `hidden=true`. |
| Alta de libro válida | Séptima fila visible, mensaje OK, formulario limpio, sin recarga | 7 filas; fila 7 = `Dune / 978-111-000-001-1 / Editorial Faro / Novela / Ana Ríos / 1234.50`; OK visible y error oculto; título/ISBN/precio `""`, editorial `""` («Elegí una editorial»), género `""` («Sin clasificar»), 0 autores marcados; `href` sin query y marca JS viva (sin recarga); selectores siguen con 3/3/3 opciones. |
| Libro con «Sin clasificar» | Séptima fila con género `Sin clasificar` y precio a dos decimales | 7 filas; fila 7 = `Ensayo X / 978-111-000-002-8 / Ediciones del Sur / Sin clasificar / Bruno Paz, Carla Vega / 10.00`; el registro guardado no tiene la propiedad `generoId` (ausente). |
| ISBN duplicado (con y sin guiones/espacios) | Rechazo con `El ISBN ya está registrado en otro libro.`; total sin cambios | `978-950-000-001-1`, `978 950 000 001 1` y `9789500000011` → 6 filas (no se agregó), un `<li>` literal `El ISBN ya está registrado en otro libro.`, error visible y OK oculto. |
| ISBN nuevo tras el duplicado | Alta aceptada; séptima fila visible | `978-222-000-009-9` → 7 filas, OK visible, error oculto, 0 `<li>` de error. |
| Título/ISBN vacíos, precio vacío, sin autores | Errores listados uno por ítem; alta rechazada | 5 `<li>` en orden: `El título es obligatorio.`, `El ISBN es obligatorio.`, `El precio es obligatorio.`, `Elegí una editorial.`, `Elegí al menos un autor.`; 6 filas; OK oculto y error visible. |
| Precio `0` o negativo | `El precio debe ser mayor que cero.` | Precio `0` y `-5` → `El precio debe ser mayor que cero.`; 6 filas en ambos casos; error visible. |
| Autor inexistente (`["1","999"]` en consola) | `Uno de los autores seleccionados no existe.` | `Validaciones.validarLibro({... autorIds:["1","999"]})` → `valido:false`, `errores:["Uno de los autores seleccionados no existe."]`; `Datos.libros` JSON idéntico antes/después. |
| Alta de cliente válida | Cuarta fila visible, mensaje OK, campos vacíos, sin recarga | 4 filas; fila 4 = `Lucía Nueva / lucia.nueva@example.com`; OK visible y error oculto; nombre y email `""`; marca JS viva (sin recarga). |
| Email inválido | `El email no tiene un formato válido.`; total sin cambios | `maria.gomez` → `El email no tiene un formato válido.`; 3 filas; error visible y OK oculto. `maria@example` → mismo texto. |
| Email existente en mayúsculas y con espacios | `El email ya está registrado.`; total sin cambios | `"  MARIA.GOMEZ@EXAMPLE.COM "` → `El email ya está registrado.`; 3 filas; error visible y OK oculto. |
| Email nuevo tras los rechazos | Alta aceptada; cuarta fila visible | `"  pedro.nuevo@example.com  "` → 4 filas; fila 4 = `Pedro Nuevo / pedro.nuevo@example.com`; OK visible y error oculto. |
| Reintento tras error | Lista de errores anterior vacía antes del nuevo resultado | 1.er envío: 5 `<li>`; 2.º envío (solo título corregido): 4 `<li>` (`ISBN`, `precio`, `editorial`, `autores`), sin el de título → la lista se reemplazó, no se acumuló; alta válida posterior: 0 `<li>`, error oculto y OK visible. |
| Texto con `<b>` o `&` | Se muestra literal, sin interpretarse como marcado | Título `"<b>X</b> & Y"` y nombre `"<b>Ana</b> & Co"`: `textContent` literal, `childElementCount=0`, `innerHTML` = `&lt;b&gt;X&lt;/b&gt; &amp; Y` (escapado). |
| Listado vacío (libros y clientes) | Mensaje de vacío visible y tabla sin filas | `Datos.libros.length=0` + `renderLibros` → 0 filas y `#libros-mensaje-vacio` visible; `Datos.clientes.length=0` + `renderClientes` → 0 filas y `#clientes-mensaje-vacio` visible. |
| Sin JavaScript | `libros.html` con 4 filas y `clientes.html` con 3, formularios y aviso presentes | Scripts deshabilitados: `libros.html` 4 filas (ids 1–4), `#form-libro` y `#aviso-maqueta` presentes, 5 enlaces de navegación; `clientes.html` 3 filas, `#form-cliente` y aviso presentes; `window.Altas` = `undefined`. |
| W3C Nu HTML Checker | 0 errores en `libros.html` y `clientes.html` | Nu (`?out=json`): `libros.html` 0 errores y 0 mensajes; `clientes.html` 0 errores y 0 mensajes (array `messages` vacío en ambos). |
| `innerHTML` / `type="module"` / `localStorage` | 0 coincidencias en los archivos del change | 0 usos de `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `type="module"` y `localStorage`; el único match textual es un comentario en `js/altas.js:4` («nunca innerHTML»), que no invoca la API. |
