"""NoEncontrado y las excepciones de stock: excepciones de dominio que la app traduce a 404 / 409 (CHG-13, D4)."""
import httpx
import pytest
from fastapi import FastAPI

from app.core.errors import (
    ClienteNoEncontrado,
    Conflicto,
    CorreoConCuenta,
    LibroDadoDeBaja,
    LibroNoEncontrado,
    NoEncontrado,
    StockExcedido,
    StockInsuficiente,
)
from app.main import app as app_real
from app.main import registrar_handlers


def _app_de_prueba() -> FastAPI:
    app = FastAPI()
    registrar_handlers(app)

    @app.get("/no-encontrado")
    async def no_encontrado():
        raise NoEncontrado("La editorial no existe.")

    @app.get("/libro-no-encontrado")
    async def libro_no_encontrado():
        raise LibroNoEncontrado(3)

    @app.get("/cliente-no-encontrado")
    async def cliente_no_encontrado():
        raise ClienteNoEncontrado(7)

    @app.get("/correo-con-cuenta")
    async def correo_con_cuenta():
        raise CorreoConCuenta(3)

    @app.get("/stock-insuficiente")
    async def stock_insuficiente():
        raise StockInsuficiente(3, disponible=2, pedido=5)

    return app


async def _get(ruta: str) -> httpx.Response:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=_app_de_prueba()), base_url="http://test") as c:
        return await c.get(ruta)


def test_no_encontrado_guarda_el_mensaje():
    error = NoEncontrado("La editorial no existe.")
    assert isinstance(error, Exception)
    assert error.mensaje == "La editorial no existe."
    assert str(error) == "La editorial no existe."


def test_libro_no_encontrado_es_no_encontrado_y_no_es_conflicto():
    error = LibroNoEncontrado(3)
    assert isinstance(error, NoEncontrado)
    assert not isinstance(error, Conflicto)
    assert error.libro_id == 3
    assert error.mensaje == "El libro no existe."


def test_libro_dado_de_baja_es_conflicto_con_su_mensaje():
    error = LibroDadoDeBaja(3)
    assert isinstance(error, Conflicto)
    assert error.libro_id == 3
    assert error.mensaje == "El libro 3 está dado de baja."


def test_stock_insuficiente_es_conflicto_y_guarda_disponible_y_pedido():
    error = StockInsuficiente(3, disponible=2, pedido=5)
    assert isinstance(error, Conflicto)
    assert (error.libro_id, error.disponible, error.pedido) == (3, 2, 5)
    assert error.mensaje == "Stock insuficiente para el libro 3: hay 2, se pidieron 5."


def test_stock_excedido_es_conflicto_con_su_mensaje():
    error = StockExcedido(3)
    assert isinstance(error, Conflicto)
    assert error.libro_id == 3
    assert error.mensaje == "El stock del libro 3 superaría el máximo permitido."


def test_cliente_no_encontrado_es_no_encontrado_y_no_es_conflicto():
    error = ClienteNoEncontrado(7)
    assert isinstance(error, NoEncontrado)
    assert not isinstance(error, Conflicto)
    assert error.cliente_id == 7
    assert error.mensaje == "El cliente no existe."


def test_correo_con_cuenta_es_conflicto_con_su_mensaje():
    error = CorreoConCuenta(3)
    assert isinstance(error, Conflicto)
    assert not isinstance(error, NoEncontrado)
    assert error.cliente_id == 3
    assert error.mensaje == "El correo de un cliente con cuenta no se puede cambiar."


@pytest.mark.parametrize(
    ("ruta", "estado", "detalle"),
    [
        ("/no-encontrado", 404, "La editorial no existe."),
        ("/libro-no-encontrado", 404, "El libro no existe."),
        ("/cliente-no-encontrado", 404, "El cliente no existe."),
        ("/correo-con-cuenta", 409, "El correo de un cliente con cuenta no se puede cambiar."),
        ("/stock-insuficiente", 409, "Stock insuficiente para el libro 3: hay 2, se pidieron 5."),
    ],
)
async def test_la_app_las_responde_con_detail_y_sin_otras_claves(ruta, estado, detalle):
    r = await _get(ruta)
    assert r.status_code == estado
    assert r.json() == {"detail": detalle}


def test_la_app_real_tiene_registrado_el_handler_de_no_encontrado():
    assert NoEncontrado in app_real.exception_handlers


# ---- CHG-14: administración de usuarios y roles (design D8) ----

def test_usuario_no_encontrado_es_no_encontrado_y_no_es_conflicto():
    from app.core.errors import UsuarioNoEncontrado

    error = UsuarioNoEncontrado(7)
    assert isinstance(error, NoEncontrado)
    assert not isinstance(error, Conflicto)
    assert error.usuario_id == 7
    assert error.mensaje == "El usuario no existe."


def test_rol_no_vigente_es_no_encontrado_y_guarda_usuario_y_rol():
    from app.core.errors import RolNoVigente

    error = RolNoVigente(7, "VENDEDOR")
    assert isinstance(error, NoEncontrado)
    assert not isinstance(error, Conflicto)
    assert (error.usuario_id, error.rol) == (7, "VENDEDOR")
    assert error.mensaje == "El usuario no tiene ese rol vigente."


def test_autorrevocacion_de_admin_es_conflicto_y_no_es_sin_permiso():
    from app.core.errors import AutoRevocacionAdmin, SinPermiso

    error = AutoRevocacionAdmin()
    assert isinstance(error, Conflicto)
    assert not isinstance(error, SinPermiso)
    assert error.mensaje == "No podés revocarte tu propio rol de administrador."


def test_sin_administradores_es_conflicto_con_su_mensaje():
    from app.core.errors import SinAdministradores

    error = SinAdministradores()
    assert isinstance(error, Conflicto)
    assert error.mensaje == "No se puede revocar: el sistema quedaría sin administradores vigentes."


def test_admin_con_vencimiento_es_peticion_invalida_y_no_conflicto():
    from app.core.errors import AdminConVencimiento, PeticionInvalida

    error = AdminConVencimiento()
    assert isinstance(error, PeticionInvalida)
    assert not isinstance(error, Conflicto)
    assert error.mensaje == "El rol ADMIN no puede tener vencimiento."


@pytest.mark.parametrize(
    ("clase", "args", "estado", "detalle"),
    [
        ("UsuarioNoEncontrado", (7,), 404, "El usuario no existe."),
        ("RolNoVigente", (7, "VENDEDOR"), 404, "El usuario no tiene ese rol vigente."),
        ("AutoRevocacionAdmin", (), 409, "No podés revocarte tu propio rol de administrador."),
        (
            "SinAdministradores",
            (),
            409,
            "No se puede revocar: el sistema quedaría sin administradores vigentes.",
        ),
        ("AdminConVencimiento", (), 422, "El rol ADMIN no puede tener vencimiento."),
    ],
)
async def test_la_app_responde_las_excepciones_de_usuarios_con_detail(clase, args, estado, detalle):
    import app.core.errors as errores

    app = FastAPI()
    registrar_handlers(app)

    @app.get("/x")
    async def x():
        raise getattr(errores, clase)(*args)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/x")
    assert r.status_code == estado
    assert r.json() == {"detail": detalle}
