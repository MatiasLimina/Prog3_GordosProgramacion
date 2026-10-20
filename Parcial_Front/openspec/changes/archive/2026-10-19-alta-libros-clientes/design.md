# Design

## Context

C-03 dejó `js/datos.js` (seed de 6 libros, 2 editoriales, 2 géneros, 3 autores y 3 clientes, ids numéricos y helpers de consulta en `window.Datos`) y `js/catalogo.js` (IIFE con `defer`, render por clonado de plantilla y `textContent`). `libros.html` y `clientes.html` **no cargan ningún script**: sus formularios tienen `novalidate` y `action`/`method="get"` hacia la misma página, sus selects y checkboxes son estáticos y sus tablas tienen 4 y 3 filas de ejemplo. Los mensajes ya existen en el HTML: `#libros-mensaje-ok`, `#libros-mensaje-error` con `<ul id="libros-errores">` vacío, `#libros-mensaje-vacio`; equivalentes en Clientes.

Restricciones que condicionan el enfoque: HTML/CSS/JS nativo sin librerías ni build; `file://` (nada de `type="module"`); prohibido `innerHTML`; CSS solo externo y sin estilos nuevos; sin tests automatizados. Ver `proposal.md` para la motivación.

## Goals / Non-Goals

**Goals:**
- Implementar F2 y F3 completos dentro de cada página: opciones generadas desde los datos, validaciones puras, alta efectiva y actualización del listado y de los selectores relacionados sin recargar.
- Reutilizar el patrón de C-03 (IIFE + global, `defer`, clonado de plantilla, `textContent`, guardas por hooks) para que el código sea reconocible y no rompa si se carga en otra vista.
- Cerrar la inconsistencia transitoria de C-03: los listados de Libros y Clientes pasan a mostrar el seed completo (6 y 3), sin duplicar filas estáticas.
- Dejar la capa de datos preparada para C-05/C-06 sin adelantar persistencia.

**Non-Goals:**
- Edición y borrado de registros.
- Persistencia (`localStorage`) y propagación de altas entre páginas: C-06.
- Regenerar o cablear los selects de `ventas.html`: C-05.
- Normalización de acentos, validación de dígito de control de ISBN, formato regional de precios o restricción a dos decimales en la entrada.
- Errores por campo (`aria-invalid`, `aria-describedby`) o estilos nuevos.
- Prevención de doble alta o deshabilitado del botón.

## Decisions

### D1 (D-A). Alcance: dos vistas y una capa de datos; `ventas.html` fuera

Se modifican `libros.html`, `clientes.html` y `js/datos.js` (solo se le agregan funciones) y se crean `js/validaciones.js` y `js/altas.js`. En el HTML de las dos vistas la única edición es agregar las etiquetas `<script defer src="...">`: no se tocan estructuras, `<template>`, mensajes ni textos. No se toca `ventas.html`, `index.html`, `historial.html`, `css/estilos.css` ni el aviso de maqueta.

**Por qué**: la consigna delimita el alta; C-05 es dueño de la venta y de sus selects, y `ventas.html` no tiene hoy ningún script. Tocar esa vista en C-04 duplicaría el trabajo de C-05 y agrandaría el riesgo. El aviso de maqueta se conserva porque `navegacion-vistas` lo exige hasta la etapa 6 y su texto («las operaciones todavía no se guardan») sigue siendo cierto.

**Alternativas descartadas**: (a) agregar `datos.js` + un script de selects a `ventas.html` en C-04 — se solapa con C-05 y obliga a mantener dos cableados; (b) regenerar los selects de `ventas.html` sin eventos — deja una vista a medio cablear que C-05 tendría que rehacer.

### D2 (D-B). Tres archivos con responsabilidades separadas, IIFE y globales

- `js/datos.js` (existente): agrega la escritura de colecciones.
- `js/validaciones.js`: normalizadores y funciones puras, en `window.Validaciones`.
- `js/altas.js`: utilidades de mensajes, listados y selects, y el wiring por página, en `window.Altas`.

Orden de carga con `defer`: `datos.js` → `validaciones.js` → `altas.js`. `catalogo.js` no se carga en estas páginas. `altas.js` se auto-inicializa al final y hace `return` si no encuentra sus hooks (`#form-libro` / `#form-cliente`), igual que `catalogo.js`, de modo que puede incluirse en ambas páginas sin errores.

