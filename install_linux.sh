#!/bin/bash

echo "========================================"
echo "  Instalador de Docling Service - Linux"
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
    echo "Instala Python con:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    echo "  Arch: sudo pacman -S python python-pip"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Python detectado: $(python3 --version)"
echo ""

# Verificar dependencias del sistema
echo "Verificando dependencias del sistema..."
if ! command -v tesseract &> /dev/null; then
    echo -e "${YELLOW}[ADVERTENCIA]${NC} Tesseract OCR no está instalado"
    echo "Instalando Tesseract..."
    
    # Detectar distribución
    if [ -f /etc/debian_version ]; then
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-spa
    elif [ -f /etc/redhat-release ]; then
        sudo dnf install -y tesseract tesseract-langpack-eng tesseract-langpack-spa
    elif [ -f /etc/arch-release ]; then
        sudo pacman -S --noconfirm tesseract tesseract-data-eng tesseract-data-spa
    fi
fi

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

# Detectar GPU NVIDIA
echo ""
echo "Detectando GPU..."

if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}[GPU NVIDIA detectada]${NC}"
    nvidia-smi
    echo ""
    echo "Instalando PyTorch con CUDA..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    
    # Verificar CUDA
    python3 -c "import torch; print(f'CUDA disponible: {torch.cuda.is_available()}')"
    if [ $? -eq 0 ]; then
        python3 -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}')"
    fi
else
    echo -e "${YELLOW}[Sin GPU NVIDIA]${NC} Instalando PyTorch para CPU..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Verificar instalación
echo ""
echo "Verificando instalación..."
python3 -c "import torch; print(f'PyTorch instalado: {torch.__version__}')"

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

# Crear servicio systemd opcional
read -p "¿Deseas crear un servicio systemd para inicio automático? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    sudo tee /etc/systemd/system/docling-service.service > /dev/null <<EOF
[Unit]
Description=Docling Document Processing Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/python $(pwd)/app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    echo -e "${GREEN}[OK]${NC} Servicio systemd creado"
    echo "Comandos útiles:"
    echo "  sudo systemctl start docling-service    # Iniciar"
    echo "  sudo systemctl enable docling-service   # Inicio automático"
    echo "  sudo systemctl status docling-service   # Ver estado"
fi