"""
Servicio FastAPI para procesamiento de documentos con Docling
Optimizado para manejo de PDFs con OCR y extracción estructurada
"""

import os
import tempfile
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid
import logging
from task_cleanup import task_cleanup_manager

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiofiles
import uvicorn

from docling.document_converter import DocumentConverter

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Detectar plataforma y GPU
def detect_hardware():
    """Detecta el hardware disponible y configura el dispositivo óptimo"""
    import platform
    system = platform.system()
    machine = platform.machine()
    
    device_info = {
        "system": system,
        "machine": machine,
        "device": "cpu",
        "gpu_available": False,
        "gpu_type": None
    }
    
    try:
        import torch
        
        # Detectar CUDA (NVIDIA GPU)
        if torch.cuda.is_available():
            device_info["device"] = "cuda"
            device_info["gpu_available"] = True
            device_info["gpu_type"] = "NVIDIA CUDA"
            device_info["gpu_name"] = torch.cuda.get_device_name(0)
            logger.info(f"🎮 GPU NVIDIA detectada: {device_info['gpu_name']}")
        
        # Detectar MPS (Apple Silicon GPU)
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device_info["device"] = "mps"
            device_info["gpu_available"] = True
            device_info["gpu_type"] = "Apple Silicon"
            logger.info(f"🎮 GPU Apple Silicon detectada (M1/M2/M3/M4)")
            # Configurar para Apple Silicon
            os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
        
        # Detectar DirectML (Windows GPU)
        elif system == "Windows":
            try:
                import torch_directml
                device_info["device"] = "dml"
                device_info["gpu_available"] = True
                device_info["gpu_type"] = "DirectML (Windows)"
                logger.info(f"🎮 GPU Windows DirectML detectada")
            except ImportError:
                pass
    except ImportError:
        logger.warning("⚠️ PyTorch no instalado, usando CPU")
    
    if not device_info["gpu_available"]:
        logger.info(f"💻 Usando CPU en {system} {machine}")
    
    return device_info

# Detectar hardware al iniciar
HARDWARE_INFO = detect_hardware()

app = FastAPI(
    title="Docling Document Processing Service",
    description="Servicio de procesamiento de documentos usando Docling para OCR y extracción estructurada",
    version="1.0.0"
)

# Evento de startup para inicializar el worker de limpieza
@app.on_event("startup")
async def startup_event():
    """Inicializar workers en background al arrancar la aplicación"""
    logger.info("🚀 Iniciando worker de limpieza de tareas...")
    asyncio.create_task(task_cleanup_manager.start_cleanup_worker())

# Configurar CORS para permitir conexiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic para requests/responses
class ProcessingStatus(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: float
    message: str
    result: Optional[Dict[str, Any]] = None

class DocumentProcessingResult(BaseModel):
    task_id: str
    document_id: str
    status: str
    pages: int
    text_blocks: List[Dict[str, Any]]
    tables: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    ocr_confidence: float
    processing_time: float

# Almacén temporal de tareas en memoria
# En producción se podría usar Redis o una base de datos
processing_tasks: Dict[str, ProcessingStatus] = {}

# Configurar Docling
def get_document_converter() -> DocumentConverter:
    """Configura y retorna el convertidor de documentos Docling"""
    
    # Crear converter con configuración mínima por defecto
    # Docling manejará automáticamente la configuración del backend
    converter = DocumentConverter()
    
    return converter

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud con información del sistema"""
    return {
        "status": "healthy",
        "service": "Docling Document Processing",
        "version": "1.0.0",
        "hardware": {
            "system": HARDWARE_INFO["system"],
            "machine": HARDWARE_INFO["machine"],
            "gpu_available": HARDWARE_INFO["gpu_available"],
            "gpu_type": HARDWARE_INFO["gpu_type"],
            "device": HARDWARE_INFO["device"]
        }
    }

@app.get("/")
async def root():
    """Endpoint raíz con información del servicio"""
    return {
        "message": "Servicio Docling para procesamiento de documentos",
        "endpoints": {
            "health": "/health",
            "process": "/process",
            "status": "/status/{task_id}",
            "docs": "/docs"
        }
    }

@app.post("/process", response_model=Dict[str, str])
async def process_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Procesa un documento (PDF o DOCX) usando Docling
    Retorna inmediatamente un task_id para consultar el progreso
    """
    
    # Validar tipo de archivo
    supported_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"  # DOCX
    ]
    
    if not file.content_type or file.content_type not in supported_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de archivo no soportado: {file.content_type}. Se admiten: PDF y DOCX."
        )
    
    # Generar ID único para la tarea
    task_id = str(uuid.uuid4())
    
    # ¡SOLUCIÓN! Leer el contenido del archivo ANTES de enviarlo al background task
    try:
        file_content = await file.read()
        logger.info(f"📄 Archivo leído en endpoint: {len(file_content)} bytes para {file.filename}")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error leyendo archivo: {str(e)}"
        )
    
    # Crear registro de tarea
    processing_tasks[task_id] = ProcessingStatus(
        task_id=task_id,
        status="pending",
        progress=0.0,
        message="Documento en cola para procesamiento"
    )
    
    # Agregar tarea en segundo plano pasando el contenido, no el archivo
    background_tasks.add_task(
        process_document_background,
        task_id=task_id,
        file_content=file_content,
        filename=file.filename
    )
    
    logger.info(f"📄 Nueva tarea de procesamiento iniciada: {task_id}")
    
    return {
        "task_id": task_id,
        "status": "accepted",
        "message": "Documento enviado para procesamiento. Use /status/{task_id} para consultar progreso."
    }

