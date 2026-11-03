# Proposal

## Why

El parcial (Cap 1–6) parte del TP de los capítulos 1–4, pero `AGENTS.md` —la guía canónica que leen los tres integrantes y los agentes de IA— todavía describe ese TP: servicios que reciben la sesión, paginación `limit/offset`, `DATABASE_URL` y `DB_ECHO`, y como fuente de verdad un `TP_Cap1a4_Consigna.pdf` que ya no está en la carpeta. Mientras eso no se corrija, cada change de F1–F3 arranca con reglas que contradicen `Parcial_Cap1a6_Consigna.pdf`. Además faltan en `requirements.txt` las tres librerías que exige la consigna (pág. 4) y de las que dependen CHG-03, CHG-10 y CHG-11. CHG-00 es la raíz del mapa de dependencias de `PLAN_PARCIAL.md`: lo bloquean CHG-03, 05, 06, 07, 09a y 09b.

## What Changes

- **Precondición ya cumplida**: `openspec init --tools claude --language es` en esta carpeta (`openspec/`, `.claude/skills/openspec-*`, `.claude/commands/opsx/`). El change sólo la verifica (`openspec list`) y la versiona en el primer commit.
- **Dependencias**: se agregan a `requirements.txt` `pydantic-settings>=2.0`, `bcrypt>=4.0` y `PyJWT>=2.8`, con el mismo estilo de pisos mínimos del archivo (versiones mínimas de la consigna, pág. 4). No se toca código que las use.
- **Reescritura de `AGENTS.md`** con las reglas del parcial (estado objetivo), reemplazando las del TP 1–4 donde se superponen:
  - Fuente de verdad: `Parcial_Cap1a6_Consigna.pdf` + `PLAN_PARCIAL.md`; se quita el aviso «Parcial en curso».
  - Capas Router → Service → UoW → Repository → Model, con quién construye, abre, confirma y cierra (el router construye el UoW por dependencia y lo pasa sin abrir; el servicio lo abre con `async with` y nunca lo construye; los repositorios hacen `flush()`, nunca `commit()`; el UoW confirma al salir, revierte ante excepción y no cierra la sesión).
  - `Settings` con pydantic-settings, URL armada con `@computed_field` desde `POSTGRES_*`, sin valor por defecto para la contraseña de la base ni la clave JWT, `SQL_ECHO`.
  - Envoltorio de listados `{items, total, page, size, pages}` en lugar de `limit/offset`.
  - Token sólo en la cookie `access_token` (`HttpOnly`, `SameSite=Lax`, `Max-Age`, `Secure` configurable); nunca en el cuerpo ni en `Authorization`.
  - 401 (sin sesión / token inválido / usuario inactivo) frente a 403 (sin rol vigente en la base, cambio de contraseña pendiente, no es dueño); también 204, 429 y 503.
  - Stock con una sola vía de escritura (movimientos de sólo agregado).
  - `intento_acceso` como única escritura con sesión y transacción propias.
  - Estructura obligatoria del parcial (págs. 8–9), dueños por integrante, convención de ramas y definición de terminado del parcial.
- **Ramas por integrante**: una rama por change (`<tipo>/<nombre-openspec>`), con el responsable que fija `PLAN_PARCIAL.md` (Matias lead, Nico persistencia y APIs, Lauti tareas acotadas).
- **Línea base**: `pytest` en verde antes y después del change.
- Se marca CHG-00 en la tabla de seguimiento de `PLAN_PARCIAL.md`.

**Fuera de alcance** (cada punto tiene su change): implementar `Settings`/lifespan y renombrar `DB_ECHO` → `SQL_ECHO` (CHG-03), `env.example` (CHG-03), repositorios y UoW (CHG-04), `paginacion.py` (CHG-05), modelos (CHG-06/07), contratos (CHG-09a/b), seguridad y auth (CHG-10/11/12), mover el seed a la raíz (CHG-17), `README.md` (CHG-20) y la carpeta `despliegue/` (CHG-01/02). `REPARTO.md` queda como registro histórico del TP 1–4.

## Capabilities

### New Capabilities

Ninguna. El change modifica documentación de trabajo, dependencias y herramientas; no cambia el comportamiento del sistema, así que declara `skip_specs: true`. Las reglas que documenta se especifican como requisitos en los changes que las implementan.

### Modified Capabilities

Ninguna (no hay specs principales todavía).

## Impact

- **Archivos**: `AGENTS.md` (reescritura), `requirements.txt` (+3 líneas), `PLAN_PARCIAL.md` (estado de CHG-00); se versionan `openspec/` y `.claude/` (comandos y skills de OpenSpec).
- **Código de la app**: ninguno. Los módulos siguen con el patrón del TP 1–4 hasta que su change los migre; `AGENTS.md` lo aclara en una nota de transición.
- **Entorno**: cada integrante corre `pip install -r requirements-dev.txt` después del merge.
- **Gobernanza**: `AGENTS.md` y `requirements.txt` son archivos compartidos del lead; la reescritura la revisa Matias antes del merge. Las reglas de auth sólo se documentan acá.
- **Desbloquea**: CHG-03, CHG-05, CHG-06, CHG-07, CHG-09a y CHG-09b.
