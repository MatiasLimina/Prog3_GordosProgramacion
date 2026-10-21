# Tasks

> Sin tests automatizados (regla dura 1): cada tarea se verifica con comportamiento observable en el navegador, la consola de DevTools o el W3C Nu HTML Checker. Los checkboxes quedan sin marcar hasta el apply.

## 1. Persistencia (`js/persistencia.js`)

- [x] 1.1 Crear `js/persistencia.js` como IIFE con `"use strict"` que exponga `window.Persistencia`; definir claves `libreria:libros`, `libreria:clientes`, `libreria:ventas`; verificar en consola que `localStorage` tiene las tres claves tras la carga.
- [x] 1.2 Implementar carga inicial: si la clave no existe, guardar el seed; si existe, parsear y reemplazar el contenido del array en memoria (preservando la referencia); verificar que al recargar no se duplican ejemplos ni ventas.
- [x] 1.3 Implementar `guardarLibros()`, `guardarClientes()`, `guardarVentas()` y `guardarTodo()`; verificar en consola que tras mutar un array y guardar, `localStorage` refleja el cambio.
- [x] 1.4 Manejar errores de parseo con try/catch: si `JSON.parse` falla, caer al seed y sobrescribir la clave; verificar que no se rompe la carga.

## 2. Integración con mutaciones

- [x] 2.1 En `js/altas.js`, tras `Datos.agregarLibro` y `Datos.agregarCliente`, llamar a `Persistencia.guardarLibros()` / `guardarClientes()`; verificar que un alta sobrevive a la recarga.
- [x] 2.2 En `js/ventas.js`, tras `Datos.agregarVenta`, llamar a `Persistencia.guardarVentas()`; verificar que una venta sobrevive a la recarga.
- [x] 2.3 Integrar `persistencia.js` en todas las páginas que cargan `datos.js` (index, libros, clientes, ventas, historial) en el orden `datos.js` → `persistencia.js` → resto; verificar carga sin errores.
- [x] 2.4 Verificar que los arrays siguen siendo los mismos por referencia (`Datos.libros === window.Datos.libros`) tras la carga desde `localStorage`.

## 3. Limpieza de avisos de maqueta

- [x] 3.1 Quitar `#aviso-maqueta` de `index.html`, `libros.html`, `clientes.html` (ventas e historial ya lo quitaron en C-05); verificar que no quedan referencias al aviso.
- [x] 3.2 Verificar que las páginas siguen renderizando catálogo, listados y ventas correctamente tras quitar el aviso.

## 4. README.md

- [x] 4.1 Crear `README.md` en la raíz con: integrantes, cómo abrir `index.html` sin npm, navegación, funcionalidades implementadas, ubicación de datos iniciales.
- [x] 4.2 Documentar claves y estructura de `localStorage` (`libreria:libros`, `libreria:clientes`, `libreria:ventas`) incluyendo un ejemplo del renglón con precio histórico, para la prueba del docente.
- [x] 4.3 Documentar funcionamiento y límites de `localStorage` (depende de navegador, perfil y ubicación; no comparte entre usuarios).
- [x] 4.4 Declarar que no se usan imágenes ajenas (o procedencia si se usaran).
- [x] 4.5 Incluir la tabla de resultados reales observados de la verificación manual (07 §Verificación), sin marcar como aprobado lo no ejecutado.

## 5. Verificación final

- [x] 5.1 Ejecutar F6: primer inicio carga ejemplos; recarga recupera datos sin duplicar; altas y venta sobreviven a la recarga.
- [x] 5.2 Ejecutar la prueba del precio histórico: cambiar el precio del libro en `localStorage` (guiado por el docente), recargar y verificar que la venta conserva precio unitario, subtotales y total.
- [x] 5.3 Ejecutar la tabla completa de verificación manual de 07 §Verificación y registrar el resultado real en el README.
- [x] 5.4 Validar todas las páginas (`index.html`, `libros.html`, `clientes.html`, `ventas.html`, `historial.html`) con el W3C Nu HTML Checker; confirmar 0 errores.
- [x] 5.5 Verificar teclado y anchos 320/1280 px en todas las páginas (foco visible, controles usables, tablas con scroll propio).
- [x] 5.6 Revisar con búsqueda de texto que no se agregó `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `type="module"` ni CDNs en los archivos del change.