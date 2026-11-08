# Proposal

## Why

La consigna del parcial («Formato de entrega», pág. 24) pide un único `Parcial_Cap1a6_<NombreDelGrupo>.zip` con dos carpetas (`parcial/` y `despliegue/`), un `README.md` con los integrantes y los pasos desde cero, y una carpeta `evidencia/` con la captura de psql de C-14 y la consola de C-15; además, un proyecto con credenciales reales en el repositorio, en la imagen o en el zip «no se corrige hasta que se subsane». Hoy no existe `evidencia/` en `parcial/`, el `README.md` todavía describe el TP 1–4 (casos C-01 a C-08, `limit`/`offset`, sin integrantes ni rutas de acceso) y el zip se armaría a mano, con riesgo de que se cuelen `.venv`, `__pycache__` o `.env`. CHG-20 es el último change: cierra la entrega y verifica la definición de terminado (`AGENTS.md`, sección 11).

## What Changes

- **README del parcial** (`README.md`): integrantes con nombre y apellido (Matias Limina, Nicolas Monjelardi, Lautaro Aguero; grupo GordosProgramacion), pasos desde cero (venv, dependencias, `.env` con `POSTGRES_*` y `JWT_SECRET` y cómo generar la clave, `docker compose up -d`, `alembic upgrade head`, `python seed.py`, uvicorn), tests, casos C-01 a C-16 y `evidencia/`, tabla de endpoints y estructura al día con el parcial (auth, roles, stock por movimientos, envoltorio de listados, UoW). Sin `DATABASE_URL`, `DB_ECHO` ni `scripts.seed`.
- **Evidencia** en `evidencia/`: `C-14_solo_agregado.txt` (salida de psql de `test/solo_agregado.sql`: UPDATE y DELETE rechazados por el disparador) y `C-15_detalle_consultas.txt` (consola de uvicorn con `SQL_ECHO=true`: el detalle de una venta con 2 renglones y el de otra con 4 emiten la misma cantidad de consultas), capturadas por el agente durante el apply; el grupo puede agregar capturas de pantalla después.
- **Script de armado** `scripts/armar_zip.py` (Python, corre igual en PowerShell y en Git Bash): arma `Parcial_Cap1a6_GordosProgramacion.zip` con `parcial/` (esta carpeta) y `despliegue/` (la carpeta hermana `../Despliegue`, sin modificarla), tomando sólo archivos que git versiona o que git no ignora, y con una lista de exclusión de respaldo (`.venv`, `__pycache__`, `.env`, cachés, `CLAUDE.local.md`). La salida va a `dist/`, que se agrega al `.gitignore`.
- **Test del script** `tests/test_armar_zip.py` (Strict TDD, sin base): sobre un repositorio git temporal, el zip tiene sólo las raíces `parcial/` y `despliegue/` y nunca `.venv`, `__pycache__`, `.env` ni archivos ignorados.
- **Revisión de secretos en el historial de git** (repositorio completo, incluida `Despliegue`): ningún `.env` versionado nunca, ninguna contraseña ni clave de firma real, `alembic.ini` sin URL. Toca seguridad: el resultado se documenta y cualquier hallazgo se escala al usuario antes de tocar nada.
- **Pasada de la definición de terminado**: base vacía con `alembic upgrade head` → `downgrade base` → `upgrade head`, seed, `/health/live` y `/health/ready` en 200, `REQUIRE_TEST_DB=1 pytest` verde.
- **Cierre del plan**: fila de CHG-20 en `PLAN_PARCIAL.md` en `mergeado (#N)`, `AGENTS.md` al día (sección 3 con `evidencia/` y el script; `main.py` en `app/` ya no «pendiente de confirmar» si así se decide), change archivado en la misma rama, revisión final del diff con el advisor.
- `docs/evidencia_c07.md` (evidencia del TP 1–4: numeración C-07 que en el parcial significa otra cosa, `DB_ECHO` y `scripts.seed`) se retira del parcial; su función la cumple `evidencia/C-15_detalle_consultas.txt`.

Fuera de alcance: cualquier cambio en `../Despliegue` (es el TP 1–4 «tal como se entregó»; su `evidencia/` de los casos D ya existe), cambios de comportamiento de la app, subir el zip al campus (lo hace un integrante a mano) y reescribir el historial de git (si la revisión encuentra un secreto, se decide con el usuario).

## Capabilities

### New Capabilities
- `entrega`: el paquete que se entrega a la cátedra: nombre y estructura del zip, qué entra y qué nunca entra, cómo se arma de forma reproducible, el contenido mínimo del `README.md` del parcial y la carpeta `evidencia/` con C-14 y C-15.

### Modified Capabilities
<!-- Ninguna: casos-de-prueba ya define los .http y el .sql de C-14/C-15; esta entrega sólo guarda su salida como evidencia y no cambia ningún requisito existente. -->

## Impact

- **Archivos nuevos:** `scripts/armar_zip.py`, `tests/test_armar_zip.py`, `evidencia/C-14_solo_agregado.txt`, `evidencia/C-15_detalle_consultas.txt`.
- **Archivos tocados:** `README.md` (reescrito para el parcial), `.gitignore` (`dist/`), `PLAN_PARCIAL.md` (fila CHG-20), `AGENTS.md` (secciones 3, 9 y 11 donde corresponda).
- **Archivos borrados:** `docs/evidencia_c07.md` (sujeto a confirmación, ver design).
- **Código de la app:** ninguno. **Dependencias:** ninguna nueva (el script usa `zipfile`, `subprocess` y `pathlib` de la biblioteca estándar y requiere `git` en el PATH).
- **`../Despliegue`:** sólo se lee para empaquetarla; no se modifica.
- **Gobernanza:** LOW/MEDIUM (documentación y script de empaquetado); la revisión de secretos es de dominio seguridad: sólo análisis, sin reescribir historial sin aprobación explícita.
