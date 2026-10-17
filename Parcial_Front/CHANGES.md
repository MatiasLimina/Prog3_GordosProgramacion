# CHANGES — Secuencia de Implementación

> Índice canónico de todos los changes del proyecto **Parcial_Front (TPI: frontend de una librería)**.
> Cada change es atómico: un agente puede implementarlo en una sesión (~4-6 horas).
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**
>
> Restricciones globales: solo HTML/CSS/JS nativos, sin librerías ni build. **Sin suite de tests ni test runners**: la verificación es manual (casos reproducibles) + validación W3C del HTML.

---

## Cómo usar este documento

1. Identificá el próximo change pendiente cuyas dependencias estén todas en `[x]`.
2. Leé los archivos de "Leer antes" de la KB (`knowledge-base/`) y `docs/consigna-ejercicio-1.md`.
3. Ejecutá `/opsx:propose <nombre-del-change>` y luego `/opsx:apply`.
4. Al terminar, verificá manualmente (casos de `07_flujos_principales.md`) y `/opsx:archive`.
5. Marcá el checkbox de Estado en este archivo (`[ ]` → `[x]`).

---

## Árbol de dependencias

```
C-01 estructura-pantallas-html
 ├── C-02 presentacion-css-adaptable ─────────────┐
 └── C-03 datos-locales-catalogo-filtro           │
       └── C-04 alta-libros-clientes              │
             └── C-05 venta-simulada-historial    │
                   └── C-06 persistencia-readme ◄─┘  (depende de C-02 y C-05)
```

### Paralelismo por fase

```
GATE 0: (inicio)
  → C-01 estructura-pantallas-html          [Agente A]

GATE 1: C-01 ✓                               ← FORK
  → C-02 presentacion-css-adaptable         [Agente A]
  → C-03 datos-locales-catalogo-filtro      [Agente B]

GATE 2: C-03 ✓
  → C-04 alta-libros-clientes               [Agente B]

GATE 3: C-04 ✓
  → C-05 venta-simulada-historial           [Agente B]

GATE 4: C-02 ✓ + C-05 ✓
  → C-06 persistencia-readme                [Agente A]
```

### Camino crítico (5 changes — mínimo irreducible)

`C-01 → C-03 → C-04 → C-05 → C-06`

(C-02 corre en paralelo a C-03/C-04/C-05 y solo debe estar listo antes de C-06.)

### Plan óptimo con 2 agentes

| Paso | Agente A (HTML/CSS/docs) | Agente B (JavaScript) |
|------|--------------------------|------------------------|
| 1 | C-01 estructura-pantallas-html | — |
| 2 | C-02 presentacion-css-adaptable | C-03 datos-locales-catalogo-filtro |
| 3 | — | C-04 alta-libros-clientes |
| 4 | — | C-05 venta-simulada-historial |
| 5 | C-06 persistencia-readme | — |

---

## FASE 1 — Estructura y presentación (Ej. 1–2)

### [C-01] `estructura-pantallas-html`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `index.html` como entrada con navegación `<nav>` clara entre las 5 vistas (multipágina o secciones; decidir y documentar, ver KB 10 #1)
  - Vistas: Catálogo (título de la librería, buscador por título, listado), Libros (form alta + listado), Clientes (form alta + listado), Ventas (select cliente, renglones, resumen/total), Historial (listado + "Ver detalle")
  - Semántica: `<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<footer>`; `<label for>` en cada campo; tablas con `<thead>` y `<th scope>`
  - Botones con texto de acción: "Registrar libro", "Registrar cliente", "Agregar renglón", "Confirmar venta", "Ver detalle"
  - Mensajes presentes en el HTML con `hidden` + `role="status"`/`role="alert"`: lista vacía, búsqueda sin resultados, operación correcta, operación rechazada
  - Datos estáticos de ejemplo (≥ 1 libro «Sin clasificar», ≥ 1 libro con varios autores; historial con ventas de muestra y maqueta de detalle)
  - Hooks para JS: `id`, `name`, `data-*` y contenedores de estado; campos anticipados de libro (título, ISBN, precio, editorial select, género select con «Sin clasificar», autores múltiples) y cliente (nombre completo, email)
  - CSS mínimo (un archivo en `css/`) solo para que sea legible; **sin lógica JS de negocio**
  - Verificación: validación W3C del HTML + revisión manual de navegación
- **Dependencias**: ninguna
- **Governance**: BAJO
- **Leer antes**:
  - `docs/consigna-ejercicio-1.md` §Ejercicio 1
  - `knowledge-base/06_funcionalidades.md` §Épica 1
  - `knowledge-base/04_modelo_de_datos.md` §Entidades
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios
  - `knowledge-base/10_preguntas_abiertas.md` §Prioridad media

### [C-02] `presentacion-css-adaptable`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Identidad visual propia en `css/` externo: variables de color, tipografía, espaciado, tarjetas, formularios, botones; clases reutilizadas
  - Layout con Flexbox/Grid; sin scroll horizontal de página a 320 px y 1280 px
  - Tablas dentro de contenedor con `overflow-x: auto` (scroll propio)
  - `:focus-visible` en todos los controles; recorrido por teclado
  - Mensajes de error con texto/ícono, no solo color; `alt` correcto en imágenes (decorativas con `alt=""`)
  - Verificación manual a 320/1280 px y con teclado
- **Dependencias**: `C-01`
- **Governance**: BAJO
- **Leer antes**:
  - `docs/consigna-ejercicio-1.md` §Campos que el HTML debe anticipar (CSS Ej. 2)
  - `knowledge-base/06_funcionalidades.md` §Épica 2
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones

---

## FASE 2 — Comportamiento JavaScript (Ej. 3–5)

> C-02 puede ejecutarse en paralelo con C-03, C-04 y C-05.

### [C-03] `datos-locales-catalogo-filtro`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `js/` con datos en arrays/objetos con ids estables: ≥ 6 libros, 2 editoriales, 2 géneros, 3 autores, 3 clientes (≥ 1 libro sin género, ≥ 1 con varios autores)
  - Render del catálogo desde el array (título, ISBN, editorial, género o «Sin clasificar», autores, precio); texto de usuario con `textContent`
  - Filtro por título: `trim`, sin distinguir mayúsculas, coincidencia parcial; vacío = todo; sin coincidencias = mensaje
  - Funciones separadas: datos, render, manejadores de eventos
  - Verificación manual: casos de búsqueda de `07_flujos_principales.md` F1
- **Dependencias**: `C-01`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Entidades, §Seed data
  - `knowledge-base/07_flujos_principales.md` §F1
  - `knowledge-base/05_reglas_de_negocio.md`
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones, §Seguridad

### [C-04] `alta-libros-clientes`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Selects de editorial y género (con «Sin clasificar») y autores (multi-select/checkboxes) generados desde los datos
  - Validaciones puras de libro: título e ISBN no vacíos, ISBN único (sin espacios ni guiones), precio numérico > 0, editorial y autores existentes, ≥ 1 autor, género opcional pero existente si se asigna
  - Validaciones puras de cliente: nombre y email no vacíos, email con formato válido, único (trim + sin distinguir mayúsculas)
  - Submit con `preventDefault`, errores cerca del formulario, alta solo si todo pasa
  - Actualización sin recarga de listados, catálogo y selects relacionados
  - Verificación manual: F2 y F3 (ISBN duplicado/nuevo, email inválido/duplicado/nuevo)
- **Dependencias**: `C-03`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/05_reglas_de_negocio.md` §RN-05..12
  - `knowledge-base/07_flujos_principales.md` §F2, §F3
  - `knowledge-base/04_modelo_de_datos.md` §Relaciones
  - `knowledge-base/06_funcionalidades.md` §Épica 4

### [C-05] `venta-simulada-historial`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Selección de cliente existente y renglones (libro existente, cantidad entera > 0); libro repetido: sumar cantidad o rechazar (elegir y documentar, KB 10 #4)
  - Cambiar cantidades y quitar renglones antes de confirmar
  - Subtotal = cantidad × precio; total = suma; importes con 2 decimales
  - "Confirmar venta" valida cliente, renglones y cantidades; registra id, fecha, cliente, renglones y total; copia el precio unitario histórico y datos descriptivos (título, nombre de cliente)
  - Limpia el formulario y muestra mensaje de resultado
  - Historial: id, fecha, cliente, total y "Ver detalle" con renglones confirmados; sin editar ni eliminar
  - Verificación manual: venta 2 × 1500 + 1 × 2000 = 5000 y casos inválidos
- **Dependencias**: `C-04` (y transitivamente `C-03`; usa los selects de libros y clientes actualizados)
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/05_reglas_de_negocio.md` §Ventas
  - `knowledge-base/07_flujos_principales.md` §F4, §F5
  - `knowledge-base/04_modelo_de_datos.md` §Venta, §Renglón
  - `knowledge-base/10_preguntas_abiertas.md` #2, #4

---

## FASE 3 — Cierre (Ej. 6)

### [C-06] `persistencia-readme`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `localStorage` para libros, clientes y ventas; primer inicio carga los ejemplos, reaperturas los recuperan sin duplicar datos iniciales ni ventas
  - Claves y estructura del catálogo guardado documentadas (para la prueba del precio histórico)
  - `README.md`: integrantes, cómo abrir `index.html` sin npm, navegación, funcionalidades implementadas/pendientes, ubicación de datos iniciales, funcionamiento y límites de localStorage (depende de navegador, perfil y ubicación; no comparte entre usuarios), procedencia de imágenes ajenas
  - Registro de los resultados **reales** observados de los casos manuales (sin marcar como aprobado lo no ejecutado)
  - Revisión final: W3C, teclado, 320/1280 px
- **Dependencias**: `C-02`, `C-05`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/07_flujos_principales.md` §F6, §Verificación manual
  - `knowledge-base/04_modelo_de_datos.md` §Persistencia
  - `knowledge-base/06_funcionalidades.md` §Épica 6
  - `knowledge-base/10_preguntas_abiertas.md` #3

---

## Resumen

| ID | Change | Ej. | Dependencias | Governance |
|----|--------|-----|--------------|------------|
| C-01 | `estructura-pantallas-html` | 1 | — | BAJO |
| C-02 | `presentacion-css-adaptable` | 2 | C-01 | BAJO |
| C-03 | `datos-locales-catalogo-filtro` | 3 | C-01 | MEDIO |
| C-04 | `alta-libros-clientes` | 4 | C-03 | MEDIO |
| C-05 | `venta-simulada-historial` | 5 | C-04 | MEDIO |
| C-06 | `persistencia-readme` | 6 | C-02, C-05 | MEDIO |

**Primer change recomendado**: `C-01` (`estructura-pantallas-html`) — `/opsx:propose estructura-pantallas-html`