**Por qué**: la KB pide validaciones puras separadas de render y eventos; separar las validaciones permite verificarlas en consola con datos de prueba sin tocar el DOM, y compartir los normalizadores entre libro y cliente. Un solo archivo de altas para libro y cliente evita duplicar el manejo de mensajes.

**Alternativas descartadas**: (a) un único `js/altas.js` con todo — mezcla lógica pura con DOM y dificulta la verificación manual; (b) `js/libros.js` + `js/clientes.js` — duplica el código común de mensajes/listados y multiplica los archivos sin ganancia; (c) extender `catalogo.js` — mezcla responsabilidades de otra vista y obliga a cargar el catálogo donde no existe.

### D3 (D-C). Capa de datos: alta e identificadores en `js/datos.js`

`window.Datos` expone además:

- `siguienteId(coleccion)`: devuelve `max(id) + 1` sobre la colección recibida, como número; si está vacía, `1`.
- `agregarLibro(libro)`: asigna `id` con `siguienteId(libros)`, inserta el objeto en `libros` y lo devuelve.
- `agregarCliente(cliente)`: ídem sobre `clientes`.

Las funciones mutan los arrays ya expuestos por referencia, de modo que cualquier vista de la misma página que lea `Datos.libros` / `Datos.clientes` ve el alta. El seed no se modifica.

**Por qué**: concentrar la mutación en la capa de datos evita que `altas.js` conozca detalles del id y deja C-05/C-06 con una única puerta de escritura. Ids numéricos mantienen la convención de C-03 y `max(id) + 1` es robusto aunque se borren registros en el futuro.

**Alternativa descartada**: calcular el id en `altas.js` — dispersa la regla y facilita duplicados si otra vista da de alta.

### D4 (D-D). Selects y checkboxes regenerados desde los datos

Al inicializar cada página:

- `#libro-editorial` y `#libro-genero` se vacían con `replaceChildren` y se reconstruyen con `createElement("option")` + `textContent` + `value`. Se **preserva la primera opción literal del HTML** (`value=""`, «Elegí una editorial» / «Sin clasificar»); las demás se generan desde `Datos.editoriales` / `Datos.generos`.
- `#libro-autores-opciones` se vacía y se reconstruye con un `createElement("div")` con clase `opcion-casilla` por autor, conteniendo `input[type=checkbox]` (`id="libro-autor-<id>"`, `name="autorIds"`, `value="<id>"`) y `<label for>`. Reemplaza los tres checkboxes estáticos.

La regeneración se repite tras un alta (los datos pueden haber cambiado) y también se puede invocar desde consola. Se selecciona por `id` y `name`, nunca por clase; el único uso de clase es replicar el contenedor visual `.opcion-casilla` que ya estiliza el CSS existente (no se agrega CSS).

**Por qué**: la consigna exige que las opciones se generen desde los datos; regenerar elimina la divergencia entre HTML estático y seed y evita ids duplicados al reconstruir. Preservar el texto literal de la primera opción mantiene el contrato visual y de accesibilidad ya validado en C-01/C-02.

**Alternativas descartadas**: (a) dejar las opciones estáticas y agregar solo las nuevas — no cumple «se generan a partir de los datos» y acumula duplicados al re-renderizar; (b) guardar estado/patch de opciones — introduce estado innecesario para 2 editoriales y 2 géneros.

### D5 (D-E). Listados por re-render completo con plantilla y fragmento

`renderLibros(libros)` y `renderClientes(clientes)` vacían `#libros-lista` / `#clientes-lista` con `replaceChildren` sobre un `DocumentFragment` y, por cada registro, clonan `#plantilla-fila-libro` / `#plantilla-fila-cliente` con `plantilla.content.firstElementChild.cloneNode(true)`. Asignan `data-libro-id` / `data-cliente-id` y escriben cada `[data-campo]` con `textContent`:

- Libro: título, ISBN, editorial resuelta (`Datos.buscarEditorial`), género resuelto o «Sin clasificar», autores unidos con `", "` y precio con `toFixed(2)`.
- Cliente: `nombre` del modelo se escribe en `data-campo="nombreCompleto"` y el email en `data-campo="email"`.

Al inicializar, el re-render reemplaza las 4 y 3 filas estáticas por los 6 libros y 3 clientes del seed. Si la colección está vacía se muestra `#libros-mensaje-vacio` / `#clientes-mensaje-vacio`.

**Por qué**: es el patrón ya establecido en C-03, evita duplicados con el HTML estático y garantiza que el listado siempre refleje los datos. `textContent` cumple RN-04 y la regla dura 5.

