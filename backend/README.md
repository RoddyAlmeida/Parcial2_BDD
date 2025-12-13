# Backend - FastAPI Server

## Configuración

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Copia el archivo de ejemplo y configura tus credenciales:

```bash
cp env.example .env
```

Edita el archivo `.env` con tus credenciales:

```env
# Supabase - URL completa (reemplaza [YOUR-PASSWORD] con tu contraseña)
SUPABASE_DB_URL=postgresql://postgres.ywgbzwjkwkabcdhgmntg:Pandax701971497z34@aws-0-us-west-2.pooler.supabase.com:5432/postgres

# Upstash Redis
UPSTASH_REDIS_REST_URL=https://splendid-civet-13398.upstash.io
UPSTASH_REDIS_REST_TOKEN=ATRWAAIncDFkYzc3NWFiOWQ0YWY0YWMyODYwNjgwYjExNmI5MjBkN3AxMTMzOTg
```

**IMPORTANTE:** El archivo `.env` está en `.gitignore` y NO se subirá al repositorio. Las contraseñas están protegidas.

### 3. Ejecutar el servidor

```bash
python main.py
```

O con uvicorn directamente:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará disponible en: `http://localhost:8000`

## Endpoints Disponibles

### Health Check
- `GET /health` - Verificar estado de servicios

### Usuarios
- `GET /usuarios` - Listar usuarios (con paginación)
- `GET /usuarios/{usuario_id}` - Obtener usuario específico
- `POST /usuarios` - Crear nuevo usuario

### Tickets
- `GET /tickets` - Listar tickets (con paginación y filtros)
- `GET /tickets/{ticket_id}` - Obtener ticket específico
- `POST /tickets` - Crear nuevo ticket
- `PATCH /tickets/{ticket_id}/estado` - Actualizar estado de ticket

### Interacciones
- `GET /tickets/{ticket_id}/interacciones` - Obtener interacciones de un ticket
- `POST /interacciones` - Crear nueva interacción

## Documentación API

Una vez que el servidor esté corriendo, puedes acceder a:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Características

- ✅ Conexión segura a Supabase (PostgreSQL)
- ✅ Soporte para Upstash Redis (REST API) y Redis local
- ✅ Caché automático con TTL
- ✅ Colas Redis para Batch Worker
- ✅ Control de concurrencia con transacciones
- ✅ Variables de entorno protegidas
- ✅ Health checks

## Estructura

```
backend/
├── main.py              # Aplicación FastAPI principal
├── config.py            # Configuración y variables de entorno
├── redis_client.py      # Cliente Redis (Upstash y local)
├── requirements.txt     # Dependencias Python
├── env.example          # Ejemplo de configuración
└── README.md           # Este archivo
```

