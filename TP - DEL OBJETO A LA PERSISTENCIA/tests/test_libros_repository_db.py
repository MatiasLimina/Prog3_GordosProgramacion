"""Repositorios del módulo `libros` contra la base real (CHG-13): el punto único de stock y las lecturas.

`registrar_movimiento` es la única vía de escritura de `libro.stock` (RN-11): un `UPDATE` condicionado
y un `MovimientoStock`, con `flush()` y sin `commit()`. Estos tests miran la base desde OTRA sesión,
que sólo ve lo confirmado.
"""
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import event, text

from app.core.tipos import INT32_MAX

pytestmark = pytest.mark.db


async def _preparar(sm, *, stock=2, isbn="ISBN-1"):
    """Inserta usuario, editorial y libro; devuelve `(libro_id, usuario_id)` como `int`."""
    from app.modules.editoriales.models import Editorial
    from app.modules.libros.models import Libro
    from app.modules.usuarios.models import Usuario

    async with sm() as s:
        usuario = Usuario(email=f"u-{isbn}@example.com", nombre="Ana", password_hash="hash-no-real")
        editorial = Editorial(nombre=f"Editorial {isbn}", pais="AR")
        s.add_all([usuario, editorial])
        await s.flush()
        libro = Libro(isbn=isbn, titulo="Ficciones", precio=Decimal("10.00"), stock=stock, editorial_id=editorial.id)
        s.add(libro)
        await s.commit()
        return libro.id, usuario.id


async def _estado(sm, libro_id):
    """`(stock, [cantidades de sus movimientos])` según OTRA sesión (sólo lo confirmado)."""
    async with sm() as s:
        stock = (await s.execute(text("SELECT stock FROM libro WHERE id = :i"), {"i": libro_id})).scalar_one()
        movimientos = (
            await s.execute(text("SELECT cantidad FROM movimiento_stock WHERE libro_id = :i ORDER BY id"), {"i": libro_id})
        ).scalars().all()
        return stock, list(movimientos)


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


# ---- registrar_movimiento: camino feliz (4.1) ----

async def test_registrar_movimiento_devuelve_stock_y_movimiento_con_cuando_cargado(sessionmaker_test):
    from app.modules.libros.repository import LibroRepository, ResultadoMovimiento

    libro_id, usuario_id = await _preparar(sessionmaker_test, stock=2)
    async with sessionmaker_test() as s:
        resultado = await LibroRepository(s).registrar_movimiento(libro_id, 3, "Reposición", usuario_id)
        assert isinstance(resultado, ResultadoMovimiento)
        assert resultado.stock == 5
        with _contar_sentencias(sessionmaker_test) as sentencias:
            movimiento = resultado.movimiento
            assert movimiento.id is not None
            assert movimiento.cuando is not None
            assert movimiento.cuando.tzinfo is not None
            assert (movimiento.libro_id, movimiento.cantidad, movimiento.motivo) == (libro_id, 3, "Reposición")
            assert movimiento.usuario_id == usuario_id
            assert movimiento.venta_id is None
        assert sentencias == []  # id y cuando ya vinieron en el RETURNING del INSERT
        await s.commit()
    assert await _estado(sessionmaker_test, libro_id) == (5, [3])


async def test_registrar_movimiento_de_salida_guarda_el_venta_id(sessionmaker_test):
    from app.modules.clientes.models import Cliente
    from app.modules.libros.repository import LibroRepository
    from app.modules.ventas.models import Venta

    libro_id, usuario_id = await _preparar(sessionmaker_test, stock=6)
    async with sessionmaker_test() as s:
        cliente = Cliente(nombre="Cli", email="cli@example.com")
        s.add(cliente)
        await s.flush()
        venta = Venta(cliente_id=cliente.id, fecha=datetime.now(UTC), total=Decimal("20.00"))
        s.add(venta)
        await s.flush()
        resultado = await LibroRepository(s).registrar_movimiento(libro_id, -2, "Venta", usuario_id, venta_id=venta.id)
        assert resultado.stock == 4
        assert resultado.movimiento.venta_id == venta.id
        await s.commit()
    assert await _estado(sessionmaker_test, libro_id) == (4, [-2])


