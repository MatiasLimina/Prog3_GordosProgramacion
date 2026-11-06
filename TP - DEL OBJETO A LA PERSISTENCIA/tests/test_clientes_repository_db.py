"""Repositorios y UoW del módulo `clientes` contra la base real (CHG-15).

Ningún repositorio confirma: confirmar es del UoW. Estos tests miran la base desde OTRA sesión,
que sólo ve lo confirmado.
"""
from contextlib import contextmanager

import pytest
from sqlalchemy import event, text
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.db


async def _cliente(sm, email="ana@example.com", nombre="Ana"):
    from app.modules.clientes.models import Cliente

    async with sm() as s:
        cliente = Cliente(nombre=nombre, email=email)
        s.add(cliente)
        await s.commit()
        return cliente.id


# ---- constraint_violada (2.1) ----

async def test_constraint_violada_devuelve_el_nombre_de_la_constraint_de_un_error_real(sessionmaker_test):
    from app.core.errors import constraint_violada
    from app.modules.clientes.models import Cliente

    await _cliente(sessionmaker_test)
    async with sessionmaker_test() as s:
        s.add(Cliente(nombre="Otra", email="ana@example.com"))
        with pytest.raises(IntegrityError) as excinfo:
            await s.flush()
    assert constraint_violada(excinfo.value) == "uq_cliente_email"


async def test_constraint_violada_de_una_fk_devuelve_su_nombre(sessionmaker_test):
    from app.core.errors import constraint_violada
    from app.modules.clientes.models import PerfilCliente

    async with sessionmaker_test() as s:
        s.add(PerfilCliente(cliente_id=999, telefono="1", direccion="d"))
        with pytest.raises(IntegrityError) as excinfo:
            await s.flush()
    assert constraint_violada(excinfo.value) == "fk_perfil_cliente_cliente_id_cliente"


def test_constraint_violada_de_un_error_sin_constraint_es_none():
    from app.core.errors import constraint_violada

    assert constraint_violada(IntegrityError("INSERT", {}, Exception("sin constraint"))) is None


@contextmanager
def _contar_sentencias(sm):
    """Lista que se llena con cada sentencia que llega a la base mientras dura el bloque."""
    sentencias: list[str] = []

    def hook(conn, cursor, statement, *args):
        sentencias.append(statement)

    engine = sm.kw["bind"].sync_engine
    event.listen(engine, "before_cursor_execute", hook)
    try:
        yield sentencias
    finally:
        event.remove(engine, "before_cursor_execute", hook)


async def _perfil(sm, cliente_id, telefono="11 2233", direccion="Calle 1"):
    from app.modules.clientes.models import PerfilCliente

    async with sm() as s:
        s.add(PerfilCliente(cliente_id=cliente_id, telefono=telefono, direccion=direccion))
        await s.commit()


async def _contar(sm, tabla):
    async with sm() as s:
        return (await s.execute(text(f"SELECT count(*) FROM {tabla}"))).scalar_one()


# ---- ClienteRepository.get_detalle (3.1) ----

async def test_get_detalle_trae_el_perfil_sin_consultas_al_leerlo(sessionmaker_test):
    from app.modules.clientes.repository import ClienteRepository

    cliente_id = await _cliente(sessionmaker_test)
    await _perfil(sessionmaker_test, cliente_id)
    async with sessionmaker_test() as s:
        cliente = await ClienteRepository(s).get_detalle(cliente_id)
        with _contar_sentencias(sessionmaker_test) as sentencias:
            assert cliente.perfil.telefono == "11 2233"
        assert sentencias == []


async def test_get_detalle_de_un_cliente_sin_perfil_tiene_perfil_none_sin_consultar(sessionmaker_test):
    from app.modules.clientes.repository import ClienteRepository

    cliente_id = await _cliente(sessionmaker_test)
    async with sessionmaker_test() as s:
        cliente = await ClienteRepository(s).get_detalle(cliente_id)
        with _contar_sentencias(sessionmaker_test) as sentencias:
            assert cliente.perfil is None
        assert sentencias == []


async def test_get_detalle_de_un_id_inexistente_es_none(sessionmaker_test):
    from app.modules.clientes.repository import ClienteRepository

    async with sessionmaker_test() as s:
        assert await ClienteRepository(s).get_detalle(999) is None


