"""Contratos de entrada y salida de auth/usuarios (sin base)."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.modules.usuarios.schemas import (
    AsignacionRolCreate,
    AuthYoRead,
    CambioPasswordCreate,
    LoginCreate,
    LoginRead,
    RegistroCreate,
    UsuarioCreate,
    UsuarioRead,
)


@pytest.mark.parametrize(
    ("schema", "datos"),
    [
        (RegistroCreate, {"email": "ana@example.com", "nombre": "Ana", "password": "secreto"}),
        (LoginCreate, {"email": "ana@example.com", "password": "secreto"}),
        (
            CambioPasswordCreate,
            {"password_actual": "secreto", "password_nueva": "nuevo"},
        ),
        (
            UsuarioCreate,
            {"email": "vendedor@example.com", "nombre": "Vendedor", "password": "temporal"},
        ),
        (AsignacionRolCreate, {"rol": "VENDEDOR", "vence_en": None}),
    ],
)
def test_todos_los_contratos_de_entrada_rechazan_campos_extra(schema, datos):
    with pytest.raises(ValidationError):
        schema(**datos, campo_desconocido="no permitido")


@pytest.mark.parametrize(
    ("schema", "datos", "campo"),
    [
        (RegistroCreate, {"email": "ana@example.com", "nombre": "Ana", "password": ""}, "password"),
        (LoginCreate, {"email": "ana@example.com", "password": ""}, "password"),
        (UsuarioCreate, {"email": "vendedor@example.com", "nombre": "Vendedor", "password": ""}, "password"),
        (
            CambioPasswordCreate,
            {"password_actual": "", "password_nueva": "nuevo"},
            "password_actual",
        ),
        (
            CambioPasswordCreate,
            {"password_actual": "actual", "password_nueva": ""},
            "password_nueva",
        ),
    ],
)
def test_cada_campo_que_llega_a_bcrypt_rechaza_mas_de_72_bytes(schema, datos, campo):
    datos[campo] = "a" + "ñ" * 36
    assert len(datos[campo].encode("utf-8")) == 73
    with pytest.raises(ValidationError, match="72 bytes"):
        schema(**datos)


@pytest.mark.parametrize(
    ("schema", "datos", "campo"),
    [
        (RegistroCreate, {"email": "ana@example.com", "nombre": "Ana", "password": "ñ" * 36}, "password"),
        (LoginCreate, {"email": "ana@example.com", "password": "ñ" * 36}, "password"),
        (UsuarioCreate, {"email": "vendedor@example.com", "nombre": "Vendedor", "password": "ñ" * 36}, "password"),
        (
            CambioPasswordCreate,
            {"password_actual": "ñ" * 36, "password_nueva": "ñ" * 36},
            "password_actual",
        ),
        (
            CambioPasswordCreate,
            {"password_actual": "actual", "password_nueva": "ñ" * 36},
            "password_nueva",
        ),
    ],
)
def test_cada_campo_de_contrasena_acepta_hasta_72_bytes(schema, datos, campo):
    assert len(datos[campo].encode("utf-8")) == 72
    schema(**datos)


def test_asignacion_rol_acepta_vencimiento_con_zona_y_futuro():
    vence_en = datetime.now(timezone.utc) + timedelta(days=1)
    asignacion = AsignacionRolCreate(rol="VENDEDOR", vence_en=vence_en)
    assert asignacion.vence_en == vence_en


def test_asignacion_rol_acepta_vencimiento_sin_limite():
    assert AsignacionRolCreate(rol="CLIENTE").vence_en is None


@pytest.mark.parametrize(
    "vence_en",
    [
        datetime.now() + timedelta(days=1),
        datetime.now(timezone.utc) - timedelta(seconds=1),
    ],
)
def test_asignacion_rol_rechaza_vencimiento_sin_zona_o_no_futuro(vence_en):
    with pytest.raises(ValidationError):
        AsignacionRolCreate(rol="VENDEDOR", vence_en=vence_en)


def test_schemas_de_salida_no_exponen_password_hash():
    usuario = UsuarioRead.model_validate(
        SimpleNamespace(
            id=1,
            email="ana@example.com",
            nombre="Ana",
            activo=True,
            debe_cambiar_password=False,
            password_hash="hash-interno",
        )
    )
    assert "password_hash" not in usuario.model_dump()

    respuesta = LoginRead(
        mensaje="Sesión iniciada",
        debe_cambiar_password=False,
        expira_en_segundos=900,
    )
    assert "token" not in respuesta.model_dump()

    yo = AuthYoRead(
        usuario=usuario,
        roles_vigentes=["CLIENTE"],
        roles_token=["CLIENTE"],
    )
    assert "password_hash" not in yo.model_dump()["usuario"]
