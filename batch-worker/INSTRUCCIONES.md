# Instrucciones de Configuración del Batch Worker

## Paso 1: Crear archivo .env

Copia el archivo de ejemplo:

```bash
cp env.example .env
```

## Paso 2: Configurar Supabase (Usuario Batch)

El Batch Worker usa un usuario diferente al API Server. Este usuario debe tener:
- Permisos SELECT en las tablas
- Permisos EXECUTE sobre procedimientos almacenados

Edita el archivo `.env`:

```env
DATABASE_URL_BATCH=postgresql://usuario_batch:password@host:5432/database
```

**Nota:** Asegúrate de que el usuario batch existe en tu base de datos y tiene los permisos correctos (ver `database/02_dcl_roles_permisos.sql`).

## Paso 3: Configurar Redis

Agrega tus credenciales de Redis (las mismas que el backend):

```env
REDIS_REST_URL=https://tu-redis.ejemplo.com
REDIS_REST_TOKEN=tu_token_aqui
```

## Paso 4: Instalar dependencias

```bash
pip install -r requirements.txt
```

## Paso 5: Ejecutar el Batch Worker

```bash
python main.py
```

El worker comenzará a escuchar en la cola `cola:batch:procesar` y procesará tareas automáticamente.

## Verificar que funciona

1. El worker debería mostrar: "✅ Conexión a Redis establecida"
2. Debería mostrar: "⏳ Esperando tareas..."
3. Para probar, envía una tarea desde el backend (crear un ticket)

## Solución de problemas

### Error: "Se requiere DATABASE_URL_BATCH"
- Verifica que el archivo `.env` existe
- Verifica que `DATABASE_URL_BATCH` está configurado correctamente

### Error: "permission denied for table"
- Verifica que el usuario batch tiene permisos SELECT
- Ejecuta los scripts SQL de permisos: `database/02_dcl_roles_permisos.sql`

### Error de conexión a Redis
- Verifica que `REDIS_REST_URL` y `REDIS_REST_TOKEN` están correctos
- Verifica tu conexión a internet

### El worker no recibe tareas
- Verifica que el backend está enviando tareas a la cola correcta
- Verifica que el nombre de la cola coincide: `cola:batch:procesar`





