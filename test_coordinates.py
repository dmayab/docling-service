#!/usr/bin/env python3
"""
Script de prueba para verificar que la extracción de coordenadas con iterate_items funciona
"""
import requests
import time
import json

def test_coordinate_extraction():
    """Prueba la extracción de coordenadas con un documento de ejemplo"""
    
    print("🧪 === TEST DE EXTRACCIÓN DE COORDENADAS ===")
    
    # URL del servicio
    base_url = "http://localhost:8000"
    
    # 1. Health check
    print("🔍 1. Verificando salud del servicio...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Servicio activo: {health['service']} v{health['version']}")
            print(f"🖥️  Hardware: {health['hardware']['device']} ({health['hardware']['gpu_type']})")
        else:
            print(f"❌ Error en health check: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al servicio: {e}")
        return False
    
    # 2. Crear un documento de prueba simple
    print("📄 2. Creando documento de prueba...")
    test_content = """
Test Document for Coordinate Extraction

This is a simple test document to verify that Docling
can extract coordinates properly using the iterate_items() API.

We expect each paragraph to have:
- Real coordinates (not 0,0,100x100)
- Page numbers
- Proper bounding boxes

This should work correctly with the new implementation.
"""
    
    # Crear archivo temporal con contenido de prueba
    import tempfile
    import os
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    print("📝 Creando PDF de prueba con ReportLab...")
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        temp_pdf_path = tmp.name
    
    try:
        # Crear PDF con ReportLab
        c = canvas.Canvas(temp_pdf_path, pagesize=letter)
        width, height = letter
        
        # Añadir texto en diferentes posiciones para probar coordenadas
        c.setFont("Helvetica", 12)
        
        # Título
        c.drawString(100, height-100, "Test Document for Coordinate Extraction")
        
        # Párrafos en diferentes posiciones
        c.drawString(100, height-150, "This is paragraph 1 at position (100, 650)")
        c.drawString(150, height-200, "This is paragraph 2 at position (150, 600)")
        c.drawString(200, height-250, "This is paragraph 3 at position (200, 550)")
        
        # Texto en la segunda mitad de la página
        c.drawString(100, height-400, "Lower section paragraph at (100, 400)")
        c.drawString(300, height-450, "Right aligned text at (300, 350)")
        
        c.save()
        
        print(f"✅ PDF creado: {temp_pdf_path}")
        
        # 3. Procesar el documento
        print("🚀 3. Procesando documento...")
        
        with open(temp_pdf_path, 'rb') as f:
            files = {'file': ('test_coordinates.pdf', f, 'application/pdf')}
            response = requests.post(f"{base_url}/process", files=files, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                task_id = result['task_id']
                print(f"✅ Documento enviado para procesamiento: {task_id}")
                
                # 4. Esperar y verificar resultados
                print("⏳ 4. Esperando resultados...")
                
                max_wait = 60  # 60 segundos máximo
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    status_response = requests.get(f"{base_url}/status/{task_id}", timeout=10)
                    
                    if status_response.status_code == 200:
                        status = status_response.json()
                        print(f"📊 Progreso: {status['progress']:.1f}% - {status['message']}")
                        
                        if status['status'] == 'completed' and status.get('result'):
                            print("🎉 ¡Procesamiento completado!")
                            
                            # 5. Analizar coordenadas extraídas
                            print("🔍 5. Analizando coordenadas extraídas...")
                            result = status['result']
                            text_blocks = result['text_blocks']
                            
                            print(f"📄 Total de páginas: {result['pages']}")
                            print(f"📝 Total de bloques de texto: {len(text_blocks)}")
                            print(f"🎯 Confianza OCR: {result['ocr_confidence']:.2f}")
                            print(f"⏱️  Tiempo de procesamiento: {result['processing_time']:.2f}s")
                            
                            # Verificar coordenadas
                            real_coordinates_count = 0
                            generic_coordinates_count = 0
                            
                            print("\n📐 === ANÁLISIS DE COORDENADAS ===")
                            
                            for i, block in enumerate(text_blocks, 1):
                                bbox = block.get('bbox', {})
                                x, y = bbox.get('x', 0), bbox.get('y', 0)
                                width, height = bbox.get('width', 0), bbox.get('height', 0)
                                
                                # Verificar si son coordenadas genéricas o reales
                                is_generic = (x == 0 and y == 0 and width in [100, 612] and height in [100, 792])
                                
                                if is_generic:
                                    generic_coordinates_count += 1
                                    coordinate_type = "❌ GENÉRICA"
                                else:
                                    real_coordinates_count += 1
                                    coordinate_type = "✅ REAL"
                                
                                print(f"Bloque {i}: {coordinate_type}")
                                print(f"  Página: {block.get('page', 'N/A')}")
                                print(f"  Tipo: {block.get('type', 'N/A')}")
                                print(f"  Posición: ({x}, {y}) | Tamaño: {width}x{height}")
                                print(f"  Texto: {block.get('text', '')[:60]}...")
                                print()
                            
                            # Resultado final
                            print("🏁 === RESULTADO FINAL ===")
                            print(f"✅ Coordenadas reales: {real_coordinates_count}")
                            print(f"❌ Coordenadas genéricas: {generic_coordinates_count}")
                            
                            if real_coordinates_count > 0:
                                print("🎉 ¡ÉXITO! El servicio está extrayendo coordenadas reales")
                                return True
                            else:
                                print("⚠️  ADVERTENCIA: Solo coordenadas genéricas encontradas")
                                return False
                        
                        elif status['status'] == 'failed':
                            print(f"❌ Error en procesamiento: {status['message']}")
                            return False
                    
                    time.sleep(2)
                
                print("⏰ Timeout esperando resultados")
                return False
            
            else:
                print(f"❌ Error enviando documento: {response.status_code}")
                print(response.text)
                return False
    
    finally:
        # Limpiar archivo temporal
        try:
            os.unlink(temp_pdf_path)
            print(f"🗑️ Archivo temporal limpiado: {temp_pdf_path}")
        except:
            pass

if __name__ == "__main__":
    success = test_coordinate_extraction()
    exit(0 if success else 1)