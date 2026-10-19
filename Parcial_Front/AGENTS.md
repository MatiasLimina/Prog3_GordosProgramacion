# Parcial_Front — Instrucciones para Agentes

> Este archivo (y su copia `CLAUDE.md`) es lo PRIMERO que todo agente lee al entrar al repo.
> Generado a partir de `knowledge-base/` y `CHANGES.md`. No editar a mano sin re-sincronizar ambos archivos.

Frontend de una librería (TPI Programación III): catálogo, libros, clientes, ventas simuladas e historial, 100 % en el navegador.

---

## Stack Tecnológico

| Capa | Tecnología | Versión |
|------|------------|---------|
| Estructura | HTML5 semántico | — |
| Estilos | CSS3 (Flexbox/Grid), archivos externos en `css/` | — |
| Comportamiento | JavaScript nativo (ES modules opcional), en `js/` | — |
| Persistencia | `localStorage` del navegador (Ej. 6) | — |
| Backend / Integraciones | Ninguno | — |

Prohibido: librerías, frameworks, CDNs de CSS/JS, npm, build tools. Recursos siempre locales.
Detalle completo: [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md)

---

## Base de Conocimiento

La fuente de verdad del dominio vive en `knowledge-base/` (índice: [README.md](knowledge-base/README.md)). **Leé el archivo relevante ANTES de implementar.**

| Archivo | Cuándo leerlo |
|---------|---------------|
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Propósito y alcance |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Operador único, sin auth |
| [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | Entidades, seed, persistencia |
| [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | Reglas RN-01..RN-24 |
| [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | Épicas por ejercicio |
| [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | Flujos y casos manuales |
| [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Estructura, patrones, seguridad |
| [09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) | Decisiones tomadas |
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | Dudas a resolver antes de codear |

> Preguntas abiertas: no hay de prioridad Alta. Las de prioridad **media** (multipágina vs. una página, formato de id/fecha de venta, claves de localStorage, libro repetido: sumar o rechazar) se deciden y documentan en el change que las toca (C-01, C-05, C-06).

---

## Skills Disponibles

Fuente: `.atl/skill-registry.md`. Ninguna skill de stack aplica (HTML/CSS/JS nativo); solo skills de flujo.

| Agente | Rol | Skills que carga |
|--------|-----|------------------|
| **HTML/CSS** (Agente A) | Estructura, presentación, README | — (sin skill de stack; seguir reglas duras y KB) |
| **JavaScript** (Agente B) | Datos, validaciones, ventas, localStorage | — (sin skill de stack; seguir reglas duras y KB) |
| **Orquestación** | KB, roadmap, reglas del proyecto, registry | `kb-creator`, `roadmap-generator`, `agent-instruction`, `skill-creator`, `find-skill` |
| **Discovery** | Investigación previa a la KB | `discovery-research`, `web-scraper` |

No aplican (instaladas pero fuera de alcance): `fastapi-python`, `python-testing-patterns`, `supabase-postgres-best-practices`, `auth-implementation-patterns`, `tdd`.

> Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md` (generado por `skill-registry`; no versionado — no está en el repo). Esta tabla solo mapea skill→rol.

---

## Roadmap de Changes

El plan completo está en [CHANGES.md](CHANGES.md). Resumen:

- **Total**: 6 changes en 3 fases (Estructura y presentación; Comportamiento JS; Cierre).
- **Camino crítico** (5): `C-01 → C-03 → C-04 → C-05 → C-06` (C-02 corre en paralelo y debe estar listo antes de C-06).
- **Primer change**: `C-01` (`estructura-pantallas-html`).

**Antes de cualquier `/opsx:propose`**: leé [CHANGES.md](CHANGES.md), identificá las dependencias del change y los archivos de "Leer antes".

---

## Reglas Duras (específicas del proyecto)

> Reglas globales ya definidas en `~/.claude/CLAUDE.md` (orquestador, governance, engram): el proyecto las hereda, excepto Strict TDD, que no aplica — ver regla 1. Acá viven solo las reglas **específicas de este proyecto**. Son contrato; romperlas es un defecto.

1. **NUNCA instalar Jest/Vitest/Playwright ni crear archivos de test** → no hay suite de tests ni test runners; el módulo Strict TDD del global NO aplica (override explícito). Verificar manualmente (casos reproducibles de la consigna, registrando el resultado real) + validar el HTML en el W3C validator.
2. **NUNCA usar frameworks, librerías, CDNs, npm, `package.json` ni herramientas de build** → solo HTML, CSS y JavaScript nativos; todos los recursos locales.
3. **NUNCA usar CSS inline ni `<style>` embebido para la identidad visual** → CSS en archivos externos en `css/`, reutilizando clases.
4. **NUNCA depender de backend, API, BD ni login real** → datos ficticios simulados en el navegador (`localStorage` en Ej. 6).
5. **NUNCA insertar datos escritos por usuarios como HTML** (`innerHTML`) → insertarlos como texto en el DOM con `textContent`.

---

## Flujo de Trabajo

```
1. Leer la KB relevante (knowledge-base/)        → entender el dominio
2. Identificar el change en CHANGES.md           → respetar dependencias
3. /opsx:propose <nombre-del-change>             → proposal + design + specs + tasks
4. /opsx:apply <nombre-del-change>               → implementar respetando las reglas duras
5. Verificar manualmente + W3C                   → casos de 07_flujos_principales.md
6. /opsx:archive <nombre-del-change> + marcar [x] en CHANGES.md
```

OPSX se entrega como **comandos** en `.claude/commands/opsx/*.md` (`propose`, `apply`, `archive`, `explore`, `sync`, `update`); no existen skills `openspec-*`. Los sub-agentes deben leer el archivo de comando correspondiente y seguirlo.

Aplicar TODAS las reglas duras en cada paso. Ante conflicto entre la KB y este archivo, las reglas duras prevalecen.
