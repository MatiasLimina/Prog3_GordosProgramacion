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
