-- ============================================
-- FASE 2.1: CONTROL DE CONCURRENCIA Y TRANSACCIONES
-- Scripts de Transacciones y Análisis de Concurrencia
-- ============================================

-- ============================================
-- ESCENARIO: Concurrencia en Actualización de Tickets
-- ============================================
-- Situación: Un usuario cambia el estado de un ticket mientras 
-- un operador registra una interacción simultáneamente.

-- ============================================
-- TRANSACCIÓN CON READ COMMITTED (Nivel por defecto)
-- ============================================
-- NOTA: Este es un ejemplo. Para ejecutarlo, primero crea datos de ejemplo
-- usando el script 05_datos_ejemplo.sql o crea tus propios registros.

/*
BEGIN TRANSACTION;
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- Usuario cambia el estado del ticket
UPDATE tickets 
SET estado = 'en_proceso',
    fecha_actualizacion = CURRENT_TIMESTAMP
WHERE id = '00000000-0000-0000-0000-000000000001';

-- Operador registra una interacción
INSERT INTO interacciones (ticket_id, usuario_id, tipo, contenido)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000002',
    'comentario',
    'Ticket actualizado a en_proceso por el usuario'
);

-- Si todo está bien, confirmar
COMMIT;

-- Si hay error, revertir
-- ROLLBACK;
*/

-- ============================================
-- TRANSACCIÓN CON SERIALIZABLE (Máximo aislamiento)
-- ============================================
-- NOTA: Este es un ejemplo. Para ejecutarlo, primero crea datos de ejemplo.

/*
BEGIN TRANSACTION;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- Usuario cambia el estado del ticket
UPDATE tickets 
SET estado = 'resuelto',
    fecha_actualizacion = CURRENT_TIMESTAMP
WHERE id = '00000000-0000-0000-0000-000000000001';

-- Operador registra una interacción
INSERT INTO interacciones (ticket_id, usuario_id, tipo, contenido)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000002',
    'cambio_estado',
    'Ticket marcado como resuelto'
);

COMMIT;
*/

-- ============================================
-- COMPARACIÓN: READ COMMITTED vs SERIALIZABLE
-- ============================================

/*
READ COMMITTED (Nivel por defecto en PostgreSQL):
- Permite lectura de datos confirmados por otras transacciones
- No previene lecturas no repetibles (non-repeatable reads)
- No previene lecturas fantasma (phantom reads)
- Menor overhead, mejor rendimiento
- Riesgo: Puede leer datos que cambian durante la transacción

SERIALIZABLE (Máximo aislamiento):
- Garantiza que las transacciones concurrentes se ejecuten como si fueran secuenciales
- Previene lecturas sucias, no repetibles y fantasma
- Mayor overhead, puede causar deadlocks
- Riesgo: Transacciones pueden fallar con error de serialización
- Uso: Cuando la consistencia es crítica
*/

-- ============================================
-- CASO DE LECTURA SUCIA (Dirty Read)
-- ============================================

/*
ESCENARIO DE LECTURA SUCIA:

Transacción 1 (Usuario):
BEGIN;
UPDATE tickets SET estado = 'cerrado' WHERE id = 'xxx';
-- Aún no hace COMMIT

Transacción 2 (Operador - READ UNCOMMITTED):
BEGIN;
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
SELECT estado FROM tickets WHERE id = 'xxx';
-- Lee 'cerrado' aunque la transacción 1 no ha confirmado

Transacción 1:
ROLLBACK; -- Revierte el cambio

Transacción 2:
-- Ha leído un dato que nunca existió realmente (lectura sucia)

NOTA: PostgreSQL no permite READ UNCOMMITTED, siempre usa al menos READ COMMITTED,
por lo que las lecturas sucias no son posibles en PostgreSQL por defecto.
*/

-- ============================================
-- CASO DE PÉRDIDA DE ACTUALIZACIÓN (Lost Update)
-- ============================================

