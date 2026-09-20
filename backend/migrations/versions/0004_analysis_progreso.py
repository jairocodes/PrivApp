"""analysis_progreso

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-21
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE analysis_temp
            ADD COLUMN IF NOT EXISTS seccion_actual INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS secciones_total INTEGER
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE analysis_temp
            DROP COLUMN IF EXISTS seccion_actual,
            DROP COLUMN IF EXISTS secciones_total
    """)
