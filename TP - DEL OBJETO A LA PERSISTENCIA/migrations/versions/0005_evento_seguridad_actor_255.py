"""evento_seguridad.actor a 255

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-05

Quinta migración (CHG-11, corrección de revisión), ESCRITA A MANO: ensancha `evento_seguridad.actor`
de VARCHAR(100) a VARCHAR(255).

Por qué existe: `actor` guarda el correo de quien hace el cambio (RN-16, p. ej. el cambio de
contraseña escribe `actor = email`) y `usuario.email` admite hasta 255 caracteres. Con 100, un correo
válido de 101 a 254 caracteres hacía fallar el INSERT del evento (StringDataRightTruncation) y
`POST /auth/cambiar-password` respondía 500. No se editó 0003 porque ya está mergeada.

Revisión: leída línea por línea antes de aplicarla. Es un solo `ALTER COLUMN ... TYPE` que ensancha
un VARCHAR: no reescribe la tabla ni pierde datos. Si se corrigió algo a mano respecto de lo que
generaría autogenerate: se escribió directamente, sin autogenerar.

Downgrade: vuelve a VARCHAR(100). Falla si ya hay un `actor` de más de 100 caracteres (Postgres no
trunca solo); aceptable en bases de desarrollo y de test.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005'
down_revision: Union[str, Sequence[str], None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'evento_seguridad', 'actor',
        existing_type=sa.String(length=100), type_=sa.String(length=255), existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'evento_seguridad', 'actor',
        existing_type=sa.String(length=255), type_=sa.String(length=100), existing_nullable=False,
    )
