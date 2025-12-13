-- ============================================
-- FASE 2.3: ESTRATEGIA DE RECUPERACIÓN
-- Plan de Backup y Recuperación Puntual
-- ============================================

-- ============================================
-- REQUISITO: RPO < 15 minutos
-- ============================================
-- RPO (Recovery Point Objective): Pérdida máxima de datos = 15 minutos
-- Esto requiere backups de logs transaccionales cada 15 minutos o menos

-- ============================================
-- ESTRATEGIA DE BACKUP MULTINIVEL
-- ============================================

/*
ESTRATEGIA PROPUESTA:

1. BACKUP COMPLETO (Full Backup)
   - Frecuencia: Diario a las 2:00 AM
   - Retención: 30 días
   - Ubicación: Almacenamiento redundante

2. BACKUP DIFERENCIAL (Differential Backup)
   - Frecuencia: Cada 6 horas (2:00, 8:00, 14:00, 20:00)
   - Retención: 7 días
   - Base: Último backup completo

3. BACKUP DE LOGS TRANSACCIONALES (Transaction Log Backup)
   - Frecuencia: Cada 10 minutos (para cumplir RPO < 15 min)
   - Retención: 24 horas
   - Crítico para recuperación puntual

VENTAJAS:
- Backup completo: Base sólida, recuperación completa
- Backup diferencial: Recuperación más rápida que solo completos
- Logs transaccionales: Permite recuperación a cualquier punto en el tiempo
*/

-- ============================================
-- CONFIGURACIÓN DE BASE DE DATOS PARA BACKUP
-- ============================================

-- En PostgreSQL/Supabase, habilitar WAL (Write-Ahead Logging)
-- Esto es necesario para backups de logs transaccionales

-- Verificar configuración de WAL
-- NOTA: Estos comandos SHOW solo funcionan en sesiones interactivas
-- En Supabase, esta configuración está gestionada por la plataforma
-- Ejecuta estos comandos solo si necesitas verificar la configuración actual

-- SHOW wal_level;
-- Debe ser 'replica' o 'logical' para backups continuos

-- Verificar archiving
-- SHOW archive_mode;
-- SHOW archive_command;

-- ============================================
-- SCRIPTS DE BACKUP COMPLETO
-- ============================================

/*
BACKUP COMPLETO usando pg_dump:

pg_dump -h [host] -U [usuario] -d [database] \
  -F c \
  -f backup_completo_$(date +%Y%m%d_%H%M%S).dump \
  -v

Programar con cron (diario a las 2:00 AM):
0 2 * * * /ruta/script/backup_completo.sh
*/

-- ============================================
-- SCRIPTS DE BACKUP DIFERENCIAL
-- ============================================

/*
BACKUP DIFERENCIAL usando pg_dump con opciones:

pg_dump -h [host] -U [usuario] -d [database] \
  -F c \
  -f backup_diferencial_$(date +%Y%m%d_%H%M%S).dump \
  --exclude-table-data=interacciones \
  -v

Nota: En PostgreSQL, los "diferenciales" se logran excluyendo
tablas grandes o usando herramientas de terceros.
Alternativa: Usar pg_basebackup con modo incremental.
*/

-- ============================================
-- BACKUP DE LOGS TRANSACCIONALES (WAL)
-- ============================================

/*
CONFIGURACIÓN PARA WAL ARCHIVING:

En postgresql.conf:
wal_level = replica
archive_mode = on
archive_command = 'cp %p /ruta/backups/wal/%f'

O para Supabase/cloud, usar herramientas nativas de backup continuo.

BACKUP DE WAL (cada 10 minutos):
- Los archivos WAL se archivan automáticamente según archive_command
- Script de verificación cada 10 minutos
*/

-- ============================================
-- PROCEDIMIENTO DE RECUPERACIÓN PUNTUAL
-- ============================================

/*
PASOS PARA RECUPERACIÓN A UN PUNTO ESPECÍFICO:

1. IDENTIFICAR EL PUNTO DE RECUPERACIÓN
   - Timestamp objetivo: 2024-01-15 14:23:00
   - Verificar backups disponibles

2. RESTAURAR BACKUP COMPLETO MÁS RECIENTE ANTES DEL PUNTO
   pg_restore -h [host] -U [usuario] -d [database] \
     backup_completo_20240115_020000.dump

3. RESTAURAR BACKUP DIFERENCIAL MÁS RECIENTE (si aplica)
   pg_restore -h [host] -U [usuario] -d [database] \
     backup_diferencial_20240115_140000.dump

4. APLICAR LOGS TRANSACCIONALES HASTA EL PUNTO OBJETIVO
   - Restaurar WAL files desde el último backup hasta el timestamp objetivo
   - PostgreSQL aplicará automáticamente los cambios

5. VERIFICAR INTEGRIDAD
   - Ejecutar DBCC CHECKDB (equivalente en PostgreSQL: VACUUM ANALYZE)
   - Verificar consistencia de datos
*/

