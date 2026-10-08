FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema para compilar paquetes nativos y pdfplumber
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Instalar torch CPU-only antes del resto para evitar que pip descargue
# la variante CUDA (532 MB) y sus dependencias de cuda_toolkit inaccesibles.
RUN pip install --no-cache-dir torch==2.5.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt

# Modelo de embeddings dentro de la imagen: el servidor no lo descarga al arrancar.
# Misma carpeta que usa app/utils/embeddings.py (CACHE_DIR = /app/.model_cache);
# va antes de COPY para que un cambio en el código no obligue a descargarlo otra vez.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-mpnet-base-v2', cache_folder='/app/.model_cache')"

COPY . .

EXPOSE 8000

# Railway asigna el puerto en PORT; 8000 fuera de la plataforma.
# Sin registro de acceso: escribiría la IP de cada solicitud (ver app/core/registro.py).
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*' --no-access-log"]
