"""Script de carga del corpus normativo en la base de datos vectorial.

Implementación completa en Sprint 2. Este archivo define la interfaz esperada.

Uso:
    docker compose exec backend python scripts/cargar_corpus.py
    docker compose exec backend python scripts/cargar_corpus.py --limpiar
"""

# TODO Sprint 2: implementar carga completa del corpus
#
# Flujo esperado:
# 1. Recorrer recursivamente corpus_normativo/
# 2. Extraer texto de PDFs con pdfplumber/pypdf
# 3. Asignar metadatos según carpeta origen (guatemala/internacional/estandares_tecnicos)
# 4. Realizar chunking (300-500 palabras, 50 palabras de solapamiento)
# 5. Generar embeddings con paraphrase-multilingual-mpnet-base-v2
# 6. Insertar en corpus_chunks (idempotente: hash para deduplicación)
# 7. Reportar estadísticas al finalizar

if __name__ == "__main__":
    print("Carga del corpus normativo — implementación pendiente (Sprint 2).")
