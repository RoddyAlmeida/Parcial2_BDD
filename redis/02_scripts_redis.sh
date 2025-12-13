#!/bin/bash
# Scripts de ejemplo para operaciones Redis
# FASE 2.2: Administración de Redis

# ============================================
# CONFIGURACIÓN
# ============================================
REDIS_HOST="localhost"
REDIS_PORT=6379
REDIS_CLI="redis-cli -h $REDIS_HOST -p $REDIS_PORT"

# ============================================
# FUNCIONES DE CACHÉ
# ============================================

# Almacenar datos de usuario con TTL
cache_usuario() {
    local usuario_id=$1
    local datos=$2
    local ttl=${3:-3600}  # Default 1 hora
    
    $REDIS_CLI SET "usuario:${usuario_id}:datos" "$datos" EX $ttl
    echo "Usuario $usuario_id almacenado en caché con TTL de $ttl segundos"
}

# Obtener datos de usuario
obtener_usuario_cache() {
    local usuario_id=$1
    $REDIS_CLI GET "usuario:${usuario_id}:datos"
}

# Almacenar ticket completo
cache_ticket() {
    local ticket_id=$1
    local datos=$2
    local ttl=${3:-900}  # Default 15 minutos
    
    $REDIS_CLI SET "ticket:${ticket_id}:completo" "$datos" EX $ttl
    echo "Ticket $ticket_id almacenado en caché con TTL de $ttl segundos"
}

# ============================================
# FUNCIONES DE COLAS
# ============================================

# Enviar tarea a la cola del Batch Worker
enviar_tarea_batch() {
    local tipo=$1
    local datos=$2
    local mensaje="{\"tipo\":\"$tipo\",\"datos\":$datos,\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
    
    $REDIS_CLI RPUSH "cola:batch:procesar" "$mensaje"
    echo "Tarea $tipo enviada a la cola"
    
    # Publicar notificación
    $REDIS_CLI PUBLISH "canal:batch:notificaciones" "{\"evento\":\"nueva_tarea\",\"tipo\":\"$tipo\"}"
}

# Ver estado de la cola
estado_cola() {
    local cola=${1:-"cola:batch:procesar"}
    local longitud=$($REDIS_CLI LLEN "$cola")
    echo "Cola: $cola"
    echo "Tareas pendientes: $longitud"
    
    if [ "$longitud" -gt 0 ]; then
        echo "Últimas 5 tareas:"
        $REDIS_CLI LRANGE "$cola" -5 -1
    fi
}

# ============================================
# MÉTRICAS Y MONITOREO
# ============================================

# Consultar métricas de memoria
metricas_memoria() {
    echo "=== MÉTRICAS DE MEMORIA ==="
    $REDIS_CLI INFO memory | grep -E "(used_memory_human|used_memory_peak_human|maxmemory_human|maxmemory_policy)"
    
    echo -e "\n=== ESTADÍSTICAS DETALLADAS ==="
    $REDIS_CLI MEMORY STATS
}

# Estadísticas generales
estadisticas_redis() {
    echo "=== ESTADÍSTICAS REDIS ==="
    $REDIS_CLI INFO stats | grep -E "(total_commands_processed|keyspace_hits|keyspace_misses|evicted_keys)"
    
    echo -e "\n=== TAMAÑO DE BASE DE DATOS ==="
    $REDIS_CLI DBSIZE
}

# ============================================
# LIMPIEZA Y MANTENIMIENTO
# ============================================

# Limpiar caché de usuario específico
limpiar_cache_usuario() {
    local usuario_id=$1
    $REDIS_CLI DEL "usuario:${usuario_id}:datos"
    echo "Caché del usuario $usuario_id eliminado"
}

# Limpiar todos los caches de un patrón
limpiar_cache_patron() {
    local patron=$1
    local claves=$($REDIS_CLI KEYS "$patron")
    
    if [ -n "$claves" ]; then
        echo "$claves" | xargs $REDIS_CLI DEL
        echo "Caché limpiado para patrón: $patron"
    else
        echo "No se encontraron claves con patrón: $patron"
    fi
}

# ============================================
# EJEMPLOS DE USO
# ============================================

# Ejemplo 1: Cachear usuario
# cache_usuario "123" '{"id":"123","nombre":"Juan","email":"juan@example.com"}' 3600

# Ejemplo 2: Enviar tarea al batch worker
# enviar_tarea_batch "procesar_ticket" '{"ticket_id":"789","accion":"cerrar"}'

# Ejemplo 3: Ver métricas
# metricas_memoria

# Ejemplo 4: Ver estado de cola
# estado_cola "cola:batch:procesar"

# ============================================
# MENÚ PRINCIPAL
# ============================================

case "$1" in
    cache-usuario)
        cache_usuario "$2" "$3" "$4"
        ;;
    obtener-usuario)
        obtener_usuario_cache "$2"
        ;;
    cache-ticket)
        cache_ticket "$2" "$3" "$4"
        ;;
    enviar-tarea)
        enviar_tarea_batch "$2" "$3"
        ;;
    estado-cola)
        estado_cola "$2"
        ;;
    metricas)
        metricas_memoria
        estadisticas_redis
        ;;
    limpiar-usuario)
        limpiar_cache_usuario "$2"
        ;;
    limpiar-patron)
        limpiar_cache_patron "$2"
        ;;
    *)
        echo "Uso: $0 {cache-usuario|obtener-usuario|cache-ticket|enviar-tarea|estado-cola|metricas|limpiar-usuario|limpiar-patron}"
        echo ""
        echo "Ejemplos:"
        echo "  $0 cache-usuario 123 '{\"id\":\"123\"}' 3600"
        echo "  $0 enviar-tarea procesar_ticket '{\"ticket_id\":\"789\"}'"
        echo "  $0 metricas"
        ;;
esac

