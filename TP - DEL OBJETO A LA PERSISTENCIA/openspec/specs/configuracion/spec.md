# configuracion Specification

## Purpose
Define de dónde lee la aplicación su configuración (variables de entorno y un archivo `.env` no versionado), cómo arma la dirección de la base, qué secretos son obligatorios y qué parámetros operativos se ajustan sin tocar el código.

## Requirements

### Requirement: Origen de la configuración
La aplicación SHALL leer su configuración de las variables de entorno y, si existe, de un archivo `.env` en el directorio desde el que se lanza. Una variable de entorno MUST tener prioridad sobre el mismo nombre en `.env`. Las variables que la configuración no declara MUST ignorarse sin error, estén en el entorno o en `.env`.

#### Scenario: El entorno pisa al archivo .env
- **WHEN** `.env` define `POSTGRES_DB=libreria` y el entorno define `POSTGRES_DB=libreria_test`
- **THEN** la configuración usa `libreria_test`

#### Scenario: Variables viejas o ajenas en .env no impiden arrancar
- **WHEN** `.env` contiene, además de las variables requeridas, `DATABASE_URL`, `DB_ECHO` o `REQUIRE_TEST_DB`
- **THEN** la configuración se construye sin error y esas variables no influyen en ella

### Requirement: Dirección de la base armada desde las variables sueltas
La dirección de conexión SHALL derivarse de las cinco variables `POSTGRES_*` con el driver `postgresql+asyncpg`, y MUST armarse con `sqlalchemy.engine.URL.create(...).render_as_string(hide_password=False)`, nunca concatenando texto. `POSTGRES_HOST` MUST valer `localhost` y `POSTGRES_PORT` MUST valer `5432` si no se definen. Los caracteres especiales del usuario o la contraseña MUST quedar escapados.

#### Scenario: URL armada con todas las variables
- **WHEN** se definen `POSTGRES_USER=u`, `POSTGRES_PASSWORD=p`, `POSTGRES_DB=db`, `POSTGRES_HOST=db.local` y `POSTGRES_PORT=5433`
- **THEN** la dirección de la base es `postgresql+asyncpg://u:p@db.local:5433/db`

#### Scenario: Host y puerto por defecto
- **WHEN** no se definen `POSTGRES_HOST` ni `POSTGRES_PORT`
- **THEN** la dirección de la base apunta a `localhost:5432`

#### Scenario: Contraseña con caracteres reservados
- **WHEN** `POSTGRES_PASSWORD` contiene a la vez `@`, `/` y `%` (p. ej. `p@ss/w%rd`)
- **THEN** la dirección de la base, interpretada de nuevo, devuelve exactamente esa contraseña, ese host y esa base

### Requirement: Alembic recibe la dirección escapada para ConfigParser
`migrations/env.py` SHALL tomar la dirección de la base de la configuración y MUST duplicar cada `%` antes de pasarla a la configuración de Alembic, porque ConfigParser interpreta `%` como interpolación.

#### Scenario: Alembic recibe la dirección con % duplicado
- **WHEN** `migrations/env.py` pasa la dirección de la base a la configuración de Alembic
- **THEN** cada `%` de la dirección escapada se duplica a `%%` antes de entregarla

### Requirement: Secretos obligatorios sin valor por defecto
`POSTGRES_PASSWORD` y la clave de firma de los tokens (`JWT_SECRET`) MUST NOT tener valor por defecto en el código. Si alguna falta o está vacía, la configuración MUST fallar y la aplicación MUST NOT arrancar. `JWT_SECRET` MUST tener al menos 32 caracteres. `POSTGRES_USER` y `POSTGRES_DB` también son obligatorias; `POSTGRES_HOST` y `POSTGRES_PORT` no.

#### Scenario: Falta la clave de firma
- **WHEN** se construye la configuración sin `JWT_SECRET` en el entorno ni en `.env`
- **THEN** falla con un error que nombra `JWT_SECRET`

#### Scenario: Falta la contraseña de la base
- **WHEN** se construye la configuración sin `POSTGRES_PASSWORD`
- **THEN** falla con un error que nombra `POSTGRES_PASSWORD`

#### Scenario: Secreto vacío
- **WHEN** `.env` contiene la línea `JWT_SECRET=` o `POSTGRES_PASSWORD=` sin valor
- **THEN** la configuración falla igual que si la variable faltara

#### Scenario: Clave de firma demasiado corta
- **WHEN** `JWT_SECRET` tiene menos de 32 caracteres
- **THEN** la configuración falla con un error que nombra `JWT_SECRET`

