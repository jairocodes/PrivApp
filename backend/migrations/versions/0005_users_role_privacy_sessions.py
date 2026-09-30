"""users_role_privacy_sessions

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-30

Agrega a users el rol, la fecha de aceptación del aviso de privacidad y la
fecha desde la que se aceptan los tokens del usuario (invalidación de todas
sus sesiones). privacy_accepted_at es obligatoria y no lleva valor por
defecto: si la tabla ya tuviera filas, la migración falla en lugar de
inventar una aceptación que no ocurrió.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(20), nullable=False, server_default="usuario"),
    )
    op.create_check_constraint(
        "ck_users_role", "users", "role IN ('usuario', 'administrador')"
    )
    op.add_column(
        "users",
        sa.Column("privacy_accepted_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("sessions_valid_from", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "sessions_valid_from")
    op.drop_column("users", "privacy_accepted_at")
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_column("users", "role")
