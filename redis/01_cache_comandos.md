# Redis: Comandos de Caché y Colas

## FASE 2.2: Administración de Redis como Caché y Queue

### 1. CACHEO DE DATOS

#### 1.1 Registrar datos del usuario con SET y TTL

```redis
# Almacenar información de usuario con TTL de 1 hora (3600 segundos)
SET usuario:123:datos '{"id":"123","nombre":"Juan Pérez","email":"juan@example.com","rol":"operador"}' EX 3600

# Almacenar con TTL de 30 minutos (1800 segundos)
SET usuario:456:datos '{"id":"456","nombre":"María García","email":"maria@example.com","rol":"usuario"}' EX 1800

# Almacenar ticket completo con TTL de 15 minutos
SET ticket:789:completo '{"id":"789","titulo":"Error en login","estado":"abierto","prioridad":"alta"}' EX 900

# Verificar TTL restante
TTL usuario:123:datos

# Obtener datos del usuario
GET usuario:123:datos

# Actualizar TTL sin modificar datos
EXPIRE usuario:123:datos 7200
```

#### 1.2 Consultar métricas de memoria

```redis
# Información general de memoria
INFO memory

# Estadísticas detalladas de memoria
MEMORY STATS

# Uso de memoria por clave (aproximado)
MEMORY USAGE usuario:123:datos

# Configuración de límites de memoria
CONFIG GET maxmemory
CONFIG GET maxmemory-policy

# Ver todas las claves (usar con precaución en producción)
KEYS *

# Contar claves por patrón
DBSIZE

# Estadísticas de comandos
INFO stats
```

#### 1.3 Operaciones avanzadas de caché

```redis
# SET con verificación de existencia (solo si no existe)
SET usuario:123:datos '{"id":"123"}' NX EX 3600

# SET con verificación de existencia (solo si existe)
SET usuario:123:datos '{"id":"123","actualizado":true}' XX EX 3600

# Incrementar contador con TTL
SET contador:tickets:abiertos 0 EX 3600
INCR contador:tickets:abiertos

# Hash para datos estructurados
HSET usuario:123 nombre "Juan Pérez" email "juan@example.com" rol "operador"
EXPIRE usuario:123 3600
HGETALL usuario:123

# Lista de tickets recientes
LPUSH tickets:recientes '{"id":"789","titulo":"Error"}'
LTRIM tickets:recientes 0 9  # Mantener solo los últimos 10
EXPIRE tickets:recientes 1800
```

### 2. COLAS PARA BATCH WORKER

#### 2.1 Enviar tarea al Batch Worker usando RPUSH

```redis
# Agregar tarea al final de la cola (FIFO)
RPUSH cola:batch:procesar '{"tipo":"procesar_ticket","ticket_id":"789","accion":"cerrar_vencidos"}'

# Agregar múltiples tareas
RPUSH cola:batch:procesar '{"tipo":"generar_reporte","fecha":"2024-01-15"}' '{"tipo":"limpiar_cache","tabla":"interacciones"}'

# Verificar longitud de la cola
LLEN cola:batch:procesar

# Ver elementos sin remover (últimos 5)
LRANGE cola:batch:procesar -5 -1
```

#### 2.2 Publicar evento usando PUBLISH (Pub/Sub)

```redis
# Publicar evento a un canal
PUBLISH canal:batch:eventos '{"evento":"ticket_actualizado","ticket_id":"789","timestamp":"2024-01-15T10:30:00Z"}'

# Publicar notificación de nueva tarea
PUBLISH canal:batch:notificaciones '{"mensaje":"nueva_tarea_disponible","cola":"cola:batch:procesar","timestamp":"2024-01-15T10:30:00Z"}'

# Suscribirse a un canal (desde otra conexión/cliente)
SUBSCRIBE canal:batch:eventos
SUBSCRIBE canal:batch:notificaciones

# Suscribirse a múltiples canales
PSUBSCRIBE canal:batch:*
```

#### 2.3 Procesamiento de colas por el Batch Worker

```redis
# El Batch Worker consume tareas con BLPOP (bloqueante)
# BLPOP cola:batch:procesar 10
# Espera hasta 10 segundos por una tarea, retorna cuando hay una disponible

# Procesar tarea con timeout
BLPOP cola:batch:procesar 30

# Procesar múltiples colas (prioridad)
BLPOP cola:batch:critica cola:batch:normal cola:batch:baja 60

# Marcar tarea como procesada (usando otra cola)
RPUSH cola:batch:procesadas '{"tarea":"...","procesada_en":"2024-01-15T10:30:00Z"}'
```

### 3. ESTRUCTURA RECOMENDADA DE CLAVES

```
usuario:{id}:datos          # Datos completos del usuario
usuario:{id}:tickets        # Lista de tickets del usuario
ticket:{id}:completo        # Ticket completo con relaciones
ticket:{id}:interacciones   # Cache de interacciones recientes
cache:estadisticas:global   # Estadísticas globales
cola:batch:procesar         # Cola principal de tareas
cola:batch:procesadas       # Historial de tareas procesadas
canal:batch:eventos         # Canal Pub/Sub para eventos
```

### 4. BENEFICIOS DE REDIS EN LA ARQUITECTURA

#### Reducción de carga sobre Supabase (Azure SQL Server):

1. **Caché de consultas frecuentes**:
   - Datos de usuario: Reduce SELECT en tabla usuarios
   - Tickets activos: Evita JOINs complejos repetitivos
   - Estadísticas: Agrega datos sin consultar tablas grandes

2. **Colas asíncronas**:
   - Procesamiento diferido: Batch Worker no bloquea API
   - Escalabilidad: Múltiples workers pueden consumir la misma cola
   - Resiliencia: Tareas persisten aunque el worker se reinicie

3. **Pub/Sub para notificaciones**:
   - Eventos en tiempo real sin polling
   - Desacoplamiento entre servicios
   - Escalabilidad horizontal

4. **Métricas y contadores**:
   - Contadores en tiempo real sin UPDATE en BD
   - Estadísticas agregadas sin GROUP BY costosos
   - Rate limiting y throttling

### 5. EJEMPLO DE FLUJO COMPLETO

```redis
# 1. API recibe request, verifica caché
GET usuario:123:datos

# 2. Si no existe, consulta BD y guarda en caché
SET usuario:123:datos '{"datos":"..."}' EX 3600

# 3. API crea ticket y envía tarea a cola
RPUSH cola:batch:procesar '{"tipo":"notificar_ticket_creado","ticket_id":"789"}'

# 4. Publica evento
PUBLISH canal:batch:eventos '{"evento":"ticket_creado","id":"789"}'

# 5. Batch Worker consume tarea
BLPOP cola:batch:procesar 30

# 6. Procesa y actualiza caché si es necesario
SET ticket:789:completo '{"datos":"actualizados"}' EX 1800
```

