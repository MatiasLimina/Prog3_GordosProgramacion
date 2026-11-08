# Librería — API con FastAPI + PostgreSQL

Parcial de Programación III (capítulos 1 a 6), grupo **GordosProgramacion**. API para una librería: catálogo (editoriales, géneros, autores, libros), clientes y ventas, con acceso por usuarios y roles, stock por movimientos y repositorios con Unit of Work.
Stack: Python 3.12+, FastAPI, SQLModel/SQLAlchemy async, asyncpg, PostgreSQL 16 (Docker), Alembic, bcrypt y PyJWT.

> Las convenciones del proyecto están en [AGENTS.md](AGENTS.md); el backlog de changes del parcial, en [PLAN_PARCIAL.md](PLAN_PARCIAL.md).

## Integrantes

Grupo **GordosProgramacion**:

- Matias Limina
- Nicolas Monjelardi
- Lautaro Aguero

## Puesta en marcha desde cero

Todos los comandos se corren **desde esta carpeta** (`parcial/` dentro del zip de la entrega; `TP - DEL OBJETO A LA PERSISTENCIA/` en el repositorio): la app busca el `.env` en el directorio actual.

### 1. Requisitos
- Python 3.12 o superior
- Docker y Docker Compose
- Git (sólo si se clona el repositorio)

### 2. Clonar el repositorio (si no se recibió el zip)
```bash
git clone https://github.com/MatiasLimina/Prog3_GordosProgramacion.git
cd Prog3_GordosProgramacion/"TP - DEL OBJETO A LA PERSISTENCIA"
```

### 3. Entorno virtual
Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
Windows (Git Bash):
```bash
python -m venv .venv
source .venv/Scripts/activate
```
Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Dependencias
```bash
pip install -r requirements-dev.txt   # app + herramientas de test
# o, sólo para correr la app:
pip install -r requirements.txt
```

