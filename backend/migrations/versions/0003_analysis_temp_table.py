"""analysis_temp_table

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-18
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS analysis_temp (
            id           SERIAL PRIMARY KEY,
            user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            texto_original TEXT  NOT NULL,
            resultado    JSONB,
            estado       VARCHAR(20) NOT NULL DEFAULT 'pendiente',
            created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_analysis_temp_user_id
            ON analysis_temp(user_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_analysis_temp_estado
            ON analysis_temp(estado)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_analysis_temp_estado")
    op.execute("DROP INDEX IF EXISTS idx_analysis_temp_user_id")
    op.execute("DROP TABLE IF EXISTS analysis_temp")
