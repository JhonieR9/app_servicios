-- ============================================
-- SCRIPT SQL PARA AGREGAR GEOLOCALIZACIÓN
-- Compatible con todas las versiones de MySQL
-- ============================================

USE profiles_cv_db;

-- ============================================
-- 1. AGREGAR COLUMNAS A PERSONAS (si no existen)
-- ============================================

-- Verificar y agregar columna estado
SET @col_exists = 0;
SELECT COUNT(*) INTO @col_exists 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'profiles_cv_db' 
AND TABLE_NAME = 'personas' 
AND COLUMN_NAME = 'estado';

SET @query = IF(@col_exists = 0,
    "ALTER TABLE personas ADD COLUMN estado ENUM('activo', 'eliminado', 'suspendido') DEFAULT 'activo'",
    "SELECT 'Columna estado ya existe' AS mensaje");
PREPARE stmt FROM @query;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Verificar y agregar columna fecha_eliminacion
SET @col_exists = 0;
SELECT COUNT(*) INTO @col_exists 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'profiles_cv_db' 
AND TABLE_NAME = 'personas' 
AND COLUMN_NAME = 'fecha_eliminacion';

SET @query = IF(@col_exists = 0,
    "ALTER TABLE personas ADD COLUMN fecha_eliminacion DATETIME NULL",
    "SELECT 'Columna fecha_eliminacion ya existe' AS mensaje");
PREPARE stmt FROM @query;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ============================================
-- 2. AGREGAR COLUMNAS GPS A DISPONIBILIDAD
-- ============================================

-- Verificar y agregar columna latitud
SET @col_exists = 0;
SELECT COUNT(*) INTO @col_exists 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'profiles_cv_db' 
AND TABLE_NAME = 'disponibilidad' 
AND COLUMN_NAME = 'latitud';

SET @query = IF(@col_exists = 0,
    "ALTER TABLE disponibilidad ADD COLUMN latitud DECIMAL(10, 8) NULL",
    "SELECT 'Columna latitud ya existe' AS mensaje");
PREPARE stmt FROM @query;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Verificar y agregar columna longitud
SET @col_exists = 0;
SELECT COUNT(*) INTO @col_exists 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'profiles_cv_db' 
AND TABLE_NAME = 'disponibilidad' 
AND COLUMN_NAME = 'longitud';

SET @query = IF(@col_exists = 0,
    "ALTER TABLE disponibilidad ADD COLUMN longitud DECIMAL(11, 8) NULL",
    "SELECT 'Columna longitud ya existe' AS mensaje");
PREPARE stmt FROM @query;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Verificar y agregar columna disponible
SET @col_exists = 0;
SELECT COUNT(*) INTO @col_exists 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'profiles_cv_db' 
AND TABLE_NAME = 'disponibilidad' 
AND COLUMN_NAME = 'disponible';

SET @query = IF(@col_exists = 0,
    "ALTER TABLE disponibilidad ADD COLUMN disponible BOOLEAN DEFAULT TRUE",
    "SELECT 'Columna disponible ya existe' AS mensaje");
PREPARE stmt FROM @query;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Verificar y agregar columna ultima_actualizacion
SET @col_exists = 0;
SELECT COUNT(*) INTO @col_exists 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'profiles_cv_db' 
AND TABLE_NAME = 'disponibilidad' 
AND COLUMN_NAME = 'ultima_actualizacion';

SET @query = IF(@col_exists = 0,
    "ALTER TABLE disponibilidad ADD COLUMN ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
    "SELECT 'Columna ultima_actualizacion ya existe' AS mensaje");
PREPARE stmt FROM @query;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ============================================
-- 3. CREAR TABLA CATEGORIAS_SERVICIO (si no existe)
-- ============================================