async def test_registrar_movimiento_no_confirma_el_rollback_lo_deshace_todo(sessionmaker_test):
    from app.modules.libros.repository import LibroRepository

    libro_id, usuario_id = await _preparar(sessionmaker_test, stock=2)
    async with sessionmaker_test() as s:
        await LibroRepository(s).registrar_movimiento(libro_id, 3, "Reposición", usuario_id)
        # Mientras la sesión no confirma, otra sesión no ve ni el cambio ni el movimiento.
        assert await _estado(sessionmaker_test, libro_id) == (2, [])
        await s.rollback()
    assert await _estado(sessionmaker_test, libro_id) == (2, [])


async def test_registrar_movimiento_no_llama_a_commit(sessionmaker_test):
    from app.modules.libros.repository import LibroRepository

    libro_id, usuario_id = await _preparar(sessionmaker_test, stock=2)
    async with sessionmaker_test() as s:
        llamadas = []
        commit_real = s.commit

        async def commit_espiado():
            llamadas.append(1)
            await commit_real()

        s.commit = commit_espiado
        await LibroRepository(s).registrar_movimiento(libro_id, 3, "Reposición", usuario_id)
        assert llamadas == []
        await s.rollback()


async def test_registrar_movimiento_con_cantidad_cero_lanza_value_error_sin_tocar_la_base(sessionmaker_test):
    from app.modules.libros.repository import LibroRepository

    libro_id, usuario_id = await _preparar(sessionmaker_test, stock=2)
    async with sessionmaker_test() as s:
        repo = LibroRepository(s)
        with _contar_sentencias(sessionmaker_test) as sentencias, pytest.raises(ValueError):
            await repo.registrar_movimiento(libro_id, 0, "Nada", usuario_id)
        assert sentencias == []
    assert await _estado(sessionmaker_test, libro_id) == (2, [])


@pytest.mark.parametrize("cantidad", [INT32_MAX + 1, -(INT32_MAX + 1)])
async def test_registrar_movimiento_fuera_de_int32_lanza_value_error_sin_tocar_la_base(sessionmaker_test, cantidad):
    from app.modules.libros.repository import LibroRepository

    libro_id, usuario_id = await _preparar(sessionmaker_test, stock=2)
    async with sessionmaker_test() as s:
        repo = LibroRepository(s)
        with _contar_sentencias(sessionmaker_test) as sentencias, pytest.raises(ValueError):
            await repo.registrar_movimiento(libro_id, cantidad, "Desborde", usuario_id)
        assert sentencias == []
    assert await _estado(sessionmaker_test, libro_id) == (2, [])


# ---- registrar_movimiento: rechazos (4.3) ----

async def test_registrar_movimiento_de_un_libro_inexistente_lanza_libro_no_encontrado(sessionmaker_test):
    from app.core.errors import Conflicto, LibroNoEncontrado
    from app.modules.libros.repository import LibroRepository

    _, usuario_id = await _preparar(sessionmaker_test)
    async with sessionmaker_test() as s:
        with pytest.raises(LibroNoEncontrado) as excinfo:
            await LibroRepository(s).registrar_movimiento(999999, 1, "Reposición", usuario_id)
    assert excinfo.value.libro_id == 999999
    assert not isinstance(excinfo.value, Conflicto)


async def test_registrar_movimiento_de_un_libro_dado_de_baja_lanza_libro_dado_de_baja(sessionmaker_test):
    from app.core.errors import LibroDadoDeBaja
    from app.modules.libros.repository import LibroRepository

    libro_id, usuario_id = await _preparar(sessionmaker_test, stock=2)
    async with sessionmaker_test() as s:
        await s.execute(text("UPDATE libro SET borrado_en = now() WHERE id = :i"), {"i": libro_id})
        await s.commit()
    async with sessionmaker_test() as s:
        with pytest.raises(LibroDadoDeBaja) as excinfo:
            await LibroRepository(s).registrar_movimiento(libro_id, 1, "Reposición", usuario_id)
    assert excinfo.value.mensaje == f"El libro {libro_id} está dado de baja."
    assert await _estado(sessionmaker_test, libro_id) == (2, [])


async def test_una_salida_mayor_al_stock_lanza_stock_insuficiente_con_el_stock_real(sessionmaker_test):
    from app.core.errors import StockInsuficiente
    from app.modules.libros.repository import LibroRepository

    libro_id, usuario_id = await _preparar(sessionmaker_test, stock=2)
    async with sessionmaker_test() as s:
        with pytest.raises(StockInsuficiente) as excinfo:
            await LibroRepository(s).registrar_movimiento(libro_id, -5, "Venta", usuario_id)
    assert excinfo.value.mensaje == f"Stock insuficiente para el libro {libro_id}: hay 2, se pidieron 5."
    assert (excinfo.value.disponible, excinfo.value.pedido) == (2, 5)
    assert await _estado(sessionmaker_test, libro_id) == (2, [])


