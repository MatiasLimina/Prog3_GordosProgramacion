# DEPLOY — Librería (TP Cap 1–4) en el VPS

## URL pública

**http://matiaslimina.me:8000**

- Salud: http://matiaslimina.me:8000/health/ready
- Catálogo: http://matiaslimina.me:8000/libros/
- Documentación interactiva: http://matiaslimina.me:8000/docs

## Fecha y hora del despliegue

8 de noviembre de 2026, 19:35 UTC (16:35 hora de Argentina).

## Cómo está armado

- **Imagen:** se construye **en el servidor** a partir de este repositorio, clonado en `/opt/prog3`.
- **Base de datos:** PostgreSQL 17, que corre en el mismo VPS como servicio de Easypanel (`gordos_programacion_db`).
  La aplicación tiene su propia base (`libreria`) y su propio usuario (`libreria`), separados de los de otros proyectos
  que comparten ese servidor de PostgreSQL.
- **Configuración:** el archivo `/opt/libreria.env` vive en el servidor, fuera del repositorio y de la imagen, con permisos
  `600` (sólo root). Contiene `DATABASE_URL` (driver `postgresql+asyncpg`), `DB_ECHO=false` y `SQL_ECHO=false`.
  Su contenido no se publica.
- **Puerto:** `8000` en el host. Los puertos 80 y 443 los usa el proxy de Easypanel (Traefik). Se abrió con `ufw allow 8000/tcp`.

## Comandos

Construcción (en el VPS):

```bash
git clone https://github.com/MatiasLimina/Prog3_GordosProgramacion.git /opt/prog3
cd /opt/prog3/Despliegue
docker build -t libreria .
```

Ejecución:

```bash
docker run -d --name libreria -p 8000:8000 --restart unless-stopped \
  --env-file /opt/libreria.env \
  --network easypanel-gordos_programacion \
  libreria
```

Carga de datos iniciales (comando del README del TP):

```bash
docker exec libreria python -m scripts.seed
```

## Cambios respecto del TP

**No se modificó el código del TP.** La única diferencia con el comando de la consigna está en cómo el contenedor llega a la base:

- La consigna usa `--add-host=host.docker.internal:host-gateway` para una base que corre **directamente en el servidor**.
- Acá la base corre dentro de Easypanel, en su red interna (`easypanel-gordos_programacion`, una red *overlay* de Docker Swarm
  creada como `attachable`). El contenedor se une a esa red con `--network` y llega a la base por el nombre del servicio,
  `gordos_programacion_db:5432`. Así PostgreSQL no queda expuesto a internet: sólo se publica el puerto de la aplicación.
  La consigna lo admite: «si la cátedra entrega otra dirección, se usa esa».

## Cómo se actualiza la aplicación

```bash
cd /opt/prog3 && git pull                 # trae el código nuevo de main
cd Despliegue && docker build -t libreria .   # se construye antes de borrar: la app sigue arriba mientras tanto
docker rm -f libreria
docker run -d --name libreria -p 8000:8000 --restart unless-stopped \
  --env-file /opt/libreria.env \
  --network easypanel-gordos_programacion \
  libreria
```

Los datos no se pierden porque viven en la base del servidor (`gordos_programacion_db`), no en el contenedor.
Si el código trae migraciones nuevas, se aplican solas al arrancar (`alembic upgrade head` en el `CMD`); si no, Alembic no repite nada.
**No hay que volver a correr el seed:** vacía todas las tablas (`TRUNCATE ... RESTART IDENTITY`) y borraría las ventas registradas.

## Evidencia

Salidas de los casos D-01 a D-08 en [`evidencia/`](evidencia/):

| Caso | Archivo | Resultado |
|---|---|---|
| D-01 | `D-01_imagenes.txt` | `python:3.12-alpine` 74,8 MB (18,7 MB de contenido); `libreria` 257 MB (59,3 MB) |
| D-02 | `D-02_build_run_ps.txt` | `healthy`; las dos migraciones aplicadas al arrancar |
| D-03 | `D-03_url_publica.txt` | `ready` 200; `/libros/` 200 con el seed; `POST /ventas/` 201, total 77000.00 |
| D-04 | `D-04_persistencia.txt` | `healthy` otra vez; datos presentes; ningún `Running upgrade` |
| D-05 | `D-05_sin_database_url.txt` | termina con `exit=1`: «Falta la variable de entorno DATABASE_URL» |
| D-06 | `D-06_contenido_imagen.txt` | sin `.env` en `/app`; `env` sin `DATABASE_URL` ni contraseñas |
| D-07 | `D-07_usuario_proceso.txt` | `uid=100(app)` |
| D-08 | `D-08_aviso_comprobante.txt` | «Comprobante de la venta 2 enviado…» después de `POST /ventas/ 201` |

**El despliegue sigue en línea hasta que se publiquen las notas.**
