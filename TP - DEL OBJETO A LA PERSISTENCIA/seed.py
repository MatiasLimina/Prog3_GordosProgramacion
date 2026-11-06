"""Deja la base en un estado inicial conocido (atómico e idempotente).

Uso:  python seed.py     (desde esta carpeta, después de `alembic upgrade head`)
"""
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import NamedTuple

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

import app.core.base  # noqa: F401  (naming convention primero)
import app.models  # noqa: F401  (todo el metadata)
from app.core.config import get_settings
from app.core.database import crear_fabrica_sesiones, crear_motor
from app.core.security import hashear_password
from app.modules.autores.models import Autor
from app.modules.editoriales.models import Editorial
from app.modules.generos.models import Genero
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.libros.models import Libro, LibroAutor
from app.modules.libros.repository import LibroRepository
from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, Usuario
from app.modules.ventas.models import RenglonVenta, Venta


class UsuarioSeed(NamedTuple):
    email: str
    nombre: str
    password: str  # contraseña de mentira: sólo vive en este archivo
    rol: str
    debe_cambiar: bool


USUARIOS = (
    UsuarioSeed("admin@example.com", "Admin Principal", "admin-seed-1", "ADMIN", False),  # id 1
    UsuarioSeed("admin2@example.com", "Admin Suplente", "admin2-seed-1", "ADMIN", False),  # id 2
    UsuarioSeed("vendedor@example.com", "Vera Vendedora", "vendedor-seed-1", "VENDEDOR", False),  # id 3
    UsuarioSeed("ana@example.com", "Ana Paz", "ana-seed-1", "CLIENTE", False),  # id 4
    UsuarioSeed("nuevo@example.com", "Nuevo Vendedor", "nuevo-seed-1", "VENDEDOR", True),  # id 5
)

MOTIVO_STOCK_INICIAL = "Stock inicial"
MOTIVO_VENTA = "Venta"  # CHG-16 MUST usar el mismo literal en las salidas de venta
ADMIN_ID = 1  # primer usuario de USUARIOS: carga el stock inicial
VENDEDOR_ID = 3  # registra la venta 1
ANA_USUARIO_ID = 4  # usuario ana: vinculado al cliente 3
FECHA_VENTA = datetime(2026, 10, 1, 15, 30, tzinfo=timezone.utc)

EDITORIALES = (("Sudamericana", "Argentina"), ("Alfaguara", "España"), ("Emecé", "Argentina"))  # ids 1..3
GENEROS = ("Novela", "Cuento", "Ensayo")  # ids 1..3
AUTORES = (
    ("Julio Cortázar", "Argentina"),  # id 1
    ("Ricardo Piglia", "Argentina"),  # id 2
    ("Adolfo Bioy Casares", "Argentina"),  # id 3
    ("Silvina Ocampo", "Argentina"),  # id 4
    ("Jorge Luis Borges", "Argentina"),  # id 5
    ("Alejandra Pizarnik", "Argentina"),  # id 6, sin libros
)


class LibroSeed(NamedTuple):
    isbn: str
    titulo: str
    precio: Decimal
    editorial_id: int
    genero_id: int | None
    stock_inicial: int
    autorias: tuple[tuple[int, str, int], ...]  # (autor_id, rol, orden)


# El orden fija los ids 1..5 (y el de los movimientos «Stock inicial»).
LIBROS = (
    LibroSeed("978-950-00-0001-1", "Rayuela", Decimal("25000.00"), 1, 1, 11, ((1, "autor", 1),)),
    LibroSeed("978-950-00-0002-8", "Antología de la literatura fantástica", Decimal("30000.00"), 3, None, 5,
              ((5, "autor", 1), (3, "coautor", 2), (4, "coautor", 3))),
    LibroSeed("978-950-00-0003-5", "Ficciones", Decimal("22000.00"), 3, 2, 10, ((5, "autor", 1),)),
    LibroSeed("978-950-00-0004-2", "Respiración artificial", Decimal("27000.00"), 2, 1, 3, ((2, "autor", 1),)),
    LibroSeed("978-950-00-0005-9", "Bestiario", Decimal("20000.00"), 1, 2, 1, ((1, "autor", 1),)),
)


async def _vaciar_tablas(session: AsyncSession) -> None:
    # TRUNCATE y no DELETE: el disparador de sólo agregado de movimiento_stock es por fila
    # (UPDATE/DELETE) y rechazaría un DELETE; TRUNCATE no lo dispara. RESTART IDENTITY deja
    # los ids desde 1 en cada corrida. La lista sale del metadata: toda tabla nueva entra sola.
    tablas = ", ".join(f'"{t.name}"' for t in SQLModel.metadata.sorted_tables)
    await session.execute(text(f"TRUNCATE {tablas} RESTART IDENTITY CASCADE"))


