"""Ayudas compartidas por los tests de auth (no son tests)."""
from sqlalchemy import text

PASSWORD = "clave-de-prueba-1"  # valor de test, no es una credencial real


async def registrar(client, email="ana@example.com", nombre="Ana", password=PASSWORD):
    return await client.post("/auth/registro", json={"email": email, "nombre": nombre, "password": password})


async def login(client, email="ana@example.com", password=PASSWORD):
    return await client.post("/auth/login", json={"email": email, "password": password})


async def contar(sessionmaker, tabla: str, donde: str = "true", **params) -> int:
    """Cuenta filas desde OTRA sesión: sólo ve lo confirmado."""
    async with sessionmaker() as s:
        return (await s.execute(text(f"SELECT count(*) FROM {tabla} WHERE {donde}"), params)).scalar_one()


async def filas(sessionmaker, sql: str, **params):
    async with sessionmaker() as s:
        return (await s.execute(text(sql), params)).mappings().all()


async def insertar_usuario(
    sessionmaker, email="ana@example.com", password=PASSWORD, *, activo=True, debe_cambiar=False, roles=()
) -> int:
    """Inserta un usuario directo en la base (sin pasar por /auth/registro). `roles`: nombres vigentes."""
    import asyncio

    from app.core.security import hashear_password
    from app.modules.usuarios.models import AsignacionRol, Usuario

    password_hash = await hashear_password(password, costo=4, semaforo=asyncio.Semaphore(1))
    async with sessionmaker() as s:
        usuario = Usuario(
            email=email, nombre="Ana", password_hash=password_hash, activo=activo, debe_cambiar_password=debe_cambiar
        )
        s.add(usuario)
        await s.flush()
        s.add_all([AsignacionRol(usuario_id=usuario.id, rol=rol) for rol in roles])
        await s.commit()
        return usuario.id


def espiar_verificacion(monkeypatch):
    """Cuenta las llamadas a `verificar_password` del servicio: devuelve la lista de (password, hash)."""
    from app.modules.usuarios import service

    llamadas = []
    real = service.verificar_password

    async def espia(password, password_hash, **kwargs):
        llamadas.append((password, password_hash))
        return await real(password, password_hash, **kwargs)

    monkeypatch.setattr(service, "verificar_password", espia)
    return llamadas


def cabecera_cookie(token: str) -> dict[str, str]:
    """Cabecera `Cookie` con un token armado a mano (no pasa por el cookie jar del cliente)."""
    return {"Cookie": f"access_token={token}"}


def token_de_prueba(usuario_id: int, roles=(), *, ahora=None) -> str:
    """Token firmado con la clave de la app de test; `ahora` permite emitirlo en el pasado."""
    from app.core.security import emitir_token
    from app.main import app as fastapi_app

    settings = fastapi_app.state.settings
    return emitir_token(
        usuario_id, roles, secreto=settings.jwt_secret, minutos=settings.jwt_expire_minutes, ahora=ahora
    )


async def entrar_como(
    client, sessionmaker, *roles, email="ana@example.com", debe_cambiar=False
) -> int:
    """Deja al `client` con una sesión iniciada como un usuario con esos roles vigentes; devuelve su id.

    Inserta el usuario y pone en el cookie jar un token firmado, sin pasar por `/auth/login`:
    no escribe en `intento_acceso` ni gasta bcrypt por test. Las cookies del `client` quedan
    puestas para todas sus peticiones siguientes.
    """
    uid = await insertar_usuario(sessionmaker, email, debe_cambiar=debe_cambiar, roles=roles)
    client.cookies.set("access_token", token_de_prueba(uid, roles))
    return uid
