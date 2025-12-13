#!/bin/bash
# Script de inicio para el backend

echo "🚀 Iniciando Backend FastAPI..."

# Verificar que existe .env
if [ ! -f .env ]; then
    echo "❌ Error: Archivo .env no encontrado"
    echo "📝 Copia env.example a .env y configura tus credenciales:"
    echo "   cp env.example .env"
    exit 1
fi

# Verificar dependencias
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Instalando dependencias..."
    pip install -r requirements.txt
fi

# Iniciar servidor
echo "✅ Iniciando servidor en http://localhost:8000"
python main.py