async def test_get_detalle_recarga_el_perfil_de_un_cliente_ya_cargado_en_la_sesion(sessionmaker_test):
    """`populate_existing`: si el cliente ya está en el mapa de identidad sin perfil, el perfil nuevo se ve."""
    from app.modules.clientes.repository import ClienteRepository

    cliente_id = await _cliente(sessionmaker_test)
    async with sessionmaker_test() as s:
        repo = ClienteRepository(s)
        assert (await repo.get_detalle(cliente_id)).perfil is None
        await _perfil(sessionmaker_test, cliente_id, telefono="99")
        assert (await repo.get_detalle(cliente_id)).perfil.telefono == "99"


# ---- PerfilClienteRepository.add (3.3) ----

async def test_alta_de_perfil_con_cliente_inexistente_es_cliente_no_encontrado_y_no_deja_nada(sessionmaker_test):
    from app.core.errors import ClienteNoEncontrado, Conflicto
    from app.modules.clientes.models import PerfilCliente
    from app.modules.clientes.unit_of_work import ClientesUoW

    async with sessionmaker_test() as s:
        with pytest.raises(ClienteNoEncontrado) as excinfo:
            async with ClientesUoW(s) as uow:
                await uow.perfiles.add(PerfilCliente(cliente_id=999, telefono="1", direccion="d"))
    assert excinfo.value.cliente_id == 999
    assert not isinstance(excinfo.value, Conflicto)
    assert excinfo.value.__cause__ is None
    assert await _contar(sessionmaker_test, "perfil_cliente") == 0


async def test_segundo_perfil_del_mismo_cliente_es_conflicto_con_mensaje_propio(sessionmaker_test):
    from app.core.errors import Conflicto
    from app.modules.clientes.models import PerfilCliente
    from app.modules.clientes.unit_of_work import ClientesUoW

    cliente_id = await _cliente(sessionmaker_test)
    await _perfil(sessionmaker_test, cliente_id)
    async with sessionmaker_test() as s:
        with pytest.raises(Conflicto) as excinfo:
            async with ClientesUoW(s) as uow:
                await uow.perfiles.add(PerfilCliente(cliente_id=cliente_id, telefono="99", direccion="Otra"))
    assert excinfo.value.mensaje == "El cliente ya tiene un perfil."
    assert "uq_" not in excinfo.value.mensaje
    assert await _contar(sessionmaker_test, "perfil_cliente") == 1


async def test_despues_del_404_un_bloque_sucesivo_con_la_misma_sesion_crea_el_perfil(sessionmaker_test):
    from app.core.errors import ClienteNoEncontrado
    from app.modules.clientes.models import PerfilCliente
    from app.modules.clientes.unit_of_work import ClientesUoW

    cliente_id = await _cliente(sessionmaker_test)
    async with sessionmaker_test() as s:
        with pytest.raises(ClienteNoEncontrado):
            async with ClientesUoW(s) as uow:
                await uow.perfiles.add(PerfilCliente(cliente_id=999, telefono="1", direccion="d"))
        async with ClientesUoW(s) as uow:
            perfil = await uow.perfiles.add(PerfilCliente(cliente_id=cliente_id, telefono="2", direccion="e"))
            assert perfil.id is not None
    assert await _contar(sessionmaker_test, "perfil_cliente") == 1


async def test_alta_de_perfil_deja_pasar_un_integrity_error_que_no_es_la_fk_del_cliente(sessionmaker_test):
    """Sólo la FK del cliente es 404: cualquier otra constraint llega intacta al UoW (acá, el UNIQUE del segundo perfil), sin traducir."""
    from app.modules.clientes.models import PerfilCliente
    from app.modules.clientes.repository import PerfilClienteRepository

    cliente_id = await _cliente(sessionmaker_test)
    await _perfil(sessionmaker_test, cliente_id)
    async with sessionmaker_test() as s:
        with pytest.raises(IntegrityError):
            await PerfilClienteRepository(s).add(PerfilCliente(cliente_id=cliente_id, telefono="3", direccion="f"))


# ---- VentaRepository.listar_de_cliente / contar_de_cliente (3.5) ----

