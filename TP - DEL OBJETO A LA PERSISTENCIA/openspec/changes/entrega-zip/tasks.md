# Tasks

> Requisitos: `specs/entrega/spec.md`. Decisiones: `design.md` (D1–D9). Todo comando se corre desde la carpeta del parcial (`TP - DEL OBJETO A LA PERSISTENCIA/`).
> Gobernanza: LOW/MEDIUM (docs y script de empaquetado). El grupo 5 (secretos) es dominio seguridad: sólo análisis; ante un hallazgo real, **detener y avisar al usuario** antes de tocar nada.
> `../Despliegue` no se modifica en ninguna tarea.

## 1. Script de armado del zip (Strict TDD)

- [x] 1.1 RED: `tests/test_armar_zip.py` (sin marca `db`) con una fixture que arma en `tmp_path` dos carpetas `git init` (sin commits) con un `.gitignore` como el real y, en disco, `.venv/`, `__pycache__/x.pyc`, `.pytest_cache/`, `.env`, `CLAUDE.local.md`, `.claude/settings.json`, un archivo ignorado, `.dockerignore` y archivos legítimos; prueba que el zip sólo tiene raíces `parcial/` y `despliegue/` y contiene los legítimos; verificar que `pytest tests/test_armar_zip.py` falla porque `scripts.armar_zip` no existe
- [x] 1.2 GREEN: `scripts/armar_zip.py` con `listar_archivos` (`git -C <carpeta> ls-files -z --cached --others --exclude-standard`, omite los que no existen en disco) y `armar_zip(origenes, destino) -> dict[str, int]` (entradas POSIX ordenadas, `ZIP_DEFLATED`, temporal + renombrado); verificar `pytest tests/test_armar_zip.py` verde
- [x] 1.3 TRIANGULATE: pruebas de exclusión (ninguna entrada con `.venv`, `__pycache__`, `.pytest_cache`, `.claude`, `.env`, `*.pyc`, `CLAUDE.local.md` ni el archivo ignorado), de inclusión de un archivo nuevo sin commitear y del `.dockerignore`, del conteo devuelto por raíz y de que las carpetas de origen quedan iguales (mismo listado y contenido); `excluida(ruta)` con la lista negra de D2 probada con al menos dos rutas que entran y dos que no; verificar `pytest tests/test_armar_zip.py` verde
- [x] 1.4 RED → GREEN: con `git add -f .env` en una carpeta de origen, `armar_zip` lanza un error que nombra el `.env` y no deja archivo en el destino; carpeta de origen inexistente → error claro; verificar `pytest tests/test_armar_zip.py` verde
- [x] 1.5 `main()` con `argparse` (`--parcial`, `--despliegue`, `--salida`; por defecto la carpeta del script, `../Despliegue` y `dist/Parcial_Cap1a6_GordosProgramacion.zip`), imprime la ruta y los conteos, código de salida ≠ 0 ante error; agregar `dist/` al `.gitignore`; REFACTOR con la suite verde; verificar `python scripts/armar_zip.py` en PowerShell y que `git status` no muestra el zip
- [x] 1.6 Abrir el zip de 1.5 y verificar a mano (o con un `python -c` sobre `zipfile`) las entradas del escenario «Las dos carpetas presentes» del spec y que no hay ninguna entrada prohibida; anotar los conteos

## 2. README del parcial

- [x] 2.1 Reescribir `README.md` según D9: integrantes (grupo GordosProgramacion: Matias Limina, Nicolas Monjelardi, Lautaro Aguero), pasos desde cero (venv en PowerShell y Git Bash, dependencias, `.env` desde `env.example` con `POSTGRES_*` y `JWT_SECRET` y el comando `python -c "import secrets; print(secrets.token_urlsafe(48))"`, `docker compose up -d`, `alembic upgrade head`, `python seed.py`, uvicorn, `/health/live` y `/health/ready`); verificar que cada comando aparece en ese orden
- [x] 2.2 Secciones de tests (`pytest`, `REQUIRE_TEST_DB=1`, base `libreria_test`), casos C-01 a C-16 (`test/`, REST Client, `python seed.py` antes de cada archivo, C-14 con psql), evidencia (enlaces a `evidencia/C-14_solo_agregado.txt` y `evidencia/C-15_detalle_consultas.txt`), endpoints del parcial agrupados por acceso (copiados de `app/main.py` y los routers, con el envoltorio `page`/`size`), estructura y «Armado de la entrega» (`python scripts/armar_zip.py`); verificar con `grep -nE "DATABASE_URL|DB_ECHO|scripts\.seed|limit|offset|evidencia_c07" README.md` que no queda ninguna instrucción vigente del TP 1–4
- [x] 2.3 Contrastar la tabla de endpoints con las rutas reales: `python -c` que liste `app.routes` (método y ruta) y verificar que toda ruta de la app figura en el README y ninguna ruta del README falta en la app

## 3. Evidencia de C-14 y C-15

