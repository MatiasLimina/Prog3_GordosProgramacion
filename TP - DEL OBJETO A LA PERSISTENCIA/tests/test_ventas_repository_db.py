"""Repositorio y UoW de `ventas` contra la base real (CHG-16).

Los datos se crean por ORM. Ningún repositorio confirma: se mira la base desde OTRA sesión,
que sólo ve lo confirmado.
"""
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import event, text

pytestmark = pytest.mark.db


@contextmanager
def _contar_sentencias(sm):
    sentencias: list[str] = []

    def hook(conn, cursor, statement, *args):
        sentencias.append(statement)

    engine = sm.kw["bind"].sync_engine
    event.listen(engine, "before_cursor_execute", hook)
    try:
        yield sentencias
    finally:
        event.remove(engine, "before_cursor_execute", hook)


async def _base(sm, *, n_libros=4):
    """Usuario, cliente y `n_libros` libros con stock 50. Devuelve `(usuario_id, cliente_id, [libro_id])`."""
    from app.modules.clientes.models import Cliente
    from app.modules.editoriales.models import Editorial
    from app.modules.libros.models import Libro
    from app.modules.usuarios.models import Usuario

    async with sm() as s:
        usuario = Usuario(email="v@example.com", nombre="Vera", password_hash="hash-no-real")
        cliente = Cliente(nombre="Ana", email="ana@example.com")
        editorial = Editorial(nombre="Eterna", pais="AR")
        s.add_all([usuario, cliente, editorial])
        await s.flush()
        libros = [
            Libro(isbn=f"I{i}", titulo=f"Libro {i}", precio=Decimal("10.00"), stock=50, editorial_id=editorial.id)
            for i in range(1, n_libros + 1)
        ]
        s.add_all(libros)
        await s.commit()
        return usuario.id, cliente.id, [libro.id for libro in libros]


async def _venta(sm, cliente_id, libro_ids):
    """Confirma una venta con un renglón por libro (cantidad 1) y devuelve su id."""
    from app.modules.ventas.models import RenglonVenta, Venta

    async with sm() as s:
        venta = Venta(cliente_id=cliente_id, fecha=datetime.now(UTC), total=Decimal("10.00") * len(libro_ids))
        venta.renglones = [
            RenglonVenta(libro_id=lid, cantidad=1, precio_unitario=Decimal("10.00")) for lid in libro_ids
        ]
        s.add(venta)
        await s.commit()
        return venta.id


# ---- VentaRepository.get_detalle / listar (3.1) ----

@pytest.mark.parametrize("n_renglones", [2, 4])
async def test_get_detalle_trae_cliente_renglones_y_libros_sin_consultas_al_leerlos(sessionmaker_test, n_renglones):
    from app.modules.ventas.repository import VentaRepository

    _, cliente_id, libros = await _base(sessionmaker_test)
    venta_id = await _venta(sessionmaker_test, cliente_id, libros[:n_renglones])
    async with sessionmaker_test() as s:
        venta = await VentaRepository(s).get_detalle(venta_id)
        with _contar_sentencias(sessionmaker_test) as leidas:
            assert venta.cliente.email == "ana@example.com"
            assert sorted(r.libro.titulo for r in venta.renglones) == [f"Libro {i}" for i in range(1, n_renglones + 1)]
        assert leidas == []


async def test_get_detalle_emite_las_mismas_sentencias_con_2_o_4_renglones(sessionmaker_test):
    from app.modules.ventas.repository import VentaRepository

    _, cliente_id, libros = await _base(sessionmaker_test)
    v2 = await _venta(sessionmaker_test, cliente_id, libros[:2])
    v4 = await _venta(sessionmaker_test, cliente_id, libros)
    cuentas = []
    for venta_id in (v2, v4):
        async with sessionmaker_test() as s:
            with _contar_sentencias(sessionmaker_test) as sentencias:
                await VentaRepository(s).get_detalle(venta_id)
            cuentas.append(len(sentencias))
    assert cuentas[0] == cuentas[1]