async def _libro(sm, isbn, *, titulo=None, de_baja=False):
    from datetime import UTC, datetime
    from decimal import Decimal

    from app.modules.editoriales.models import Editorial
    from app.modules.libros.models import Libro

    async with sm() as s:
        editorial = Editorial(nombre=f"Editorial {isbn}", pais="AR")
        s.add(editorial)
        await s.flush()
        libro = Libro(
            isbn=isbn, titulo=titulo or f"Título {isbn}", precio=Decimal("10.00"), stock=5, editorial_id=editorial.id,
            borrado_en=datetime.now(UTC) if de_baja else None,
        )
        s.add(libro)
        await s.commit()
        return libro.id


async def _venta(sm, cliente_id, libro_ids):
    """Una venta con un renglón por cada libro de `libro_ids`; devuelve su id."""
    from datetime import UTC, datetime
    from decimal import Decimal

    from app.modules.ventas.models import RenglonVenta, Venta

    async with sm() as s:
        venta = Venta(cliente_id=cliente_id, fecha=datetime.now(UTC), total=Decimal("10.00") * len(libro_ids))
        venta.renglones = [
            RenglonVenta(libro_id=libro_id, cantidad=1, precio_unitario=Decimal("10.00")) for libro_id in libro_ids
        ]
        s.add(venta)
        await s.commit()
        return venta.id


def _leer_todo(ventas):
    """Toca lo que muestra un `VentaRead`: cliente, renglones y libro de cada renglón."""
    return [(v.id, v.cliente.id, [(r.libro.titulo, r.cantidad) for r in v.renglones]) for v in ventas]


async def test_listar_de_cliente_trae_solo_las_suyas_en_orden_de_id_con_el_detalle_precargado(sessionmaker_test):
    from app.modules.ventas.repository import VentaRepository

    ana = await _cliente(sessionmaker_test)
    beto = await _cliente(sessionmaker_test, email="beto@example.com", nombre="Beto")
    libro = await _libro(sessionmaker_test, "ISBN-1")
    v1 = await _venta(sessionmaker_test, ana, [libro])
    v2 = await _venta(sessionmaker_test, ana, [libro])
    await _venta(sessionmaker_test, beto, [libro])
    v4 = await _venta(sessionmaker_test, ana, [libro])
    async with sessionmaker_test() as s:
        ventas = await VentaRepository(s).listar_de_cliente(ana, offset=0, limit=10)
        with _contar_sentencias(sessionmaker_test) as sentencias:
            detalle = _leer_todo(ventas)
        assert sentencias == []
    assert [v[0] for v in detalle] == [v1, v2, v4]
    assert all(v[1] == ana for v in detalle)
    assert detalle[0][2] == [("Título ISBN-1", 1)]


async def test_listar_de_cliente_pagina_con_offset_y_limit(sessionmaker_test):
    from app.modules.ventas.repository import VentaRepository

    ana = await _cliente(sessionmaker_test)
    libro = await _libro(sessionmaker_test, "ISBN-1")
    ids = [await _venta(sessionmaker_test, ana, [libro]) for _ in range(3)]
    async with sessionmaker_test() as s:
        repo = VentaRepository(s)
        assert [v.id for v in await repo.listar_de_cliente(ana, offset=2, limit=2)] == ids[2:]
        assert [v.id for v in await repo.listar_de_cliente(ana, offset=0, limit=1)] == ids[:1]


async def test_listar_de_cliente_sigue_mostrando_el_libro_dado_de_baja(sessionmaker_test):
    from app.modules.ventas.repository import VentaRepository

    ana = await _cliente(sessionmaker_test)
    baja = await _libro(sessionmaker_test, "ISBN-B", titulo="Libro viejo", de_baja=True)
    await _venta(sessionmaker_test, ana, [baja])
    async with sessionmaker_test() as s:
        ventas = await VentaRepository(s).listar_de_cliente(ana, offset=0, limit=10)
        with _contar_sentencias(sessionmaker_test) as sentencias:
            assert ventas[0].renglones[0].libro.titulo == "Libro viejo"
        assert sentencias == []


