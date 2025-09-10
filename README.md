# Docling REST API Service

## ⚠️ IMPORTANTE: Este NO es Docling oficial

**[Docling de IBM](https://github.com/DS4SD/docling)** es una librería Python para procesamiento de documentos.

**Este proyecto** es un servicio REST API que envuelve Docling para poder usarlo desde aplicaciones web como tlegal.

### ¿Por qué este servicio?
- Docling es una librería Python, no un servicio web
- tlegal (y otras apps web) necesitan endpoints HTTP
- Este servicio actúa como puente entre Docling y aplicaciones web

## Características

- 🔍 **OCR Avanzado**: Extracción de texto usando Tesseract con múltiples idiomas
- 📄 **Análisis Estructurado**: Identificación de tablas, párrafos, encabezados y elementos
- 🎯 **Coordenadas Precisas**: Información de posición (bbox) para cada elemento
- ⚡ **API Asíncrona**: Procesamiento en segundo plano con seguimiento de progreso
- 🐳 **Docker Ready**: Despliegue fácil con Docker y Docker Compose
- 🔧 **Configurable**: Optimizaciones específicas para diferentes tipos de documentos

## Instalación y Configuración

### Prerrequisitos

- Docker Desktop
- 4GB+ RAM disponible
- 2GB+ espacio en disco

### 🚀 Instalación Súper Rápida (Recomendada)

**Opción 1: Docker con imagen pre-construida (Más rápido)**
```bash
# Descargar docker-compose simple
curl -O https://raw.githubusercontent.com/dmayab/docling-service/main/docker-compose.simple.yml

# Ejecutar el servicio
docker-compose -f docker-compose.simple.yml up -d

# Verificar que esté funcionando
curl http://localhost:8000/health
```

**Opción 2: Construcción local**
```bash
# Clonar el repositorio
git clone https://github.com/dmayab/docling-service.git
cd docling-service

# Construir y ejecutar
docker-compose up --build
```

### Imagen Docker Oficial

La imagen Docker está disponible en GitHub Container Registry:
```bash
docker pull ghcr.io/dmayab/docling-service:latest
```

**Uso directo con Docker:**
```bash
docker run -p 8000:8000 -d ghcr.io/dmayab/docling-service:latest
```

### Configuración Avanzada

#### Con Nginx (Recomendado para Producción)
```bash
# Incluir proxy Nginx
docker-compose --profile production up --build
```

#### Solo el servicio básico
```bash
# Solo FastAPI sin Nginx
docker-compose up docling-service
```

## Uso de la API

### Endpoint Principal: Procesar Documento

```bash
curl -X POST "http://localhost:8000/process" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@documento.pdf"
```

**Respuesta:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "accepted",
  "message": "Documento enviado para procesamiento"
}
```

### Consultar Progreso

```bash
curl http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000
```

**Respuesta (En progreso):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 75.0,
  "message": "Ejecutando OCR y extracción estructurada",
  "result": null
}
```

**Respuesta (Completado):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100.0,
  "message": "Procesamiento completado en 12.34s",
  "result": {
    "document_id": "doc-123",
    "pages": 5,
    "text_blocks": [
      {
        "page": 1,
        "text": "Contenido del párrafo",
        "type": "text",
        "confidence": 0.95,
        "bbox": {
          "x": 100,
          "y": 200,
          "width": 400,
          "height": 50
        }
      }
    ],
    "tables": [],
    "metadata": {
      "filename": "documento.pdf",
      "total_text_blocks": 150,
      "total_tables": 3
    },
    "ocr_confidence": 0.89
  }
}
```

## Integración con Frontend

### Configuración del Servicio

En tu aplicación React/TypeScript, configura la URL del servicio:

```typescript
// src/config/doclingConfig.ts
export const DOCLING_CONFIG = {
  serviceUrl: process.env.REACT_APP_DOCLING_URL || 'http://localhost:8000',
  timeout: 300000, // 5 minutos
  pollInterval: 2000 // 2 segundos
};
```

### Cliente TypeScript

```typescript
// src/services/doclingClient.ts
interface DoclingProcessingResult {
  task_id: string;
  document_id: string;
  status: string;
  pages: number;
  text_blocks: Array<{
    page: number;
    text: string;
    type: string;
    confidence: number;
    bbox?: {
      x: number;
      y: number;
      width: number;
      height: number;
    };
  }>;
  tables: Array<any>;
  metadata: Record<string, any>;
  ocr_confidence: number;
  processing_time: number;
}

class DoclingClient {
  constructor(private baseUrl: string) {}

  async processDocument(file: File): Promise<string> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/process`, {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    return result.task_id;
  }

  async getTaskStatus(taskId: string): Promise<{
    status: string;
    progress: number;
    result?: DoclingProcessingResult;
  }> {
    const response = await fetch(`${this.baseUrl}/status/${taskId}`);
    return await response.json();
  }

  async pollUntilComplete(taskId: string): Promise<DoclingProcessingResult> {
    while (true) {
      const status = await this.getTaskStatus(taskId);
      
      if (status.status === 'completed' && status.result) {
        return status.result;
      } else if (status.status === 'failed') {
        throw new Error('Document processing failed');
      }

      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
}

export const doclingClient = new DoclingClient(DOCLING_CONFIG.serviceUrl);
```

## Configuración Multi-Máquina

Para usar el servicio desde otra máquina:

1. **Configurar IP del host:**
```bash
# En la máquina servidor
docker-compose up --build
# El servicio estará disponible en http://IP_DEL_SERVIDOR:8000
```

2. **En la aplicación cliente:**
```typescript
// Configurar URL del servicio remoto
const DOCLING_CONFIG = {
  serviceUrl: 'http://192.168.1.100:8000', // IP del servidor
  // ... resto de configuración
};
```

3. **Configurar firewall (si es necesario):**
```bash
# macOS - permitir conexiones en puerto 8000
sudo pfctl -d  # Deshabilitar firewall temporalmente
# O configurar reglas específicas
```

## Monitoreo y Logs

### Ver logs en tiempo real:
```bash
docker-compose logs -f docling-service
```

### Estadísticas de contenedor:
```bash
docker stats tlegal-docling-service
```

### Health check manual:
```bash
curl http://localhost:8000/health
```

## Solución de Problemas

### Error de memoria insuficiente
```bash
# Incrementar límites de memoria
docker run --memory=4g --memory-swap=8g docling-service
```

### Error de permisos en macOS
```bash
# Dar permisos a Docker para archivos
xattr -d com.apple.quarantine docling-service/
```

### Puerto ocupado
```bash
# Cambiar puerto en docker-compose.yml
ports:
  - "8001:8000"  # Usar puerto 8001 en lugar de 8000
```

## Rendimiento

- **Documentos pequeños (< 10 páginas)**: ~5-15 segundos
- **Documentos medianos (10-50 páginas)**: ~15-60 segundos  
- **Documentos grandes (50+ páginas)**: ~1-5 minutos

## Desarrollo

### Ejecutar en modo desarrollo:
```bash
pip install -r requirements.txt
python app.py
```

### Tests:
```bash
pytest tests/
```

## Licencia

Este servicio utiliza [Docling](https://github.com/DS4SD/docling) bajo licencia MIT.