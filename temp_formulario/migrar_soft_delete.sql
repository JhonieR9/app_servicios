-- =====================================================
-- MIGRACIÓN: Agregar Soft Delete (Papelera de Reciclaje)
-- =====================================================

USE profiles_cv_db;

-- Agregar columna fecha_eliminacion si no existe
ALTER TABLE personas 
ADD COLUMN IF NOT EXISTS fecha_eliminacion TIMESTAMP NULL AFTER fecha_actualizacion;

-- Modificar columna estado para incluir 'eliminado'
ALTER TABLE personas 
MODIFY COLUMN estado ENUM('activo', 'inactivo', 'eliminado') DEFAULT 'activo';

-- Actualizar registros existentes para asegurar que estén activos
UPDATE personas SET estado = 'activo' WHERE estado IS NULL OR estado = '';

SELECT 'Migración completada exitosamente' AS resultado;
