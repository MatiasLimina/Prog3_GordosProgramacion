"""Seguridad de la app: hash y verificación de contraseñas con bcrypt, y token de acceso.

CHG-10 es el núcleo: CHG-11 (login), CHG-12 (autorización), CHG-14 (alta de personal) y
CHG-17 (seed) usan estas funciones sin conocer bcrypt. El módulo no tiene estado global
ni conoce FastAPI: quien llama pasa `costo` y `semaforo` (el de la app vive en
`app.state.semaforo_bcrypt`, creado por el lifespan). Un script fuera de la app, como el
seed, crea su propio `asyncio.Semaphore` dentro de su bucle de eventos.
"""
import asyncio
import math
import re
import secrets
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from pydantic import SecretStr

ALGORITMO_JWT = "HS256"  # constante, no configuración
LIMITE_BYTES_BCRYPT = 72
_MENSAJE_PASSWORD_LARGA = "La contraseña supera los 72 bytes que admite bcrypt."
# Mensajes fijos: nunca incluyen el token ni la clave (el módulo no escribe en el log).
_MENSAJE_TOKEN_INVALIDO = "El token no es válido."
_MENSAJE_TOKEN_VENCIDO = "El token venció."
_ID_USUARIO = re.compile(r"[1-9][0-9]*")  # entero positivo, sin ceros a la izquierda


class TokenInvalido(Exception):
    """El token no se puede aceptar: firma, formato, algoritmo o datos incorrectos.

    CHG-12 atrapa sólo esta clase (cubre también `TokenVencido`) y responde 401.
    """


class TokenVencido(TokenInvalido):
    """El token estaba bien firmado pero su `exp` ya pasó (sin margen de tolerancia).

    Permite distinguir «la sesión venció» de un token inválido; sigue siendo un `TokenInvalido`.
    """


@dataclass(frozen=True)
class DatosToken:
    """Lo que lleva un token verificado.

    Los roles son informativos (RN-04): los vigentes se leen de la base en cada petición.
    """

    usuario_id: int
    roles: list[str]
    vence_en: datetime  # con zona horaria UTC


def _supera_limite_bcrypt(password: str) -> bool:
    # Se cuentan bytes, no caracteres: una «ñ» ocupa 2.
    return len(password.encode()) > LIMITE_BYTES_BCRYPT


async def hashear_password(password: str, *, costo: int, semaforo: asyncio.Semaphore) -> str:
    """Hash bcrypt de `password` con sal aleatoria y el costo recibido (`BCRYPT_COST`).

    Es asíncrona y no tiene versión síncrona a propósito: bcrypt bloquea ~300 ms con
    costo 12, así que corre en un hilo (`asyncio.to_thread`) y bajo `semaforo`
    (`BCRYPT_MAX_CONCURRENTES`), para que ningún caller se saltee ninguna de las dos
    cosas. Llamarla ANTES de abrir la transacción: no hay que tener una conexión tomada
    mientras se calcula el hash.

    Lanza `ValueError` si la contraseña pasa de 72 bytes. El 422 es del contrato
    (CHG-09a): esta guarda es defensiva y evita que bcrypt 4 trunque en silencio.
    """
    if _supera_limite_bcrypt(password):
        raise ValueError(_MENSAJE_PASSWORD_LARGA)
    sal = bcrypt.gensalt(rounds=costo)
    async with semaforo:
        return (await asyncio.to_thread(bcrypt.hashpw, password.encode(), sal)).decode()


async def verificar_password(
    password: str, password_hash: str, *, semaforo: asyncio.Semaphore
) -> bool:
    """True sólo si `password` corresponde a `password_hash`; False si no corresponde.

    Un `password_hash` mal formado o vacío no da False: bcrypt lanza ValueError
    («Invalid salt»). Los hashes vienen de `hashear_password`, así que eso sería un dato
    corrupto en la base; qué responder en ese caso lo decide el login (CHG-11).

    Sirve igual para el hash de un usuario y para el ficticio del arranque (RN-08: el
    login decide cuál pasar y ambos caminos usan el mismo hilo y el mismo semáforo).
    Una contraseña de más de 72 bytes da False sin llamar a bcrypt: ninguna guardada
    puede tenerlos, y bcrypt 4 la habría truncado y dado True si coincidían los primeros 72.
    """
    if _supera_limite_bcrypt(password):
        return False
    async with semaforo:
        return await asyncio.to_thread(
            bcrypt.checkpw, password.encode(), password_hash.encode()
        )


