# Design

## Context

Motivación: ver `proposal.md` («Why»). Requisitos: specs `hash-de-contrasenas`, `token-de-acceso` y el delta de `ciclo-de-vida`.

Estado actual que condiciona el diseño:

- `app/core/security.py` sólo tiene `calcular_hash_ficticio(costo) -> str` (síncrona, `bcrypt.hashpw` con `gensalt(rounds=costo)`); su firma y sus 4 tests no cambian.
- `Settings` ya tiene `jwt_secret: SecretStr` (mínimo 32 caracteres, o sea al menos 256 bits: PyJWT no emite `InsecureKeyLengthWarning` con HS256), `jwt_expire_minutes` (≥ 1), `bcrypt_cost` (4–31) y `bcrypt_max_concurrentes` (≥ 1). El comentario de `config.py` ya fija que el algoritmo no es configuración.
- El lifespan arma `settings`, `engine`, `sessionmaker` y `hash_ficticio` en `app.state`; el hash ficticio se calcula con `asyncio.to_thread` y sin semáforo (en el arranque no hay concurrencia).
- `requirements.txt` pide `bcrypt>=4.0` y `PyJWT>=2.8`. bcrypt 4 trunca en silencio una contraseña de más de 72 bytes; bcrypt 5 lanza `ValueError`. PyJWT ≥ 2.10 exige que `sub` sea texto.
- Gobernanza: dominio CRITICAL (seguridad). Ningún código se escribe hasta que el usuario apruebe este diseño (tarea 1.1).

## Goals / Non-Goals

**Goals:**
- Una API chica y pura en `app/core/security.py` que CHG-11, CHG-12, CHG-14 y CHG-17 usen sin conocer bcrypt ni PyJWT.
- Que ningún caller pueda saltearse el hilo aparte ni el semáforo: no hay una variante pública síncrona de hash o verificación.
- Tests deterministas (sin `sleep` para el vencimiento, sin base de datos, sin marca `db`).

**Non-Goals:**
- Cookie, endpoints, `get_usuario_actual`, `requiere_rol`, `intento_acceso`, límite de intentos (CHG-11/12).
- Elegir entre hash real y ficticio, y medir que el tiempo sea parejo (RN-08 es de CHG-11; acá sólo se garantiza que los dos caminos pasan por la misma función).
- Revocación de tokens, refresh tokens, `iat`/`jti`, rotación de la clave.
- Validadores de 72 bytes de los contratos (CHG-09a): la guarda de acá es defensiva, no reemplaza al 422.

## Decisions

### API resultante (referencia para CHG-11/12/17)

```python
ALGORITMO_JWT = "HS256"            # constante, no configuración
LIMITE_BYTES_BCRYPT = 72

class TokenInvalido(Exception): ...
class TokenVencido(TokenInvalido): ...

@dataclass(frozen=True)
class DatosToken:
    usuario_id: int
    roles: list[str]
    vence_en: datetime              # con tzinfo=UTC

async def hashear_password(password: str, *, costo: int, semaforo: asyncio.Semaphore) -> str
async def verificar_password(password: str, password_hash: str, *, semaforo: asyncio.Semaphore) -> bool
def emitir_token(usuario_id: int, roles: Iterable[str], *, secreto: SecretStr, minutos: int,
                 ahora: datetime | None = None) -> str
def verificar_token(token: str, *, secreto: SecretStr) -> DatosToken
def calcular_hash_ficticio(costo: int) -> str   # sin cambios
```

Los nombres son la propuesta; los fija la aprobación de la tarea 1.1.

### D1 · Cómo llegan el semáforo y el costo: parámetros explícitos (elegida)

Las funciones reciben `costo`, `semaforo`, `secreto` y `minutos` como argumentos con nombre obligatorio. El lifespan crea el semáforo y lo guarda en `app.state.semaforo_bcrypt`; el caller (en CHG-11, una dependencia o el router) lo toma de ahí junto con `settings` y se lo pasa al servicio.

