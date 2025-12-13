-- ============================================
-- DATOS DE EJEMPLO PARA PRUEBAS
-- ============================================
-- Este script crea datos de ejemplo para poder ejecutar
-- los scripts de transacciones (03_transacciones_concurrencia.sql)
-- ============================================

-- ============================================
-- CREAR USUARIOS DE EJEMPLO
-- ============================================

-- Usuario 1: Administrador
INSERT INTO usuarios (email, nombre, rol)
VALUES ('admin@example.com', 'Administrador Sistema', 'admin')
ON CONFLICT (email) DO NOTHING
RETURNING id;

-- Usuario 2: Operador
INSERT INTO usuarios (email, nombre, rol)
VALUES ('operador@example.com', 'Operador Soporte', 'operador')
ON CONFLICT (email) DO NOTHING
RETURNING id;

-- Usuario 3: Usuario final
INSERT INTO usuarios (email, nombre, rol)
VALUES ('usuario@example.com', 'Usuario Final', 'usuario')
ON CONFLICT (email) DO NOTHING
RETURNING id;

-- ============================================
-- CREAR TICKETS DE EJEMPLO
-- ============================================

-- Obtener IDs de usuarios (asumiendo que se crearon arriba)
DO $$
DECLARE
    v_usuario_id UUID;
    v_ticket_id UUID;
BEGIN
    -- Obtener ID del primer usuario
    SELECT id INTO v_usuario_id FROM usuarios WHERE email = 'usuario@example.com' LIMIT 1;
    
    IF v_usuario_id IS NULL THEN
        RAISE NOTICE 'No se encontró usuario de ejemplo. Creando uno...';
        INSERT INTO usuarios (email, nombre, rol)
        VALUES ('usuario@example.com', 'Usuario Final', 'usuario')
        RETURNING id INTO v_usuario_id;
    END IF;
    
    -- Crear ticket de ejemplo
    INSERT INTO tickets (usuario_id, titulo, descripcion, estado, prioridad)
    VALUES (
        v_usuario_id,
        'Error al iniciar sesión',
        'No puedo iniciar sesión en el sistema. Aparece un error 500.',
        'abierto',
        'alta'
    )
    ON CONFLICT DO NOTHING
    RETURNING id INTO v_ticket_id;
    
    IF v_ticket_id IS NOT NULL THEN
        RAISE NOTICE 'Ticket de ejemplo creado con ID: %', v_ticket_id;
    END IF;
END $$;

-- ============================================
-- NOTA: Para usar estos datos en los scripts de transacciones
-- ============================================
-- Los scripts de transacciones usan UUIDs hardcodeados.
-- Para que funcionen, puedes:
-- 1. Reemplazar los UUIDs en 03_transacciones_concurrencia.sql con los IDs reales
-- 2. O usar este script para crear datos y luego consultar los IDs:
--
-- SELECT id FROM usuarios ORDER BY fecha_creacion LIMIT 3;
-- SELECT id FROM tickets ORDER BY fecha_creacion LIMIT 1;
--

