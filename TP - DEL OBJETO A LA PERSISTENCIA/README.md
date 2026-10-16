# Librería — API con FastAPI + PostgreSQL

TP "Del objeto a la persistencia" (Programación III). API para una librería: catálogo (editoriales, géneros, autores, libros), clientes y ventas.
Stack: Python 3.12+, FastAPI, SQLModel/SQLAlchemy async, asyncpg, PostgreSQL 16 (Docker) y Alembic.

> Las convenciones del proyecto están en [AGENTS.md](AGENTS.md); el reparto de tareas, en [REPARTO.md](REPARTO.md).

## Puesta en marcha desde cero

### 1. Requisitos
- Python 3.12 o superior
- Docker y Docker Compose
- Git

### 2. Clonar el repositorio
```bash
git clone https://github.com/MatiasLimina/Prog3_GordosProgramacion.git
cd Prog3_GordosProgramacion/"TP - DEL OBJETO A LA PERSISTENCIA"
```

### 3. Entorno virtual
Windows (Git Bash):
```bash
python -m venv .venv
source .venv/Scripts/activate
```
Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
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
```bash
cp env.example .env
```
Editá `.env` y reemplazá los valores de ejemplo por los tuyos (usuario, clave y base de PostgreSQL; `DATABASE_URL` tiene que usar los mismos). El archivo `.env` **no se commitea**.

Si el puerto 5432 ya está ocupado (por ejemplo, por un PostgreSQL instalado en Windows), agregá `POSTGRES_PORT=5433` en `.env` y usá `5433` en `DATABASE_URL`.

### 6. Base de datos
```bash
docker compose up -d
```
Levanta PostgreSQL 16 con las credenciales de `.env`. Podés ver el estado con `docker compose ps` (debe figurar `healthy`).

### 7. Esquema (migraciones)
```bash
alembic upgrade head
```

El esquema se crea sólo con Alembic; la app nunca usa `create_all`.

### 8. Datos iniciales
```bash
python -m scripts.seed
```
Deja la base en un estado inicial conocido (vacía las tablas y carga editoriales, géneros, autores, libros, 2 clientes —el 2 es Tomás Ríos—, un perfil y una venta, con ids fijos). Se puede correr las veces que haga falta.

### 9. Servidor
```bash
uvicorn app.main:app --reload
```
Probar:
- http://localhost:8000/health/live → `{"estado": "vivo"}`
- http://localhost:8000/health/ready → verifica la conexión con la base
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
   Los tests con base real usan `libreria_test` (se deriva de `DATABASE_URL`; el conftest recrea el esquema en cada corrida, nunca toca la base de desarrollo). Si la base no responde, esos tests se **saltean** con un aviso. Con `REQUIRE_TEST_DB=1 pytest` la falta de base es un **fallo**: usarlo antes de entregar para no confiar en skips.

Los casos de prueba HTTP (C-01 a C-08) están en la carpeta `test/` y se ejecutan con la extensión **REST Client** de VS Code; cada caso indica en un comentario el resultado esperado.

## Endpoints de clientes y ventas

| Método y ruta | Códigos | Notas |
|---|---|---|
| `POST /clientes/` | 201, 409, 422 | 409 si el email ya existe (C-02) |
| `GET /clientes/` | 200, 422 | paginado (`limit` 1–100, `offset` ≥ 0) |
| `GET /clientes/{id}` | 200, 404 | incluye el perfil (o `null`) |
| `PATCH /clientes/{id}` | 200, 404, 409, 422 | sólo cambia lo enviado |
| `POST /clientes/{id}/perfil` | 201, 404, 409 | 409 si ya tiene perfil (C-03); 404 si el cliente no existe |
| `GET /clientes/{id}/ventas` | 200, 404 | paginado, con renglones |
| `POST /ventas/` | 201, 409, 422 | renglones dentro del cuerpo; ver abajo |
| `GET /ventas/` | 200, 422 | paginado |
| `GET /ventas/{id}` | 200, 404 | cliente y renglones con precarga (C-07) |

No existen `PATCH`/`DELETE` de ventas ni el alta de renglones por separado.

**`POST /ventas/`** recibe `{"cliente_id": 2, "renglones": [{"libro_id": 1, "cantidad": 2}, ...]}`. Precio unitario, subtotal, total y fecha los calcula el servidor (RN-06, RN-07): enviarlos es un **422**. Al confirmarse la venta se **descuenta el stock** de cada libro en una sola transacción: si un libro o el cliente no existen, o el stock no alcanza (C-05), responde **409** y no queda ningún descuento. Tras el alta se agenda una `BackgroundTask` que simula el envío del comprobante y lo deja en el log (`uvicorn.error`) unos 0,5 s después de responder.

## Diagnóstico de consultas (C-07)

Con `DB_ECHO=true` en `.env` (y reiniciando el servidor) la consola muestra cada consulta SQL emitida. Sirve para comprobar que el detalle de un libro y de una venta emiten la misma cantidad de consultas con 1 o con N autores/renglones.

Evidencia: [docs/evidencia_c07.md](docs/evidencia_c07.md) — sentencias SQL y cantidad de consultas del detalle de libro y de venta con 1 y con N autores/renglones (2 consultas en todos los casos).

## Estructura

```
app/
├── main.py            # app, lifespan y routers
├── models.py          # registro central de modelos (para Alembic)
├── core/              # config, database, pagination, errors, tipos
└── modules/<módulo>/  # models.py, schemas.py, service.py, router.py
migrations/            # Alembic (async)
scripts/seed.py        # carga inicial
test/*.http            # casos de prueba C-01 a C-08
tests/                 # pytest
```
Módulos: `health`, `editoriales`, `generos`, `autores`, `libros`, `clientes`, `ventas`.
Convenciones, reglas y nombres de constraints: [AGENTS.md](AGENTS.md).

## Estado actual
- Hecho: infraestructura, `health`, `editoriales`, `generos`, `autores`, `libros`, `clientes`, `ventas`, migraciones, seed.
- Evidencia C-07: [docs/evidencia_c07.md](docs/evidencia_c07.md).
