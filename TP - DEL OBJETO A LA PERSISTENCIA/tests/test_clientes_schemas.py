"""Validaciones de los DTO de clientes (sin base)."""
import pytest
from pydantic import ValidationError

from app.modules.clientes.schemas import ClienteCreate, ClienteUpdate, PerfilCreate


def test_cliente_create_valido():
    c = ClienteCreate(nombre="Ana", email="ana@example.com")
    assert (c.nombre, c.email) == ("Ana", "ana@example.com")


@pytest.mark.parametrize("email", ["sin-arroba", "a@", "@b.com", "a b@c.com", ""])
def test_cliente_create_email_invalido(email):
    with pytest.raises(ValidationError):
        ClienteCreate(nombre="Ana", email=email)


@pytest.mark.parametrize("nombre", ["", "   "])
def test_cliente_create_nombre_vacio(nombre):
    with pytest.raises(ValidationError):
        ClienteCreate(nombre=nombre, email="ana@example.com")


def test_cliente_create_no_acepta_id():
    with pytest.raises(ValidationError):
        ClienteCreate(id=5, nombre="Ana", email="ana@example.com")


def test_cliente_update_vacio_es_valido_y_no_marca_campos():
    assert ClienteUpdate().model_dump(exclude_unset=True) == {}


def test_cliente_update_parcial_solo_marca_lo_enviado():
    assert ClienteUpdate(nombre="Nuevo").model_dump(exclude_unset=True) == {"nombre": "Nuevo"}


@pytest.mark.parametrize("campo", ["nombre", "email"])
def test_cliente_update_rechaza_null_explicito(campo):
    with pytest.raises(ValidationError):
        ClienteUpdate(**{campo: None})


def test_cliente_update_email_invalido():
    with pytest.raises(ValidationError):
        ClienteUpdate(email="no-es-email")


@pytest.mark.parametrize("campo", ["telefono", "direccion"])
def test_perfil_create_campos_obligatorios_no_vacios(campo):
    datos = {"telefono": "1122334455", "direccion": "Calle 1"}
    datos[campo] = " "
    with pytest.raises(ValidationError):
        PerfilCreate(**datos)


def test_perfil_create_valido():
    p = PerfilCreate(telefono="1122334455", direccion="Calle 1")
    assert p.telefono == "1122334455"
