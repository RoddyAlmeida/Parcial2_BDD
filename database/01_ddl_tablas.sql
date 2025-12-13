-- ============================================
-- FASE 1.1: DISEÑO FÍSICO Y OPTIMIZACIÓN DE ALMACENAMIENTO
-- Sistema de Tickets de Soporte
-- ============================================

-- ============================================
-- TABLA: Usuarios
-- ============================================
-- Justificación del diseño:
-- - id: UUID para evitar colisiones y mejorar seguridad
-- - email: VARCHAR(255) con UNIQUE para autenticación
-- - nombre: VARCHAR(100) suficiente para nombres completos
-- - rol: VARCHAR(20) para roles del sistema (admin, operador, usuario)
-- - activo: BOOLEAN para soft delete
-- - fecha_creacion: TIMESTAMP para auditoría
-- - fecha_actualizacion: TIMESTAMP para tracking de cambios

CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('admin', 'operador', 'usuario')),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Índice para búsquedas por email (frecuente en autenticación)
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);

-- Índice para filtrar usuarios activos
CREATE INDEX IF NOT EXISTS idx_usuarios_activo ON usuarios(activo) WHERE activo = TRUE;

COMMENT ON TABLE usuarios IS 'Tabla de usuarios del sistema de tickets';
COMMENT ON COLUMN usuarios.id IS 'Identificador único UUID del usuario';
COMMENT ON COLUMN usuarios.email IS 'Email único para autenticación';
COMMENT ON COLUMN usuarios.rol IS 'Rol del usuario: admin, operador o usuario';

-- ============================================
-- TABLA: Tickets
-- ============================================
-- Justificación del diseño:
-- - id: UUID para evitar colisiones
-- - usuario_id: FK a usuarios, NOT NULL porque cada ticket pertenece a un usuario
-- - titulo: VARCHAR(200) para títulos descriptivos
-- - descripcion: TEXT para descripciones largas sin límite
-- - estado: VARCHAR(20) con CHECK para control de valores válidos
-- - prioridad: VARCHAR(10) para clasificación
-- - fecha_creacion: TIMESTAMP para ordenamiento temporal
-- - fecha_actualizacion: TIMESTAMP para tracking
-- - fecha_cierre: TIMESTAMP NULL para tickets abiertos

CREATE TABLE IF NOT EXISTS tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'abierto' 
        CHECK (estado IN ('abierto', 'en_proceso', 'resuelto', 'cerrado')),
    prioridad VARCHAR(10) NOT NULL DEFAULT 'media'
        CHECK (prioridad IN ('baja', 'media', 'alta', 'critica')),
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre TIMESTAMP WITH TIME ZONE NULL,
    
    CONSTRAINT fk_tickets_usuario FOREIGN KEY (usuario_id) 
        REFERENCES usuarios(id) ON DELETE RESTRICT
);

-- Índice para búsquedas por usuario (consultas frecuentes)
CREATE INDEX IF NOT EXISTS idx_tickets_usuario_id ON tickets(usuario_id);

-- Índice compuesto para filtrar por estado y fecha (dashboard)
CREATE INDEX IF NOT EXISTS idx_tickets_estado_fecha ON tickets(estado, fecha_creacion DESC);

-- Índice para búsquedas por prioridad
CREATE INDEX IF NOT EXISTS idx_tickets_prioridad ON tickets(prioridad) WHERE prioridad IN ('alta', 'critica');

COMMENT ON TABLE tickets IS 'Tabla principal de tickets de soporte';
COMMENT ON COLUMN tickets.estado IS 'Estado del ticket: abierto, en_proceso, resuelto, cerrado';
COMMENT ON COLUMN tickets.prioridad IS 'Prioridad: baja, media, alta, critica';

-- ============================================
-- TABLA: Interacciones (Tabla más grande)
-- ============================================
-- Justificación del diseño:
-- - id: BIGSERIAL para alto volumen (más eficiente que UUID en tablas grandes)
-- - ticket_id: FK a tickets, NOT NULL
-- - usuario_id: FK a usuarios (puede ser NULL si es sistema)
-- - tipo: VARCHAR(20) para clasificar interacciones
-- - contenido: TEXT para mensajes largos
-- - fecha_creacion: TIMESTAMP crítico para ordenamiento y filtrado
-- Esta tabla crecerá rápidamente con el uso del sistema

CREATE TABLE IF NOT EXISTS interacciones (
    id BIGSERIAL PRIMARY KEY,
    ticket_id UUID NOT NULL,
    usuario_id UUID NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('comentario', 'cambio_estado', 'asignacion', 'archivo')),
    contenido TEXT NOT NULL,
    metadata JSONB NULL,
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_interacciones_ticket FOREIGN KEY (ticket_id) 
        REFERENCES tickets(id) ON DELETE CASCADE,
    CONSTRAINT fk_interacciones_usuario FOREIGN KEY (usuario_id) 
        REFERENCES usuarios(id) ON DELETE SET NULL
);

-- ============================================
-- ÍNDICE COMPUESTO NON-CLUSTERED OPTIMIZADO
-- ============================================
-- Estrategia de Índices: Índice compuesto para Interacciones
-- 
-- Este índice compuesto (ticket_id, fecha_creacion) optimiza:
-- 1. Consultas que filtran por ticket_id (muy frecuente)
-- 2. Ordenamiento por fecha_creacion dentro de cada ticket
-- 3. Consultas que combinan ambos criterios
--
-- Mejoras de rendimiento:
-- - Reduce búsquedas secuenciales en tablas grandes
-- - Permite acceso directo a interacciones de un ticket ordenadas
-- - Mejora JOINs con la tabla tickets
-- - Facilita paginación eficiente
--
-- Ejemplo de consulta optimizada:
-- SELECT * FROM interacciones 
-- WHERE ticket_id = 'xxx' 
-- ORDER BY fecha_creacion DESC
-- LIMIT 20;

CREATE INDEX IF NOT EXISTS idx_interacciones_ticket_fecha 
    ON interacciones(ticket_id, fecha_creacion DESC);

-- Índice adicional para búsquedas por usuario
CREATE INDEX IF NOT EXISTS idx_interacciones_usuario_id ON interacciones(usuario_id) 
    WHERE usuario_id IS NOT NULL;

-- Índice para búsquedas por tipo de interacción
CREATE INDEX IF NOT EXISTS idx_interacciones_tipo ON interacciones(tipo);

-- Índice GIN para búsquedas en metadata JSONB
CREATE INDEX IF NOT EXISTS idx_interacciones_metadata ON interacciones USING GIN(metadata);

COMMENT ON TABLE interacciones IS 'Tabla de interacciones/comentarios en tickets (tabla de alto volumen)';
COMMENT ON COLUMN interacciones.id IS 'Identificador BIGSERIAL para alto rendimiento en tablas grandes';
COMMENT ON INDEX idx_interacciones_ticket_fecha IS 'Índice compuesto optimizado para consultas por ticket y fecha';

-- ============================================
-- TRIGGER: Actualización automática de fecha_actualizacion
-- ============================================

CREATE OR REPLACE FUNCTION actualizar_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_actualizar_tickets
    BEFORE UPDATE ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_fecha_actualizacion();

CREATE TRIGGER trigger_actualizar_usuarios
    BEFORE UPDATE ON usuarios
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_fecha_actualizacion();

