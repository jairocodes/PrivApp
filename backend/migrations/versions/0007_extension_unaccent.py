"""extension_unaccent

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-30

Activa la extensión unaccent (contrib estándar de PostgreSQL) para que las
búsquedas por texto no distingan acentos. No modifica tablas ni datos.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS unaccent")
