"""analysis_temp_text_hash

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-03

Agrega analysis_temp.text_hash: SHA-256 del texto analizado (normalizado), para
reutilizar el resultado de un texto idéntico analizado con la misma versión de
las instrucciones y del corpus. Los análisis existentes quedan con NULL.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE analysis_temp ADD COLUMN IF NOT EXISTS text_hash VARCHAR(64)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_analysis_temp_text_hash ON analysis_temp(text_hash)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_analysis_temp_text_hash")
    op.execute("ALTER TABLE analysis_temp DROP COLUMN IF EXISTS text_hash")
