#!/bin/bash
# Script para ejecutar Docling con GPU en Mac M1/M2/M3/M4

echo "🚀 Iniciando Docling con soporte GPU para Apple Silicon..."

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado"
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno
source venv/bin/activate

# Instalar dependencias
echo "📚 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# Instalar PyTorch con soporte Metal (GPU Apple)
echo "🎮 Instalando PyTorch con soporte GPU para Apple Silicon..."
pip install --upgrade torch torchvision torchaudio

# Verificar GPU
python3 -c "import torch; print(f'🎮 GPU disponible: {torch.backends.mps.is_available()}')"

# Ejecutar servicio
echo "✅ Iniciando servicio Docling con GPU..."
export PYTORCH_ENABLE_MPS_FALLBACK=1
python3 app.py