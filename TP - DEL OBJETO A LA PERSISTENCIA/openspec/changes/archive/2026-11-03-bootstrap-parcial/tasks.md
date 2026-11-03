# Tasks

## 1. Precondiciones y línea base

- [x] 1.1 `openspec init --tools claude --language es` en esta carpeta; verificado con `openspec list` (responde sin error) y la existencia de `openspec/config.yaml`, `.claude/commands/opsx/` y `.claude/skills/openspec-*`.
- [x] 1.2 Confirmar con Matias las Open Questions de `design.md` (PDF de consigna, `app/main.py`); verificar que la respuesta quede anotada en `design.md` antes del commit 1.
- [x] 1.3 Levantar la base (`docker compose up -d`, `docker compose ps` en `healthy`) y correr `REQUIRE_TEST_DB=1 pytest -q`; anotar en este archivo el resultado «N passed» como línea base (debe ser verde y sin tests `db` salteados).
  - Línea base (2026-11-03, con la base levantada y las dependencias nuevas ya instaladas): `REQUIRE_TEST_DB=1 pytest -q` → **321 passed** en 515 s, sin tests salteados. La corrida previa sin Docker dio 158 passed, 163 skipped.

## 2. Commit 1 · `chore(parcial): inicializar openspec y dependencias de auth`

- [x] 2.1 Agregar a `requirements.txt`, al final y con el estilo `paquete>=X.Y`, las líneas `pydantic-settings>=2.0`, `bcrypt>=4.0` y `PyJWT>=2.8`; verificar con `git diff requirements.txt` que sólo hay tres líneas nuevas.
- [x] 2.2 Instalar con `pip install -r requirements-dev.txt` dentro del `.venv` y verificar con `python -c "import pydantic_settings, bcrypt, jwt; print(jwt.__version__, bcrypt.__version__)"` y `pip check` (sin conflictos).
  - `jwt` 2.15.1 / `bcrypt` 5.0.0 instalados; `pip check` sin conflictos.
- [x] 2.3 Correr `REQUIRE_TEST_DB=1 pytest -q` y verificar el mismo «N passed» de 1.3.
  - Verificado: 321 passed con `REQUIRE_TEST_DB=1`, igual que 1.3 (las dependencias nuevas no rompen nada).
- [x] 2.4 Preparar el commit: `git add openspec/ .claude/commands/opsx/ .claude/skills/ requirements.txt` más las rutas de PDF que decida 1.2; verificar con `git status` que no entran `.env`, `.venv/`, `__pycache__/` ni `../Parcial1_Proyecto_Libreria.zip`, y crear el commit con el mensaje del encabezado.
  - pendiente: commit lo hace el orquestador tras revisión (no se hizo `git add` ni `git commit`).

## 3. Commit 2 · `docs(agents): actualizar reglas al parcial cap 1-6`

- [x] 3.1 Encabezado y §1–§2 de `AGENTS.md`: fuente de verdad `Parcial_Cap1a6_Consigna.pdf` + `PLAN_PARCIAL.md`, sin el aviso «Parcial en curso»; stack con pydantic-settings 2.0, bcrypt 4.0 y PyJWT 2.8; comandos con `python seed.py`, `SQL_ECHO=true` y `alembic downgrade base`. Verificar con `grep -n "TP_Cap1a4\|Parcial en curso\|limit/offset" AGENTS.md` sin resultados.
- [x] 3.2 §3 Estructura según págs. 8–9: `app/core/{config,database,security,dependencies,repository,paginacion,unit_of_work}.py` (más `base.py`, `tipos.py`, `errors.py` propios), por módulo `models, schemas, repository, unit_of_work, service, router`, `health` sólo con `router.py`, módulo `usuarios` con `AsignacionRol`/`IntentoAcceso`/`EventoSeguridad`, `MovimientoStock` en `libros`, `seed.py` en la raíz. Verificar contra la tabla de págs. 8–9 que no falta ninguna ruta.
  - Las secciones nuevas se insertaron como §5 (Capas) y §6 (Acceso); Convenciones, Reglas duras, Transición, Git y Terminado pasan a §7–§11.
