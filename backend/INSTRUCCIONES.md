# Instrucciones de Configuración del Backend

## Paso 1: Crear archivo .env

Copia el archivo de ejemplo:

```bash
cp env.example .env
```

## Paso 2: Configurar Supabase

Edita el archivo `.env` y reemplaza `[YOUR-PASSWORD]` con tu contraseña real:

```env
SUPABASE_DB_URL=postgresql://postgres.ywgbzwjkwkabcdhgmntg:Pandax701971497z34@aws-0-us-west-2.pooler.supabase.com:5432/postgres
```

**IMPORTANTE:** 
- El archivo `.env` NO se subirá al repositorio (está en `.gitignore`)
- NUNCA compartas tu contraseña públicamente
- Usa variables de entorno en producción

## Paso 3: Configurar Upstash Redis

Agrega tus credenciales de Upstash:

```env
UPSTASH_REDIS_REST_URL=https://splendid-civet-13398.upstash.io
UPSTASH_REDIS_REST_TOKEN=ATRWAAIncDFkYzc3NWFiOWQ0YWY0YWMyODYwNjgwYjExNmI5MjBkN3AxMTMzOTg
```

## Paso 4: Instalar dependencias

```bash
pip install -r requirements.txt
```

## Paso 5: Ejecutar el servidor

### Opción 1: Script de inicio (Windows)
```bash
start.bat
```

### Opción 2: Script de inicio (Linux/Mac)
```bash
chmod +x start.sh
./start.sh
```

### Opción 3: Manualmente
```bash
python main.py
```

## Verificar que funciona

1. El servidor debería iniciar en `http://localhost:8000`
2. Visita `http://localhost:8000/health` para verificar el estado
3. Visita `http://localhost:8000/docs` para ver la documentación de la API

## Solución de problemas

### Error: "Se requiere SUPABASE_DB_URL"
- Verifica que el archivo `.env` existe
- Verifica que `SUPABASE_DB_URL` está configurado correctamente

### Error de conexión a Redis
- Verifica que `UPSTASH_REDIS_REST_URL` y `UPSTASH_REDIS_REST_TOKEN` están correctos
- Verifica tu conexión a internet

### Error de conexión a Supabase
- Verifica que la contraseña en `SUPABASE_DB_URL` es correcta
- Verifica que tu IP está permitida en Supabase (si aplica)