@app.get("/status/{task_id}", response_model=ProcessingStatus)
async def get_processing_status(task_id: str):
    """Consulta el estado de procesamiento de un documento"""
    
    # Primero buscar en tareas activas
    if task_id in processing_tasks:
        return processing_tasks[task_id]
    
    # Si no está activa, buscar en tareas completadas retenidas
    completed_task = task_cleanup_manager.get_task(task_id)
    if completed_task:
        return completed_task
    
    # No encontrada en ningún sitio
    raise HTTPException(
        status_code=404,
        detail=f"Tarea {task_id} no encontrada o expirada"
    )

@app.delete("/status/{task_id}")
async def delete_processing_task(task_id: str):
    """Elimina una tarea completada del registro"""
    
    if task_id not in processing_tasks:
        raise HTTPException(
            status_code=404,
            detail=f"Tarea {task_id} no encontrada"
        )
    
    del processing_tasks[task_id]
    
    return {"message": f"Tarea {task_id} eliminada"}

async def process_document_background(task_id: str, file_content: bytes, filename: str):
    """
    Procesa un documento en segundo plano usando Docling
    """
    
    import time
    start_time = time.time()
    
    try:
        logger.info(f"🚀 Iniciando proceso en background para tarea: {task_id}")
        logger.info(f"📄 Archivo recibido: {filename}, tamaño: {len(file_content)} bytes")
        
        # Actualizar estado
        processing_tasks[task_id].status = "processing"
        processing_tasks[task_id].progress = 10.0
        processing_tasks[task_id].message = "Iniciando procesamiento con Docling"
        
        # El contenido ya está disponible como bytes
        content = file_content
        logger.info(f"📄 Contenido disponible: {len(content)} bytes")
        
        # Detectar tipo de archivo por extensión
        file_extension = os.path.splitext(filename)[1].lower()
        is_pdf = file_extension == '.pdf'
        is_docx = file_extension == '.docx'
        
        logger.info(f"📄 Tipo detectado: {'PDF' if is_pdf else 'DOCX' if is_docx else 'DESCONOCIDO'}")
        
        # Crear archivo temporal usando el método más directo
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_filename = f"docling_{task_id}_{filename}"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        logger.info(f"💾 Creando archivo temporal: {temp_path}")
        
        # Escribir archivo directamente usando open() tradicional
        with open(temp_path, 'wb') as temp_file:
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())  # Forzar sincronización
        
        logger.info(f"✅ Archivo temporal creado: {os.path.getsize(temp_path)} bytes")
        
        processing_tasks[task_id].progress = 30.0
        processing_tasks[task_id].message = "Archivo temporal creado, iniciando conversión"
        
        # Procesar con Docling
        converter = get_document_converter()
        
        processing_tasks[task_id].progress = 50.0
        processing_tasks[task_id].message = "Ejecutando OCR y extracción estructurada"
        
        # Convertir documento
        result = converter.convert(temp_path)
        
        processing_tasks[task_id].progress = 80.0
        processing_tasks[task_id].message = "Procesando resultados y extrayendo datos"
        
        # Extraer información estructurada usando la API correcta de Docling
        text_blocks = []
        
        # Verificar la estructura del resultado
        logger.info(f"📊 Tipo de resultado: {type(result)}")
        logger.info(f"🔍 DEBUG: Explorando estructura correcta de Docling")
        
        # Extraer bloques de texto con coordenadas reales usando iterate_items()
        try:
            # Acceder al documento Docling
            document = result.document
            logger.info(f"📄 Documento: {type(document)}")
            logger.info(f"📄 Número de páginas: {document.num_pages()}")
            
            # Usar la API correcta de Docling: iterate_items()
            element_count = 0
            total_elements = None
            
            # Para PDFs grandes, intentar obtener un conteo aproximado
            try:
                total_elements = len(list(document.iterate_items()))
                logger.info(f"📊 Total estimado de elementos: {total_elements}")
            except:
                logger.info(f"📊 No se pudo estimar total de elementos, usando progreso incremental")
            
            for item, level in document.iterate_items():
                element_count += 1
                
                # Actualizar progreso cada 10 elementos o cada 5% del total
                if total_elements and element_count % max(1, total_elements // 20) == 0:
                    progress_pct = 80.0 + (element_count / total_elements) * 15.0  # 80-95%
                    processing_tasks[task_id].progress = min(95.0, progress_pct)
                    processing_tasks[task_id].message = f"Procesando elementos: {element_count}/{total_elements}"
                elif element_count % 10 == 0:
                    # Fallback: progreso cada 10 elementos
                    progress_pct = 80.0 + min(15.0, (element_count / 100) * 15.0)
                    processing_tasks[task_id].progress = min(95.0, progress_pct)
                    processing_tasks[task_id].message = f"Procesando elementos: {element_count}"
                
                # Verificar si el elemento tiene texto
                item_text = ""
                if hasattr(item, 'text') and item.text:
                    item_text = item.text.strip()
                
                # Solo procesar elementos con texto válido
                if item_text and len(item_text) > 3:
                    # Verificar si el elemento tiene provenance (página y coordenadas)
                    if hasattr(item, 'prov') and len(item.prov) > 0:
                        # Obtener información de provenance (página y bbox)
                        prov = item.prov[0]  # Tomar la primera provenance
                        page_no = prov.page_no
                        bbox = prov.bbox
                        
                        # PDF: Coordenadas reales disponibles
                        if is_pdf and bbox:
                            text_blocks.append({
                                "page": page_no,
                                "text": item_text,
                                "type": item.label if hasattr(item, 'label') else "text",
                                "confidence": 1.0,  # Docling es muy confiable
                                "bbox": {
                                    "x": float(bbox.l),
                                    "y": float(bbox.t), 
                                    "width": float(bbox.r - bbox.l),
                                    "height": float(bbox.t - bbox.b)  # Docling usa coordenadas invertidas
                                }
                            })
                            
                            logger.info(f"✅ PDF Elemento extraído: Página {page_no}, Tipo: {item.label if hasattr(item, 'label') else 'text'}")
                            logger.info(f"   Coordenadas: ({bbox.l:.1f}, {bbox.t:.1f}) a ({bbox.r:.1f}, {bbox.b:.1f})")
                            logger.info(f"   Texto: {item_text[:60]}...")
                        
                        # DOCX: Sin coordenadas físicas, usar página lógica
                        elif is_docx:
                            text_blocks.append({
                                "page": page_no if page_no else 1,  # DOCX puede no tener página específica
                                "text": item_text,
                                "type": item.label if hasattr(item, 'label') else "text",
                                "confidence": 1.0,
                                "bbox": None  # DOCX no tiene coordenadas físicas
                            })
                            
                            logger.info(f"✅ DOCX Elemento extraído: Página {page_no if page_no else 1}, Tipo: {item.label if hasattr(item, 'label') else 'text'}")
                            logger.info(f"   Sin coordenadas (DOCX)")
                            logger.info(f"   Texto: {item_text[:60]}...")
                    
                    else:
                        # Elemento sin provenance - asumir página 1 para DOCX
                        if is_docx:
                            text_blocks.append({
                                "page": 1,
                                "text": item_text,
                                "type": item.label if hasattr(item, 'label') else "text",
                                "confidence": 1.0,
                                "bbox": None  # DOCX no tiene coordenadas físicas
                            })
                            
                            logger.info(f"✅ DOCX Elemento sin provenance: Tipo: {item.label if hasattr(item, 'label') else 'text'}")
                            logger.info(f"   Texto: {item_text[:60]}...")
                        else:
                            # PDF sin provenance - debug
                            logger.info(f"⚠️ PDF Elemento sin provenance: {item.label if hasattr(item, 'label') else 'unknown'} - {item_text[:40]}...")
            
            logger.info(f"📊 Procesamiento completado: {element_count} elementos totales, {len(text_blocks)} con coordenadas")
            
            # Si no se encontraron elementos con coordenadas válidas, usar respaldo
            if not text_blocks:
                logger.warning("⚠️ No se encontraron elementos con coordenadas válidas")
                # Obtener texto como respaldo, pero sin coordenadas específicas
                doc_text = document.export_to_markdown()
                logger.info(f"📄 Usando texto completo como respaldo: {len(doc_text)} caracteres")
                
                if doc_text and len(doc_text.strip()) > 0:
                    text_blocks.append({
                        "page": 1,
                        "text": doc_text,
                        "type": "document",
                        "confidence": 0.8,
                        "bbox": {
                            "x": 0,
                            "y": 0,
                            "width": 612,  # Tamaño estándar de página
                            "height": 792
                        }
                    })
                    
        except Exception as e:
            logger.error(f"❌ Error extrayendo elementos con coordenadas: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Método de respaldo final
            try:
                doc_text = result.document.export_to_markdown() if hasattr(result, 'document') else "Error extracting text"
                text_blocks.append({
                    "page": 1,
                    "text": doc_text[:1000],  # Limitar texto de respaldo
                    "type": "fallback",
                    "confidence": 0.5,
                    "bbox": {
                        "x": 0,
                        "y": 0,
                        "width": 100,
                        "height": 100
                    }
                })
            except Exception as fallback_error:
                logger.error(f"❌ Error en respaldo: {fallback_error}")
                text_blocks.append({
                    "page": 1,
                    "text": "Error processing document",
                    "type": "error",
                    "confidence": 0.0,
                    "bbox": {"x": 0, "y": 0, "width": 100, "height": 100}
                })
        
        # Extraer tablas (simplificado por ahora)
        tables = []
        # TODO: Implementar extracción de tablas cuando entendamos mejor la estructura de Docling
        
        # Calcular confianza promedio de OCR
        confidences = [block.get("confidence", 1.0) for block in text_blocks]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        processing_time = time.time() - start_time
        
        # Crear resultado final
        result_data = {
            "task_id": task_id,
            "document_id": str(uuid.uuid4()),
            "status": "completed",
            "pages": document.num_pages() if 'document' in locals() else len(set(block.get('page', 1) for block in text_blocks)),
            "text_blocks": text_blocks,
            "tables": tables,
            "metadata": {
                "filename": filename,
                "file_size": len(content),
                "total_text_blocks": len(text_blocks),
                "total_tables": len(tables),
            },
            "ocr_confidence": avg_confidence,
            "processing_time": processing_time
        }
        
        # Actualizar estado final
        processing_tasks[task_id].status = "completed"
        processing_tasks[task_id].progress = 100.0
        processing_tasks[task_id].message = f"Procesamiento completado en {processing_time:.2f}s"
        processing_tasks[task_id].result = result_data
        
        # Mover tarea completada al sistema de retención
        task_cleanup_manager.mark_for_cleanup(task_id, processing_tasks[task_id])
        logger.info(f"✅ Procesamiento completado para tarea {task_id}: {len(text_blocks)} bloques, {len(tables)} tablas")
        logger.info(f"📦 Tarea {task_id} movida al cache de retención (disponible por 5 min)")
        
    except Exception as e:
        # Manejar errores
        processing_tasks[task_id].status = "failed"
        processing_tasks[task_id].progress = 0.0
        processing_tasks[task_id].message = f"Error: {str(e)}"
        
        logger.error(f"❌ Error procesando tarea {task_id}: {str(e)}")
        
    finally:
        # Limpiar archivo temporal
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
                logger.info(f"🗑️ Archivo temporal limpiado: {temp_path}")
        except Exception as cleanup_error:
            logger.warning(f"⚠️ Error limpiando archivo temporal: {cleanup_error}")

if __name__ == "__main__":
    # Configuración para desarrollo
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )