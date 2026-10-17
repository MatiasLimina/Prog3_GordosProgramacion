# Handoff — Parcial_Front

> Nota de traspaso entre máquinas (notebook → PC de escritorio). Fecha: 2026-10-17.
> Borrar este archivo cuando se retome el trabajo y ya no haga falta.

## Dónde quedó

- **Rama**: `feat/parcial-front-fundacion` (pusheada a `origin`).
- **Fundación completa**: `knowledge-base/` (10 archivos), `CHANGES.md` (6 changes), `CLAUDE.md`/`AGENTS.md`, `openspec/`.
- **Change activo**: `estructura-pantallas-html` (C-01).
  - Artefactos de planificación: 4/4 (proposal, specs, design, tasks).
  - Implementación: **0/26 tareas**. Todavía no existe ningún HTML/CSS/JS.
- Ningún change archivado → `openspec/specs/` vacío. Todos los changes de `CHANGES.md` siguen en `[ ]`.

## Bloqueante antes de `/opsx:apply`

Dos decisiones abiertas (ver `openspec/changes/estructura-pantallas-html/design.md` § Open Questions y la cabecera de `tasks.md`):

1. **Nombre de la librería** — supuesto actual: "Librería Papel y Tinta".
2. **Formato de id y fecha de venta en la maqueta** — supuesto actual: ids numéricos y `DD/MM/AAAA`.

Al decidir: reemplazar cada ítem de Open Questions por la decisión, ajustar §D4 si cambia algo y quitar el aviso de `tasks.md`.

## Cómo retomar en la PC de escritorio

```bash
git fetch origin
git switch feat/parcial-front-fundacion
git pull --ff-only
cd Parcial_Front
openspec list --json
openspec status --change estructura-pantallas-html
```

- `.atl/skill-registry.md` **no se versiona** (ver `CLAUDE.md`). Regenerarlo con la skill `skill-registry` si el orquestador lo necesita.
- Después: resolver las 2 decisiones → `/opsx:apply estructura-pantallas-html`.

## Recordatorios

- Reglas duras del proyecto en `CLAUDE.md`: sin tests ni test runners (Strict TDD no aplica), sin frameworks/CDN/npm, CSS solo en `css/`, nada de backend, `textContent` en lugar de `innerHTML` para datos de usuario.
- Verificación de C-01: manual + W3C validator (tareas 7.1–7.4).
