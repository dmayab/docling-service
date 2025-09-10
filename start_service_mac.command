#!/bin/bash
# Script de inicio fácil para macOS - hacer doble click para ejecutar

cd "$(dirname "$0")"

echo "🚀 Iniciando Docling Service..."
echo ""

# Verificar si el entorno virtual existe
if [ ! -d "venv" ]; then
    echo "⚠️ Entorno virtual no encontrado"
    echo "Ejecutando instalación..."
    ./install_mac.sh
fi

# Activar entorno y ejecutar
source venv/bin/activate
echo "✅ Servicio iniciando en http://localhost:8000"
echo ""
echo "Presiona Ctrl+C para detener"
echo ""
python3 app.py

# Mantener terminal abierta si se cierra el servicio
echo ""
echo "Servicio detenido. Presiona cualquier tecla para cerrar..."
read -n 1