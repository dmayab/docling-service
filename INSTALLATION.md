# 📦 Guía de Instalación Universal

## Instalación Rápida por Plataforma

### 🍎 macOS (Intel o Apple Silicon)
```bash
./install_mac.sh
```
- **Apple Silicon (M1/M2/M3/M4)**: Usará GPU automáticamente ⚡
- **Intel Mac**: Usará CPU optimizado

### 🪟 Windows
```batch
install_windows.bat
```
- **GPU NVIDIA**: Se detecta y configura automáticamente ⚡
- **GPU AMD/Intel**: Usa DirectML automáticamente
- **Sin GPU**: CPU optimizado

### 🐧 Linux
```bash
./install_linux.sh
```
- **GPU NVIDIA**: Se detecta con CUDA automáticamente ⚡
- **Sin GPU**: CPU optimizado

## 🐳 Docker (Cualquier plataforma)
```bash
docker-compose up -d
```
**Nota**: Docker usa CPU por defecto. Para GPU, usa instalación nativa.

## Verificar Instalación

Después de instalar, verifica el hardware detectado:
```bash
curl http://localhost:8000/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "hardware": {
    "system": "Darwin",       // o "Windows", "Linux"
    "gpu_available": true,    // true si hay GPU
    "gpu_type": "Apple Silicon", // tipo de GPU
    "device": "mps"          // "cuda", "mps", "dml", o "cpu"
  }
}
```

## Rendimiento Esperado

| Plataforma | GPU | Tiempo/PDF | Notas |
|------------|-----|------------|-------|
| Mac M1/M2/M3/M4 | ✅ MPS | 5-10s | GPU Apple Silicon |
| Windows NVIDIA | ✅ CUDA | 2-5s | Mejor rendimiento |
| Windows AMD/Intel | ✅ DirectML | 8-15s | GPU genérica |
| Linux NVIDIA | ✅ CUDA | 2-5s | Mejor rendimiento |
| Cualquiera | ❌ CPU | 20-30s | Sin aceleración |

## Solución de Problemas

### Error: "torch not found"
```bash
pip install torch torchvision
```

### Mac: "MPS backend not available"
Normal en Intel Macs. Usa CPU automáticamente.

### Windows: "CUDA not available"
Normal sin GPU NVIDIA. Usa DirectML o CPU automáticamente.

### Linux: "Tesseract not found"
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Fedora
sudo dnf install tesseract

# Arch
sudo pacman -S tesseract
```

## Configuración en tlegal

1. Abre tlegal
2. Ve a **Configuración → Procesamiento Docling**
3. Ingresa: `http://localhost:8000`
4. Click en **Probar Conexión**
5. Verifica que muestre tu hardware
6. **Guardar**

## Preguntas Frecuentes

**¿Necesito GPU?**
No, pero mejora el rendimiento 5-10x.

**¿Funciona en ARM/Raspberry Pi?**
Sí, pero lento (~60s por PDF).

**¿Puedo usar GPU en Docker?**
- Linux: Sí, con `--gpus all`
- Windows/Mac: No recomendado, usa instalación nativa

**¿Consume mucha RAM?**
- Mínimo: 2GB
- Recomendado: 4GB
- Con GPU: 2GB (la GPU maneja la carga)

## Soporte

- Issues: [GitHub Issues](https://github.com/tu-repo/docling-service/issues)
- Documentación: Este archivo
- Logs: `docker logs tlegal-docling-service` o consola Python