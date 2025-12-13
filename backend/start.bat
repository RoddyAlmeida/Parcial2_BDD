@echo off
REM Script de inicio para el backend (Windows)

echo Iniciando Backend FastAPI...

REM Verificar que existe .env
if not exist .env (
    echo Error: Archivo .env no encontrado
    echo Copia env.example a .env y configura tus credenciales:
    echo    copy env.example .env
    pause
    exit /b 1
)

REM Verificar dependencias
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Instalando dependencias...
    pip install -r requirements.txt
)

REM Iniciar servidor
echo Iniciando servidor en http://localhost:8000
python main.py

pause

