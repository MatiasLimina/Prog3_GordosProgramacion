from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.modules.autores.models import Autor
from app.modules.editoriales.models import Editorial
from app.modules.generos.models import Genero
from app.modules.libros.models import Libro, LibroAutor
from scripts.seed import cargar_datos

pytestmark = pytest.mark.db


async def conteos(session):
    return {
        m.__name__: (await session.execute(select(func.count()).select_from(m))).scalar()
        for m in (Editorial, Genero, Autor, Libro, LibroAutor)
    }


async def correr_seed(sessionmaker_test):
    async with sessionmaker_test() as s:
        await cargar_datos(s)


async def test_ids_y_precios_clave(sessionmaker_test):
    await correr_seed(sessionmaker_test)
    async with sessionmaker_test() as s:
        rayuela = await s.get(Libro, 1)
        assert (rayuela.titulo, rayuela.precio) == ("Rayuela", Decimal("25000.00"))
        respiracion = await s.get(Libro, 4)
        assert (respiracion.titulo, respiracion.precio) == ("Respiración artificial", Decimal("27000.00"))
        assert (await s.get(Editorial, 1)).nombre == "Sudamericana"
        assert (await s.get(Genero, 1)).nombre == "Novela"
        assert await s.get(Autor, 3) is not None
        assert await s.get(Autor, 4) is not None


async def test_datos_validos_de_libros(sessionmaker_test):
    await correr_seed(sessionmaker_test)
    async with sessionmaker_test() as s:
        libros = (await s.execute(select(Libro))).scalars().all()
        assert all(l.stock > 0 for l in libros)
        assert all(l.isbn.startswith("978-") for l in libros)
        assert "978-950-00-0006-6" not in {l.isbn for l in libros}  # lo usa el ejemplo de POST /libros
        assert all(isinstance(l.precio, Decimal) for l in libros)


async def test_hay_libro_con_varios_autores_y_libro_sin_genero(sessionmaker_test):
    await correr_seed(sessionmaker_test)
    async with sessionmaker_test() as s:
        por_libro = (
            await s.execute(
                select(LibroAutor.libro_id, func.count()).group_by(LibroAutor.libro_id)
            )
        ).all()
        assert max(c for _, c in por_libro) >= 2
        sin_genero = (await s.execute(select(Libro).where(Libro.genero_id.is_(None)))).scalars().all()
        assert len(sin_genero) >= 1
        # las autorías tienen rol y orden válidos
        autorias = (await s.execute(select(LibroAutor))).scalars().all()
        assert all(a.orden >= 1 and a.rol for a in autorias)


async def test_devuelve_conteos_reales_para_el_resumen(sessionmaker_test):
    async with sessionmaker_test() as s:
        devuelto = await cargar_datos(s)
    async with sessionmaker_test() as s:
        reales = await conteos(s)
    assert devuelto == {
        "editoriales": reales["Editorial"], "generos": reales["Genero"], "autores": reales["Autor"],
        "libros": reales["Libro"], "autorias": reales["LibroAutor"],
    }


async def test_es_idempotente(sessionmaker_test):
    await correr_seed(sessionmaker_test)
    async with sessionmaker_test() as s:
        primero = await conteos(s)
        ids1 = (await s.execute(select(Libro.id, Libro.isbn).order_by(Libro.id))).all()
    await correr_seed(sessionmaker_test)
    async with sessionmaker_test() as s:
        segundo = await conteos(s)
        ids2 = (await s.execute(select(Libro.id, Libro.isbn).order_by(Libro.id))).all()
    assert primero == segundo
    assert all(v > 0 for v in primero.values())
    assert ids1 == ids2


async def test_seed_pisa_datos_previos(sessionmaker_test):
    async with sessionmaker_test() as s:
        s.add(Editorial(nombre="Basura", pais="X"))
        await s.commit()
    await correr_seed(sessionmaker_test)
    async with sessionmaker_test() as s:
        nombres = (await s.execute(select(Editorial.nombre))).scalars().all()
        assert "Basura" not in nombres
        assert (await s.get(Editorial, 1)).nombre == "Sudamericana"


async def test_post_libro_del_ejemplo_de_la_consigna_da_201(client, sessionmaker_test):
    await correr_seed(sessionmaker_test)
    r = await client.post(
        "/libros/",
        json={
            "isbn": "978-950-00-0006-6",
            "titulo": "Los que aman, odian",
            "precio": "21000.00",
            "stock": 4,
            "editorial_id": 1,
            "genero_id": 1,
            "autores": [
                {"autor_id": 3, "rol": "coautor", "orden": 1},
                {"autor_id": 4, "rol": "coautor", "orden": 2},
            ],
        },
    )
    assert r.status_code == 201, r.text
    assert [a["autor_id"] for a in r.json()["autores"]] == [3, 4]