async def _cargar_usuarios(session: AsyncSession, hashes: list[str]) -> None:
    session.add_all(
        [
            Usuario(email=u.email, nombre=u.nombre, password_hash=h, debe_cambiar_password=u.debe_cambiar)
            for u, h in zip(USUARIOS, hashes)
        ]
    )
    await session.flush()
    session.add_all([AsignacionRol(usuario_id=i, rol=u.rol) for i, u in enumerate(USUARIOS, start=1)])
    session.add(EventoSeguridad(actor="SISTEMA", accion="Carga de los datos iniciales"))
    await session.flush()


async def _cargar_catalogo(session: AsyncSession) -> None:
    # Orden de inserción = ids. El stock NO se asigna acá: entra sólo por el punto único (RN-11).
    session.add_all([Editorial(nombre=n, pais=p) for n, p in EDITORIALES])
    session.add_all([Genero(nombre=n) for n in GENEROS])
    session.add_all([Autor(nombre=n, nacionalidad=nac) for n, nac in AUTORES])
    await session.flush()
    session.add_all(
        [
            Libro(isbn=l.isbn, titulo=l.titulo, precio=l.precio, editorial_id=l.editorial_id, genero_id=l.genero_id)
            for l in LIBROS
        ]
    )
    await session.flush()
    session.add_all(
        [
            LibroAutor(libro_id=i, autor_id=a, rol=rol, orden=orden)
            for i, l in enumerate(LIBROS, start=1)
            for a, rol, orden in l.autorias
        ]
    )
    await session.flush()
    repo = LibroRepository(session)
    for libro_id, l in enumerate(LIBROS, start=1):  # ascendente de libro_id
        await repo.registrar_movimiento(libro_id, l.stock_inicial, MOTIVO_STOCK_INICIAL, ADMIN_ID)


async def _cargar_clientes_y_venta(session: AsyncSession) -> None:
    session.add_all(
        [
            Cliente(nombre="Lucía Fernández", email="lucia@example.com"),  # id 1
            Cliente(nombre="Tomás Ríos", email="tomas@example.com"),  # id 2
            Cliente(nombre="Ana Paz", email="ana@example.com", usuario_id=ANA_USUARIO_ID),  # id 3
        ]
    )
    await session.flush()
    session.add(PerfilCliente(cliente_id=1, telefono="11 5555-0101", direccion="Av. Corrientes 1234, CABA"))

    # Venta 1 (cliente 1): libro 1 x 1 y libro 3 x 2, con el precio copiado del libro y el total calculado.
    pedido = ((1, 1), (3, 2))  # (libro_id, cantidad), ascendente de libro_id
    precios = {}
    for libro_id, _ in pedido:
        precios[libro_id] = (await session.get(Libro, libro_id)).precio
    total = sum((precios[i] * c for i, c in pedido), Decimal("0.00"))
    venta = Venta(cliente_id=1, fecha=FECHA_VENTA, total=total)
    session.add(venta)
    await session.flush()
    session.add_all(
        [RenglonVenta(venta_id=venta.id, libro_id=i, cantidad=c, precio_unitario=precios[i]) for i, c in pedido]
    )
    await session.flush()
    repo = LibroRepository(session)
    for libro_id, cantidad in pedido:
        await repo.registrar_movimiento(libro_id, -cantidad, MOTIVO_VENTA, VENDEDOR_ID, venta_id=venta.id)


async def _contar(session: AsyncSession) -> dict[str, int]:
    return {
        t.name: (await session.execute(select(func.count()).select_from(t))).scalar_one()
        for t in SQLModel.metadata.sorted_tables
    }


async def cargar_datos(session: AsyncSession, *, costo: int, semaforo: asyncio.Semaphore) -> dict[str, int]:
    """Vacía las tablas y carga los datos iniciales en UNA transacción. Devuelve conteos."""
    # bcrypt va ANTES de abrir la transacción: no corre con la conexión tomada.
    hashes = await asyncio.gather(
        *(hashear_password(u.password, costo=costo, semaforo=semaforo) for u in USUARIOS)
    )
    # Una sola transacción: si algo falla, se revierte también el TRUNCATE (es transaccional).
    async with session.begin():
        await _vaciar_tablas(session)
        await _cargar_usuarios(session, hashes)
        await _cargar_catalogo(session)
        await _cargar_clientes_y_venta(session)
        conteos = await _contar(session)
    return conteos


async def main() -> None:
    settings = get_settings()
    motor = crear_motor(settings)
    fabrica = crear_fabrica_sesiones(motor)
    # El semáforo se crea dentro del bucle de este script (asyncio.run), no al importar.
    semaforo = asyncio.Semaphore(settings.bcrypt_max_concurrentes)
    try:
        async with fabrica() as session:
            conteos = await cargar_datos(session, costo=settings.bcrypt_cost, semaforo=semaforo)
    finally:
        await motor.dispose()
    print("Seed cargado:")
    for tabla, cantidad in conteos.items():
        print(f"  {tabla}: {cantidad}")
    print("Usuarios: " + ", ".join(f"{u.email} ({u.rol})" for u in USUARIOS))  # nunca las contraseñas


if __name__ == "__main__":
    asyncio.run(main())
