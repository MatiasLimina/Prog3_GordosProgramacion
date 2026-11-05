"""Modelo MovimientoStock: estructura, integridad y navegación (sin base)."""

import subprocess
import sys

import pytest
from sqlalchemy import DateTime
from sqlalchemy.orm import configure_mappers
from sqlmodel import SQLModel

import app.models  # noqa: F401
from app.modules.libros.models import Libro, MovimientoStock
from app.modules.ventas.models import Venta


def _constraints(modelo):
    return {c.name for c in modelo.__table__.constraints}


def _indices(modelo):
    return {i.name for i in modelo.__table__.indexes}


def test_movimiento_stock_registrado_en_metadata():
    assert "movimiento_stock" in SQLModel.metadata.tables


def test_columnas_exactas_y_unica_nullable_es_venta_id():
    t = MovimientoStock.__table__
    assert t.name == "movimiento_stock"
    assert set(t.c.keys()) == {"id", "libro_id", "venta_id", "usuario_id", "cantidad", "motivo", "cuando"}
    assert t.primary_key.columns.keys() == ["id"]
    assert {c.name for c in t.c if c.nullable} == {"venta_id"}


def test_cuando_es_timestamptz_con_default_del_servidor():
    cuando = MovimientoStock.__table__.c.cuando
    assert isinstance(cuando.type, DateTime)
    assert cuando.type.timezone is True
    assert "now()" in str(cuando.server_default.arg).lower()


def test_motivo_tiene_largo_255():
    assert MovimientoStock.__table__.c.motivo.type.length == 255


def test_cantidad_no_cero_con_nombre_y_texto():
    textos = {c.name: str(c.sqltext) for c in MovimientoStock.__table__.constraints if hasattr(c, "sqltext")}
    assert textos == {"ck_movimiento_stock_cantidad_no_cero": "cantidad <> 0"}


@pytest.mark.parametrize(
    "nombre,destino",
    [
        ("fk_movimiento_stock_libro_id_libro", "libro"),
        ("fk_movimiento_stock_venta_id_venta", "venta"),
        ("fk_movimiento_stock_usuario_id_usuario", "usuario"),
    ],
)
def test_claves_foraneas_con_nombre_sin_ondelete(nombre, destino):
    fks = {fk.name: fk for fk in MovimientoStock.__table__.foreign_key_constraints}
    assert nombre in fks
    assert fks[nombre].ondelete is None
    assert fks[nombre].elements[0].target_fullname == f"{destino}.id"


def test_indices_en_las_tres_claves_foraneas():
    assert _indices(MovimientoStock) == {
        "ix_movimiento_stock_libro_id",
        "ix_movimiento_stock_venta_id",
        "ix_movimiento_stock_usuario_id",
    }


def test_importar_solo_libros_models_define_el_check():
    codigo = (
        "import sys; sys.path.insert(0, '.')\n"
        "from app.modules.libros.models import MovimientoStock\n"
        "n = {c.name for c in MovimientoStock.__table__.constraints}\n"
        "assert 'ck_movimiento_stock_cantidad_no_cero' in n, n\n"
    )
    r = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, check=False)
    assert r.returncode == 0, r.stderr


@pytest.mark.parametrize(
    "lado_a,lado_b,destino",
    [
        (Libro.movimientos, "libro", MovimientoStock),
        (MovimientoStock.libro, "movimientos", Libro),
        (Venta.movimientos, "venta", MovimientoStock),
        (MovimientoStock.venta, "movimientos", Venta),
    ],
)
def test_back_populates_y_destino(lado_a, lado_b, destino):
    configure_mappers()
    assert lado_a.property.back_populates == lado_b
    assert lado_a.property.mapper.class_ is destino


@pytest.mark.parametrize("coleccion", [Libro.movimientos, Venta.movimientos])
def test_colecciones_no_borran_en_cascada_y_no_ponen_nulos(coleccion):
    configure_mappers()
    prop = coleccion.property
    assert prop.uselist is True
    assert prop.passive_deletes == "all"
    assert prop.cascade.delete is False