async def test_get_detalle_con_libro_dado_de_baja_lo_sigue_mostrando(sessionmaker_test):
    from app.modules.ventas.repository import VentaRepository

    _, cliente_id, libros = await _base(sessionmaker_test)
    venta_id = await _venta(sessionmaker_test, cliente_id, libros[:2])
    async with sessionmaker_test() as s:
        await s.execute(text("UPDATE libro SET borrado_en = now() WHERE id = :i"), {"i": libros[0]})
        await s.commit()
    async with sessionmaker_test() as s:
        venta = await VentaRepository(s).get_detalle(venta_id)
        with _contar_sentencias(sessionmaker_test) as leidas:
            assert all(r.libro.titulo for r in venta.renglones)
            assert any(r.libro.borrado_en is not None for r in venta.renglones)
        assert leidas == []


async def test_get_detalle_de_un_id_inexistente_es_none(sessionmaker_test):
    from app.modules.ventas.repository import VentaRepository

    async with sessionmaker_test() as s:
        assert await VentaRepository(s).get_detalle(999) is None


async def test_listar_pagina_por_id_con_detalle_y_cuenta_igual_que_count(sessionmaker_test):
    from app.modules.ventas.repository import VentaRepository

    _, cliente_id, libros = await _base(sessionmaker_test)
    ids = [await _venta(sessionmaker_test, cliente_id, libros[:n]) for n in (1, 2, 3)]
    async with sessionmaker_test() as s:
        repo = VentaRepository(s)
        pagina = await repo.listar(offset=1, limit=1)
        assert [v.id for v in pagina] == [ids[1]]
        with _contar_sentencias(sessionmaker_test) as leidas:
            assert pagina[0].cliente.nombre == "Ana"
            assert len(pagina[0].renglones) == 2
        assert leidas == []
        assert await repo.count() == 3


async def test_listar_emite_las_mismas_sentencias_con_1_o_3_ventas(sessionmaker_test):
    from app.modules.ventas.repository import VentaRepository

    _, cliente_id, libros = await _base(sessionmaker_test)
    await _venta(sessionmaker_test, cliente_id, libros[:1])
    cuentas = []
    for _ in range(2):
        async with sessionmaker_test() as s:
            with _contar_sentencias(sessionmaker_test) as sentencias:
                await VentaRepository(s).listar(offset=0, limit=20)
            cuentas.append(len(sentencias))
        await _venta(sessionmaker_test, cliente_id, libros[:2])
        await _venta(sessionmaker_test, cliente_id, libros)
    assert cuentas[0] == cuentas[1]


# ---- VentasUoW (3.5) ----

async def test_ventas_uow_compone_los_repositorios_con_la_misma_sesion(sessionmaker_test):
    from app.modules.clientes.repository import ClienteRepository
    from app.modules.libros.repository import LibroRepository
    from app.modules.usuarios.repository import AsignacionRolRepository
    from app.modules.ventas.repository import VentaRepository
    from app.modules.ventas.unit_of_work import VentasUoW

    async with sessionmaker_test() as s:
        uow = VentasUoW(s)
        assert isinstance(uow.ventas, VentaRepository)
        assert isinstance(uow.libros, LibroRepository)
        assert isinstance(uow.clientes, ClienteRepository)
        assert isinstance(uow.asignaciones, AsignacionRolRepository)
        assert {uow.ventas.session, uow.libros.session, uow.clientes.session, uow.asignaciones.session} == {s}


async def test_ventas_uow_traduce_la_fk_del_cliente_a_conflicto_sin_nombrar_la_constraint(sessionmaker_test):
    from app.core.errors import Conflicto
    from app.modules.ventas.models import Venta
    from app.modules.ventas.unit_of_work import VentasUoW

    async with sessionmaker_test() as s:
        with pytest.raises(Conflicto) as excinfo:
            async with VentasUoW(s) as uow:
                await uow.ventas.add(Venta(cliente_id=999, fecha=datetime.now(UTC), total=Decimal("0")))
    assert excinfo.value.mensaje == "El cliente indicado no existe."
    async with sessionmaker_test() as otra:
        assert (await otra.execute(text("SELECT count(*) FROM venta"))).scalar_one() == 0