-- ============================================
-- MANTENIMIENTO: RECONSTRUCCIÓN DE ÍNDICES
-- ============================================

-- Reconstruir un índice específico
REINDEX INDEX idx_interacciones_ticket_fecha;

-- Reconstruir todos los índices de una tabla
REINDEX TABLE interacciones;

-- Reconstruir todos los índices de la base de datos
-- REINDEX DATABASE nombre_base_datos;

-- Reconstruir con análisis de estadísticas
REINDEX INDEX CONCURRENTLY idx_interacciones_ticket_fecha;

COMMENT ON INDEX idx_interacciones_ticket_fecha IS 
'Índice reconstruido para optimizar consultas por ticket y fecha';

-- ============================================
-- MANTENIMIENTO: VERIFICACIÓN DE INTEGRIDAD
-- ============================================

-- En PostgreSQL, equivalente a DBCC CHECKDB:

-- Verificar integridad de una tabla
VACUUM ANALYZE interacciones;

-- Verificar integridad completa
VACUUM ANALYZE;

-- Verificar con opciones detalladas
VACUUM VERBOSE ANALYZE interacciones;

-- Verificar estructura de índices
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan;

-- ============================================
-- MANTENIMIENTO: ACTUALIZACIÓN DE ESTADÍSTICAS
-- ============================================

-- Actualizar estadísticas de una tabla
ANALYZE interacciones;

-- Actualizar estadísticas de todas las tablas
ANALYZE;

-- Actualizar con opciones
ANALYZE VERBOSE interacciones;

-- Ver estadísticas actuales
SELECT 
    schemaname,
    tablename,
    n_live_tup as live_tuples,
    n_dead_tup as dead_tuples,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;

-- ============================================
-- PLAN DE MANTENIMIENTO PROGRAMADO
-- ============================================

/*
TAREAS DE MANTENIMIENTO RECOMENDADAS:

DIARIO (2:00 AM):
- Backup completo
- VACUUM ANALYZE en tablas de alto volumen

CADA 6 HORAS:
- Backup diferencial
- Verificación de integridad de índices críticos

CADA 10 MINUTOS:
- Backup de logs transaccionales (WAL)

SEMANAL (Domingo 3:00 AM):
- REINDEX en índices fragmentados
- Análisis completo de estadísticas
- Verificación de espacio en disco

MENSUAL:
- Revisión de estrategia de backup
- Prueba de recuperación en ambiente de prueba
- Optimización de índices no utilizados
*/

-- ============================================
-- MONITOREO DE BACKUPS
-- ============================================

-- Verificar último backup (si se registra en tabla)
CREATE TABLE IF NOT EXISTS backup_log (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(20) NOT NULL, -- 'completo', 'diferencial', 'log'
    fecha_backup TIMESTAMP WITH TIME ZONE NOT NULL,
    archivo VARCHAR(255) NOT NULL,
    tamaño_bytes BIGINT,
    estado VARCHAR(20) NOT NULL, -- 'exitoso', 'fallido'
    observaciones TEXT
);

-- Insertar registro de backup
INSERT INTO backup_log (tipo, fecha_backup, archivo, tamaño_bytes, estado)
VALUES (
    'completo',
    CURRENT_TIMESTAMP,
    'backup_completo_20240115_020000.dump',
    1073741824, -- 1GB
    'exitoso'
);

-- Consultar historial de backups
SELECT 
    tipo,
    fecha_backup,
    archivo,
    pg_size_pretty(tamaño_bytes) as tamaño,
    estado
FROM backup_log
ORDER BY fecha_backup DESC
LIMIT 10;

-- ============================================
-- SCRIPT DE VERIFICACIÓN DE BACKUPS
-- ============================================

/*
Verificar que los backups estén actualizados:

1. Backup completo: Debe existir uno de las últimas 24 horas
2. Backup diferencial: Debe existir uno de las últimas 6 horas
3. Backup de log: Debe existir uno de los últimos 10 minutos

Si algún backup falta, generar alerta.
*/

