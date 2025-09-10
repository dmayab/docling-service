# Dockerfile para Docling Service
# Optimizado para Apple Silicon (M4) y compatible con x86_64
FROM python:3.11-slim-bookworm

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 docling && \
    mkdir -p /app/temp && \
    chown -R docling:docling /app

# Cambiar a usuario no-root
USER docling
WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY --chown=docling:docling requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Agregar directorio local de pip al PATH
ENV PATH="/home/docling/.local/bin:${PATH}"

# Copiar código de la aplicación
COPY --chown=docling:docling . .

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando para ejecutar la aplicación
CMD ["python", "app.py"]