- Por qué: es el mismo estilo que `calcular_hash_ficticio(costo)`; el módulo no tiene estado global ni conoce FastAPI; los tests pasan un `asyncio.Semaphore(n)` propio; el seed (CHG-17) crea su `asyncio.Semaphore(1)` y usa `settings.bcrypt_cost` sin arrancar la app. Pasar `SecretStr` (no `str`) mantiene la clave envuelta hasta la línea que firma.
- Alternativa B · objeto creado en el lifespan (p. ej. `Hasheador(costo, semaforo)` en `app.state`): ata costo y semáforo una sola vez y simplifica a los callers, pero agrega una clase y un objeto más en el estado, y el seed tendría que construirlo igual. Es una mejora posible si en CHG-11 los callers repiten demasiado; no cambia las specs.
- Alternativa C · leer `app.state` desde `security.py`: acopla el núcleo a FastAPI y a una app arrancada, y rompe el seed y los tests unitarios. Descartada.

### D2 · Errores de verificación del token: dos excepciones propias, una subclase de la otra (elegida)

`verificar_token` traduce las excepciones de PyJWT: `jwt.ExpiredSignatureError` → `TokenVencido`; cualquier otro `jwt.InvalidTokenError` (firma, formato, algoritmo, claim faltante) y los chequeos de forma propios → `TokenInvalido`. Siempre `raise ... from None` y con un mensaje fijo en español, sin el token ni la clave.

- Por qué: CHG-12 atrapa sólo `TokenInvalido` (cubre las dos) y responde 401; si quiere distinguir (un mensaje «la sesión venció»), atrapa antes `TokenVencido`. No depende de PyJWT. `from None` deja `__cause__` en `None` y suprime el contexto, así el traceback no muestra el error interno de PyJWT.
- Orden seguro: PyJWT verifica la firma antes que `exp`, así que un token alterado y vencido da `TokenInvalido`: nunca se confía en un `exp` sin firma válida.
- Alternativa B · dejar pasar las excepciones de PyJWT: acopla CHG-12 a la librería y expone sus mensajes. Descartada.
- Alternativa C · devolver `None` si no verifica: pierde la diferencia entre vencido e inválido y es fácil olvidarse de chequearlo. Descartada.
- Alternativa D · una sola excepción con un campo `motivo`: equivalente pero obliga a inspeccionar el campo; la jerarquía es más idiomática.

Chequeos de verificación: `algorithms=["HS256"]` (rechaza `none`, HS512 y confusión de algoritmo), `options={"require": ["exp", "sub", "roles"]}`, `sub` que coincide con `[1-9][0-9]*` (se convierte a `int`), `roles` lista de `str`. Cualquier otra forma → `TokenInvalido`.

### D3 · Hash ficticio: `security.py` sólo ofrece la verificación genérica (elegida)

`verificar_password(password, password_hash, ...)` sirve para cualquier hash; CHG-11 hace `usuario.password_hash if usuario else app.state.hash_ficticio` y llama a la misma función. Así los dos caminos pasan por el mismo semáforo y el mismo hilo, que es lo que hace parejo el tiempo (RN-08).

- Alternativa B · `verificar_o_ficticio(password, hash_o_none, hash_ficticio, ...)` en `security.py`: centraliza RN-08 pero mezcla una regla del login con el núcleo y agrega una función que sólo usa un caller. Queda como refactor posible en CHG-11 si el servicio lo pide.

### D4 · Reloj y vencimiento: UTC con zona, sin margen (elegida)

`exp = ahora + timedelta(minutes=minutos)` con `ahora = datetime.now(timezone.utc)` por defecto. `emitir_token` acepta `ahora` (sólo con zona; uno sin zona → `ValueError`) para que los tests sean deterministas: el token vencido se emite con `ahora` 2 horas atrás, sin `sleep`. `verificar_token` usa el reloj real de PyJWT con `leeway=0`: la misma app emite y verifica con el mismo reloj, así que no hay desfase que tolerar. `DatosToken.vence_en` es `datetime` con `tzinfo=UTC` (lo usará CHG-11 si quiere mostrarlo; el `Max-Age` de la cookie sale de `jwt_expire_minutes`).

- Alternativa B · `leeway` de unos segundos: útil con varios servidores con relojes distintos; no es el caso. Se puede agregar sin cambiar la API.
- Alternativa C · inyectar un reloj también en la verificación: PyJWT no lo admite sin desactivar `verify_exp` y chequearlo a mano, lo que duplica lógica sensible. Descartada.

### D5 · Límite de 72 bytes: guarda defensiva en `security.py` (elegida)

