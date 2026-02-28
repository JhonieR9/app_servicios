-- ============================================
-- SCRIPT SQL PARA MVP - APP TIPO DIDI
-- Base de datos: profiles_cv_db
-- ============================================

USE profiles_cv_db;

-- ============================================
-- 1. TABLA CATEGORIAS DE SERVICIO
-- ============================================
CREATE TABLE IF NOT EXISTS categorias_servicio (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nombre_categoria VARCHAR(100) NOT NULL,
    descripcion TEXT,
    icono VARCHAR(50),
    estado ENUM('activo', 'inactivo') DEFAULT 'activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar categorías básicas
INSERT INTO categorias_servicio (nombre_categoria, descripcion, icono) VALUES
('Plomería', 'Reparación e instalación de tuberías y sistemas de agua', '🔧'),
('Electricidad', 'Instalación y reparación eléctrica', '⚡'),
('Limpieza', 'Servicios de limpieza para hogar y oficina', '🧹'),
('Carpintería', 'Trabajos en madera y muebles', '🪚'),
('Pintura', 'Pintura de interiores y exteriores', '🎨'),
('Jardinería', 'Mantenimiento de jardines y áreas verdes', '🌱'),
('Cerrajería', 'Servicios de cerrajería y seguridad', '🔑'),
('Mudanza', 'Servicios de transporte y mudanza', '📦');

-- ============================================
-- 2. TABLA SOLICITUDES DE SERVICIO
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
-- 3. TABLA CALIFICACIONES
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
-- 4. TABLA TRABAJADOR_CATEGORIAS (Relación N:N)
-- ============================================
CREATE TABLE IF NOT EXISTS trabajador_categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_trabajador INT NOT NULL,
    id_categoria INT NOT NULL,
    experiencia_anos INT DEFAULT 0,
    certificado BOOLEAN DEFAULT FALSE,
    fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_trabajador) REFERENCES personas(id_persona) ON DELETE CASCADE,
    FOREIGN KEY (id_categoria) REFERENCES categorias_servicio(id_categoria) ON DELETE CASCADE,
    UNIQUE KEY unique_trabajador_categoria (id_trabajador, id_categoria)
);

-- ============================================
-- 5. TABLA DISPONIBILIDAD TRABAJADOR
-- ============================================
CREATE TABLE IF NOT EXISTS disponibilidad_trabajador (
    id_disponibilidad INT AUTO_INCREMENT PRIMARY KEY,
    id_trabajador INT NOT NULL,
    disponible BOOLEAN DEFAULT TRUE,
    latitud DECIMAL(10, 8) NULL,
    longitud DECIMAL(11, 8) NULL,
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_trabajador) REFERENCES personas(id_persona) ON DELETE CASCADE
);

-- ============================================
-- 6. TABLA NOTIFICACIONES
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
-- 7. MEJORAS A TABLA CLIENTES EXISTENTE
-- ============================================
ALTER TABLE clientes 
ADD COLUMN IF NOT EXISTS foto_perfil VARCHAR(255) NULL,
ADD COLUMN IF NOT EXISTS fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

-- ============================================
-- 8. ÍNDICES PARA OPTIMIZACIÓN
-- ============================================
CREATE INDEX idx_solicitud_estado ON solicitudes_servicio(estado);
CREATE INDEX idx_solicitud_cliente ON solicitudes_servicio(id_cliente);
CREATE INDEX idx_solicitud_trabajador ON solicitudes_servicio(id_trabajador);
CREATE INDEX idx_solicitud_categoria ON solicitudes_servicio(id_categoria);
CREATE INDEX idx_calificacion_trabajador ON calificaciones(id_trabajador);
CREATE INDEX idx_notificacion_usuario ON notificaciones(id_usuario, tipo_usuario, leida);

-- ============================================
-- 9. VISTAS ÚTILES
-- ============================================

-- Vista: Resumen de trabajadores con calificación promedio
CREATE OR REPLACE VIEW vista_trabajadores_calificacion AS
SELECT 
    t.id_persona as id_trabajador,
    t.nombre_completo,
    t.ciudad,
    t.departamento,
    COUNT(DISTINCT tc.id_categoria) as total_categorias,
    COALESCE(AVG(c.puntuacion), 0) as calificacion_promedio,
    COUNT(DISTINCT c.id_calificacion) as total_calificaciones,
    COUNT(DISTINCT s.id_solicitud) as servicios_completados
FROM personas t
LEFT JOIN trabajador_categorias tc ON t.id_persona = tc.id_trabajador
LEFT JOIN calificaciones c ON t.id_persona = c.id_trabajador AND c.tipo_calificacion = 'cliente_a_trabajador'
LEFT JOIN solicitudes_servicio s ON t.id_persona = s.id_trabajador AND s.estado = 'completada'
GROUP BY t.id_persona;

-- Vista: Historial de servicios del cliente
CREATE OR REPLACE VIEW vista_historial_cliente AS
SELECT 
    s.id_solicitud,
    s.id_cliente,
    c.nombre_completo as nombre_cliente,
    s.id_trabajador,
    t.nombre_completo as nombre_trabajador,
    cat.nombre_categoria,
    s.titulo,
    s.estado,
    s.fecha_solicitud,
    s.fecha_finalizacion,
    s.precio_final,
    cal.puntuacion as calificacion_dada
FROM solicitudes_servicio s
INNER JOIN clientes c ON s.id_cliente = c.id_cliente
LEFT JOIN personas t ON s.id_trabajador = t.id_persona
INNER JOIN categorias_servicio cat ON s.id_categoria = cat.id_categoria
LEFT JOIN calificaciones cal ON s.id_solicitud = cal.id_solicitud AND cal.tipo_calificacion = 'cliente_a_trabajador';

-- ============================================
-- SCRIPT COMPLETADO
-- ============================================
