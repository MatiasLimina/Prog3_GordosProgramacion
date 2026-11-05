"""solo agregado movimiento_stock

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-05 11:40:42.496324

Cuarta migración (CHG-08), ESCRITA A MANO: instala el disparador que hace de `movimiento_stock`
una tabla de sólo agregado (RN-12). Autogenerate no ve funciones ni disparadores, por eso no se
generó y por eso un `revision --autogenerate` futuro tampoco va a intentar borrarlos.

Revisión: leída línea por línea antes de aplicarla (design D3 del change migraciones-3-4).
Revisión de Nico: aprobada el 2026-11-05.

Qué hace:
- `movimiento_stock_solo_agregado()`: función PL/pgSQL que hace RAISE EXCEPTION con el texto
  «movimiento_stock es de sólo agregado: no se permite <UPDATE|DELETE> sobre el movimiento <id>. ...».
  - ERRCODE `restrict_violation` = SQLSTATE 23001, clase 23 (violación de integridad): asyncpg lo
    levanta como `IntegrityConstraintViolationError` y SQLAlchemy como `IntegrityError`, así que el
    UnitOfWork lo convierte en `Conflicto` (409) y nunca en 500 (RN-15). Con el P0001 por defecto de
    RAISE saldría un error interno.
  - CONSTRAINT `movimiento_stock_solo_agregado`: llena `constraint_name` del error para que
    `app/core/errors.py` elija el mensaje por nombre, como con cualquier UNIQUE o FK.
- `tg_movimiento_stock_solo_agregado`: BEFORE UPDATE OR DELETE ... FOR EACH ROW. Por fila, para poder
  nombrar la operación (TG_OP) y la fila (OLD.id).

TRUNCATE NO SE BLOQUEA A PROPÓSITO: un disparador por fila no corre con TRUNCATE, y el conftest de
los tests y el seed vacían todas las tablas con TRUNCATE. Consecuencia: el seed tiene que seguir
vaciando con TRUNCATE (con DELETE FROM movimiento_stock fallaría).

Sin `IF EXISTS` ni `OR REPLACE`: si la base no está en el estado esperado, la migración debe fallar
y no taparlo. Acciones referenciales: ninguna FK hacia/desde `movimiento_stock` usa CASCADE ni SET NULL
(lo comprueba un test), porque harían un DELETE/UPDATE que este disparador rechazaría.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Escrito a mano (autogenerate no ve funciones ni disparadores). Se ejecuta como un solo
    # statement; el $$ evita escapar las comillas simples del RAISE.
    op.execute(
        """
        CREATE FUNCTION movimiento_stock_solo_agregado() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'movimiento_stock es de sólo agregado: no se permite % sobre el movimiento %. Los errores se corrigen con un movimiento que compense.', TG_OP, OLD.id
                USING ERRCODE = 'restrict_violation',
                      CONSTRAINT = 'movimiento_stock_solo_agregado',
                      TABLE = 'movimiento_stock';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER tg_movimiento_stock_solo_agregado
        BEFORE UPDATE OR DELETE ON movimiento_stock
        FOR EACH ROW EXECUTE FUNCTION movimiento_stock_solo_agregado()
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Primero el disparador (depende de la función) y después la función. Sin IF EXISTS a propósito.
    op.execute("DROP TRIGGER tg_movimiento_stock_solo_agregado ON movimiento_stock")
    op.execute("DROP FUNCTION movimiento_stock_solo_agregado()")
