# 01 — Visión y objetivos

## Propósito
TPI de Programación III (Tecnicatura Universitaria en Programación a Distancia, Prof. Matías Torres): construir el **frontend de una librería** que presenta su catálogo y registra libros, clientes y ventas. Todo se simula en el navegador; no hay backend.

## Objetivos
- Construir interfaces con HTML semántico y CSS propio.
- Relacionar formularios, listados y navegación con las entidades del proyecto.
- Aplicar JavaScript nativo: datos locales, DOM, eventos.
- Validar entradas y comprobar el comportamiento con casos manuales reproducibles.

## Objetivos por actor
- **Operador de la librería** (único actor): consultar y filtrar el catálogo, dar de alta libros y clientes, componer y confirmar ventas, consultar el historial.

## Alcance
- 5 vistas: Catálogo, Libros, Clientes, Ventas, Historial, con navegación clara.
- Etapa 1 (Ej. 1–2): estructura HTML + CSS con datos estáticos, una interacción básica (filtro o validación); lo pendiente se marca como maqueta.
- Etapa 2 (Ej. 3–6): datos locales, filtro, altas con validación, venta simulada e historial, persistencia en localStorage, README con casos manuales.
- Evaluación (100 pts): HTML 20, CSS 20, Datos/catálogo 15, Altas 15, Ventas 20, Cierre 10.

## Fuera de alcance
- API, backend, base de datos, servidor, login real, `fetch`.
- Stock, cobros, facturación fiscal.
- Editar/eliminar libros o clientes; ABM de editoriales, géneros y autores; pantalla para editar precios.
- Dígito de control del ISBN.
- Librerías, frameworks, CDNs, npm, herramientas de build.
