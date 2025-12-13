-- ============================================
-- FASE 1.2: HARDENING Y GESTIÓN DE USUARIOS
-- Configuración de Roles y Permisos
-- ============================================

-- ============================================
-- CREACIÓN DE ROLES
-- ============================================

-- ROL API: Para el servidor FastAPI
-- Permisos: SELECT, INSERT, UPDATE (sin DELETE)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rol_api') THEN
        CREATE ROLE rol_api;
    END IF;
END
$$;

-- ROL BATCH: Para el proceso Batch Worker
-- Permisos: EXECUTE sobre procedimientos y SELECT en tablas
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rol_batch') THEN
        CREATE ROLE rol_batch;
    END IF;
END
$$;

-- ============================================
-- CREACIÓN DE USUARIOS
-- ============================================

-- Usuario para el API Server
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'usuario_api') THEN
        CREATE USER usuario_api WITH PASSWORD 'api_secure_password_2024!';
    END IF;
END
$$;

-- Usuario para el Batch Worker
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'usuario_batch') THEN
        CREATE USER usuario_batch WITH PASSWORD 'batch_secure_password_2024!';
    END IF;
END
$$;

-- ============================================
-- ASIGNACIÓN DE ROLES A USUARIOS
-- ============================================

GRANT rol_api TO usuario_api;
GRANT rol_batch TO usuario_batch;

-- ============================================
-- PERMISOS PARA ROL_API (API Server)
-- ============================================

-- Permisos SELECT en todas las tablas necesarias
GRANT SELECT ON usuarios TO rol_api;
GRANT SELECT ON tickets TO rol_api;
GRANT SELECT ON interacciones TO rol_api;

-- Permisos INSERT para crear nuevos registros
GRANT INSERT ON usuarios TO rol_api;
GRANT INSERT ON tickets TO rol_api;
GRANT INSERT ON interacciones TO rol_api;

-- Permisos UPDATE para modificar registros existentes
GRANT UPDATE ON usuarios TO rol_api;
GRANT UPDATE ON tickets TO rol_api;
GRANT UPDATE ON interacciones TO rol_api;

-- Permisos para usar las secuencias (necesario para INSERT con DEFAULT)
GRANT USAGE, SELECT ON SEQUENCE interacciones_id_seq TO rol_api;

-- DENY explícito de DELETE (seguridad adicional)
-- Nota: En PostgreSQL, si no se otorga el permiso, está denegado por defecto
-- Pero para documentación y claridad, usamos REVOKE
REVOKE DELETE ON usuarios FROM rol_api;
REVOKE DELETE ON tickets FROM rol_api;
REVOKE DELETE ON interacciones FROM rol_api;

-- ============================================
-- PERMISOS PARA ROL_BATCH (Batch Worker)
-- ============================================

-- Permisos SELECT en tablas necesarias para procesamiento
GRANT SELECT ON usuarios TO rol_batch;
GRANT SELECT ON tickets TO rol_batch;
GRANT SELECT ON interacciones TO rol_batch;

-- Permisos EXECUTE sobre procedimientos almacenados
-- (Se otorgará cuando se creen los procedimientos)
-- Ejemplo: GRANT EXECUTE ON FUNCTION procesar_tickets_vencidos() TO rol_batch;

-- Permiso para usar secuencias si es necesario
GRANT USAGE, SELECT ON SEQUENCE interacciones_id_seq TO rol_batch;

-- DENY de INSERT, UPDATE, DELETE (solo lectura y ejecución)
REVOKE INSERT ON usuarios FROM rol_batch;
REVOKE INSERT ON tickets FROM rol_batch;
REVOKE INSERT ON interacciones FROM rol_batch;

REVOKE UPDATE ON usuarios FROM rol_batch;
REVOKE UPDATE ON tickets FROM rol_batch;
REVOKE UPDATE ON interacciones FROM rol_batch;

REVOKE DELETE ON usuarios FROM rol_batch;
REVOKE DELETE ON tickets FROM rol_batch;
REVOKE DELETE ON interacciones FROM rol_batch;

-- ============================================
-- PROCEDIMIENTO ALMACENADO DE EJEMPLO
-- ============================================
-- Este procedimiento será ejecutado por el Batch Worker

CREATE OR REPLACE FUNCTION procesar_tickets_vencidos()
RETURNS TABLE (
    ticket_id UUID,
    dias_abierto INTEGER,
    estado_actual VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        EXTRACT(DAY FROM (CURRENT_TIMESTAMP - t.fecha_creacion))::INTEGER as dias_abierto,
        t.estado
    FROM tickets t
    WHERE t.estado IN ('abierto', 'en_proceso')
      AND t.fecha_creacion < CURRENT_TIMESTAMP - INTERVAL '7 days'
    ORDER BY t.fecha_creacion ASC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Otorgar permiso EXECUTE al rol_batch
GRANT EXECUTE ON FUNCTION procesar_tickets_vencidos() TO rol_batch;

COMMENT ON FUNCTION procesar_tickets_vencidos IS 'Procedimiento para identificar tickets vencidos (ejecutado por Batch Worker)';

-- ============================================
-- VERIFICACIÓN DE PERMISOS
-- ============================================
-- Scripts para verificar que los permisos están correctamente configurados

-- Ver roles y usuarios
-- SELECT rolname FROM pg_roles WHERE rolname IN ('rol_api', 'rol_batch', 'usuario_api', 'usuario_batch');

-- Ver permisos de rol_api
-- SELECT grantee, table_name, privilege_type 
-- FROM information_schema.role_table_grants 
-- WHERE grantee = 'rol_api';

-- Ver permisos de rol_batch
-- SELECT grantee, table_name, privilege_type 
-- FROM information_schema.role_table_grants 
-- WHERE grantee = 'rol_batch';

