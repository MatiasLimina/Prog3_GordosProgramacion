# Design

## Context

El proyecto ya tiene las cinco vistas multipágina (`index.html` es Catálogo) con un contrato de hooks fijado en C-01: JS selecciona por `id`, `name` y `data-*`, nunca por clase; se muestra/oculta con el atributo `hidden`; las tarjetas se clonan desde `#plantilla-tarjeta-libro`; los textos se escriben con `textContent`. C-01 y C-02 están archivados; no existe `js/` ni ninguna etiqueta `<script>`.

El catálogo actual de `index.html` tiene `<ul id="catalogo-lista">` con 4 `<li data-libro-id>` estáticos, un formulario `#catalogo-busqueda` (`role="search"`, `input#catalogo-buscar[name="busqueda"]`, botón "Buscar") y dos mensajes ocultos: `#catalogo-mensaje-vacio` y `#catalogo-mensaje-sin-resultados`. Ver `proposal.md` para la motivación.

## Goals / Non-Goals

**Goals:**
- Dejar un módulo de datos reutilizable por C-04 (altas), C-05 (ventas) y C-06 (persistencia) sin reescribirlo.
- Separar datos, filtro/render y eventos en unidades identificables, cumpliendo la consigna y la RN-04.
- Mantener el HTML válido y funcional sin JavaScript (los 4 libros de ejemplo siguen en el marcado).

**Non-Goals:**
- Persistencia (`localStorage`), altas, ventas e historial (C-04, C-05, C-06).
- Renderizar las tablas de `libros.html` y `ventas.html`.
- Normalización de acentos en la búsqueda (`jardin` no encuentra `jardín`): no lo pide la KB ni la consigna.
- Modularización con `type="module"` o un bundler.

## Decisions

### D1. Dos archivos JS clásicos, sin módulos

- `js/datos.js`: colecciones (`libros`, `editoriales`, `generos`, `autores`, `clientes`) y helpers de consulta (`buscarEditorial`, `buscarGenero`, `buscarAutores`, `buscarLibro`), expuestos en `window.Datos`.
- `js/catalogo.js`: `filtrarLibros`, `renderCatalogo`, `actualizarEstados`, `inicializarCatalogo`, expuestos en `window.Catalogo`.

Ambos se cargan en `index.html` con `<script defer src="...">`, en ese orden. Se usa IIFE + objeto global en lugar de `type="module"` porque los módulos no cargan con `file://` por CORS y la consigna exige abrir `index.html` con doble clic. **Alternativa considerada**: un único `js/catalogo.js` con secciones — se descarta porque C-04/C-05 necesitan los datos en varias páginas y duplicarlos generaría divergencia.

### D2. Seed definitivo (ids numéricos)

Se reutilizan los 4 libros del HTML estático y se agregan 2 nuevos con ISBN único y relaciones válidas:

| id | Título | ISBN | Precio | editorialId | generoId | autorIds |
|----|--------|------|--------|-------------|----------|----------|
| 1 | El jardín de las horas | 978-950-000-001-1 | 1500.00 | 1 | 1 | [1] |
| 2 | Mapas del silencio | 978-950-000-002-8 | 2000.00 | 2 | 2 | [2, 3] |
| 3 | Cuentos de medianoche | 978-950-000-003-5 | 3200.50 | 1 | — (sin género) | [3] |
| 4 | La ciudad invisible | 978-950-000-004-2 | 2750.00 | 2 | 1 | [1, 2] |
| 5 | El arte de la memoria | 978-950-000-005-9 | 1890.00 | 2 | 2 | [1, 3] |
| 6 | Relatos del río | 978-950-000-006-6 | 2400.75 | 1 | — (sin género) | [2] |

- Editoriales: `1 Ediciones del Sur`, `2 Editorial Faro`.
- Géneros: `1 Novela`, `2 Ensayo`.
- Autores: `1 Ana Ríos`, `2 Bruno Paz`, `3 Carla Vega`.
- Clientes: `1 María Gómez / maria.gomez@example.com`, `2 Juan Pérez / juan.perez@example.com`, `3 Lucía Fernández / lucia.fernandez@example.com`.

Los ids son números en el modelo; los helpers de consulta normalizan el valor recibido con `String(...)` para tolerar los ids que llegan como texto desde `data-*` y `option.value` (necesario en C-04/C-05). `generoId` se omite cuando el libro no tiene género (no se usa `null`), de modo que «Sin clasificar» se derive de la ausencia del campo.