#### Scenario: Faltan el usuario o la base
- **WHEN** se construye la configuración sin `POSTGRES_USER` o sin `POSTGRES_DB`
- **THEN** la configuración falla con un error que nombra la variable que falta

### Requirement: Los secretos no se filtran
El error que produce una configuración inválida SHALL estar en español, nombrar las variables con problema y MUST NOT incluir el valor de ninguna variable. La representación de texto de la configuración MUST NOT mostrar `POSTGRES_PASSWORD` ni `JWT_SECRET`.

#### Scenario: Error sin la contraseña presente
- **WHEN** `POSTGRES_PASSWORD=secreto-de-prueba` está definida y falta `JWT_SECRET`
- **THEN** el mensaje de error nombra `JWT_SECRET` y no contiene `secreto-de-prueba`

#### Scenario: repr de la configuración
- **WHEN** se convierte a texto una configuración válida
- **THEN** el texto no contiene el valor de `POSTGRES_PASSWORD` ni el de `JWT_SECRET`

### Requirement: Parámetros de autenticación configurables
Costo de bcrypt (`BCRYPT_COST`, 4–31, por defecto 12), máximo de llamadas a bcrypt simultáneas (`BCRYPT_MAX_CONCURRENTES` ≥ 1, por defecto 4), `COOKIE_SECURE` (por defecto falso) y duración del token en minutos (`JWT_EXPIRE_MINUTES` ≥ 1, por defecto 60) SHALL salir de la configuración. Un valor fuera de rango MUST hacer fallar la configuración con un error que nombra la variable. El algoritmo de firma del token MUST NOT formar parte de la configuración.

#### Scenario: Valores por defecto de autenticación
- **WHEN** sólo se definen las variables obligatorias
- **THEN** el costo de bcrypt es 12, el máximo de bcrypt simultáneos es 4, la cookie no es `Secure` y el token dura 60 minutos

#### Scenario: Valores de autenticación tomados del entorno
- **WHEN** se definen `BCRYPT_COST=4`, `BCRYPT_MAX_CONCURRENTES=2`, `COOKIE_SECURE=true` y `JWT_EXPIRE_MINUTES=15`
- **THEN** la configuración refleja exactamente esos valores

#### Scenario: Costo de bcrypt fuera de rango
- **WHEN** `BCRYPT_COST=3` o `BCRYPT_COST=32`
- **THEN** la configuración falla con un error que nombra `BCRYPT_COST`

#### Scenario: Mínimos de autenticación
- **WHEN** `BCRYPT_MAX_CONCURRENTES=0` o `JWT_EXPIRE_MINUTES=0`
- **THEN** la configuración falla con un error que nombra esa variable

### Requirement: Parámetros de base configurables
Tamaño del pool (`DB_POOL_SIZE` ≥ 1, por defecto 5), desborde (`DB_MAX_OVERFLOW` ≥ 0, por defecto 10) y eco de SQL (`SQL_ECHO`, por defecto falso) SHALL salir de la configuración. Un valor fuera de rango MUST hacer fallar la configuración con un error que nombra la variable.

#### Scenario: Valores por defecto de la base
- **WHEN** sólo se definen las variables obligatorias
- **THEN** el pool es 5 con 10 de desborde y el eco de SQL está apagado

#### Scenario: Valores de la base tomados del entorno
- **WHEN** se definen `DB_POOL_SIZE=2`, `DB_MAX_OVERFLOW=1` y `SQL_ECHO=true`
- **THEN** la configuración refleja exactamente esos valores

#### Scenario: Mínimos de la base
- **WHEN** `DB_POOL_SIZE=0` o `DB_MAX_OVERFLOW=-1`
- **THEN** la configuración falla con un error que nombra esa variable

#### Scenario: Booleanos aceptados
- **WHEN** `SQL_ECHO` vale `true`, `1` o `yes` (sin distinguir mayúsculas)
- **THEN** el eco de SQL queda encendido; con `false`, `0` o `no` queda apagado

### Requirement: La configuración se lee al usarla, no al importar
Importar los módulos de la aplicación MUST NOT leer ni validar la configuración. La configuración SHALL construirse sólo cuando el arranque de la aplicación, una migración o un script la piden.

#### Scenario: Importar la app sin variables definidas
- **WHEN** se importa la aplicación en un entorno sin ninguna variable de configuración y sin `.env`
- **THEN** la importación termina sin error
