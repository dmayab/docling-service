# Docling Service - Guía de Despliegue

## Descripción
Servicio REST API para procesamiento de documentos PDF con OCR usando Docling de IBM Research.

## Requisitos
- Docker y Docker Compose
- 4GB RAM mínimo
- 10GB espacio en disco (para modelos de ML)

## Instalación Rápida

### Opción 1: Docker (Recomendado)
```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/docling-service.git
cd docling-service

# Construir y ejecutar
docker-compose up -d

# Verificar que funciona
curl http://localhost:8000/health
```

### Opción 2: Instalación Local (Mac con GPU M1/M2/M3/M4)
```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias con soporte GPU para Mac
pip install -r requirements.txt
pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu

# Ejecutar
python app.py
```

## Configuración en el Cliente (tlegal)

En la aplicación tlegal, solo necesitas configurar la URL del servicio:

1. Ir a Configuración → Procesamiento Docling
2. Ingresar la URL del servicio (ej: `http://localhost:8000`)
3. Hacer clic en "Probar Conexión"
4. Guardar

## API Endpoints

### Health Check
```
GET /health
```

### Procesar Documento
```
POST /process
Content-Type: multipart/form-data
Body: file (PDF)

Response: { "task_id": "uuid" }
```

### Consultar Estado
```
GET /status/{task_id}

Response: {
  "status": "completed",
  "result": {
    "text_blocks": [...],
    "pages": 1,
    "ocr_confidence": 0.95
  }
}
```

## Rendimiento Esperado

- **Primera ejecución**: 2-3 minutos (descarga de modelos)
- **Procesamiento normal**: 10-30 segundos por PDF
- **Con GPU (M1/M2/M3/M4)**: 5-15 segundos por PDF

## Solución de Problemas

### Error: "I/O operation on closed file"
✅ Ya corregido en esta versión

### Error: "PyPdfiumDocumentBackend missing arguments"
✅ Ya corregido en esta versión

### Lentitud en procesamiento
- Verificar RAM disponible (mínimo 4GB)
- Para Mac con chip Apple: usar instalación local con GPU

## Notas para Desarrolladores

Este servicio es **completamente independiente** y puede ser usado por cualquier aplicación que necesite:
- Extraer texto de PDFs
- OCR automático
- Detección de tablas
- Coordenadas de texto para búsqueda visual

## Licencia
MIT