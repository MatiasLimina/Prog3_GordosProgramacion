# Design

## Context

C-05 dejó `js/datos.js` con arrays en memoria (`libros`, `clientes`, `ventas`, etc.), `js/altas.js` y `js/ventas.js` mutando esos arrays, y `js/catalogo.js`/`js/historial.js` leyéndolos. No hay persistencia: al recargar se reinicia el seed. C-06 cierra con `localStorage`.

Restricciones: HTML/CSS/JS nativo sin librerías ni build; `file://` (nada de `type="module"`); prohibido `innerHTML`; CSS solo externo; sin tests automatizados.

## Goals / Non-Goals

**Goals:**
- Persistir libros, clientes y ventas en `localStorage`.
- Primer inicio: carga el seed; reaperturas: recupera lo guardado sin duplicar.
- Documentar claves y estructura (README) para la prueba del precio histórico.
- Revisión final: W3C, teclado, 320/1280 px; quitar avisos de maqueta.

**Non-Goals:**
- Sincronización entre pestañas/usuarios (fuera de alcance).
- Migración de esquemas (no hay versiones previas persistidas).

## Decisions

### D1. Claves y formato
- `libreria:libros`, `libreria:clientes`, `libreria:ventas`.
- Valor: `JSON.stringify(array)`. Se guardan los arrays tal cual (con ids, referencias, precio histórico).

### D2. Carga inicial (primer inicio)
Al cargar `persistencia.js`, para cada colección:
- Si la clave no existe en `localStorage`, se serializa el seed actual (los arrays ya definidos en `datos.js`) y se guarda.
- Si existe, se parsea y se **reemplaza el contenido** del array en memoria (`array.length = 0; array.push(...parsed)`), preservando la referencia que `Datos` expone.

### D3. Guardado tras mutación
`Persistencia` expone `guardarLibros()`, `guardarClientes()`, `guardarVentas()` y `guardarTodo()`. `altas.js` y `ventas.js` las invocan tras cada alta exitosa. También se guarda al confirmar venta.

### D4. Orden de carga
`defer`: `datos.js` → `persistencia.js` → `validaciones.js` → (vista). `persistencia.js` se auto-inicializa al final: carga desde `localStorage` si hay, si no guarda el seed. Debe ejecutarse antes de que las vistas rendericen; como todos usan `defer` y `persistencia.js` se carga antes de los scripts de vista (catalogo/altas/ventas/historial), al inicializarse al final del archivo se ejecuta en orden de carga, antes de los siguientes scripts. OK.

### D5. Integración sin romper referencias
Los arrays de `Datos` se mutan por referencia (`length = 0` + `push`), por lo que `Datos.libros` sigue siendo el mismo objeto y las vistas ven los datos cargados.

### D6. Avisos de maqueta
Se eliminan los párrafos `#aviso-maqueta` de `index.html`, `libros.html`, `clientes.html`, `ventas.html` (ya quitado), `historial.html` (ya quitado).

### D7. README.md
Se crea en la raíz con las secciones pedidas por la consigna y la tabla de resultados reales observados de la verificación manual (07 §Verificación), sin marcar como aprobado lo no ejecutado.

### D8. Verificación final
W3C de todas las páginas, teclado, 320/1280 px, prueba de precio histórico (cambiar precio en `localStorage` y recargar Historial).

## Risks / Trade-offs
- `JSON.parse` puede fallar si el usuario corrompe los datos; se maneja con try/catch cayendo al seed (y sobrescribiendo).
- `localStorage` depende de navegador/perfil/ubicación; no comparte entre usuarios (documentado en README).
- Guardar en cada mutación es síncrono y suficiente para el volumen de datos.