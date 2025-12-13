# Batch Worker - Procesamiento Asíncrono

El Batch Worker es un proceso independiente que consume tareas de una cola Redis y las procesa de forma asíncrona.

## Características

- ✅ Consume tareas de cola Redis (en la nube o local)
- ✅ Ejecuta procedimientos almacenados en la base de datos
- ✅ Procesa tickets vencidos
- ✅ Genera reportes de estadísticas
- ✅ Manejo de errores y reintentos
- ✅ Logging detallado

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

Edita el archivo `.env`:

```env
# Base de Datos - Usuario Batch (diferente al del API)
DATABASE_URL_BATCH=postgresql://usuario_batch:password@host:5432/postgres

# Redis (mismo que el backend)
REDIS_REST_URL=https://tu-redis.ejemplo.com
REDIS_REST_TOKEN=tu_token_aqui
```

**IMPORTANTE:** El usuario batch debe tener permisos EXECUTE sobre procedimientos almacenados.

## Ejecución

```bash
python main.py
```

El worker comenzará a escuchar en la cola `cola:batch:procesar` y procesará tareas automáticamente.

## Tipos de Tareas Soportadas

### 1. notificar_ticket_creado
Procesa notificaciones cuando se crea un nuevo ticket.

```json
{
  "tipo": "notificar_ticket_creado",
  "ticket_id": "uuid-del-ticket"
}
```

### 2. procesar_tickets_vencidos
Ejecuta el procedimiento almacenado para encontrar tickets vencidos.

```json
{
  "tipo": "procesar_tickets_vencidos"
}
```

### 3. generar_reporte
Genera un reporte de estadísticas para una fecha específica.

```json
{
  "tipo": "generar_reporte",
  "fecha": "2024-01-15"
}
```

### 4. limpiar_cache
Limpia claves específicas del caché.

```json
{
  "tipo": "limpiar_cache",
  "claves": ["ticket:123:completo", "usuario:456:datos"]
}
```

## Colas Redis

- **cola:batch:procesar**: Cola principal de tareas pendientes
- **cola:batch:procesadas**: Historial de tareas procesadas exitosamente
- **cola:batch:fallidas**: Tareas que fallaron durante el procesamiento

## Logs

El worker genera logs detallados de todas las operaciones:
- Tareas recibidas
- Tareas procesadas
- Errores y excepciones
- Estadísticas de procesamiento

## Notas sobre Redis REST API

Si usas Redis a través de REST API (servicios en la nube), ten en cuenta:
- No soporta `KEYS` directamente (usa estructuras de datos específicas)
- `BLPOP` se implementa con polling (cada 500ms)
- Todas las operaciones son HTTP requests

Para mejor rendimiento, considera usar Redis local en desarrollo y Redis en la nube en producción.





