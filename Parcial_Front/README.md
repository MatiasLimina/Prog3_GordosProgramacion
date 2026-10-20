# Librería Papel y Tinta — Frontend

TPI Programación III. Frontend de una librería: catálogo, libros, clientes, ventas simuladas e historial, 100 % en el navegador, sin backend.

## Integrantes

- (Completar con los nombres del equipo antes de la entrega.)

## Cómo abrir la aplicación

No se requiere npm ni herramientas de build. Abrir `index.html` con doble clic (protocolo `file://`) en cualquier navegador moderno. La navegación se realiza desde el menú `<nav>` entre las vistas: Catálogo, Libros, Clientes, Ventas e Historial.

## Estructura del proyecto

```
Parcial_Front/
├── index.html          Catálogo y buscador
├── libros.html         Alta y listado de libros
├── clientes.html       Alta y listado de clientes
├── ventas.html         Composición y confirmación de ventas
├── historial.html      Historial y detalle de ventas
├── css/estilos.css     Identidad visual (CSS externo)
├── js/
│   ├── datos.js        Datos locales y seed
│   ├── persistencia.js Carga/guardado en localStorage
│   ├── validaciones.js Validaciones puras
│   ├── catalogo.js     Catálogo y filtro
│   ├── altas.js        Altas de libros y clientes
│   ├── ventas.js       Composición y confirmación
│   └── historial.js    Render del historial
└── README.md
```

## Funcionalidades implementadas

- Catálogo generado desde datos locales, con filtro por título (sin distinguir mayúsculas, coincidencia parcial, `trim`).
- Alta de libros (título, ISBN único, precio > 0, editorial, género opcional «Sin clasificar», uno o más autores) y de clientes (nombre completo, email válido y único), con validación y actualización sin recarga.
- Venta simulada: selección de cliente, renglones con libro y cantidad entera > 0 (libro repetido suma cantidad), cambio/quita de renglones, subtotales y total con 2 decimales, confirmación con precio unitario histórico.
- Historial de ventas con listado y detalle de renglones; ventas inmutables (sin editar ni eliminar).
- Persistencia en `localStorage`: primer inicio carga ejemplos; reaperturas recuperan lo guardado sin duplicar.

## Ubicación de los datos iniciales

El seed vive en `js/datos.js`: 6 libros, 2 editoriales, 2 géneros, 3 autores, 3 clientes y 2 ventas de ejemplo. Se carga la primera vez que se abre la aplicación en un perfil sin datos guardados; a partir de entonces se leen desde `localStorage`.

## Persistencia (`localStorage`)

Claves utilizadas (prefijo `libreria:`):

- `libreria:libros` — array de libros.
- `libreria:clientes` — array de clientes.
- `libreria:ventas` — array de ventas.

Estructura de una venta (para la prueba del precio histórico):

```json
{
  "id": 1,
  "fecha": "2026-10-01T00:00:00.000Z",
  "clienteId": 1,
  "clienteNombre": "María Gómez",
  "renglones": [
    { "libroId": 1, "titulo": "El jardín de las horas", "cantidad": 2, "precioUnitario": 1500, "subtotal": 3000 },
    { "libroId": 2, "titulo": "Mapas del silencio", "cantidad": 1, "precioUnitario": 2000, "subtotal": 2000 }
  ],
  "total": 5000
}
```

El `precioUnitario` de cada renglón se **copia al confirmar** y no se relee del catálogo, por lo que la venta conserva su importe aunque cambie el precio del libro.

### Funcionamiento y límites

- El almacenamiento depende del navegador, del perfil y de la ubicación (protocolo `file://` o dominio). No se comparte entre usuarios ni entre navegadores.
- Si se borran los datos del navegador, se pierden las altas y ventas; el próximo inicio vuelve a cargar los ejemplos.
- Los datos se guardan de forma síncrona tras cada alta o venta confirmada.

## Imágenes

No se utilizan imágenes ajenas en la aplicación; no hay procedencia que declarar.

## Verificación manual (resultados observados)

| Caso | Esperado | Resultado observado |
|------|----------|---------------------|
| Búsqueda en mayúsculas parcial; vacía; inexistente | Coincidencias sin distinguir caso; catálogo completo; mensaje sin resultados | Verificado en navegador: `EL JARDÍN` devuelve «El jardín de las horas»; búsqueda vacía muestra los 6 libros; búsqueda `zzz` muestra el mensaje «sin resultados». |
| Libro con ISBN existente y luego nuevo | Duplicado rechazado; válido en catálogo y selección de venta | Verificado: ISBN `978-950-000-001-1` (y su variante sin guiones) se rechaza; ISBN nuevo se acepta y aparece en el listado y en el selector de ventas. |
| Cliente con email inválido, existente en mayúsculas, nuevo | Se rechazan los dos primeros; el nuevo aparece | Verificado: `maria.gomez` y `  MARIA.GOMEZ@EXAMPLE.COM ` se rechazan; email nuevo se acepta y aparece en el listado. |
| Venta sin cliente, cantidad 0/negativa/decimal; libro repetido | No se confirma; no se crea otro renglón | Verificado: no se registra venta y se listan errores; el libro repetido suma cantidad al renglón existente. |
| Venta 2 × 1500 y 1 × 2000 | Subtotales 3000 y 2000; total 5000; detalle en historial | Verificado: subtotales 3000.00 y 2000.00, total 5000.00; el detalle del Historial muestra los mismos valores. |
| Cambio del precio del catálogo en `localStorage` y recarga | La venta conserva precio unitario, subtotales y total | Verificado: tras modificar `libreria:libros` y recargar, la venta muestra 1500.00 / 2000.00 y total 5000.00. |
| Recarga tras altas y venta | Datos recuperados sin duplicar ejemplos ni ventas | Verificado: altas de libro/cliente y venta confirmada persisten tras recargar; no se duplican los ejemplos. |
| Teclado y anchos 320/1280 px | Foco visible, controles usables, tabla con scroll propio | Verificado visualmente: foco visible en controles, sin scroll horizontal de página a 320 y 1280 px, tablas con scroll propio. |