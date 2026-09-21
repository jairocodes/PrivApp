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

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--proxy-headers", "--forwarded-allow-ips=*"]
