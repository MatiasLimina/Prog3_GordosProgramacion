# Kiosco Catálogo y Pedidos API

API REST desarrollada en FastAPI que simula la gestión de un kiosco, su catálogo de productos y un sistema de pedidos.

Cumple con estándares de asincronía y concurrencia (PEP 8, Type hints, Pydantic, etc.).

## Instalación y Configuración

El proyecto requiere Python 3.10 o superior (se recomienda 3.11+ para aprovechar plenamente `asyncio.TaskGroup`).

1. **Entorno Virtual:**

   ```bash
   python -m venv venv
   # Activar en Windows
   venv\Scripts\activate
   # Activar en macOS/Linux
   source venv/bin/activate
   ```
2. **Instalación de dependencias:**

   ```bash
   pip install fastapi uvicorn pydantic
   ```

## Ejecución

Inicie el servidor de desarrollo en la raíz del proyecto ejecutando:

```bash
uvicorn main:app --reload
```

## Exploración

Puede acceder a la documentación interactiva en:

* [Swagger UI](http://127.0.0.1:8000/docs)
* [ReDoc](http://127.0.0.1:8000/redoc)

## Características principales demostradas

- **Concurrencia vs Secuencialidad:** Compare el tiempo de respuesta realizando un `GET /pedidos/demo/secuencial` y un `GET /pedidos/demo/concurrente`.
- **Tareas en segundo plano:** `POST /pedidos` imprime en la consola del servidor un mensaje simulando el envío asíncrono de un correo de confirmación.
- **Protección contra condiciones de carrera:** Resta segura del inventario mediante bloqueos en memoria.
- **Validaciones Avanzadas:** `PATCH /productos/{id}` admite actualizaciones parciales (incluyendo distinción de `null`), y validación cruzada entre propiedades `stock` y `reserved_stock`.