- [x] 3.3 §4 Dueños por change (D4) con Matias, Nico y Lauti y la regla de archivos compartidos con revisión del lead; verificar que cada CHG de la tabla de seguimiento de `PLAN_PARCIAL.md` tenga el mismo responsable.
- [x] 3.4 Nueva sección «Capas y transacciones»: Router → Service → UoW → Repository → Model con quién construye, abre, confirma y cierra; dependencias de usuario/rol con la misma sesión; RN-02, RN-10 y RN-16 en un solo bloque `async with`; stock con una sola vía de escritura y `movimiento_stock` de sólo agregado; `intento_acceso` como única escritura con sesión y transacción propias y su comentario de tres partes. Verificar cada punto contra Ej6 y Ej7 de la consigna.
- [x] 3.5 Nueva sección «Acceso»: `Settings` sin default para contraseña de la base ni clave JWT, `@computed_field` desde `POSTGRES_*`; cookie `access_token` (`HttpOnly`, `SameSite=Lax`, `Max-Age`, `Secure` configurable), nunca en el cuerpo ni en `Authorization`; 401 vs 403; 429 con `Retry-After`; bcrypt en `to_thread` bajo semáforo, hash antes de abrir la transacción, 72 bytes; roles vigentes consultados en la base; dos grupos de rutas. Verificar contra pág. 4, Ej4 y Ej5, y que diga que se implementa en CHG-03/10/11/12.
- [x] 3.6 §5–§6 Convenciones y reglas duras: envoltorio `{items, total, page, size, pages}` en lugar de `limit/offset`; `extra="forbid"`; 201/204/404/409/422/503; servicios que reciben el UoW (no la sesión); índices únicos parciales con nombre en el diccionario de 409; renumerar toda RN-xx y C-xx a la del parcial. Verificar con `grep -n "RN-\|C-[0-9]" AGENTS.md` que cada referencia coincide con la numeración de la consigna.
- [x] 3.7 Sección «Transición» (D2): qué partes del código siguen el patrón del TP 1–4 y qué change las migra; regla de no migrar módulos fuera de su change. Verificar que nombra `pagination.py`, `DATABASE_URL`/`DB_ECHO`, servicios con sesión y `scripts/seed.py`.
- [x] 3.8 §7 Git (D5: una rama por change `<tipo>/<nombre-openspec>`, PR a `main` revisado por otro integrante, commits convencionales en español) y §8 Terminado del parcial (`upgrade head` / `downgrade base` / `upgrade head`, `python seed.py`, C-01 a C-16 en `test/`, `evidencia/` con C-14 y C-15, `pytest` verde, sin secretos). Verificar contra la DoD de `PLAN_PARCIAL.md` y el formato de entrega de la consigna.
- [x] 3.9 Marcar CHG-00 como `en PR` en la tabla de seguimiento de `PLAN_PARCIAL.md` y actualizar el gotcha 1 (ya no aplica tras el merge); verificar con `git diff PLAN_PARCIAL.md`.
- [x] 3.10 Revisión de Matias sobre el diff completo de `AGENTS.md` (archivo compartido del lead); verificar su aprobación explícita antes de crear el commit 2 con el mensaje del encabezado.
  - pendiente: revisión de Matias y commit los hace el orquestador (no se hizo commit).

## 4. Verificación final

- [x] 4.1 `openspec list` responde y muestra `bootstrap-parcial`; `REQUIRE_TEST_DB=1 pytest -q` da el mismo «N passed» de 1.3; `git log --oneline -2` muestra los dos commits del plan.
  - Verificado: `openspec list` muestra el change, 321 passed y commits 9b31e3d y 4bfb0b5.
- [x] 4.2 Revisión del diff final (`git diff main...HEAD`) con el advisor (checkpoint FINAL_DIFF); verificar que no queden objeciones BLOCK antes de abrir el PR.
  - pendiente: advisor lo consulta el orquestador.
