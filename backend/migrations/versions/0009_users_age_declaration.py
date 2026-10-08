"""users_age_declaration

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-30

Fecha en que la persona declaró, al registrarse, que es mayor de 18 años o que
cuenta con el consentimiento de su madre, padre o persona encargada (lo exige
el contrato de servicios de OpenAI para que menores usen sus servicios).
Admite nulos solo por las cuentas creadas antes de pedir la declaración; el
registro la exige a todas las cuentas nuevas.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("age_declaration_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "age_declaration_at")
