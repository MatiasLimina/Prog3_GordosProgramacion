# Design

## Context

Motivación y alcance: ver `proposal.md`. Requisitos: ver `specs/entrega/spec.md`.

Estado que condiciona el enfoque:

- **Un solo repositorio git para las dos carpetas.** La raíz del repo es `Prog3/` (la carpeta padre); `TP - DEL OBJETO A LA PERSISTENCIA/` (el parcial, ~340 archivos versionados) y `Despliegue/` (el TP 1–4, ~105) son subcarpetas. Las dos tienen su propio `.gitignore` con `.env`, `.venv/`, `__pycache__/`, `*.py[cod]`, `.pytest_cache/` y cachés de herramientas; el del parcial ignora además `CLAUDE.local.md`. En disco hay `__pycache__/` en la raíz del parcial y en `scripts/`, `.pytest_cache/` en `Despliegue/` y un `.venv` local: un zip armado a mano los arrastraría.
- **Archivos versionados que no son del proyecto:** el parcial versiona `.claude/` (comandos y skills del asistente). También versiona `openspec/`, `AGENTS.md`, `CLAUDE.md` (sólo `@AGENTS.md`), `PLAN_PARCIAL.md`, `REPARTO.md` y la consigna en PDF.
- **`Despliegue/` ya está completa**: `Dockerfile`, `.dockerignore`, `env.example`, `DEPLOY.md` y `evidencia/D-01` a `D-08` versionados (CHG-02, #64). No se toca.
- **Historial**: 355 commits en todas las ramas; una primera pasada (`git log --all --diff-filter=A --name-only`) no encontró ningún `.env` agregado nunca. Los dos `alembic.ini` tienen `# sqlalchemy.url =` comentado.
- **C-14** (`test/solo_agregado.sql`) ya trae en comentarios cómo correrlo con `docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < test/solo_agregado.sql`, con `\set VERBOSITY verbose`.
- **C-15** (`test/c15_detalle_consultas.http`): login de `admin@example.com` (contraseña de mentira del seed), `GET /ventas/1` (venta del seed, 2 renglones), `POST /ventas/` con los libros 1 a 4 × 1 y `GET` de esa venta (4 renglones). `SQL_ECHO=true` activa `echo` del motor (`app/core/database.py`), que loguea cada sentencia, `BEGIN (implicit)`, los parámetros y `COMMIT`/`ROLLBACK`; uvicorn loguea la línea de acceso **después** de las consultas de cada pedido.
- **README actual**: ya tiene `POSTGRES_*`, `JWT_SECRET` y `python seed.py`, pero los casos son C-01 a C-08 del TP, la tabla de endpoints es la del TP (`limit`/`offset`, sin `/auth`, `/usuarios`, `/eventos`, `/mis-ventas`, reposición ni baja), cita `docs/evidencia_c07.md` y no tiene integrantes.
- **Tests**: `pytest.ini` con `pythonpath = .` y `testpaths = tests`; `tests/conftest.py` importa la app (genera un `JWT_SECRET` de prueba), así que un test sin base corre igual sin Docker.

## Goals / Non-Goals

**Goals:**
- Que el zip se arme con un comando y que, por construcción, no pueda llevar un secreto ni un archivo local aunque esté en disco.
- Que la evidencia de C-14 y C-15 sea texto legible por quien corrige, reproducible con los archivos de `test/` y sin datos sensibles.
- Que la entrega cumpla la definición de terminado verificada en esta rama, no supuesta.

**Non-Goals:**
- Reescribir el historial de git (si aparece un secreto real se decide con el grupo: rotarlo y, si hace falta, `git filter-repo`, en otro trabajo).
- Automatizar la captura de evidencia con un script versionado: se captura una vez, en el apply, y el archivo explica cómo repetirla con `test/`.
- Validar el zip contra el campus o subirlo.

## Decisions

### D1 · Lista de archivos desde git (`git ls-files`), no un recorrido del disco ni `git archive`

`scripts/armar_zip.py` corre, para cada carpeta de origen, `git -C <carpeta> ls-files -z --cached --others --exclude-standard` y empaqueta esas rutas leyendo el contenido **del disco**.

- **Por qué:** el `.gitignore` de cada carpeta pasa a ser la lista de exclusión principal; un `.env`, un `.venv` o un `__pycache__` en disco no entran aunque existan. `--others --exclude-standard` suma los archivos nuevos no ignorados (la evidencia recién capturada, el README editado) sin obligar a commitear antes de armar; `-z` evita el escapado de rutas con espacios o acentos (`TP - DEL OBJETO…`).
- **Alternativa `git archive HEAD`:** es lo más hermético (sólo lo commiteado), pero obliga a commitear antes de cada prueba del zip y no ve cambios sin commitear; además `git archive` de una subcarpeta exige prefijos y `--worktree-attributes`. Descartado por fricción; el riesgo que cubre (empaquetar algo no commiteado) lo cubre el `git status` limpio que piden las tareas antes del armado final.
- **Alternativa `os.walk` + lista negra:** depende de que la lista negra esté completa; un archivo local nuevo (`notas.txt`, un dump) se colaría. Descartado.
- Un archivo versionado que ya no existe en disco (borrado sin commitear) se omite.

### D2 · Lista negra de respaldo y aborto ante un `.env` versionado

Además del `.gitignore`, el script descarta toda ruta con un segmento `.venv`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.git` o `.claude`, todo `*.pyc`/`*.pyo` y `CLAUDE.local.md`. Si git **versiona** (o tiene en el índice) un archivo llamado `.env`, el script **aborta** con un error que lo nombra y no escribe el zip.

- **Por qué:** defensa en profundidad para lo que la consigna nombra explícitamente. Un `.env` versionado no es un archivo para filtrar en silencio: significa un secreto en el repo (y en el historial), que la consigna penaliza con «no se corrige»; abortar obliga a resolverlo.
- **`.claude/` afuera:** es configuración del asistente de cada integrante, no parte del proyecto que se corrige. `openspec/`, `AGENTS.md`, `CLAUDE.md`, `PLAN_PARCIAL.md`, `REPARTO.md` y la consigna **sí** entran: documentan diseño y reparto, el README remite a `AGENTS.md`, y no tienen secretos. Alternativa (dejar sólo lo que lista la consigna) descartada: la consigna fija un mínimo, no un máximo, y recortar a mano es otra fuente de error.

### D3 · Estructura del zip y salida

- Entradas `parcial/<ruta relativa>` y `despliegue/<ruta relativa>`, con `/` como separador (`PurePosixPath`), sin entradas de directorio, ordenadas para que dos armados del mismo árbol listen igual. `ZIP_DEFLATED`; `zipfile` marca UTF-8 los nombres no ASCII.
- Orígenes por defecto: la carpeta del script (`parcial`) y `<parcial>/../Despliegue` (`despliegue`); se pueden cambiar por argumentos (`--parcial`, `--despliegue`) y la salida con `--salida`. Por defecto la salida es `dist/Parcial_Cap1a6_GordosProgramacion.zip` dentro del parcial, y `dist/` se agrega al `.gitignore`: queda fuera del repo, fuera del propio zip (está ignorada) y en un lugar fijo. Alternativa: escribir en `Prog3/` (al lado del zip del parcial 1) — descartada porque esa carpeta es la raíz del repo y el zip quedaría como archivo sin seguimiento. El nombre del grupo vive en una constante (`GRUPO = "GordosProgramacion"`).
- Si falta una carpeta de origen o `git` no está en el PATH, error claro y código de salida distinto de cero. Al terminar imprime la ruta del zip y cuántos archivos tiene cada raíz.
- Escribe a un temporal y lo renombra al final: un error a mitad de camino no deja un zip a medias.

### D4 · Diseño testeable (Strict TDD)

El script expone funciones puras o casi: `excluida(ruta) -> bool` (lista negra), `listar_archivos(carpeta) -> list[str]` (git + filtros + aborto por `.env`) y `armar_zip(origenes: dict[str, Path], destino: Path) -> dict[str, int]`; `main()` sólo parsea argumentos. `tests/test_armar_zip.py` (sin marca `db`):

- arma en `tmp_path` dos carpetas `git init` (sin commits: `--others` las ve), con un `.gitignore` como el real y en disco `.venv/`, `__pycache__/x.pyc`, `.pytest_cache/`, `.env`, `CLAUDE.local.md`, `.claude/`, un archivo ignorado y archivos legítimos;
- verifica raíces (`parcial/`, `despliegue/` y nada más), exclusiones, inclusión de un archivo nuevo sin commitear y de un `.dockerignore`, el conteo devuelto y que las carpetas de origen no cambian;
- verifica el aborto con `git add -f .env` (sin zip en el destino).

Los tests llaman a git por `subprocess`; con `user.name`/`user.email` no hace falta configurar nada porque no se commitea.

### D5 · Evidencia como texto con encabezado y resumen

Archivos en `evidencia/` (carpeta nueva del parcial):

- `C-14_solo_agregado.txt`: encabezado (fecha, commit, comando exacto) y la salida de `docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -a' < test/solo_agregado.sql` corrido justo después de `python seed.py` (`-a` repite cada sentencia del script antes de su resultado, así se lee qué pedido produjo qué error).
- `C-15_detalle_consultas.txt`: encabezado (fecha, commit, cómo se reproduce con `test/c15_detalle_consultas.http`), una tabla resumen (pedido, renglones, consultas totales del pedido y consultas propias del detalle de la venta) y, por cada `GET /ventas/{id}`, el fragmento de consola desde la primera sentencia del pedido hasta su línea de acceso de uvicorn. Se cuentan sentencias SQL (no `BEGIN`, `COMMIT`, `ROLLBACK` ni líneas de parámetros), igual que la evidencia del TP.
- **Cómo se captura C-15:** uvicorn con `SQL_ECHO=true` y la consola redirigida a un archivo de la carpeta temporal; los pedidos se hacen con un cliente HTTP desde la carpeta temporal siguiendo exactamente los pasos del `.http` (la extensión REST Client no corre por línea de comandos). El helper no se versiona (ver Non-Goals).
- **Sin datos sensibles:** sólo entran los fragmentos de los dos `GET` (el login queda afuera); antes de guardar se revisa que no haya cookies, hashes, `JWT_SECRET` ni la contraseña de la base. Capturas de pantalla, si el grupo las agrega, van al lado con el mismo prefijo.
- Alternativa (sólo capturas de pantalla): la consigna acepta «la captura o el fragmento de consola»; el texto se puede buscar, revisar en el PR y regenerar.

### D6 · Revisión de secretos sin herramientas nuevas

Sobre `git log --all` del repo completo (las dos carpetas y el resto de `Prog3/`):

1. archivos `.env` (o `*.env` no `env.example`) agregados alguna vez: `git log --all --diff-filter=A --name-only`;
2. contenido: `git log --all -p -G '<patrón>'` para `POSTGRES_PASSWORD=.+`, `JWT_SECRET=.+`, URLs `postgres(ql)?(\+asyncpg)?://usuario:contraseña@`, `sqlalchemy.url = ` sin comentar, `password=`/`PASSWORD:` en `docker-compose`, claves privadas (`BEGIN .*PRIVATE KEY`);
3. cada coincidencia se clasifica: valor de mentira de tests o del seed (`admin-seed-1`, contraseñas de prueba de `tests/`), plantilla vacía, o **real**.

Si aparece un valor real se **detiene** el change y se avisa al usuario (dominio seguridad: análisis, sin reescribir nada). El resultado (comandos y conclusión, sin repetir valores) va a la descripción del PR, no al zip. Si `gitleaks` está instalado se corre además, pero no es requisito. Alternativa (instalar `gitleaks`/`trufflehog`): descartada como dependencia; los patrones del proyecto son pocos y conocidos.

### D7 · Definición de terminado sin tocar la base de desarrollo

- **Reversibilidad** sobre una base **nueva y vacía** (`libreria_dod`, creada con `createdb` dentro del contenedor): `alembic upgrade head` → `alembic downgrade base` → `alembic upgrade head` con `POSTGRES_DB=libreria_dod` en el entorno del comando (pydantic-settings prioriza el entorno sobre `.env`); al final se borra. Así no se pierde el estado de la base de desarrollo.
- Después: `python seed.py` en la base de desarrollo, uvicorn, `/health/live` y `/health/ready` en 200; `REQUIRE_TEST_DB=1 pytest` verde (incluye los `.http` C-01 a C-16 sobre el seed y el invariante de stock); `git check-ignore .env`; revisión de los dos `env.example` y `alembic.ini`.

### D8 · `docs/evidencia_c07.md` se borra

Es evidencia del TP 1–4: su «C-07» es el N+1 del TP (en el parcial C-07 es revocar un rol), cita `DB_ECHO` y `python -m scripts.seed`, y quien corrige podría tomarla por evidencia del parcial. La reemplaza `evidencia/C-15_detalle_consultas.txt`; el original queda en el historial y en `despliegue/docs/evidencia_c07.md`. Si `docs/` queda vacía, desaparece.

### D9 · README reescrito para el parcial

Se conserva la estructura del README actual (requisitos, clonar, venv, dependencias, `.env`, base, migraciones, seed, servidor, tests) y se agregan/cambian: sección **Integrantes** (grupo GordosProgramacion: Matias Limina, Nicolas Monjelardi, Lautaro Aguero), arranque con `docker compose up -d` antes de Alembic, casos **C-01 a C-16** (`test/`, REST Client, `python seed.py` antes de cada archivo, C-14 con psql), **Evidencia** (enlace a los dos archivos), **Endpoints** del parcial agrupados por acceso (abiertos, `/auth`, personal, ADMIN, propio) con el envoltorio `page`/`size`, **Estructura** con `repository.py`/`unit_of_work.py`, `evidencia/` y `scripts/armar_zip.py`, y **Armado de la entrega** (`python scripts/armar_zip.py`). Los comandos se dan para PowerShell y Git Bash donde difieren (activar el venv, copiar `env.example`). Las rutas se copian de los routers al implementar, no de esta lista.

## Risks / Trade-offs

- [Un archivo nuevo legítimo queda sin agregar al repo y aun así entra al zip (D1 incluye no ignorados)] → antes del armado final, `git status` limpio en la rama; el resumen del script con conteos permite comparar contra `git ls-files | wc -l`.
- [Un archivo sensible no ignorado y no versionado en disco entraría (p. ej. un `dump.sql`)] → mismo control de `git status` limpio; el armado final se hace después del commit.
- [La consola de C-15 incluye consultas de sesión y roles además del detalle] → la tabla separa «consultas del pedido» de «consultas del detalle»; el mismo usuario hace los dos pedidos, así ambas cifras son comparables, como ya advierte el `.http`.
- [Docker o el puerto 5432/5433 no disponibles en la máquina donde corre el apply] → la evidencia y la DoD quedan como tareas pendientes y se reporta; el resto (README, script, test) no depende de la base.
- [Patrones de secretos con falsos negativos (formatos no previstos)] → se suma una búsqueda manual de los valores reales del `.env` local en el historial (`git log --all -S`), sin imprimirlos.
- [La consigna lista `main.py` sin el prefijo `app/`] → se mantiene `app/main.py` (lo que arranca `uvicorn app.main:app`, consistente con el TP 1–4); ver Open Questions.

## Migration Plan

Sin migración de datos. Orden: test del script (RED) → script (GREEN) → README → evidencia → borrado de `docs/evidencia_c07.md` → revisión de secretos → DoD → commit → armado final del zip sobre el árbol commiteado → advisor → plan y archivo del change. Volver atrás es revertir el commit; el zip vive fuera del repo.

## Open Questions

- ¿La cátedra acepta `app/main.py` en lugar de `main.py` en la raíz? `AGENTS.md` lo dejó «pendiente de confirmar antes de CHG-20». No cambia este change (el README documenta `uvicorn app.main:app`); si la cátedra pidiera la raíz, sería un change aparte.
- Capturas de pantalla de C-14/C-15: el grupo puede agregarlas a `evidencia/` después; el script las incluye solo.