async def test_una_salida_exacta_al_stock_deja_el_libro_en_cero(sessionmaker_test):
    from app.modules.libros.repository import LibroRepository

    libro_id, usuario_id = await _preparar(sessionmaker_test, stock=2)
    async with sessionmaker_test() as s:
        resultado = await LibroRepository(s).registrar_movimiento(libro_id, -2, "Venta", usuario_id)
        await s.commit()
    assert resultado.stock == 0
    assert await _estado(sessionmaker_test, libro_id) == (0, [-2])


async def test_una_entrada_que_pasa_el_maximo_de_int32_lanza_stock_excedido_y_no_un_error_de_base(sessionmaker_test):
    from app.core.errors import StockExcedido
    from app.modules.libros.repository import LibroRepository

    libro_id, usuario_id = await _preparar(sessionmaker_test, stock=INT32_MAX - 1)
    async with sessionmaker_test() as s:
        with pytest.raises(StockExcedido) as excinfo:
            await LibroRepository(s).registrar_movimiento(libro_id, 2, "Reposición", usuario_id)
    assert excinfo.value.mensaje == f"El stock del libro {libro_id} superaría el máximo permitido."
    assert await _estado(sessionmaker_test, libro_id) == (INT32_MAX - 1, [])


async def test_una_entrada_que_llega_justo_al_maximo_de_int32_es_valida(sessionmaker_test):
    from app.modules.libros.repository import LibroRepository

    libro_id, usuario_id = await _preparar(sessionmaker_test, stock=INT32_MAX - 1)
    async with sessionmaker_test() as s:
        resultado = await LibroRepository(s).registrar_movimiento(libro_id, 1, "Reposición", usuario_id)
        await s.commit()
    assert resultado.stock == INT32_MAX
    assert await _estado(sessionmaker_test, libro_id) == (INT32_MAX, [1])


async def test_el_mensaje_de_stock_insuficiente_usa_el_stock_de_la_base_y_no_el_de_la_sesion(sessionmaker_test):
    from app.core.errors import StockInsuficiente
    from app.modules.libros.models import Libro
    from app.modules.libros.repository import LibroRepository

    libro_id, usuario_id = await _preparar(sessionmaker_test, stock=2)
    async with sessionmaker_test() as a, sessionmaker_test() as b:
        assert (await a.get(Libro, libro_id)).stock == 2  # la sesión A tiene el libro cargado con stock 2
        await LibroRepository(b).registrar_movimiento(libro_id, -1, "Venta", usuario_id)
        await b.commit()  # la sesión B lo deja en 1
        with pytest.raises(StockInsuficiente) as excinfo:
            await LibroRepository(a).registrar_movimiento(libro_id, -5, "Venta", usuario_id)
    assert excinfo.value.mensaje == f"Stock insuficiente para el libro {libro_id}: hay 1, se pidieron 5."


# ---- registrar_movimiento: sincroniza el Libro ya cargado en la sesión (4.5) ----

async def test_el_libro_ya_cargado_en_la_sesion_muestra_el_stock_nuevo_sin_consultar(sessionmaker_test):
    from app.modules.libros.models import Libro
    from app.modules.libros.repository import LibroRepository

    libro_id, usuario_id = await _preparar(sessionmaker_test, stock=2)
    async with sessionmaker_test() as s:
        libro = await s.get(Libro, libro_id)
        assert libro.stock == 2
        resultado = await LibroRepository(s).registrar_movimiento(libro_id, 4, "Reposición", usuario_id)
        with _contar_sentencias(sessionmaker_test) as sentencias:
            assert libro.stock == 6  # sin MissingGreenlet: el atributo no quedó expirado
        assert sentencias == []
        assert libro.stock == resultado.stock
        await s.rollback()


async def test_el_libro_cargado_con_un_stock_viejo_queda_con_el_valor_de_la_base(sessionmaker_test):
    """Si otra sesión cambió el stock, evaluar `stock + 4` en Python sobre el valor en memoria daría 6."""
    from app.modules.libros.models import Libro
    from app.modules.libros.repository import LibroRepository

    libro_id, usuario_id = await _preparar(sessionmaker_test, stock=2)
    async with sessionmaker_test() as a, sessionmaker_test() as b:
        libro = await a.get(Libro, libro_id)  # A lo carga con stock 2
        await LibroRepository(b).registrar_movimiento(libro_id, -1, "Venta", usuario_id)
        await b.commit()  # B lo deja en 1
        resultado = await LibroRepository(a).registrar_movimiento(libro_id, 4, "Reposición", usuario_id)
        assert resultado.stock == 5
        with _contar_sentencias(sessionmaker_test) as sentencias:
            assert libro.stock == 5
        assert sentencias == []
        await a.rollback()