async def test_contar_de_cliente_coincide_con_el_total_y_no_precarga(sessionmaker_test):
    from app.modules.ventas.repository import VentaRepository

    ana = await _cliente(sessionmaker_test)
    beto = await _cliente(sessionmaker_test, email="beto@example.com", nombre="Beto")
    libro = await _libro(sessionmaker_test, "ISBN-1")
    for _ in range(3):
        await _venta(sessionmaker_test, ana, [libro])
    await _venta(sessionmaker_test, beto, [libro])
    async with sessionmaker_test() as s:
        repo = VentaRepository(s)
        with _contar_sentencias(sessionmaker_test) as sentencias:
            assert await repo.contar_de_cliente(ana) == 3
        assert await repo.contar_de_cliente(beto) == 1
        assert await repo.contar_de_cliente(999) == 0
    assert len(sentencias) == 1
    assert "JOIN" not in sentencias[0].upper()


async def test_la_cantidad_de_sentencias_de_listar_de_cliente_no_depende_de_ventas_ni_renglones(sessionmaker_test):
    from app.modules.ventas.repository import VentaRepository

    chico = await _cliente(sessionmaker_test)
    grande = await _cliente(sessionmaker_test, email="beto@example.com", nombre="Beto")
    l1 = await _libro(sessionmaker_test, "ISBN-1")
    l2 = await _libro(sessionmaker_test, "ISBN-2")
    await _venta(sessionmaker_test, chico, [l1])
    for _ in range(3):
        await _venta(sessionmaker_test, grande, [l1, l2])

    async def sentencias_de(cliente_id):
        async with sessionmaker_test() as s:
            with _contar_sentencias(sessionmaker_test) as sentencias:
                _leer_todo(await VentaRepository(s).listar_de_cliente(cliente_id, offset=0, limit=10))
            return len(sentencias)

    assert await sentencias_de(chico) == await sentencias_de(grande)


# ---- ClientesUoW y UsuariosUoW (3.7) ----

async def test_clientes_uow_compone_los_tres_repositorios_con_la_misma_sesion(sessionmaker_test):
    from app.modules.clientes.repository import (
        ClienteRepository,
        PerfilClienteRepository,
    )
    from app.modules.clientes.unit_of_work import ClientesUoW
    from app.modules.ventas.repository import VentaRepository

    async with sessionmaker_test() as s:
        uow = ClientesUoW(s)
        assert isinstance(uow.clientes, ClienteRepository)
        assert isinstance(uow.perfiles, PerfilClienteRepository)
        assert isinstance(uow.ventas, VentaRepository)
        assert uow.clientes.session is uow.perfiles.session is uow.ventas.session is s


def test_el_mensaje_de_correo_repetido_es_el_mismo_en_clientes_y_en_el_registro():
    from app.modules.clientes.unit_of_work import ClientesUoW
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    assert ClientesUoW.MENSAJES["uq_cliente_email"] == "Ya existe un cliente con ese correo."
    assert ClientesUoW.MENSAJES["uq_cliente_email"] == UsuariosUoW.MENSAJES["uq_cliente_email"]


async def test_usuarios_uow_usa_el_repositorio_de_clientes(sessionmaker_test):
    from app.modules.clientes.repository import ClienteRepository
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    async with sessionmaker_test() as s:
        assert isinstance(UsuariosUoW(s).clientes, ClienteRepository)


async def test_ningun_repositorio_confirma(sessionmaker_test, monkeypatch):
    from app.modules.clientes.models import Cliente, PerfilCliente
    from app.modules.clientes.unit_of_work import ClientesUoW

    async with sessionmaker_test() as s:
        confirmaciones = []
        real = s.commit

        async def espia():
            confirmaciones.append(1)
            await real()

        monkeypatch.setattr(s, "commit", espia)
        uow = ClientesUoW(s)  # sin `async with`: nadie confirma
        cliente = await uow.clientes.add(Cliente(nombre="Ana", email="ana@example.com"))
        await uow.clientes.update(cliente, {"nombre": "Ana P."})
        await uow.perfiles.add(PerfilCliente(cliente_id=cliente.id, telefono="1", direccion="d"))
        await uow.clientes.get_detalle(cliente.id)
        await uow.ventas.listar_de_cliente(cliente.id, offset=0, limit=10)
        await uow.ventas.contar_de_cliente(cliente.id)
        assert confirmaciones == []
        await s.rollback()
    assert await _contar(sessionmaker_test, "cliente") == 0