@pytest.mark.parametrize("lado", [MovimientoStock.libro, MovimientoStock.venta])
def test_lados_del_movimiento_son_a_uno(lado):
    configure_mappers()
    assert lado.property.uselist is False


def test_movimiento_usuario_y_usuario_movimientos_se_corresponden():
    from app.modules.usuarios.models import Usuario

    configure_mappers()
    rel_mov = MovimientoStock.__mapper__.relationships["usuario"]
    rel_usr = Usuario.__mapper__.relationships["movimientos"]
    assert rel_mov.back_populates == "movimientos"
    assert rel_usr.back_populates == "usuario"
    assert rel_mov.uselist is False
    assert rel_usr.uselist is True
    assert rel_usr.mapper.class_ is MovimientoStock
    assert rel_usr.passive_deletes == "all"
    assert "delete" not in rel_usr.cascade


def test_metadata_ordena_las_14_tablas_y_las_fk_a_usuario_resuelven():
    tablas = {t.name for t in SQLModel.metadata.sorted_tables}
    assert len(tablas) == 14
    assert {"usuario", "movimiento_stock", "cliente"} <= tablas
    for tabla, columna in (("cliente", "usuario_id"), ("movimiento_stock", "usuario_id")):
        fks = SQLModel.metadata.tables[tabla].c[columna].foreign_keys
        assert {fk.column.table.name for fk in fks} == {"usuario"}


# --- Guarda de acciones referenciales (RN-12: el disparador rechaza UPDATE y DELETE) ---


def _fk_incompatibles_con_solo_agregado(metadata):
    """FK cuya acción referencial haría que la base intente borrar o modificar movimientos.

    - Hacia movimiento_stock con ON DELETE CASCADE: borrar el padre dispararía un DELETE.
    - Desde movimiento_stock con ON DELETE CASCADE (DELETE) o SET NULL (UPDATE).
    """
    encontradas = []
    for tabla in metadata.tables.values():
        for fk in tabla.foreign_key_constraints:
            accion = (fk.ondelete or "").upper()
            hacia_movimiento = fk.referred_table.name == "movimiento_stock"
            desde_movimiento = tabla.name == "movimiento_stock"
            if hacia_movimiento and accion == "CASCADE":
                encontradas.append(fk.name)
            elif desde_movimiento and accion in ("CASCADE", "SET NULL"):
                encontradas.append(fk.name)
    return sorted(encontradas)


def _metadata_con_acciones_incompatibles():
    from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table

    md = MetaData()
    Table("movimiento_stock", md, Column("id", Integer, primary_key=True),
          Column("libro_id", Integer, ForeignKey("libro.id", ondelete="SET NULL", name="fk_ms_libro")),
          Column("venta_id", Integer, ForeignKey("venta.id", ondelete="CASCADE", name="fk_ms_venta")),
          Column("usuario_id", Integer, ForeignKey("usuario.id", ondelete="RESTRICT", name="fk_ms_usuario")))
    Table("libro", md, Column("id", Integer, primary_key=True))
    Table("venta", md, Column("id", Integer, primary_key=True))
    Table("usuario", md, Column("id", Integer, primary_key=True))
    Table("ajuste", md, Column("id", Integer, primary_key=True),
          Column("movimiento_id", Integer,
                 ForeignKey("movimiento_stock.id", ondelete="CASCADE", name="fk_ajuste_mov")))
    Table("nota", md, Column("id", Integer, primary_key=True),
          Column("movimiento_id", Integer,
                 ForeignKey("movimiento_stock.id", ondelete="RESTRICT", name="fk_nota_mov")))
    return md


def test_la_guarda_detecta_cascade_hacia_y_cascade_o_set_null_desde_movimiento_stock():
    assert _fk_incompatibles_con_solo_agregado(_metadata_con_acciones_incompatibles()) == [
        "fk_ajuste_mov",
        "fk_ms_libro",
        "fk_ms_venta",
    ]


def test_metadata_real_no_tiene_fk_incompatibles_con_el_solo_agregado():
    assert _fk_incompatibles_con_solo_agregado(SQLModel.metadata) == []
