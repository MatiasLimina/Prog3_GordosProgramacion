# entrega Specification

## Purpose
Define el paquete que el grupo entrega a la cátedra: el zip con los dos proyectos (`parcial/` y `despliegue/`), lo que entra y lo que nunca entra, cómo se arma de forma reproducible y sin filtrar secretos, el `README.md` del parcial y la carpeta `evidencia/` con los casos C-14 y C-15.

## Requirements

### Requirement: Nombre y raíces del zip
La entrega SHALL ser un único archivo `Parcial_Cap1a6_GordosProgramacion.zip`. Sus entradas MUST colgar sólo de dos carpetas raíz: `parcial/` (este proyecto) y `despliegue/` (el TP 1–4 de la carpeta hermana `Despliegue`). Los nombres de las entradas MUST usar `/` como separador, sin rutas absolutas ni `..`.

#### Scenario: Sólo dos raíces
- **WHEN** se listan las entradas del zip armado
- **THEN** cada una empieza con `parcial/` o con `despliegue/` y ninguna con otra carpeta, una ruta absoluta o `..`

#### Scenario: Las dos carpetas presentes
- **WHEN** se abre el zip
- **THEN** están `parcial/README.md`, `parcial/requirements.txt`, `parcial/env.example`, `parcial/alembic.ini`, `parcial/migrations/`, `parcial/test/` y `parcial/app/`, y `despliegue/Dockerfile`, `despliegue/.dockerignore`, `despliegue/env.example`, `despliegue/DEPLOY.md` y `despliegue/evidencia/`

### Requirement: Lo que nunca entra al zip
El zip MUST NOT contener, en ninguna de las dos carpetas, entradas dentro de `.venv/`, `__pycache__/`, `.pytest_cache/`, `.git/` ni `.claude/` (configuración local del asistente), archivos `.env`, archivos `*.pyc`, `CLAUDE.local.md` ni ningún archivo que el `.gitignore` del proyecto ignore.

#### Scenario: Entorno, cachés y secretos excluidos
- **WHEN** las carpetas de origen tienen `.venv/`, `__pycache__/`, `.pytest_cache/`, un `.env` y un `CLAUDE.local.md` en disco
- **THEN** el zip armado no tiene ninguna entrada con esos nombres ni dentro de esas carpetas

#### Scenario: Archivo ignorado por git
- **WHEN** un archivo de la carpeta de origen coincide con un patrón del `.gitignore`
- **THEN** no aparece en el zip

#### Scenario: Un .env versionado por error
- **WHEN** git versiona un archivo llamado `.env` dentro de una de las carpetas de origen
- **THEN** el armado se detiene con un error que nombra el archivo y no deja un zip

### Requirement: Contenido tomado de git
Salvo lo excluido por el requisito anterior, el zip SHALL incluir los archivos que git versiona en cada carpeta de origen y los no versionados que git no ignora, con el contenido que tienen en disco. Un archivo versionado que ya no existe en disco MUST NOT figurar. La carpeta `Despliegue` MUST empaquetarse tal como está, sin modificarla.

#### Scenario: Archivo nuevo sin commitear
- **WHEN** existe un archivo nuevo no ignorado (por ejemplo, una evidencia recién capturada) que todavía no se commiteó
- **THEN** el zip lo incluye

#### Scenario: Despliegue intacto
- **WHEN** se arma el zip
- **THEN** `git status` de la carpeta `Despliegue` no muestra cambios causados por el armado

### Requirement: Armado reproducible y multiplataforma
El zip SHALL armarse con un solo comando, corrido desde la carpeta del proyecto, que funcione igual en PowerShell y en Git Bash. La salida por defecto MUST quedar en una carpeta que git ignora, y el comando MUST informar la ruta del zip y la cantidad de archivos de cada raíz.

#### Scenario: Armado en Windows
- **WHEN** se corre `python scripts/armar_zip.py` desde la carpeta del proyecto en PowerShell
- **THEN** queda `dist/Parcial_Cap1a6_GordosProgramacion.zip` y la salida informa su ruta y cuántos archivos tiene `parcial/` y cuántos `despliegue/`

