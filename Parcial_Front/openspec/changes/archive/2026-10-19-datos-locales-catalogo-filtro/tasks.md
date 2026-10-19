# Tasks

> Sin tests automatizados (regla dura 1): cada tarea se verifica con comportamiento observable en el navegador, consola de DevTools o el W3C Nu HTML Checker.

## 1. Datos locales

- [x] 1.1 Crear `js/datos.js` con las colecciones `editoriales`, `generos`, `autores`, `clientes` y `libros` del seed de `design.md` §D2 (ids numéricos, 2/2/3/3/6 registros) expuestas en `window.Datos` mediante una IIFE; verificar en consola que `Datos.libros.length === 6`, `Datos.editoriales.length === 2`, `Datos.generos.length === 2`, `Datos.autores.length === 3` y `Datos.clientes.length === 3`
- [x] 1.2 Agregar a `js/datos.js` los helpers `buscarLibro`, `buscarEditorial`, `buscarGenero` y `buscarAutores` con normalización de id a texto; verificar en consola que `Datos.buscarEditorial(1).nombre === "Ediciones del Sur"`, `Datos.buscarAutores([2, 3])` devuelve 2 autores y `Datos.buscarLibro("3").titulo === "Cuentos de medianoche"`
- [x] 1.3 Verificar la integridad del seed con un recorrido en consola: cada libro tiene editorial existente, al menos un autor existente, `generoId` ausente o existente, ISBN único y precio numérico > 0; comprobar además que el libro 3 y el 6 no tienen `generoId` y que los libros 2, 4 y 5 tienen 2 autores

## 2. Filtro, render y estados

- [x] 2.1 Crear `js/catalogo.js` con `filtrarLibros(libros, consulta)` pura (sin mutar la entrada) que aplique `trim`, `toLowerCase` e `includes` sobre el título; verificar en consola `Catalogo.filtrarLibros(Datos.libros, "JARDÍN")` → 1 resultado, `"  mapas  "` → 1, `"zzz"` → 0 y `"   "` → 6
- [x] 2.2 Implementar `renderCatalogo(libros)` clonando `#plantilla-tarjeta-libro`, asignando `data-libro-id` al `<li>` y escribiendo cada `[data-campo]` con `textContent`, reemplazando la lista con `replaceChildren()` sobre un `DocumentFragment`; verificar en `index.html` que se ven 6 tarjetas, sin duplicados de los 4 libros estáticos y sin usar `innerHTML` en el archivo
- [x] 2.3 Formatear el precio con dos decimales y unir los autores con `, `; verificar que el libro 3 muestra `Sin clasificar` y `3200.50`, y que el libro 2 muestra `Bruno Paz, Carla Vega`
- [x] 2.4 Implementar `actualizarEstados(totalLibros, resultados)` alternando el atributo `hidden` sobre `#catalogo-lista`, `#catalogo-mensaje-vacio` y `#catalogo-mensaje-sin-resultados` según `design.md` §D6; verificar en consola con `Datos.libros.length = 0; Catalogo.renderCatalogo(Datos.libros)` que aparece solo el mensaje de vacío y la lista queda oculta
- [x] 2.5 Implementar `inicializarCatalogo()` que registre `input` en `#catalogo-buscar` y `submit` en `#catalogo-busqueda` con `preventDefault()`, y haga el primer render; verificar que al escribir se filtra en vivo, que Enter no recarga la página y que la URL no cambia

## 3. Integración en la vista Catálogo

- [x] 3.1 Agregar a `index.html`, antes de `</body>`, `<script defer src="js/datos.js"></script>` y `<script defer src="js/catalogo.js"></script>` en ese orden; verificar con doble clic sobre `index.html` (protocolo `file://`) que la consola no muestra errores y el catálogo lista 6 libros
- [x] 3.2 Verificar el respaldo sin JavaScript: deshabilitar JS en el navegador y comprobar que `index.html` sigue mostrando los 4 libros estáticos y el buscador, sin errores de estructura
- [x] 3.3 Validar `index.html` en el W3C Nu HTML Checker y confirmar 0 errores

## 4. Verificación manual del flujo F1

- [x] 4.1 Ejecutar y registrar los casos de `knowledge-base/07_flujos_principales.md` §F1: `JARDÍN` → coincidencia de «El jardín de las horas» sin distinguir mayúsculas; búsqueda vacía → 6 libros; `zzz` → 0 libros y mensaje «No se encontraron libros con ese título.»; anotar el resultado real observado
- [x] 4.2 Verificar que el buscador conserva el foco visible, se alcanza con Tab y el filtro se puede limpiar con teclado (borrar el texto restaura el catálogo completo)
- [x] 4.3 Revisar a 320 px y 1280 px que el catálogo generado no provoca scroll horizontal de página y que las tarjetas conservan el layout de C-02

## Resultados observados de la verificación

Ejecutado el 2026-10-19 sobre `index.html` abierto con `file://` en Chrome headless (CDP), con Node 24 para la lógica pura y el W3C Nu HTML Checker para el marcado.

| Caso | Resultado observado |
|------|---------------------|
| Carga inicial con JS | 6 tarjetas, ids 1–6, sin duplicar los 4 `<li>` estáticos; mensajes ocultos y lista visible |
| Precios | Los 6 precios muestran dos decimales (`1500.00`, `2000.00`, `3200.50`, `2750.00`, `1890.00`, `2400.75`) |
| Libro 3 (sin género) | Género `Sin clasificar`, precio `3200.50`, autores `Carla Vega` |
| Libro 2 (varios autores) | Autores `Bruno Paz, Carla Vega` |
| Libro 5 (varios autores) | Autores `Ana Ríos, Carla Vega` |
| Búsqueda `JARDÍN` | 1 resultado: «El jardín de las horas» (sin distinguir mayúsculas) |
| Búsqueda `  mapas  ` | 1 resultado: «Mapas del silencio» (trim aplicado) |
| Búsqueda `CIUDAD` | 1 resultado: «La ciudad invisible» |
| Búsqueda vacía / solo espacios | 6 libros |
| Búsqueda `zzz` | 0 libros; visible `#catalogo-mensaje-sin-resultados`; lista y mensaje de vacío ocultos |
| Limpiar la búsqueda | Vuelven los 6 libros; ambos mensajes ocultos |
| Envío del formulario | `preventDefault` aplicado; la URL no cambia y no hay recarga |
| Foco del buscador | `document.activeElement` es `#catalogo-buscar`; foco visible por CSS de C-02 |
| Catálogo sin libros (`Datos.libros.length = 0`) | Visible `#catalogo-mensaje-vacio`; sin resultados y lista ocultos; 0 tarjetas |
| Sin JavaScript | 4 libros estáticos, buscador, botón y aviso de maqueta presentes; 5 enlaces de navegación |
| 320 px | `scrollWidth` 305 ≤ `clientWidth` 305; sin desbordes de elementos |
| 1280 px | `scrollWidth` 1265 ≤ `clientWidth` 1265; sin desbordes de elementos |
| `innerHTML` en `js/` e `index.html` | 0 coincidencias (tampoco `outerHTML`, `insertAdjacentHTML` ni `document.write`) |
| W3C Nu HTML Checker (`index.html`) | 0 mensajes (0 errores, 0 advertencias) |