CREATE TABLE IF NOT EXISTS categorias_servicio (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nombre_categoria VARCHAR(100) NOT NULL,
    descripcion TEXT,
    icono VARCHAR(50),
    estado ENUM('activo', 'inactivo') DEFAULT 'activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar categorías básicas (IGNORE para evitar duplicados)
INSERT IGNORE INTO categorias_servicio (id_categoria, nombre_categoria, descripcion, icono) VALUES
(1, 'Plomería', 'Reparación e instalación de tuberías y sistemas de agua', '🔧'),
(2, 'Electricidad', 'Instalación y reparación eléctrica', '⚡'),
(3, 'Limpieza', 'Servicios de limpieza para hogar y oficina', '🧹'),
(4, 'Carpintería', 'Trabajos en madera y muebles', '🪚'),
(5, 'Pintura', 'Pintura de interiores y exteriores', '🎨'),
(6, 'Jardinería', 'Mantenimiento de jardines y áreas verdes', '🌱'),
(7, 'Cerrajería', 'Servicios de cerrajería y seguridad', '🔑'),
(8, 'Mudanza', 'Servicios de transporte y mudanza', '📦');

-- ============================================
-- 4. CREAR TABLA SOLICITUDES_SERVICIO (si no existe)
-- ============================================

CREATE TABLE IF NOT EXISTS solicitudes_servicio (
    id_solicitud INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_categoria INT NOT NULL,
    id_trabajador INT NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    direccion_servicio TEXT NOT NULL,
    ciudad VARCHAR(100),
    departamento VARCHAR(100),
    fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_programada DATETIME NULL,
    estado ENUM('pendiente', 'aceptada', 'en_proceso', 'completada', 'cancelada') DEFAULT 'pendiente',
    precio_estimado DECIMAL(10,2) NULL,
    precio_final DECIMAL(10,2) NULL,
    tiempo_estimado INT NULL COMMENT 'Tiempo en minutos',
    notas_adicionales TEXT,
    fecha_aceptacion DATETIME NULL,
    fecha_inicio DATETIME NULL,
    fecha_finalizacion DATETIME NULL,
    motivo_cancelacion TEXT NULL,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente) ON DELETE CASCADE,
    FOREIGN KEY (id_categoria) REFERENCES categorias_servicio(id_categoria),
    FOREIGN KEY (id_trabajador) REFERENCES personas(id_persona) ON DELETE SET NULL
);

-- ============================================
-- 5. CREAR TABLA CALIFICACIONES (si no existe)
-- ============================================

CREATE TABLE IF NOT EXISTS calificaciones (
    id_calificacion INT AUTO_INCREMENT PRIMARY KEY,
    id_solicitud INT NOT NULL,
    id_cliente INT NOT NULL,
    id_trabajador INT NOT NULL,
    tipo_calificacion ENUM('cliente_a_trabajador', 'trabajador_a_cliente') NOT NULL,
    puntuacion INT NOT NULL CHECK (puntuacion BETWEEN 1 AND 5),
    comentario TEXT,
    fecha_calificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_solicitud) REFERENCES solicitudes_servicio(id_solicitud) ON DELETE CASCADE,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente) ON DELETE CASCADE,
    FOREIGN KEY (id_trabajador) REFERENCES personas(id_persona) ON DELETE CASCADE
);

-- ============================================
-- 6. CREAR TABLA NOTIFICACIONES (si no existe)
-- ============================================

CREATE TABLE IF NOT EXISTS notificaciones (
    id_notificacion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    tipo_usuario ENUM('cliente', 'trabajador') NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    mensaje TEXT NOT NULL,
    tipo_notificacion ENUM('solicitud', 'aceptacion', 'cancelacion', 'completado', 'calificacion', 'sistema') NOT NULL,
    leida BOOLEAN DEFAULT FALSE,
    id_solicitud INT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_solicitud) REFERENCES solicitudes_servicio(id_solicitud) ON DELETE CASCADE
);

-- ============================================
-- 7. CREAR ÍNDICES (si no existen)
-- ============================================

-- Índices para solicitudes_servicio
SET @index_exists = (SELECT COUNT(*) FROM information_schema.statistics 
    WHERE table_schema = 'profiles_cv_db' AND table_name = 'solicitudes_servicio' AND index_name = 'idx_solicitud_estado');
SET @query = IF(@index_exists = 0, 
    'CREATE INDEX idx_solicitud_estado ON solicitudes_servicio(estado)', 
    'SELECT "Índice idx_solicitud_estado ya existe"');
PREPARE stmt FROM @query; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @index_exists = (SELECT COUNT(*) FROM information_schema.statistics 
    WHERE table_schema = 'profiles_cv_db' AND table_name = 'solicitudes_servicio' AND index_name = 'idx_solicitud_cliente');
SET @query = IF(@index_exists = 0, 
    'CREATE INDEX idx_solicitud_cliente ON solicitudes_servicio(id_cliente)', 
    'SELECT "Índice idx_solicitud_cliente ya existe"');
PREPARE stmt FROM @query; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @index_exists = (SELECT COUNT(*) FROM information_schema.statistics 
    WHERE table_schema = 'profiles_cv_db' AND table_name = 'solicitudes_servicio' AND index_name = 'idx_solicitud_trabajador');