### 5. Variables de entorno
PowerShell:
```powershell
Copy-Item env.example .env
```
Git Bash / Linux / macOS:
```bash
cp env.example .env
```
Editá `.env` y completá lo que viene vacío o de ejemplo:
- `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_DB`: las credenciales de la base. **`POSTGRES_PASSWORD` viene vacía a propósito** (Postgres no arranca sin contraseña). La URL de la base se arma sola con las variables `POSTGRES_*`.
- `JWT_SECRET`: la clave de firma del token (obligatoria, mínimo 32 caracteres). Generá una con:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```

El archivo `.env` **no se commitea** (está en `.gitignore`) y no viaja en el zip. Si el puerto 5432 ya está ocupado (por ejemplo, por un PostgreSQL instalado en Windows), poné `POSTGRES_PORT=5433` en `.env` (Docker y la app usan el mismo valor).

### 6. Base de datos
```bash
docker compose up -d
```
Levanta PostgreSQL 16 con las credenciales de `.env`. Podés ver el estado con `docker compose ps` (debe figurar `healthy`).

### 7. Esquema (migraciones)
```bash
alembic upgrade head
```
El esquema se crea sólo con Alembic; la app nunca usa `create_all`. Para comprobar que las migraciones son reversibles, sobre una base vacía: `alembic downgrade base` y otra vez `alembic upgrade head`.

### 8. Datos iniciales
```bash
python seed.py
```
Deja la base en un estado inicial conocido: vacía las tablas y carga 5 usuarios con sus roles, editoriales, géneros, autores, 5 libros con su stock inicial por movimientos, 3 clientes, un perfil y una venta, con ids fijos. Es atómico (o carga todo o no cambia nada) y se puede correr las veces que haga falta. Las contraseñas de prueba de los usuarios sembrados (de mentira) están sólo en `seed.py`.

### 9. Servidor
```bash
uvicorn app.main:app --reload
```
Probar:
- http://localhost:8000/health/live → 200, no toca la base
- http://localhost:8000/health/ready → 200 si la base contesta (503 si no)
- http://localhost:8000/docs → documentación interactiva (Swagger)

## Tests

1. Crear una vez la base de tests (usa las credenciales del contenedor, sin escribirlas):
   ```bash
   docker compose exec -T postgres sh -c 'createdb -U "$POSTGRES_USER" libreria_test'
   ```
2. Correr:
   ```bash
   pytest
   ```
   Los tests con base real usan `libreria_test` (se deriva de las variables `POSTGRES_*`, cambiando sólo la base; el conftest recrea el esquema en cada corrida con `alembic upgrade head` y nunca toca la base de desarrollo). Si la base no responde, esos tests se **saltean** con un aviso. Con `REQUIRE_TEST_DB=1` la falta de base es un **fallo**: usarlo antes de entregar para no confiar en skips.
   PowerShell: `$env:REQUIRE_TEST_DB = "1"; pytest`. Git Bash / Linux / macOS: `REQUIRE_TEST_DB=1 pytest`.

`pytest` también corre los `.http` de `test/` (C-01 a C-16, menos C-14) contra la app sobre la carga inicial, y comprueba el invariante de stock.

## Casos de prueba (C-01 a C-16)

Están en la carpeta `test/`, un archivo `cNN_*.http` por caso, y se ejecutan con la extensión **REST Client** de VS Code. Cada pedido indica en un comentario el código esperado.

1. Antes de **cada** archivo, dejar la base en el estado inicial: `python seed.py`.
2. Con el servidor levantado (`uvicorn app.main:app --reload`), correr cada archivo de arriba abajo.

| Caso | Archivo | Qué prueba |
|---|---|---|
| C-01 | `c01_parametro_ruta.http` | Parámetro de ruta que no es un entero de 32 bits → 422 |
| C-02 | `c02_registro.http` | Auto-registro y correos repetidos |
| C-03 | `c03_cookie_login.http` | El token viaja sólo en la cookie `access_token` |
| C-04 | `c04_login_indistinguible.http` | Correo existente con clave mala y correo inexistente: misma respuesta |
| C-05 | `c05_limite_intentos.http` | Límite de intentos: el sexto da 429 con `Retry-After` |
| C-06 | `c06_401_403_propio.http` | 401 contra 403, y lo propio |
| C-07 | `c07_revocar_rol.http` | Revocar un rol con la sesión abierta |
| C-08 | `c08_autoproteccion.http` | Nadie se revoca su propio ADMIN |
| C-09 | `c09_cambio_obligatorio.http` | Cambio obligatorio de contraseña |
| C-10 | `c10_venta_valida.http` | Venta válida: renglones, total, descuento de stock y movimientos |
| C-11 | `c11_venta_sin_stock.http` | Venta sin stock: 409 y ninguna escritura |
| C-12 | `c12_venta_rechazada.http` | Cliente o libro inexistente, o libro dado de baja: 409 |
| C-13 | `c13_reponer_baja_isbn.http` | Reposición, baja lógica y alta del mismo ISBN |
| C-14 | `solo_agregado.sql` | `movimiento_stock` es de sólo agregado (disparador); se corre con psql |
| C-15 | `c15_detalle_consultas.http` | El detalle de una venta emite la misma cantidad de consultas con 2 o 4 renglones |
| C-16 | `c16_busqueda_paginacion_patch.http` | Búsqueda con parámetros ligados, paginación con filtro y PATCH parcial |

**C-14** no es un `.http`: es un script SQL que se corre con psql sobre la carga inicial (`python seed.py` antes):
```bash
docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -a' < test/solo_agregado.sql
```
`test/invariante_stock.sql` comprueba que `libro.stock` sea la suma de los movimientos de cada libro.

**C-15** necesita `SQL_ECHO=true` en `.env` (y reiniciar el servidor) para que la consola muestre cada consulta emitida.

## Evidencia

La carpeta [`evidencia/`](evidencia/) tiene la salida de los dos casos que no se ven en una respuesta HTTP:

- [`evidencia/C-14_solo_agregado.txt`](evidencia/C-14_solo_agregado.txt): salida de psql de `test/solo_agregado.sql`; el UPDATE y el DELETE sobre `movimiento_stock` los rechaza el disparador.
- [`evidencia/C-15_detalle_consultas.txt`](evidencia/C-15_detalle_consultas.txt): consola de uvicorn con `SQL_ECHO=true`; el detalle de una venta de 2 renglones y el de una de 4 emiten la misma cantidad de consultas.

## Endpoints

Los listados devuelven el envoltorio `{items, total, page, size, pages}` (`page` ≥ 1, `size` entre 1 y 100, 20 por defecto; una página más allá de la última da 422). El token viaja sólo en la cookie `access_token`, nunca en el cuerpo ni en `Authorization`. Sin sesión responde 401; con sesión pero sin el rol (o con el cambio de contraseña pendiente) responde 403. Todas las rutas pueden responder 422 si el cuerpo o los parámetros no cumplen el contrato.

### Abiertas (sin sesión)

| Método y ruta | Códigos | Notas |
|---|---|---|
| `GET /health/live` | 200 | no toca la base |
| `GET /health/ready` | 200, 503 | ejecuta `SELECT 1` |
| `POST /auth/registro` | 201, 409, 422 | crea usuario, rol CLIENTE y ficha de cliente; 409 si el correo ya existe |
| `POST /auth/login` | 200, 401, 429, 422 | pone la cookie `access_token`; 429 con `Retry-After` tras 5 fallos en 60 s |
| `POST /auth/logout` | 200 | borra la cookie |
| `GET /libros/` | 200, 422 | paginado; filtros `titulo` (parte del título, parámetro ligado, sin distinguir mayúsculas) y `genero_id`; no muestra libros dados de baja |
| `GET /libros/{libro_id}` | 200, 404, 422 | editorial, género y autores con precarga |
| `GET /editoriales/` | 200, 422 | paginado |
| `GET /editoriales/{editorial_id}` | 200, 404, 422 | |
| `GET /editoriales/{editorial_id}/libros` | 200, 404, 422 | paginado |
| `GET /generos/` | 200, 422 | paginado |
| `GET /generos/{genero_id}/libros` | 200, 404, 422 | paginado |
| `GET /autores/` | 200, 422 | paginado |
| `GET /autores/{autor_id}` | 200, 404, 422 | |
| `GET /autores/{autor_id}/libros` | 200, 404, 422 | paginado, con el rol del autor en cada libro |

### Con sesión, sin rol

| Método y ruta | Códigos | Notas |
|---|---|---|
| `GET /auth/yo` | 200, 401 | usuario, roles vigentes (de la base) y roles del token (informativos); no pasa por el control del cambio obligatorio |
| `POST /auth/cambiar-password` | 200, 401, 422 | contraseña actual y nueva; no invalida sesiones; no pasa por el control del cambio obligatorio |
| `GET /mis-ventas` | 200, 401, 403 | paginado; las ventas del cliente asociado al usuario |
| `GET /ventas/{venta_id}` | 200, 401, 403, 404, 422 | cliente y renglones con precarga (número fijo de consultas); personal, o el cliente dueño de la venta (si no, 403) |

### Personal (VENDEDOR o ADMIN)

| Método y ruta | Códigos | Notas |
|---|---|---|
| `POST /clientes/` | 201, 409, 422 | 409 si el correo ya existe |
| `GET /clientes/` | 200, 422 | paginado |
| `GET /clientes/{cliente_id}` | 200, 404, 422 | incluye el perfil (o `null`) |
| `PATCH /clientes/{cliente_id}` | 200, 404, 409, 422 | sólo cambia lo enviado |
| `POST /clientes/{cliente_id}/perfil` | 201, 404, 409, 422 | 409 si ya tiene perfil |
| `GET /clientes/{cliente_id}/ventas` | 200, 404, 422 | paginado, con renglones |
| `POST /ventas/` | 201, 409, 422 | renglones dentro del cuerpo; ver abajo |
| `GET /ventas/` | 200, 422 | paginado |

### Sólo ADMIN

| Método y ruta | Códigos | Notas |
|---|---|---|
| `POST /editoriales/` | 201, 409, 422 | 409 si el nombre ya existe |
| `PATCH /editoriales/{editorial_id}` | 200, 404, 409, 422 | sólo cambia lo enviado |
| `POST /generos/` | 201, 409, 422 | 409 si el nombre ya existe |
| `POST /autores/` | 201, 422 | |
| `PATCH /autores/{autor_id}` | 200, 404, 422 | sólo cambia lo enviado |
| `POST /libros/` | 201, 409, 422 | autores dentro del cuerpo; `stock_inicial` deja un movimiento; 409 por ISBN repetido entre vigentes o editorial/autor/género inexistente |
| `PATCH /libros/{libro_id}` | 200, 404, 409, 422 | sólo cambia lo enviado; el stock no se edita por acá |
| `DELETE /libros/{libro_id}` | 204, 404, 422 | baja lógica (`borrado_en`): no aparece en el catálogo y no se vende ni repone, pero las ventas viejas lo siguen mostrando |
| `POST /libros/{libro_id}/reponer` | 200, 404, 409, 422 | suma stock con un movimiento; 409 si el libro está dado de baja |
| `GET /libros/{libro_id}/movimientos` | 200, 404, 422 | paginado; historial de stock del libro |
| `POST /usuarios/` | 201, 409, 422 | alta de personal con contraseña provisoria (queda con el cambio de contraseña pendiente); no asigna rol: se da después con `POST /usuarios/{usuario_id}/roles` |
| `GET /usuarios/{usuario_id}/roles` | 200, 404, 422 | |
| `POST /usuarios/{usuario_id}/roles` | 201, 404, 409, 422 | el vencimiento llega con zona horaria y en el futuro |
| `DELETE /usuarios/{usuario_id}/roles/{rol}` | 200, 404, 409, 422 | revoca (escribe `revocada_en`); 409 si es tu propio ADMIN o el último administrador |
| `GET /eventos/` | 200, 422 | paginado; historial de seguridad (`evento_seguridad`) |

No existen `PATCH`/`DELETE` de ventas ni el alta de renglones por separado.

**`POST /ventas/`** recibe `{"cliente_id": 2, "renglones": [{"libro_id": 1, "cantidad": 2}, ...]}`. Precio unitario, subtotal, total y fecha los calcula el servidor: enviarlos es un **422**. Al confirmarse la venta se copia el precio de cada libro, se descuenta su stock y se deja un movimiento por renglón, todo en una sola transacción: si un libro o el cliente no existen, el libro está dado de baja o el stock no alcanza, responde **409** y no queda ninguna escritura. Tras el alta se agenda una `BackgroundTask` que simula el envío del comprobante y lo deja en el log (`uvicorn.error`) unos 0,5 s después de responder, sólo si la venta se confirmó.

## Estructura

```
app/
├── main.py            # app, lifespan y los dos grupos de rutas (abierto / protegido)
├── models.py          # registro central de modelos (para Alembic)
├── core/              # config, database, security, dependencies, repository, unit_of_work, paginacion, errors, base, tipos
└── modules/<módulo>/  # models.py, schemas.py, repository.py, unit_of_work.py, service.py, router.py
migrations/            # Alembic (async)
seed.py                # carga inicial (raíz)
scripts/armar_zip.py   # arma el zip de la entrega
test/                  # casos C-01 a C-16 (.http), solo_agregado.sql (C-14) e invariante_stock.sql
tests/                 # pytest
evidencia/             # salida de psql (C-14) y consola (C-15)
```
Módulos: `health`, `usuarios`, `editoriales`, `generos`, `autores`, `libros`, `clientes`, `ventas`.
Flujo de capas: Router → Service → UoW → Repository → Model. Convenciones, reglas y nombres de constraints: [AGENTS.md](AGENTS.md).

## Armado de la entrega

El zip `Parcial_Cap1a6_GordosProgramacion.zip` tiene dos carpetas: `parcial/` (esta) y `despliegue/` (la carpeta hermana `Despliegue`, el TP 1–4 con su despliegue en el VPS). Se arma desde esta carpeta, igual en PowerShell que en Git Bash:
```bash
python scripts/armar_zip.py
```
Queda en `dist/` (ignorada por git) y el comando informa la ruta y cuántos archivos tiene cada carpeta. Sólo entran los archivos que git versiona o que no ignora, sin `.venv`, `__pycache__`, cachés, `.claude/` ni `CLAUDE.local.md`; si git lista un `.env` o una variante (`.env.local`...), versionada o sin ignorar, el armado se detiene con un error. Requiere `git` en el PATH.