def calcular_hash_ficticio(costo: int) -> str:
    """Hash bcrypt de una contraseña aleatoria que se descarta (nadie la conoce).

    El login lo verifica cuando el correo no existe, para que tarde lo mismo que con
    un correo real (RN-08): por eso usa el MISMO costo que los hashes reales.
    Es síncrona y bloquea (~300 ms con costo 12): el lifespan la llama con
    `asyncio.to_thread`.
    """
    # token_urlsafe(32) da 43 caracteres ASCII: debajo del límite de 72 bytes de bcrypt.
    contrasena = secrets.token_urlsafe(32).encode()
    return bcrypt.hashpw(contrasena, bcrypt.gensalt(rounds=costo)).decode()


def emitir_token(
    usuario_id: int,
    roles: Iterable[str],
    *,
    secreto: SecretStr,
    minutos: int,
    ahora: datetime | None = None,
) -> str:
    """JWT HS256 con exactamente `sub` (id como texto), `exp` y `roles`.

    `ahora` sólo existe para que los tests sean deterministas: debe tener zona horaria
    (si no, `ValueError`); por defecto es el reloj real en UTC. `minutos` sale de
    `JWT_EXPIRE_MINUTES`. La clave viaja como `SecretStr` y se abre en una sola línea.
    El token nunca se loguea.
    """
    if ahora is None:
        ahora = datetime.now(timezone.utc)
    elif ahora.tzinfo is None:
        raise ValueError("El instante de emisión debe tener zona horaria.")
    claims = {
        "sub": str(usuario_id),
        "exp": ahora + timedelta(minutes=minutos),
        "roles": [str(rol) for rol in roles],
    }
    return jwt.encode(claims, secreto.get_secret_value(), algorithm=ALGORITMO_JWT)


def verificar_token(token: str, *, secreto: SecretStr) -> DatosToken:
    """Valida firma (sólo HS256), vencimiento y forma del token y devuelve sus datos.

    Lanza `TokenVencido` si venció y `TokenInvalido` ante cualquier otra falla, incluido
    un `exp` que no sea un número finito representable como fecha. La firma se chequea
    antes que `exp`: un token alterado y vencido es inválido, nunca se confía en un
    `exp` sin firma válida. Los errores llevan un mensaje fijo y `from None` para que ni
    el token ni la clave aparezcan en un traceback.
    """
    try:
        # verify_exp=False: PyJWT acepta un exp de texto o booleano; el vencimiento se
        # valida abajo, con la firma ya verificada.
        claims = jwt.decode(
            token,
            secreto.get_secret_value(),
            algorithms=[ALGORITMO_JWT],
            options={"require": ["exp", "sub", "roles"], "verify_exp": False},
        )
    except jwt.InvalidTokenError:
        raise TokenInvalido(_MENSAJE_TOKEN_INVALIDO) from None
    exp = claims["exp"]
    # bool es subclase de int: True/False no son un instante.
    if isinstance(exp, bool) or not isinstance(exp, (int, float)) or not math.isfinite(exp):
        raise TokenInvalido(_MENSAJE_TOKEN_INVALIDO)
    try:
        vence_en = datetime.fromtimestamp(exp, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        raise TokenInvalido(_MENSAJE_TOKEN_INVALIDO) from None
    if vence_en <= datetime.now(timezone.utc):  # mismo borde que PyJWT, sin margen
        raise TokenVencido(_MENSAJE_TOKEN_VENCIDO) from None
    sub, roles = claims["sub"], claims["roles"]
    if not isinstance(sub, str) or not _ID_USUARIO.fullmatch(sub):
        raise TokenInvalido(_MENSAJE_TOKEN_INVALIDO)
    if not isinstance(roles, list) or not all(isinstance(rol, str) for rol in roles):
        raise TokenInvalido(_MENSAJE_TOKEN_INVALIDO)
    return DatosToken(usuario_id=int(sub), roles=roles, vence_en=vence_en)
