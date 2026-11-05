"""Modelos de usuarios, roles y seguridad: estructura, constraints y relaciones (sin base)."""

import pytest
from sqlalchemy import DateTime
from sqlalchemy.orm import configure_mappers
from sqlmodel import SQLModel

import app.models  # noqa: F401
from app.modules.usuarios.models import (
    AsignacionRol,
    EventoSeguridad,
    IntentoAcceso,
    Usuario,
)


def _constraints(modelo):
    return {c.name for c in modelo.__table__.constraints}


def _indices(modelo):
    return {i.name for i in modelo.__table__.indexes}


def test_modelos_registrados_en_metadata():
    tablas = SQLModel.metadata.tables
    for nombre in ("usuario", "asignacion_rol", "intento_acceso", "evento_seguridad"):
        assert nombre in tablas, f"Tabla {nombre} no registrada en metadata"


@pytest.mark.parametrize(
    "modelo,tabla,columnas",
    [
        (
            Usuario,
            "usuario",
            {"id", "email", "nombre", "password_hash", "activo", "debe_cambiar_password"},
        ),
        (
            AsignacionRol,
            "asignacion_rol",
            {"id", "usuario_id", "rol", "desde", "vence_en", "revocada_en", "otorgada_por"},
        ),
        (
            IntentoAcceso,
            "intento_acceso",
            {"id", "cuando", "email", "ip", "exito"},
        ),
        (
            EventoSeguridad,
            "evento_seguridad",
            {"id", "cuando", "actor", "accion"},
        ),
    ],
)
def test_tabla_y_columnas(modelo, tabla, columnas):
    t = modelo.__table__
    assert t.name == tabla
    assert set(t.c.keys()) == columnas
    assert t.primary_key.columns.keys() == ["id"]


def test_usuario_sin_columna_rol():
    assert "rol" not in Usuario.__table__.c


def test_usuario_columnas_no_nulas():
    t = Usuario.__table__
    for col in ("email", "nombre", "password_hash", "activo", "debe_cambiar_password"):
        assert not t.c[col].nullable, f"{col} en usuario no debería ser nulable"


def test_asignacion_rol_nulabilidades():
    t = AsignacionRol.__table__
    for col in ("usuario_id", "rol", "desde"):
        assert not t.c[col].nullable, f"{col} en asignacion_rol debe ser obligatorio"
    for col in ("vence_en", "revocada_en", "otorgada_por"):
        assert t.c[col].nullable, f"{col} en asignacion_rol debe ser nulable"


def test_fechas_con_zona_horaria_timestamptz():
    for modelo, col in [
        (AsignacionRol, "desde"),
        (AsignacionRol, "vence_en"),
        (AsignacionRol, "revocada_en"),
        (IntentoAcceso, "cuando"),
        (EventoSeguridad, "cuando"),
    ]:
        tipo = modelo.__table__.c[col].type
        assert isinstance(tipo, DateTime), f"{modelo.__name__}.{col} no es DateTime"
        assert tipo.timezone is True, f"{modelo.__name__}.{col} no tiene timezone=True (timestamptz)"


@pytest.mark.parametrize(
    "modelo,nombre",
    [
        (Usuario, "uq_usuario_email"),
        (AsignacionRol, "ck_asignacion_rol_rol_valido"),
        (AsignacionRol, "fk_asignacion_rol_usuario_id_usuario"),
        (AsignacionRol, "fk_asignacion_rol_otorgada_por_usuario"),
    ],
)
def test_constraints_con_nombre_de_la_convencion(modelo, nombre):
    assert nombre in _constraints(modelo)


def test_indices_asignacion_rol():
    indices = _indices(AsignacionRol)
    assert "ix_asignacion_rol_usuario_id" in indices
    assert "ix_asignacion_rol_otorgada_por" in indices
    assert "uq_asignacion_rol_usuario_rol_vigente" in indices


def test_indice_parcial_uq_asignacion_rol_usuario_rol_vigente():
    t = AsignacionRol.__table__
    idx = next(i for i in t.indexes if i.name == "uq_asignacion_rol_usuario_rol_vigente")
    assert idx.unique is True
    assert [c.name for c in idx.columns] == ["usuario_id", "rol"]
    where = idx.dialect_options.get("postgresql", {}).get("where")
    assert where is not None, "El índice no tiene postgresql_where"
    assert "revocada_en IS NULL" in str(where)


def test_indice_compuesto_intento_acceso():
    t = IntentoAcceso.__table__
    idx = next(i for i in t.indexes if i.name == "ix_intento_acceso_email_ip_cuando")
    assert [c.name for c in idx.columns] == ["email", "ip", "cuando"]


def test_unicos_sin_indice_redundante():
    # unique=True sin index=True: no debe haber ix_usuario_email
    assert "ix_usuario_email" not in _indices(Usuario)


def test_check_expresion_roles_validos():
    textos = {
        c.name: str(c.sqltext)
        for c in AsignacionRol.__table__.constraints
        if hasattr(c, "sqltext")
    }
    assert (
        textos["ck_asignacion_rol_rol_valido"]
        == "rol IN ('ADMIN', 'VENDEDOR', 'CLIENTE')"
    )


def test_relaciones_usuario_asignacion_rol():
    # Mappers deben configurarse limpiamente
    configure_mappers()
    rel_usuario = Usuario.__mapper__.relationships["asignaciones"]
    assert rel_usuario.target == AsignacionRol.__table__
    assert rel_usuario.back_populates == "usuario"

    rel_asignacion = AsignacionRol.__mapper__.relationships["usuario"]
    assert rel_asignacion.target == Usuario.__table__
    assert rel_asignacion.back_populates == "asignaciones"

    rel_otorgada = AsignacionRol.__mapper__.relationships["otorgada_por_usuario"]
    assert rel_otorgada.target == Usuario.__table__


def test_acuerdo_chg_07_usuario_sin_cliente_ni_movimientos_todavia():
    # Según acuerdo con Nico, CHG-06 sale sin cliente ni movimientos en Usuario
    # para no romper mappers antes de que CHG-07 defina Cliente.usuario y MovimientoStock.usuario.
    relaciones = Usuario.__mapper__.relationships.keys()
    assert "cliente" not in relaciones
    assert "movimientos" not in relaciones
