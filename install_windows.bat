@echo off
echo ========================================
echo   Instalador de Docling Service - Windows
echo ========================================
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado
    echo Por favor instala Python 3.9+ desde https://python.org
    pause
    exit /b 1
)

echo [OK] Python detectado
echo.

REM Crear entorno virtual
echo Creando entorno virtual...
python -m venv venv

REM Activar entorno
echo Activando entorno virtual...
call venv\Scripts\activate.bat

REM Actualizar pip
echo Actualizando pip...
python -m pip install --upgrade pip

REM Instalar dependencias base
echo Instalando dependencias base...
pip install -r requirements.txt

REM Detectar GPU NVIDIA
echo.
echo Detectando GPU...
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo [GPU NVIDIA DETECTADA] Instalando PyTorch con CUDA...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
) else (
    REM Intentar DirectML para GPUs AMD/Intel
    echo [CPU/GPU GENERICA] Instalando PyTorch con DirectML...
    pip install torch torchvision
    pip install torch-directml
)

echo.
echo ========================================
echo   Instalacion completada!
echo ========================================
echo.
echo Para iniciar el servicio:
echo   1. venv\Scripts\activate
echo   2. python app.py
echo.
echo El servicio estara disponible en:
echo   http://localhost:8000
echo.
pause