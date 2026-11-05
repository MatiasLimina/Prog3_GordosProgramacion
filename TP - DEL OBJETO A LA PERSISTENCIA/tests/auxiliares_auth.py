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