**Alternativas descartadas**: (a) insertar una fila al final — duplica el seed y deja filas obsoletas; (b) `innerHTML` con plantillas de texto — prohibido por la regla dura 5.

### D6 (D-F). Validaciones puras y textos de error exactos

`window.Validaciones` expone:

- `normalizarIsbn(valor)`: `String(valor).trim()` y quita espacios y guiones (`/[\s-]/g`). Para comparar, además `toLowerCase()`.
- `normalizarEmail(valor)`: `String(valor).trim().toLowerCase()`.
- `validarLibro(entrada, libros)`: `entrada` es `{ titulo, isbn, precio, editorialId, generoId, autorIds }` tal como llega del formulario (strings y array de strings). Devuelve `{ valido, errores: [textos], datosNormalizados }`.
- `validarCliente(entrada, clientes)`: ídem para `{ nombreCompleto, email }`.

**Reglas de validación de libro (RN-05..RN-09)**:

- Título `trim() === ""` → error de obligatorio. ISBN `trim() === ""` → error de obligatorio.
- ISBN: se compara normalizado contra todos los libros (sin espacios, sin guiones, sin distinguir mayúsculas). Coincidencia → error de duplicado. El valor guardado conserva el texto con `trim()` (no se guarda despojado de guiones, para no alterar lo que escribió el usuario).
- Precio: si el texto `trim() === ""` → obligatorio (se evalúa **antes** de convertir, porque `Number("") === 0`). Si `Number(...)` es `NaN` → no numérico. Si `<= 0` → debe ser mayor que cero. Se guarda como número.
- Editorial: `""` → «Elegí una editorial»; si `Datos.buscarEditorial` devuelve `null` → no existe.
- Autores: sin ids seleccionados → al menos uno; en caso contrario se comparan **cantidades**: ids normalizados a `String` y únicos contra el resultado de `Datos.buscarAutores(ids)`; si las longitudes difieren, hay al menos un autor inexistente. Esto es obligatorio porque `buscarAutores` omite ids inexistentes en silencio. Se guardan como números.
- Género: `""` → se **omite** `generoId` del registro (ni `""` ni `0`); valor no vacío e inexistente → error. Se guarda como número.

**Reglas de validación de cliente (RN-10..RN-12)**:

- Nombre `trim() === ""` → obligatorio; se guarda con `trim()`.
- Email `trim() === ""` → obligatorio; formato `^[^\s@]+@[^\s@]+\.[^\s@]+$` sobre el valor con `trim()`; unicidad comparando `trim().toLowerCase()` contra todos los clientes. Se guarda con `trim()` (sin forzar minúsculas, para no alterar el dato).

**Textos exactos** (un `<li>` por error, escritos con `textContent`, en el orden en que se detectan):

| Libro | Cliente |
|---|---|
| `El título es obligatorio.` | `El nombre completo es obligatorio.` |
| `El ISBN es obligatorio.` | `El email es obligatorio.` |
| `El ISBN ya está registrado en otro libro.` | `El email no tiene un formato válido.` |
| `El precio es obligatorio.` | `El email ya está registrado.` |
| `El precio debe ser un número.` | |
| `El precio debe ser mayor que cero.` | |
| `Elegí una editorial.` | |
| `La editorial seleccionada no existe.` | |
| `Elegí al menos un autor.` | |
| `Uno de los autores seleccionados no existe.` | |
| `El género seleccionado no existe.` | |

**Por qué**: funciones puras sin DOM son verificables desde la consola (la KB las exige), y los textos quedan fijados antes del apply para que la verificación manual sea reproducible. No se agregan `aria-invalid`/`aria-describedby` porque no hay estilos para ellos y la regla dura 3 prohíbe CSS inline; el bloque `.mensaje--error` con `<ul>` ya existe y está estilizado.

**Alternativas descartadas**: (a) un solo texto concatenado — el HTML ya prevé una lista y el mensaje por error es más claro; (b) validar por campo con mensajes junto a cada input — requiere CSS nuevo; (c) validación nativa del navegador — `novalidate` la desactiva y no cubre unicidad.

### D7 (D-G). Envío: `preventDefault`, alta atómica, limpieza y mensajes excluyentes

El `submit` de cada formulario hace `preventDefault()` **siempre**, antes de validar (los formularios apuntan a la misma página con `method="get"`; sin esto se recarga y se pierde todo). Luego:

