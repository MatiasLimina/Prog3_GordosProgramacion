"""Deja la base en un estado inicial conocido (idempotente).

Uso:  python -m scripts.seed     (después de `alembic upgrade head`)

Vacía TODAS las tablas con TRUNCATE ... RESTART IDENTITY y vuelve a cargar los
mismos datos, así los ids son siempre los mismos (los casos .http y la
corrección dependen de ellos: editorial 1, género 1, autores 3 y 4, libros 1 y 4,
cliente 2 = Tomás Ríos, y una venta 1 ya cargada, así que la próxima venta es la 2).
"""
import asyncio
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

import app.core.base  # noqa: F401  (naming convention primero)
import app.models  # noqa: F401  (todo el metadata)
from app.core.config import get_settings
from app.core.database import crear_engine_y_sessionmaker
from app.modules.autores.models import Autor
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.editoriales.models import Editorial
from app.modules.generos.models import Genero
from app.modules.libros.models import Libro, LibroAutor
from app.modules.ventas.models import RenglonVenta, Venta


async def _vaciar_tablas(session: AsyncSession) -> None:
    # La lista sale del metadata: toda tabla registrada entra sola.
    tablas = ", ".join(f'"{t.name}"' for t in SQLModel.metadata.sorted_tables)
    await session.execute(text(f"TRUNCATE {tablas} RESTART IDENTITY CASCADE"))


async def _cargar_catalogo(session: AsyncSession) -> None:
    # El orden de inserción determina los ids (1, 2, 3, ...).
    session.add_all(
        [
            Editorial(nombre="Sudamericana", pais="Argentina"),  # id 1
            Editorial(nombre="Alfaguara", pais="España"),  # id 2
            Editorial(nombre="Emecé", pais="Argentina"),  # id 3
        ]
    )
    session.add_all(
        [
            Genero(nombre="Novela"),  # id 1
            Genero(nombre="Cuento"),  # id 2
            Genero(nombre="Ensayo"),  # id 3
        ]
    )
    session.add_all(
        [
            Autor(nombre="Julio Cortázar", nacionalidad="Argentina"),  # id 1
            Autor(nombre="Ricardo Piglia", nacionalidad="Argentina"),  # id 2
            Autor(nombre="Adolfo Bioy Casares", nacionalidad="Argentina"),  # id 3
            Autor(nombre="Silvina Ocampo", nacionalidad="Argentina"),  # id 4
            Autor(nombre="Jorge Luis Borges", nacionalidad="Argentina"),  # id 5
        ]
    )
    await session.flush()

    libros = [
        Libro(isbn="978-950-07-0001-1", titulo="Rayuela", precio=Decimal("25000.00"),
              stock=10, editorial_id=1, genero_id=1),  # id 1
        # Sin género (genero_id NULL) y con tres autores: útil para C-07.
        Libro(isbn="978-950-04-0002-2", titulo="Antología de la literatura fantástica",
              precio=Decimal("22000.00"), stock=5, editorial_id=3, genero_id=None),  # id 2
        Libro(isbn="978-950-04-0003-3", titulo="El Aleph", precio=Decimal("18500.50"),
              stock=8, editorial_id=3, genero_id=2),  # id 3
        Libro(isbn="978-950-07-0004-4", titulo="Respiración artificial",
              precio=Decimal("27000.00"), stock=6, editorial_id=2, genero_id=1),  # id 4
    ]
    session.add_all(libros)
    await session.flush()

    session.add_all(
        [
            LibroAutor(libro_id=1, autor_id=1, rol="autor", orden=1),
            LibroAutor(libro_id=2, autor_id=5, rol="autor", orden=1),
            LibroAutor(libro_id=2, autor_id=3, rol="coautor", orden=2),
            LibroAutor(libro_id=2, autor_id=4, rol="coautor", orden=3),
            LibroAutor(libro_id=3, autor_id=5, rol="autor", orden=1),
            LibroAutor(libro_id=4, autor_id=2, rol="autor", orden=1),
        ]
    )
    await session.flush()


async def _cargar_clientes(session: AsyncSession) -> None:
    # El cliente id 2 es "Tomás Ríos" / tomas@example.com (lo pide el ejemplo de
    # POST /ventas de la consigna), por lo que el id 1 va antes.
    session.add_all(
        [
            Cliente(nombre="Lucía Fernández", email="lucia@example.com"),  # id 1
            Cliente(nombre="Tomás Ríos", email="tomas@example.com"),  # id 2
        ]
    )
    await session.flush()

    session.add(
        PerfilCliente(cliente_id=1, telefono="11 5555-0101", direccion="Av. Corrientes 1234, CABA")
    )

    # Venta id 1 (cliente 1): precios copiados del libro (RN-06), total = suma (RN-07)
    # y stock ya descontado en el catálogo sembrado (Antología: 5 -> 4, El Aleph: 8 -> 6).
    # Usa los libros 2 y 3 para que el ejemplo de la consigna (libros 1 y 4) tenga stock completo.
    venta = Venta(
        cliente_id=1,
        fecha=datetime(2026, 10, 1, 15, 30, tzinfo=timezone.utc),
        total=Decimal("22000.00") + 2 * Decimal("18500.50"),  # 59001.00
    )
    venta.renglones.append(RenglonVenta(libro_id=2, cantidad=1, precio_unitario=Decimal("22000.00")))
    venta.renglones.append(RenglonVenta(libro_id=3, cantidad=2, precio_unitario=Decimal("18500.50")))
    session.add(venta)
    await session.flush()
    for libro_id, cantidad in ((2, 1), (3, 2)):
        libro = await session.get(Libro, libro_id)
        libro.stock -= cantidad
    await session.flush()


async def cargar_datos(session: AsyncSession) -> dict[str, int]:
    """Vacía las tablas y carga los datos iniciales. Devuelve conteos para el resumen."""
    await _vaciar_tablas(session)
    await _cargar_catalogo(session)
    await _cargar_clientes(session)
    await session.commit()
    return await _contar(session)


async def _contar(session: AsyncSession) -> dict[str, int]:
    modelos = {"editoriales": Editorial, "generos": Genero, "autores": Autor,
               "libros": Libro, "autorias": LibroAutor, "clientes": Cliente,
               "perfiles": PerfilCliente, "ventas": Venta, "renglones": RenglonVenta}
    return {
        nombre: (await session.execute(select(func.count()).select_from(modelo))).scalar_one()
        for nombre, modelo in modelos.items()
    }


async def main() -> None:
    settings = get_settings()
    engine, sessionmaker = crear_engine_y_sessionmaker(settings.database_url, settings.db_echo)
    try:
        async with sessionmaker() as session:
            c = await cargar_datos(session)
    finally:
        await engine.dispose()
    print(
        f"Seed cargado: {c['editoriales']} editoriales, {c['generos']} géneros, "
        f"{c['autores']} autores, {c['libros']} libros, {c['autorias']} autorías, "
        f"{c['clientes']} clientes, {c['perfiles']} perfiles, {c['ventas']} ventas, "
        f"{c['renglones']} renglones."
    )


if __name__ == "__main__":
    asyncio.run(main())
