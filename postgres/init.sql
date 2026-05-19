-- Inicialización de la base de datos privapp_db
-- Este script se ejecuta automáticamente al crear el contenedor PostgreSQL.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Las tablas relacionales (users, sessions, analysis_temp) se crean
-- mediante migraciones de Alembic. Este script solo activa las extensiones
-- necesarias y crea la tabla vectorial del corpus, que no es gestionada
-- por el ORM sino por el script de carga del corpus.

CREATE TABLE IF NOT EXISTS corpus_chunks (
    id          SERIAL PRIMARY KEY,
    documento_fuente    VARCHAR(255)    NOT NULL,
    jurisdiccion        VARCHAR(50)     NOT NULL,
    referencia          VARCHAR(255),
    categoria_tematica  VARCHAR(100),
    texto_original      TEXT            NOT NULL,
    embedding           vector(768)     NOT NULL,
    metadatos           JSONB,
    fecha_carga         TIMESTAMP       DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_corpus_embedding
    ON corpus_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_corpus_jurisdiccion
    ON corpus_chunks(jurisdiccion);

CREATE INDEX IF NOT EXISTS idx_corpus_categoria
    ON corpus_chunks(categoria_tematica);
