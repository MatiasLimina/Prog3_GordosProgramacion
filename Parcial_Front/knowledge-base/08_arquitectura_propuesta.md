# 08 — Arquitectura propuesta

## Patrones
- Separación estructura (HTML) / presentación (CSS) / comportamiento (JS).
- Funciones acotadas con responsabilidades reconocibles: datos/repositorio (localStorage), validaciones puras, renderizado, manejadores de eventos.
- Validaciones como funciones puras (fáciles de verificar manualmente).
- Ids estables en datos; el HTML expone ids, `name` y `data-*` para JS.

## Estructura de directorios propuesta
```
index.html            (+ libros.html, clientes.html, ventas.html, historial.html si multipágina)
css/                  (estilos externos, clases reutilizadas)
js/                   (datos, validaciones, render, eventos, storage)
assets/               (imágenes locales, con procedencia si son ajenas)
README.md
```
La estructura final de `js/` queda a decisión del equipo (ver 09/10).

## Seguridad
Sin seguridad real (datos ficticios, sin servidor). Única medida: insertar texto de usuario con `textContent` para evitar inyección HTML (RN-04).

## Verificación y calidad
**Sin test runners ni tests automáticos.** Validación W3C del HTML; casos manuales (07); revisión de teclado y de 320/1280 px.

## Variables de entorno / build
No aplica: sin npm, sin build, sin env vars, sin dependencias instaladas. Se abre `index.html` en el navegador.