# ---- registrar_movimiento: concurrencia (4.7, caracterización) ----

async def test_dos_salidas_concurrentes_sobre_el_ultimo_ejemplar_dejan_una_sola_y_la_otra_es_insuficiente(
    sessionmaker_test,
):
    """El `UPDATE` condicionado bloquea la fila: la segunda espera, reevalúa con lo confirmado y se rechaza.

    Dos `DELETE` concurrentes del mismo libro devuelven ambos 204 (la baja es idempotente): aceptado.
    """
    import asyncio

    from app.core.errors import StockInsuficiente
    from app.modules.libros.repository import LibroRepository

    libro_id, usuario_id = await _preparar(sessionmaker_test, stock=1)
    async with sessionmaker_test() as a, sessionmaker_test() as b:
        await LibroRepository(a).registrar_movimiento(libro_id, -1, "Venta A", usuario_id)  # sin confirmar
        pid_b = (await b.execute(text("SELECT pg_backend_pid()"))).scalar_one()  # antes de usar B en la tarea
        tarea_b = asyncio.create_task(LibroRepository(b).registrar_movimiento(libro_id, -1, "Venta B", usuario_id))
        # B queda esperando el bloqueo de la fila que tiene A: se comprueba en el servidor, no por tiempo.
        async with sessionmaker_test() as observador:
            for _ in range(50):
                espera = (
                    await observador.execute(
                        text("SELECT wait_event_type FROM pg_stat_activity WHERE pid = :p"), {"p": pid_b}
                    )
                ).scalar_one_or_none()
                if espera == "Lock":
                    break
                await asyncio.sleep(0.1)
            else:
                pytest.fail("B nunca quedó esperando un bloqueo de fila (wait_event_type = 'Lock') en 5 s")
        assert not tarea_b.done(), "B no debería terminar mientras A no confirma"
        await a.commit()
        with pytest.raises(StockInsuficiente) as excinfo:
            await asyncio.wait_for(tarea_b, timeout=5)
        await b.rollback()
    assert excinfo.value.mensaje == f"Stock insuficiente para el libro {libro_id}: hay 0, se pidieron 1."
    assert await _estado(sessionmaker_test, libro_id) == (0, [-1])


# ---- lecturas de LibroRepository y MovimientoStockRepository (4.8) ----

async def _catalogo(sm):
    """Editorial, dos géneros, un autor y cuatro libros; devuelve los ids por clave."""
    from app.modules.autores.models import Autor
    from app.modules.editoriales.models import Editorial
    from app.modules.generos.models import Genero
    from app.modules.libros.models import Libro, LibroAutor

    async with sm() as s:
        editorial = Editorial(nombre="Eterna Cadencia", pais="AR")
        ficcion, ensayo = Genero(nombre="Ficción"), Genero(nombre="Ensayo")
        autor = Autor(nombre="Jorge Luis Borges", nacionalidad="Argentina")
        s.add_all([editorial, ficcion, ensayo, autor])
        await s.flush()
        titulos = [
            ("Ficciones", ficcion.id), ("100% ficción", ficcion.id), ("1000 años", ensayo.id), ("Otro ensayo", ensayo.id),
        ]
        libros = [
            Libro(isbn=f"ISBN-{i}", titulo=t, precio=Decimal("10.00"), stock=0, editorial_id=editorial.id, genero_id=g)
            for i, (t, g) in enumerate(titulos, start=1)
        ]
        s.add_all(libros)
        await s.flush()
        s.add(LibroAutor(libro_id=libros[0].id, autor_id=autor.id, rol="autor", orden=1))
        await s.commit()
        return {"ficciones": libros[0].id, "cien": libros[1].id, "mil": libros[2].id, "otro": libros[3].id,
                "ficcion": ficcion.id, "ensayo": ensayo.id}


async def test_get_detalle_trae_editorial_genero_y_autores_sin_consultas_extra(sessionmaker_test):
    from app.modules.libros.repository import LibroRepository

    ids = await _catalogo(sessionmaker_test)
    async with sessionmaker_test() as s:
        libro = await LibroRepository(s).get_detalle(ids["ficciones"])
        with _contar_sentencias(sessionmaker_test) as sentencias:
            assert libro.editorial.nombre == "Eterna Cadencia"
            assert libro.genero.nombre == "Ficción"
            assert [la.autor.nombre for la in libro.autorias] == ["Jorge Luis Borges"]
        assert sentencias == []