/*
ESCENARIO DE PÉRDIDA DE ACTUALIZACIÓN:

Situación inicial: Ticket con prioridad = 'media'

Transacción 1 (Usuario A):
BEGIN;
SELECT prioridad FROM tickets WHERE id = 'xxx'; -- Lee 'media'
-- Usuario A decide cambiar a 'alta'
UPDATE tickets SET prioridad = 'alta' WHERE id = 'xxx';
COMMIT;

Transacción 2 (Usuario B - simultánea):
BEGIN;
SELECT prioridad FROM tickets WHERE id = 'xxx'; -- Lee 'media' (antes del commit de A)
-- Usuario B decide cambiar a 'baja'
UPDATE tickets SET prioridad = 'baja' WHERE id = 'xxx';
COMMIT;

Resultado: La actualización de Usuario A se perdió, el ticket queda en 'baja'
cuando debería estar en 'alta' según la intención de A.

SOLUCIÓN: Usar SELECT FOR UPDATE para bloqueo pesimista
*/

-- ============================================
-- TRANSACCIÓN CON BLOQUEO PESIMISTA (Prevención de Lost Update)
-- ============================================
-- NOTA: Este es un ejemplo. Para ejecutarlo, primero crea datos de ejemplo.

/*
BEGIN TRANSACTION;
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- Bloquear el registro para lectura/escritura
SELECT * FROM tickets 
WHERE id = '00000000-0000-0000-0000-000000000001'
FOR UPDATE;

-- Ahora podemos actualizar con seguridad
UPDATE tickets 
SET prioridad = 'alta',
    fecha_actualizacion = CURRENT_TIMESTAMP
WHERE id = '00000000-0000-0000-0000-000000000001';

-- Registrar la interacción
INSERT INTO interacciones (ticket_id, usuario_id, tipo, contenido)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000003',
    'cambio_estado',
    'Prioridad actualizada a alta'
);

COMMIT;
*/

-- ============================================
-- TRANSACCIÓN CON MANEJO DE ERRORES
-- ============================================
-- NOTA: Este es un ejemplo. Para ejecutarlo, primero crea datos de ejemplo.

/*
DO $$
DECLARE
    v_ticket_id UUID := '00000000-0000-0000-0000-000000000001';
    v_usuario_id UUID := '00000000-0000-0000-0000-000000000002';
BEGIN
    BEGIN
        -- Iniciar transacción implícita
        UPDATE tickets 
        SET estado = 'en_proceso',
            fecha_actualizacion = CURRENT_TIMESTAMP
        WHERE id = v_ticket_id;
        
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Ticket no encontrado: %', v_ticket_id;
        END IF;
        
        INSERT INTO interacciones (ticket_id, usuario_id, tipo, contenido)
        VALUES (
            v_ticket_id,
            v_usuario_id,
            'cambio_estado',
            'Estado actualizado a en_proceso'
        );
        
        -- Si llegamos aquí, todo está bien
        RAISE NOTICE 'Transacción completada exitosamente';
        
    EXCEPTION
        WHEN OTHERS THEN
            -- En caso de error, hacer rollback automático
            RAISE NOTICE 'Error en transacción: %', SQLERRM;
            RAISE;
    END;
END $$;
*/

-- ============================================
-- EJEMPLO DE TRANSACCIÓN COMPLEJA CON MÚLTIPLES OPERACIONES
-- ============================================
-- NOTA: Este es un ejemplo. Para ejecutarlo, primero crea datos de ejemplo.

/*
BEGIN TRANSACTION;

-- 1. Actualizar estado del ticket
UPDATE tickets 
SET estado = 'resuelto',
    fecha_cierre = CURRENT_TIMESTAMP,
    fecha_actualizacion = CURRENT_TIMESTAMP
WHERE id = '00000000-0000-0000-0000-000000000001'
  AND estado != 'resuelto'; -- Evitar actualizaciones innecesarias

-- 2. Registrar interacción de cierre
INSERT INTO interacciones (ticket_id, usuario_id, tipo, contenido)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000002',
    'cambio_estado',
    'Ticket marcado como resuelto y cerrado'
);

-- 3. Verificar que la operación fue exitosa
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM tickets
    WHERE id = '00000000-0000-0000-0000-000000000001'
      AND estado = 'resuelto';
    
    IF v_count = 0 THEN
        RAISE EXCEPTION 'Error: El ticket no se actualizó correctamente';
    END IF;
END $$;

-- Confirmar si todo está bien
COMMIT;

-- O revertir en caso de error
-- ROLLBACK;
*/