#### Scenario: El zip no se versiona
- **WHEN** se arma el zip y se corre `git status`
- **THEN** el zip no aparece como archivo nuevo

### Requirement: README del parcial
`parcial/README.md` SHALL tener los nombres y apellidos de los integrantes (Matias Limina, Nicolas Monjelardi, Lautaro Aguero) y el nombre del grupo, y los pasos para levantar el proyecto desde cero: entorno virtual, dependencias, `.env` con las variables `POSTGRES_*` y `JWT_SECRET` y el comando que genera la clave de firma, base en Docker, `alembic upgrade head`, `python seed.py` y arranque del servidor.

#### Scenario: Integrantes
- **WHEN** quien corrige abre el `README.md` del parcial
- **THEN** encuentra los tres integrantes con nombre y apellido y el nombre del grupo

#### Scenario: Pasos desde cero
- **WHEN** alguien sigue el `README.md` en una máquina sin el proyecto instalado
- **THEN** cada paso, desde crear el entorno virtual hasta `/health/ready` en 200, está escrito en orden con su comando

### Requirement: README al día con el parcial
`parcial/README.md` MUST describir el proyecto del parcial y no el TP 1–4: los casos C-01 a C-16 de `test/` y cómo se corren, la carpeta `evidencia/`, los listados con el envoltorio `{items, total, page, size, pages}` y las rutas de acceso. MUST NOT indicar `DATABASE_URL`, `DB_ECHO`, `python -m scripts.seed` ni paginación con `limit`/`offset`.

#### Scenario: Sin restos del TP 1–4
- **WHEN** se busca en el `README.md` del parcial `DATABASE_URL`, `DB_ECHO`, `scripts.seed`, `limit` u `offset`
- **THEN** no aparece ninguno como instrucción vigente

#### Scenario: Casos y evidencia enlazados
- **WHEN** quien corrige busca cómo demostrar C-14 y C-15
- **THEN** el `README.md` indica el archivo de `test/` que los corre y el archivo de `evidencia/` con su salida

### Requirement: Evidencia de C-14
`parcial/evidencia/` SHALL tener la salida de psql de `test/solo_agregado.sql` corrido sobre la carga inicial, donde se ven el UPDATE y el DELETE sobre `movimiento_stock` rechazados por el disparador y la fila sin cambios antes y después.

#### Scenario: Los dos rechazos visibles
- **WHEN** quien corrige abre la evidencia de C-14
- **THEN** ve el comando usado, el error del disparador para el UPDATE y para el DELETE, y la misma fila en la consulta del principio y en la del final

### Requirement: Evidencia de C-15
`parcial/evidencia/` SHALL tener el fragmento de consola del servidor con `SQL_ECHO=true` que muestra las consultas emitidas por el detalle de una venta con 2 renglones y por el de otra con 4, con la cantidad de consultas de cada uno, que MUST ser la misma.

#### Scenario: Misma cantidad con 2 y con 4 renglones
- **WHEN** quien corrige compara los dos bloques de la evidencia de C-15
- **THEN** cada bloque identifica su pedido (`GET /ventas/{id}` y la cantidad de renglones) y los dos tienen la misma cantidad de consultas

### Requirement: Sin secretos en la entrega
Ni el zip ni el historial de git del repositorio SHALL contener credenciales reales: ningún `.env` versionado alguna vez, ninguna contraseña real de base de datos ni clave de firma JWT real, y `alembic.ini` sin URL de conexión. Las contraseñas de mentira del seed y los valores vacíos de `env.example` MAY figurar.

#### Scenario: Historial limpio
- **WHEN** se revisa el historial completo de git en busca de archivos `.env` y de valores de `POSTGRES_PASSWORD`, `JWT_SECRET` o URLs con contraseña
- **THEN** no aparece ninguna credencial real, o el hallazgo queda documentado y escalado al grupo antes de entregar

#### Scenario: alembic.ini sin URL
- **WHEN** se abre `parcial/alembic.ini` o `despliegue/alembic.ini`
- **THEN** la línea `sqlalchemy.url` está comentada o ausente