### D3. Render por clonado de plantilla

`renderCatalogo(libros)` vacía `#catalogo-lista` con `replaceChildren()` sobre un `DocumentFragment`, y por cada libro clona `#plantilla-tarjeta-libro`, asigna `data-libro-id` al `<li>` y escribe cada `[data-campo]` con `textContent`. No se construye marcado por concatenación ni se usa `innerHTML` (RN-04). **Alternativa considerada**: `innerHTML` con template strings — descartada por seguridad y por la regla dura 5.

Los 4 `<li>` estáticos se conservan como contenido de respaldo sin JS; el primer render los reemplaza, así que no se duplican. Al terminar de pintar, `renderCatalogo` invoca `actualizarEstados(Datos.libros.length, libros.length)` para que lista y mensajes queden siempre coherentes (ver D6).

### D4. Formato de precio

`precio.toFixed(2)` produce `1500.00` / `3200.50`, idéntico al marcado actual y a los casos manuales (`1500`, `3200.5`). **Alternativa considerada**: `Intl.NumberFormat('es-AR')` genera `1.500,00`; se descarta para no contradecir la presentación ya validada en C-01/C-02 y porque la KB fija "dos decimales", no un formato regional.

### D5. Filtro puro y búsqueda en vivo

`filtrarLibros(libros, consulta)` devuelve un array nuevo y no muta la entrada:
`consulta.trim().toLowerCase()` comparado con `libro.titulo.toLowerCase()` usando `includes`. Los acentos no se normalizan (ver Non-Goals). El evento `input` de `#catalogo-buscar` vuelve a renderizar; el `submit` de `#catalogo-busqueda` hace `preventDefault()` y aplica el mismo filtro, para no recargar ni perder el estado.

### D6. Estados con `hidden`

`actualizarEstados(totalLibros, resultados)`:
- `totalLibros === 0` → muestra `#catalogo-mensaje-vacio`, oculta el de sin resultados y la lista.
- `resultados === 0` → muestra `#catalogo-mensaje-sin-resultados`, oculta el de vacío y la lista.
- caso contrario → oculta ambos y muestra la lista.

Se alterna el atributo `hidden` (el CSS ya garantiza `[hidden] { display: none !important; }`). El aviso de maqueta `#aviso-maqueta` se conserva porque `navegacion-vistas` lo exige en todas las vistas hasta la etapa 6.

### D7. Inicialización

Con `defer`, el DOM ya está parseado cuando corre `catalogo.js`; `inicializarCatalogo()` se invoca al final del archivo, sin `DOMContentLoaded`. Registra `input` y `submit`, y hace el primer render con `Datos.libros`.

## Risks / Trade-offs

- **[Inconsistencia transitoria]** Hasta C-04, `libros.html` y `ventas.html` siguen mostrando 4 libros estáticos mientras el catálogo muestra 6. → Es esperada por el orden del roadmap; se documentará en el README (C-06) y no se toca el HTML de esas vistas.
- **[Módulos ES bloqueados en `file://`]** → Se usan scripts clásicos con `defer`; queda verificado abriendo `index.html` con doble clic.
- **[Acentos no normalizados]** `"JARDIN"` no encuentra «jardín». → Se documenta como límite deliberado; el caso manual de la consigna usa una parte del título en mayúsculas conservando la tilde.
- **[Mutación accidental del seed]** Al exponer `window.Datos` para verificación manual, la consola puede alterar los arrays. → Se recarga la página para restaurar el seed; la persistencia y su recuperación llegan en C-06.
- **[Duplicación de ids al dar de alta]** C-04 deberá calcular el siguiente id; este change deja los ids numéricos contiguos para hacerlo trivial (`max(id) + 1`).
- **[Lista oculta y accesibilidad]** Ocultar la lista con `hidden` mientras se muestra un mensaje evita que un lector de pantalla anuncie contenido obsoleto. → Los mensajes ya tienen `role="status"`.

## Migration Plan

No hay migración de datos: no existe almacenamiento previo. El cambio es aditivo (nuevos archivos JS + dos etiquetas `<script>` en `index.html`). Reversión: quitar las dos etiquetas `<script>` de `index.html` y borrar `js/`; el catálogo vuelve a mostrar los 4 libros estáticos.

## Open Questions

Ninguna que afecte specs, enfoque o desglose de tareas. Las decisiones pendientes de C-05 y C-06 (formato de id/fecha de venta, claves de `localStorage`, tratamiento del libro repetido) pertenecen a esos changes y no condicionan este.