- [x] 3.1 Preparar la base: `docker compose up -d`, `alembic upgrade head`, `python seed.py`; verificar `docker compose ps` en `healthy` y que el seed termina sin error
- [x] 3.2 Capturar C-14 en `evidencia/C-14_solo_agregado.txt` (D5): encabezado con fecha, commit y comando, y la salida de `docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -a' < test/solo_agregado.sql`; verificar que el archivo muestra los dos `ERROR:  23001` del disparador (UPDATE y DELETE) y la misma fila en el primer y el último `SELECT`
- [x] 3.3 Capturar C-15 en `evidencia/C-15_detalle_consultas.txt` (D5): `python seed.py`, uvicorn con `SQL_ECHO=true` y la consola a un archivo de la carpeta temporal, y los pasos de `test/c15_detalle_consultas.http` con un cliente HTTP desde la carpeta temporal (login admin, `GET /ventas/1`, `POST /ventas/` con libros 1–4, `GET` de la nueva); guardar encabezado, tabla resumen y los fragmentos de los dos `GET`; verificar que los dos detalles tienen la misma cantidad de consultas y que el archivo no contiene `access_token`, `Set-Cookie`, `$2b$`, `JWT_SECRET` ni la contraseña de la base
- [x] 3.4 Borrar `docs/evidencia_c07.md` (D8) y verificar con `grep -rn "evidencia_c07" --include=*.md .` (fuera de `openspec/changes/archive/`) que nada lo enlaza

## 4. Documentación del proyecto

- [x] 4.1 `AGENTS.md`: sección 2 con `python scripts/armar_zip.py`; sección 3 con `scripts/armar_zip.py` y `evidencia/` (C-14 y C-15 en texto); sección 11, punto 7, con el nombre real del zip y el comando que lo arma; verificar con `grep -n "armar_zip\|GordosProgramacion" AGENTS.md`
- [x] 4.2 `PLAN_PARCIAL.md`, sección CHG-20: anotar el script, la salida en `dist/` y los archivos de evidencia; verificar que la sección nombra `scripts/armar_zip.py`

## 5. Revisión de secretos (dominio seguridad: sólo análisis)

- [x] 5.1 Archivos: `git log --all --diff-filter=A --name-only --format=` filtrado por `(^|/)\.env$` y `\.env\.` (salvo `env.example`) sobre el repo completo; verificar que no aparece ninguno, o detener y avisar
- [x] 5.2 Contenido (D6): `git log --all -p -G` con los patrones de `POSTGRES_PASSWORD=.+`, `JWT_SECRET=.+`, URLs `postgres…://usuario:clave@`, `sqlalchemy.url =` sin comentar, contraseñas en `docker-compose` y `BEGIN .*PRIVATE KEY`; clasificar cada coincidencia (fake de tests/seed, plantilla vacía o real) sin copiar valores a ningún archivo; además `git log --all -S` con los valores del `.env` local sin imprimirlos; verificar que no hay ningún valor real, o detener y avisar
- [x] 5.3 Configuración actual: `git check-ignore .env` en las dos carpetas, `sqlalchemy.url` comentado en los dos `alembic.ini`, y los dos `env.example` sin valores reales (`despliegue/env.example` con la forma de `DATABASE_URL`); si `gitleaks` está instalado, correrlo sobre el repo; dejar el resumen (comandos y conclusión, sin valores) listo para la descripción del PR

## 6. Definición de terminado (integración)

- [x] 6.1 Reversibilidad sobre base nueva y vacía (D7): `createdb libreria_dod` dentro del contenedor; con `POSTGRES_DB=libreria_dod` en el entorno del comando, `alembic upgrade head` → `alembic downgrade base` → `alembic upgrade head` sin errores; borrar `libreria_dod`; verificar los tres códigos de salida 0
- [x] 6.2 `python seed.py` en la base de desarrollo, `uvicorn app.main:app`, y `GET /health/live` y `GET /health/ready` en 200; verificar con curl o httpx
- [x] 6.3 `REQUIRE_TEST_DB=1 pytest` completo verde (incluye `tests/test_armar_zip.py`, los `.http` C-01 a C-16 sobre el seed y el invariante de stock); verificar el resumen de pytest sin fallos ni skips de base
- [x] 6.4 `git status` limpio salvo los archivos de este change, y armado de prueba con `python scripts/armar_zip.py`: verificar que el conteo de `parcial/` coincide con `git ls-files` de la carpeta menos las exclusiones de D2 y que `git -C ../Despliegue status --short` no muestra cambios

## 7. Cierre

- [x] 7.1 Checkpoint FINAL_DIFF: consultar al `advisor` sobre `git diff main` (script, test, README, evidencia, AGENTS/PLAN) con el resumen de 5.3; atender CONCERNS y no seguir con un BLOCK sin confirmación del usuario
- [ ] 7.2 Commit `chore(entrega): README, evidencia y armado del zip` y PR a `main` cuando el usuario lo pida; verificar que el PR muestra los archivos esperados y ningún `.env` ni `dist/`
- [ ] 7.3 Con el número del PR: fila de CHG-20 en `PLAN_PARCIAL.md` (sección 2) en `mergeado (#N)` y `openspec archive entrega-zip` en la misma rama (AGENTS §10); verificar `openspec list --json` sin el change y la fila actualizada
- [ ] 7.4 Armado final sobre el árbol commiteado: `python scripts/armar_zip.py`, con `git status --short` limpio en las dos carpetas (parcial y Despliegue), verificar de nuevo las entradas obligatorias y prohibidas del zip y dejar `dist/Parcial_Cap1a6_GordosProgramacion.zip` listo para que un integrante lo suba al campus