SET @query = IF(@index_exists = 0, 
    'CREATE INDEX idx_solicitud_trabajador ON solicitudes_servicio(id_trabajador)', 
    'SELECT "Índice idx_solicitud_trabajador ya existe"');
PREPARE stmt FROM @query; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @index_exists = (SELECT COUNT(*) FROM information_schema.statistics 
    WHERE table_schema = 'profiles_cv_db' AND table_name = 'solicitudes_servicio' AND index_name = 'idx_solicitud_categoria');
SET @query = IF(@index_exists = 0, 
    'CREATE INDEX idx_solicitud_categoria ON solicitudes_servicio(id_categoria)', 
    'SELECT "Índice idx_solicitud_categoria ya existe"');
PREPARE stmt FROM @query; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Índices para calificaciones
SET @index_exists = (SELECT COUNT(*) FROM information_schema.statistics 
    WHERE table_schema = 'profiles_cv_db' AND table_name = 'calificaciones' AND index_name = 'idx_calificacion_trabajador');
SET @query = IF(@index_exists = 0, 
    'CREATE INDEX idx_calificacion_trabajador ON calificaciones(id_trabajador)', 
    'SELECT "Índice idx_calificacion_trabajador ya existe"');
PREPARE stmt FROM @query; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Índices para notificaciones
SET @index_exists = (SELECT COUNT(*) FROM information_schema.statistics 
    WHERE table_schema = 'profiles_cv_db' AND table_name = 'notificaciones' AND index_name = 'idx_notificacion_usuario');
SET @query = IF(@index_exists = 0, 
    'CREATE INDEX idx_notificacion_usuario ON notificaciones(id_usuario, tipo_usuario, leida)', 
    'SELECT "Índice idx_notificacion_usuario ya existe"');
PREPARE stmt FROM @query; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Índices para personas
SET @index_exists = (SELECT COUNT(*) FROM information_schema.statistics 
    WHERE table_schema = 'profiles_cv_db' AND table_name = 'personas' AND index_name = 'idx_personas_estado');
SET @query = IF(@index_exists = 0, 
    'CREATE INDEX idx_personas_estado ON personas(estado)', 
    'SELECT "Índice idx_personas_estado ya existe"');
PREPARE stmt FROM @query; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ============================================
-- 8. CREAR VISTAS
-- ============================================

-- Vista: Trabajadores con calificación
CREATE OR REPLACE VIEW vista_trabajadores_calificacion AS
SELECT 
    p.id_persona as id_trabajador,
    p.nombre_completo,
    p.ciudad,
    COUNT(DISTINCT sp.categoria) as total_categorias,
    COALESCE(AVG(c.puntuacion), 0) as calificacion_promedio,
    COUNT(DISTINCT c.id_calificacion) as total_calificaciones,
    COUNT(DISTINCT s.id_solicitud) as servicios_completados
FROM personas p
LEFT JOIN servicios_persona sp ON p.id_persona = sp.id_persona
LEFT JOIN calificaciones c ON p.id_persona = c.id_trabajador AND c.tipo_calificacion = 'cliente_a_trabajador'
LEFT JOIN solicitudes_servicio s ON p.id_persona = s.id_trabajador AND s.estado = 'completada'
WHERE p.estado = 'activo' OR p.estado IS NULL
GROUP BY p.id_persona;

-- Vista: Historial de clientes
CREATE OR REPLACE VIEW vista_historial_cliente AS
SELECT 
    s.id_solicitud,
    s.id_cliente,
    c.nombre_completo as nombre_cliente,
    s.id_trabajador,
    p.nombre_completo as nombre_trabajador,
    cat.nombre_categoria,
    s.titulo,
    s.estado,
    s.fecha_solicitud,
    s.fecha_finalizacion,
    s.precio_final,
    cal.puntuacion as calificacion_dada
FROM solicitudes_servicio s
INNER JOIN clientes c ON s.id_cliente = c.id_cliente
LEFT JOIN personas p ON s.id_trabajador = p.id_persona
INNER JOIN categorias_servicio cat ON s.id_categoria = cat.id_categoria
LEFT JOIN calificaciones cal ON s.id_solicitud = cal.id_solicitud AND cal.tipo_calificacion = 'cliente_a_trabajador';

-- ============================================
-- SCRIPT COMPLETADO
-- ============================================

SELECT 'Script ejecutado correctamente. Columnas GPS agregadas a la tabla disponibilidad.' AS resultado;
