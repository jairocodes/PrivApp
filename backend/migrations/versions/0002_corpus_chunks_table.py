"""corpus_chunks_table

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-18

Nota: la tabla también puede existir si el contenedor fue inicializado
con postgres/init.sql. Por eso se usa CREATE TABLE IF NOT EXISTS.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute("""
        CREATE TABLE IF NOT EXISTS corpus_chunks (
            id               SERIAL PRIMARY KEY,
            documento_fuente VARCHAR(255)             NOT NULL,
            jurisdiccion     VARCHAR(50)              NOT NULL,
            referencia       VARCHAR(255),
            categoria_tematica VARCHAR(100),
            texto_original   TEXT                     NOT NULL,
            embedding        vector(768)              NOT NULL,
            metadatos        JSONB,
            fecha_carga      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_corpus_embedding
            ON corpus_chunks USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_corpus_jurisdiccion
            ON corpus_chunks(jurisdiccion)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_corpus_categoria
            ON corpus_chunks(categoria_tematica)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_corpus_categoria")
    op.execute("DROP INDEX IF EXISTS idx_corpus_jurisdiccion")
    op.execute("DROP INDEX IF EXISTS idx_corpus_embedding")
    op.execute("DROP TABLE IF EXISTS corpus_chunks")
