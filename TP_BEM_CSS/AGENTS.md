# 🤖 Guía de Contexto para el Proyecto: Feria de Proyectos

Este documento define las reglas técnicas, la metodología y la estructura obligatoria para el desarrollo del trabajo práctico grupal de CSS avanzado y BEM.

## 📌 Contexto del Proyecto
- **Objetivo:** Construir una página web responsive de una "feria de proyectos" cumpliendo con criterios estrictos de CSS.
- **Metodología CSS:** Metodología BEM estricta.

## 🏗️ Convenciones Técnicas Obligatorias

### 1. Estructura y Nomenclatura BEM
- **Bloques independientes obligatorios:** 
  - `.page-header` (Encabezado y navegación)
  - `.project-list` (Contenedor de tarjetas)
  - `.project-card` (Tarjeta individual de proyecto)
  - `.modal` (Panel o aviso superpuesto)
- **Formato de elementos:** `bloque_elemento` (Ej: `.project-card_title`, `.project-card_button`)
- **Formato de modificadores:** `bloque--modificador` o `bloque_elemento--modificador` (Ej: `.project-card--destacado`)
- *Restricción:* No usar nombres genéricos (`.red`, `.title`, `button` sin contexto) y aplicar siempre la clase base junto al modificador.

### 2. Display y Visibilidad
- Usar `display: block` para zonas verticales.
- Usar `display: inline-block` para alinear tarjetas o botones en línea.
- Ocultamiento total sin espacio: `display: none`.
- Ocultamiento conservando espacio: `visibility: hidden`.
- Usar `opacity` para estados visuales.

### 3. Posicionamiento y Apilamiento
- Contenedor de referencia: `position: relative`.
- Badges, etiquetas o avisos flotantes: `position: absolute`.
- Control de capas: `z-index`.
- Títulos de sección o filtros fijos al scrollear: `position: sticky`.

### 4. Selectores y Estados
- Selector descendente (Ej: `.project-list p`)
- Combinador hijo directo (Ej: `.project-card > .project-card_title`)
- Pseudo-clases interactivas: `:hover`, `:focus` (manteniendo indicador visible para teclado) y `:nth-child()`.