async def test_get_detalle_de_un_libro_dado_de_baja_o_inexistente_es_none(sessionmaker_test):
    from app.modules.libros.repository import LibroRepository

    ids = await _catalogo(sessionmaker_test)
    async with sessionmaker_test() as s:
        await s.execute(text("UPDATE libro SET borrado_en = now() WHERE id = :i"), {"i": ids["ficciones"]})
        await s.commit()
    async with sessionmaker_test() as s:
        repo = LibroRepository(s)
        assert await repo.get_detalle(ids["ficciones"]) is None
        assert await repo.get_detalle(999999) is None


@pytest.mark.parametrize(
    ("titulo", "esperados"),
    [
        ("FICC", ["ficciones", "cien"]),  # sin distinguir mayúsculas
        ("100%", ["cien"]),  # el % es literal: no es comodín (no trae «1000 años»)
        ("1000", ["mil"]),
        ("' OR '1'='1", []),  # parámetro ligado
        (None, ["ficciones", "cien", "mil", "otro"]),
        ("", ["ficciones", "cien", "mil", "otro"]),
    ],
)
async def test_buscar_y_contar_por_titulo(sessionmaker_test, titulo, esperados):
    from app.modules.libros.repository import LibroRepository

    ids = await _catalogo(sessionmaker_test)
    async with sessionmaker_test() as s:
        repo = LibroRepository(s)
        encontrados = await repo.buscar(titulo=titulo, genero_id=None, offset=0, limit=10)
        assert [l.id for l in encontrados] == [ids[k] for k in esperados]
        assert await repo.contar(titulo=titulo, genero_id=None) == len(esperados)


async def test_buscar_y_contar_por_genero_y_solo_vigentes_con_el_mismo_filtro(sessionmaker_test):
    from app.modules.libros.repository import LibroRepository

    ids = await _catalogo(sessionmaker_test)
    async with sessionmaker_test() as s:
        await s.execute(text("UPDATE libro SET borrado_en = now() WHERE id = :i"), {"i": ids["cien"]})
        await s.commit()
    async with sessionmaker_test() as s:
        repo = LibroRepository(s)
        pagina = await repo.buscar(titulo=None, genero_id=ids["ficcion"], offset=0, limit=1)
        assert [l.id for l in pagina] == [ids["ficciones"]]
        assert await repo.contar(titulo=None, genero_id=ids["ficcion"]) == 1  # el dado de baja no cuenta
        # `total` no depende del límite de la página: con limit=1 sigue contando todos los del filtro.
        pagina_ensayo = await repo.buscar(titulo=None, genero_id=ids["ensayo"], offset=1, limit=1)
        assert [l.id for l in pagina_ensayo] == [ids["otro"]]
        assert await repo.contar(titulo=None, genero_id=ids["ensayo"]) == 2


async def test_buscar_precarga_editorial_y_genero(sessionmaker_test):
    from app.modules.libros.repository import LibroRepository

    await _catalogo(sessionmaker_test)
    async with sessionmaker_test() as s:
        libros = await LibroRepository(s).buscar(titulo=None, genero_id=None, offset=0, limit=10)
        with _contar_sentencias(sessionmaker_test) as sentencias:
            assert {l.editorial.nombre for l in libros} == {"Eterna Cadencia"}
            assert {l.genero.nombre for l in libros} == {"Ficción", "Ensayo"}
        assert sentencias == []


async def test_el_conteo_no_arrastra_la_precarga_en_su_sql(sessionmaker_test):
    from app.modules.libros.repository import LibroRepository

    await _catalogo(sessionmaker_test)
    async with sessionmaker_test() as s:
        with _contar_sentencias(sessionmaker_test) as sentencias:
            await LibroRepository(s).contar(titulo="fic", genero_id=None)
        assert len(sentencias) == 1
        assert "JOIN" not in sentencias[0].upper()


