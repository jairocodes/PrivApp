"""corpus_chunks_active

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-30

Agrega corpus_chunks.active: indica si el fragmento participa en la
recuperación semántica. Se modifica por documento fuente completo; los
fragmentos existentes quedan activos.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQL directo (como 0002): corpus_chunks también puede venir de init.sql.
    op.execute("""
        ALTER TABLE corpus_chunks
            ADD COLUMN IF NOT EXISTS active BOOLEAN NOT NULL DEFAULT TRUE
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_corpus_documento_fuente
            ON corpus_chunks(documento_fuente)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_corpus_documento_fuente")
    op.execute("ALTER TABLE corpus_chunks DROP COLUMN IF EXISTS active")
