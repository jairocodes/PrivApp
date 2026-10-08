"""users_email_minusculas

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-30

Pasa a minúsculas los correos guardados: desde ahora el registro y el inicio
de sesión los normalizan, así que una cuenta con mayúsculas ya no podría
iniciar sesión. Si dos cuentas solo se distinguen por mayúsculas, la
migración se detiene y las lista para resolverlas a mano (no se fusionan
cuentas automáticamente). La migración inversa no restaura las mayúsculas.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conexion = op.get_bind()
    repetidos = conexion.execute(sa.text(
        "SELECT lower(email) FROM users GROUP BY lower(email) HAVING count(*) > 1"
    )).scalars().all()
    if repetidos:
        raise RuntimeError(
            "Hay cuentas que solo se distinguen por mayúsculas en el correo: "
            + ", ".join(repetidos)
            + ". Resuélvalas antes de aplicar esta migración."
        )
    op.execute("UPDATE users SET email = lower(email) WHERE email <> lower(email)")


def downgrade() -> None:
    pass