async def test_listar_y_contar_los_movimientos_de_un_libro_en_orden_de_id(sessionmaker_test):
    from app.modules.libros.repository import LibroRepository, MovimientoStockRepository

    libro_id, usuario_id = await _preparar(sessionmaker_test, stock=0)
    otro_id, _ = await _preparar(sessionmaker_test, stock=0, isbn="ISBN-2")
    async with sessionmaker_test() as s:
        libros = LibroRepository(s)
        for cantidad in (4, 3, -2):
            await libros.registrar_movimiento(libro_id, cantidad, "m", usuario_id)
        await libros.registrar_movimiento(otro_id, 9, "m", usuario_id)  # de otro libro: no cuenta
        await s.commit()
    async with sessionmaker_test() as s:
        repo = MovimientoStockRepository(s)
        assert [m.cantidad for m in await repo.listar_de_libro(libro_id, offset=0, limit=10)] == [4, 3, -2]
        assert [m.cantidad for m in await repo.listar_de_libro(libro_id, offset=1, limit=1)] == [3]
        assert await repo.contar_de_libro(libro_id) == 3
        assert await repo.contar_de_libro(999999) == 0


# ---- LibrosUoW (5.1) ----

CLAVES_DE_LIBROS_HOY = {
    "uq_libro_isbn_vigente",
    "fk_libro_editorial_id_editorial",
    "fk_libro_genero_id_genero",
    "fk_libro_autor_autor_id_autor",
    "fk_libro_autor_libro_id_libro",
    "pk_libro_autor",
    "ck_libro_precio_positivo",
    "ck_libro_stock_no_negativo",
    "ck_libro_autor_orden_positivo",
    "ck_libro_autor_rol_valido",
}


async def test_libros_uow_compone_los_repositorios_con_la_misma_sesion(sessionmaker_test):
    from app.modules.libros.repository import LibroRepository, MovimientoStockRepository
    from app.modules.libros.unit_of_work import LibrosUoW

    async with sessionmaker_test() as s:
        uow = LibrosUoW(s)
        assert isinstance(uow.libros, LibroRepository)
        assert isinstance(uow.movimientos, MovimientoStockRepository)
        assert uow.libros.session is s and uow.movimientos.session is s


def test_libros_uow_tiene_las_diez_claves_de_hoy_mas_las_de_stock_con_textos_en_espanol():
    from app.modules.libros.unit_of_work import LibrosUoW

    assert CLAVES_DE_LIBROS_HOY <= set(LibrosUoW.MENSAJES)
    assert set(LibrosUoW.MENSAJES) - CLAVES_DE_LIBROS_HOY == {
        "movimiento_stock_solo_agregado",
        "fk_movimiento_stock_usuario_id_usuario",
    }
    assert LibrosUoW.MENSAJES["uq_libro_isbn_vigente"] == "Ya existe un libro con ese ISBN."
    assert LibrosUoW.MENSAJES["fk_movimiento_stock_usuario_id_usuario"] == "El usuario indicado no existe."
    assert all(m.endswith(".") for m in LibrosUoW.MENSAJES.values())


async def test_modificar_un_movimiento_confirmado_da_conflicto_con_mensaje_propio(sessionmaker_test):
    from app.core.errors import Conflicto
    from app.modules.libros.unit_of_work import LibrosUoW

    libro_id, usuario_id = await _preparar(sessionmaker_test, stock=0)
    async with sessionmaker_test() as s, LibrosUoW(s) as uow:
        resultado = await uow.libros.registrar_movimiento(libro_id, 3, "Reposición", usuario_id)
        movimiento_id = resultado.movimiento.id
    async with sessionmaker_test() as s:
        with pytest.raises(Conflicto) as excinfo:
            async with LibrosUoW(s) as uow:
                movimiento = await uow.movimientos.get_by_id(movimiento_id)
                movimiento.motivo = "Corregido"
                await uow.session.flush()
    assert excinfo.value.mensaje == (
        "Los movimientos de stock no se modifican ni se borran: un error se corrige con otro movimiento."
    )
    assert "movimiento_stock_solo_agregado" not in excinfo.value.mensaje


async def test_un_movimiento_con_usuario_inexistente_da_conflicto_con_mensaje_propio(sessionmaker_test):
    from app.core.errors import Conflicto
    from app.modules.libros.unit_of_work import LibrosUoW

    libro_id, _ = await _preparar(sessionmaker_test, stock=0)
    async with sessionmaker_test() as s:
        with pytest.raises(Conflicto) as excinfo:
            async with LibrosUoW(s) as uow:
                await uow.libros.registrar_movimiento(libro_id, 3, "Reposición", 999999)
    assert excinfo.value.mensaje == "El usuario indicado no existe."
    assert await _estado(sessionmaker_test, libro_id) == (0, [])  # el UoW revirtió el UPDATE también
