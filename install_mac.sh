#!/bin/bash

echo "========================================"
echo "  Instalador de Docling Service - macOS"
echo "========================================"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Python 3 no está instalado"
    echo "Instala Python con: brew install python3"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Python detectado: $(python3 --version)"
echo ""

# Detectar arquitectura
ARCH=$(uname -m)
echo "Arquitectura detectada: $ARCH"

# Crear entorno virtual
echo "Creando entorno virtual..."
python3 -m venv venv

# Activar entorno
source venv/bin/activate

# Actualizar pip
echo "Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias base
echo "Instalando dependencias base..."
pip install -r requirements.txt

# Detectar tipo de Mac e instalar PyTorch apropiado
echo ""
echo "Configurando PyTorch..."

if [[ "$ARCH" == "arm64" ]]; then
    echo -e "${GREEN}[Apple Silicon detectado]${NC} Instalando PyTorch con soporte MPS (GPU)..."
    pip install torch torchvision torchaudio
    echo ""
    echo -e "${YELLOW}NOTA:${NC} Tu Mac con chip Apple Silicon puede usar GPU para acelerar el procesamiento"
    echo "El servicio detectará y usará automáticamente la GPU MPS"
else
    echo -e "${YELLOW}[Intel Mac detectado]${NC} Instalando PyTorch para CPU..."
    pip install torch torchvision torchaudio
fi

# Verificar instalación
echo ""
echo "Verificando instalación..."
python3 -c "import torch; print(f'PyTorch instalado: {torch.__version__}')"

if [[ "$ARCH" == "arm64" ]]; then
    python3 -c "import torch; print(f'GPU MPS disponible: {torch.backends.mps.is_available()}')"
fi

echo ""
echo "========================================"
echo -e "${GREEN}  ¡Instalación completada!${NC}"
echo "========================================"
echo ""
echo "Para iniciar el servicio:"
echo "  1. source venv/bin/activate"
echo "  2. python3 app.py"
echo ""
echo "El servicio estará disponible en:"
echo "  http://localhost:8000"
echo ""

# Preguntar si iniciar ahora
read -p "¿Deseas iniciar el servicio ahora? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo "Iniciando servicio..."
    python3 app.py
fi