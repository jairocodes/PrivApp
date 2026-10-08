"""busqueda_exacta_corpus

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-30

Elimina el índice aproximado ivfflat de corpus_chunks.embedding. El índice se
creaba con la tabla vacía, así que sus listas no representaban el corpus y la
búsqueda devolvía fragmentos menos relevantes que la búsqueda exacta. Con el
tamaño actual del corpus (cientos de fragmentos) la búsqueda exacta tarda
milisegundos. Si el corpus llegara a decenas de miles de fragmentos, conviene
crear un índice nuevo después de cargar los datos (ver downgrade).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_corpus_embedding")


def downgrade() -> None:
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_corpus_embedding
            ON corpus_chunks USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
    """)