1. Vacía la lista de errores (`replaceChildren()`) y oculta ambos mensajes.
2. Arma la entrada desde el formulario: `#libro-titulo`, `#libro-isbn`, `#libro-precio`, `#libro-editorial`, `#libro-genero` y `querySelectorAll('input[name="autorIds"]:checked')`.
3. Llama a la validación pura. Si hay errores: agrega un `<li>` con `textContent` por error, muestra `#libros-mensaje-error` y no toca los datos.
4. Si es válido: `Datos.agregarLibro(datosNormalizados)` / `agregarCliente`, re-renderiza el listado **y** regenera los selects/checkboxes, muestra el mensaje OK y limpia el formulario (editorial a «Elegí una editorial», género a «Sin clasificar», ninguna casilla marcada, campos de texto vacíos).

No se deshabilita el botón ni se agregan guardas anti-doble-alta: no está exigido y complica la verificación manual.

**Por qué**: cumple RN-13 (envío controlado, errores cerca, alta solo si todo pasa) y RN-14 (actualización sin recarga) sin estado extra.

**Alternativa descartada**: limpiar el formulario solo en éxito pero conservar los errores visibles hasta el próximo submit — confunde el estado; el diseño vacía y recalcula en cada intento.

### D8 (D-H). Limitación transitoria: multipágina sin persistencia

Hasta C-06 no hay `localStorage`: `datos.js` se recarga en cada navegación y reinicia el seed. Por lo tanto:

- F2/F3 se cumplen y se verifican **dentro de la misma página**: tras el alta, el listado y las opciones relacionadas de esa página cambian sin recargar.
- La propagación al catálogo de `index.html` y a los selects de `ventas.html` **no es observable** en C-04 y queda diferida: los selects de ventas a C-05, la persistencia entre páginas a C-06.
- Un alta se pierde al navegar o recargar. El aviso de maqueta sigue siendo correcto.

**Por qué**: adelantar persistencia invadiría C-06 y rompería la separación del roadmap; ocultar la limitación haría fallar la verificación manual con una expectativa imposible. Es la misma estrategia con la que C-03 documentó la inconsistencia 4-vs-6.

**Alternativas descartadas**: (a) adelantar `localStorage` mínimo — fuera de alcance y cambia el contrato de C-06; (b) mantener los datos en `sessionStorage` como puente — inventa una persistencia no pedida y con claves que C-06 tendría que migrar.

### D9 (D-I). Verificación manual y W3C, sin tests automatizados

La regla dura 1 prohíbe test runners y archivos de test. `tasks.md` incluye un bloque de verificación manual con los casos de F2/F3 (ISBN duplicado y nuevo; email inválido, duplicado en mayúsculas y nuevo), los estados del formulario, la limpieza, la actualización del listado y de los selects, y la apertura con `file://`. Cada caso tiene una columna de «resultado observado» que completa el apply. Se valida además `libros.html` y `clientes.html` con el W3C Nu HTML Checker.

**Por qué**: es el mecanismo de calidad definido por el proyecto; los casos provienen de la tabla de la consigna y de `07_flujos_principales.md`.

### D10 (D-J). Restricciones duras de implementación

- IIFE con `"use strict"` y global (`window.Validaciones`, `window.Altas`), sin `type="module"` (rompe en `file://`).
- Prohibido `innerHTML`, `outerHTML`, `insertAdjacentHTML` y `document.write`; todo texto con `textContent`.
- Selección por `id`, `name` y `data-*`; nunca por clase (la clase solo se usa para crear el contenedor `.opcion-casilla` que el CSS existente estiliza).
- Mostrar/ocultar solo con el atributo `hidden` (el CSS ya tiene `[hidden] { display: none !important; }`).
- Sin CSS nuevo ni inline; sin librerías, npm, build ni CDN.
- Guardas: cada inicializador hace `return` si faltan sus hooks, para poder cargar los scripts en cualquier vista.

## Risks / Trade-offs