`len(password.encode("utf-8")) > 72`:
- `hashear_password` lanza `ValueError("La contraseña supera los 72 bytes que admite bcrypt.")` antes de tomar el semáforo. Nunca se guarda un hash que bcrypt 4 habría truncado o que bcrypt 5 rechazaría.
- `verificar_password` devuelve `False` sin llamar a bcrypt. Como ninguna contraseña guardada pasa de 72 bytes, ninguna de 73 puede coincidir; con bcrypt 4 sin esta guarda, una de 73 bytes cuyos primeros 72 coinciden daría verdadero. El atajo no filtra nada sobre el correo: depende sólo del largo de lo que mandó el cliente.

El contrato (CHG-09a) sigue respondiendo 422 antes: esta guarda no debería dispararse en una petición. Si se dispara en `hashear_password`, revela un contrato sin validador (un test de CHG-11 lo detecta como 500).

- Alternativa B · confiar sólo en el contrato: el comportamiento cambiaría según la versión de bcrypt instalada. Descartada.
- Alternativa C · `ValueError` también en la verificación: convertiría un login con contraseña larga en 500 si el contrato fallara; `False` es el resultado correcto y seguro.

### D6 · bcrypt bajo el semáforo y en un hilo; JWT síncrono

Patrón: `async with semaforo: return await asyncio.to_thread(bcrypt.hashpw, ...)` (ídem `checkpw`). El semáforo acota cuántos hilos del ejecutor por defecto ocupa bcrypt (cada llamada tarda ~300 ms con costo 12), así otras llamadas a `to_thread` no se quedan sin hilos. Firmar y verificar el JWT (HMAC, microsegundos) no bloquea: son funciones síncronas comunes.

### D7 · Semáforo en el lifespan

`app.state.semaforo_bcrypt = asyncio.Semaphore(settings.bcrypt_max_concurrentes)`, creado después de `get_settings()` (si la configuración falla no se crea nada) y antes del `yield`. Se crea dentro del bucle que corre la app; cada arranque crea el suyo, así los tests con un bucle por test no comparten un semáforo atado a otro bucle. No necesita liberarse al apagar.

### D8 · Roles en el token

Se guardan como lista de textos en el orden recibido (`[str(r) for r in roles]`; si CHG-06 define los roles como `StrEnum`, `str()` da su valor). Son informativos (RN-04): CHG-12 consulta los vigentes en la base.

## Risks / Trade-offs

- [El seed o un script usa un semáforo creado en otro bucle de eventos → `RuntimeError` de asyncio] → D1: quien no corre dentro de la app crea su propio semáforo en su bucle; documentado en el docstring del módulo.
- [Un caller olvida pasar el semáforo de la app y crea uno nuevo por petición → concurrencia sin límite] → `semaforo` es obligatorio y sin valor por defecto; CHG-11 lo toma de `app.state` en un solo lugar (una dependencia).
- [El hash ficticio usa un costo distinto del real → el tiempo delata el correo] → ya cubierto por la spec de `ciclo-de-vida` (mismo `BCRYPT_COST`); este change no lo toca.
- [La clave aparece en un traceback o en un log] → la clave viaja como `SecretStr` y se abre sólo en la llamada a PyJWT; `from None` en toda traducción; el módulo no usa `logging`; un test verifica mensaje, `__cause__`, `__suppress_context__` y `caplog`.
- [PyJWT < 2.10 instalado no exige `sub` texto] → el chequeo propio de `sub` (D2) no depende de la versión.
- [Tests de concurrencia frágiles por tiempos] → el doble de bcrypt duerme 50 ms en el hilo y mide el máximo de llamadas simultáneas con un contador protegido por `threading.Lock`; la aserción es «nunca más de N» (y «alguna vez N» con N = 2), no una duración.
- [Trade-off D1] → los callers repiten `costo=settings.bcrypt_cost, semaforo=app.state.semaforo_bcrypt`; si en CHG-11 molesta, se envuelve en una dependencia sin tocar este módulo.

## Migration Plan

Sin migraciones ni variables nuevas. Se mergea antes de CHG-11 y CHG-17. Rollback: revertir el commit; nada más depende de estas funciones hasta CHG-11.

## Open Questions

- Tipo de los roles que define CHG-06 (`StrEnum` o texto): no cambia la API (D8 acepta ambos); se confirma al integrar CHG-11.
- Si CHG-11 envuelve `costo` + `semaforo` en una dependencia o en un objeto (Alternativa B de D1): se decide en CHG-11 sin tocar este módulo.