- **[Alta perdida al navegar o recargar]** Hasta C-06 no hay persistencia. → Se documenta como limitación transitoria (D8); la verificación de F2/F3 se hace en la misma página y el README de C-06 explicará la recuperación.
- **[F2/F3 mencionan «catálogo y selector de ventas»]** No son observables entre páginas en C-04. → `ventas.html` queda fuera (C-05) y el catálogo se regenera al abrir `index.html` con el seed; queda escrito en proposal/design/tasks.
- **[`libros.html` y `clientes.html` no cargan scripts]** Sin `datos.js` no existe `window.Datos`. → Se agregan las tres etiquetas `defer` en orden; verificación con `file://`.
- **[Datos solo en memoria]** Cualquier navegación reinicia el seed. → Igual que arriba; no se adelanta almacenamiento.
- **[`buscarAutores` omite ids inexistentes]** `[1, 999]` devuelve solo el autor 1 sin error. → La validación compara cantidad de ids únicos contra cantidad de autores encontrados.
- **[Mapeo modelo ↔ formulario ↔ `data-campo`]** Cliente usa `nombre` en datos y `nombreCompleto` en el formulario y la tabla; libro usa `editorialId`/`generoId`/`autorIds` y la tabla usa `editorial`/`genero`/`autores`. → El render resuelve relaciones y mapea explícitamente; se documenta en D5.
- **[`escribirCampo` de `catalogo.js` es privada]** No se puede reutilizar. → Se duplica la escritura mínima en `altas.js` (no se exporta ni se toca `catalogo.js`).
- **[Filas estáticas y `<template>`]** `#libros-lista` tiene 4 filas y `#clientes-lista` 3; los `<template>` no están en el DOM consultable. → Re-render con `replaceChildren` y `plantilla.content.firstElementChild.cloneNode(true)`.
- **[`novalidate` desactiva la validación nativa]** `required`, `min`, `step` y `type="email"` no bloquean el envío. → Toda la validación es JS; el precio vacío se detecta antes de convertir.
- **[`action` + `method="get"` sin `preventDefault`]** Recarga y pérdida de datos. → `preventDefault()` incondicional en el submit.
- **[Ids repetidos entre páginas]** `#aviso-maqueta` se repite en cada documento, lo cual es válido. → Los scripts solo consultan el documento actual y usan guardas.
- **[Checkboxes con `name="autorIds"` repetido]** `form.elements.autorIds.value` no sirve. → Se leen con `querySelectorAll('input[name="autorIds"]:checked')` y se convierten a número.
- **[Género vacío vs. campo ausente]** El seed omite `generoId`. → Con «Sin clasificar» se omite el campo; nunca se guarda `""` ni `0`.
- **[Editorial con opción vacía y `required` inerte]** → Se rechaza `""` en JS y se verifica existencia con `buscarEditorial`.
- **[Normalización de ISBN y email]** Sin regla explícita se cuelan duplicados. → ISBN sin espacios ni guiones y sin distinguir mayúsculas; email `trim().toLowerCase()`; se comparan contra todos los registros.
- **[`getAttribute`/`data-campo` y `textContent`]** Los mensajes contienen `<p>` y `<ul>`; reemplazar su estructura con `innerHTML` violaría la regla. → Solo se escriben nodos hoja (`#libros-errores`, celdas `[data-campo]`).
- **[CSS sin estilos de error por campo]** → No se marcan campos; el error se concentra en `.mensaje--error`.
- **[Aviso de maqueta potencialmente engañoso]** Tras C-04 las altas funcionan pero no persisten. → Se conserva literal porque sigue siendo cierto y la spec lo exige hasta la etapa 6.
- **[Inconsistencia 4 vs. 6 libros]** El HTML solo trae 4. → El primer render muestra los 6 del seed sin duplicar.
- **[`ventas.html` desactualizado]** Solo lista libros 1–4. → Queda explícitamente para C-05.
- **[`catalogo.js` se auto-inicializa]** Si se cargara en estas páginas no renderiza nada útil. → No se carga; `altas.js` tiene su propio wiring con guardas.
- **[Precio con dos decimales]** El input `step="0.01"` no restringe por `novalidate`. → Se acepta cualquier número > 0 y se guarda como número; la tabla y el catálogo muestran `toFixed(2)`.
- **[W3C y `defer`]** Agregar `<script defer src>` es válido. → Se valida cada página modificada con el Nu HTML Checker.

## Migration Plan

No hay migración de datos: el seed vive en memoria y no existe almacenamiento previo. El cambio es aditivo: dos archivos JS nuevos, tres funciones agregadas a `datos.js` y tres etiquetas `<script>` por vista. Reversión: quitar las etiquetas `<script>` de `libros.html` y `clientes.html` y borrar `js/validaciones.js` y `js/altas.js`; las funciones agregadas a `datos.js` quedan sin uso y no afectan a C-03.

## Open Questions

Ninguna que afecte specs, enfoque o desglose de tareas. Quedan diferidas, por dependencia de roadmap: la generación de los selects de libros y clientes de `ventas.html` (C-05), el formato de id y fecha de venta (C-05), el tratamiento del libro repetido en una venta (C-05) y las claves y estructura de `localStorage` (C-06).
