-- ============================================
-- SISTEMA DE AUTENTICACIÓN
-- Base de datos: profiles_cv_db
-- ============================================

USE profiles_cv_db;

-- ============================================
-- 1. AGREGAR COLUMNAS DE AUTENTICACIÓN A PERSONAS
-- ============================================

ALTER TABLE personas 
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
ADD COLUMN IF NOT EXISTS telefono_verificado TINYINT(1) DEFAULT 0,
ADD COLUMN IF NOT EXISTS correo_verificado TINYINT(1) DEFAULT 0,
ADD COLUMN IF NOT EXISTS ultimo_login DATETIME,
ADD COLUMN IF NOT EXISTS intentos_fallidos INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS bloqueado_hasta DATETIME;

-- ============================================
-- 2. AGREGAR COLUMNAS DE AUTENTICACIÓN A CLIENTES
-- ============================================

ALTER TABLE clientes 
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
ADD COLUMN IF NOT EXISTS telefono_verificado TINYINT(1) DEFAULT 0,
ADD COLUMN IF NOT EXISTS correo_verificado TINYINT(1) DEFAULT 0,
ADD COLUMN IF NOT EXISTS ultimo_login DATETIME,
ADD COLUMN IF NOT EXISTS intentos_fallidos INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS bloqueado_hasta DATETIME;

-- ============================================
-- 3. TABLA DE CÓDIGOS DE VERIFICACIÓN SMS
-- ============================================

CREATE TABLE IF NOT EXISTS codigos_verificacion (
    id_codigo INT PRIMARY KEY AUTO_INCREMENT,
    tipo_usuario ENUM('trabajador', 'cliente') NOT NULL,
    id_usuario INT NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    codigo VARCHAR(6) NOT NULL,
    tipo_verificacion ENUM('registro', 'login', 'recuperacion') NOT NULL,
    usado TINYINT(1) DEFAULT 0,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion TIMESTAMP NOT NULL,
    fecha_uso TIMESTAMP NULL,
    INDEX idx_telefono (telefono),
    INDEX idx_codigo (codigo),
    INDEX idx_expiracion (fecha_expiracion)
);

-- ============================================
-- 4. TABLA DE SESIONES
-- ============================================

CREATE TABLE IF NOT EXISTS sesiones (
    id_sesion INT PRIMARY KEY AUTO_INCREMENT,
    tipo_usuario ENUM('trabajador', 'cliente', 'admin') NOT NULL,
    id_usuario INT NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion TIMESTAMP NOT NULL,
    activa TINYINT(1) DEFAULT 1,
    INDEX idx_token (token),
    INDEX idx_usuario (tipo_usuario, id_usuario)
);

-- ============================================
-- 5. TABLA DE INTENTOS DE LOGIN
-- ============================================

CREATE TABLE IF NOT EXISTS intentos_login (
    id_intento INT PRIMARY KEY AUTO_INCREMENT,
    tipo_usuario ENUM('trabajador', 'cliente', 'admin') NOT NULL,
    correo VARCHAR(255),
    ip_address VARCHAR(45),
    exitoso TINYINT(1) NOT NULL,
    mensaje TEXT,
    fecha_intento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_correo (correo),
    INDEX idx_fecha (fecha_intento)
);

-- ============================================
-- 6. ÍNDICES PARA MEJORAR RENDIMIENTO
-- ============================================

-- Índice en correo_persona para búsquedas rápidas
ALTER TABLE correo_persona ADD INDEX IF NOT EXISTS idx_correo (correo);

-- Índice en correo_cliente para búsquedas rápidas
ALTER TABLE correo_cliente ADD INDEX IF NOT EXISTS idx_correo (correo);

-- ============================================
-- 7. CONFIGURACIÓN DE SEGURIDAD
-- ============================================

-- Crear tabla de configuración de seguridad
CREATE TABLE IF NOT EXISTS configuracion_seguridad (
    id_config INT PRIMARY KEY AUTO_INCREMENT,
    clave VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT NOT NULL,
    descripcion TEXT,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insertar configuraciones por defecto
INSERT INTO configuracion_seguridad (clave, valor, descripcion) VALUES
('max_intentos_login', '5', 'Máximo de intentos de login antes de bloquear'),
('tiempo_bloqueo_minutos', '30', 'Tiempo de bloqueo en minutos después de exceder intentos'),
('duracion_sesion_horas', '24', 'Duración de la sesión en horas'),
('longitud_codigo_sms', '6', 'Longitud del código SMS'),
('expiracion_codigo_minutos', '10', 'Tiempo de expiración del código SMS en minutos'),
('requiere_verificacion_sms', '1', 'Si requiere verificación SMS (1=sí, 0=no)')
ON DUPLICATE KEY UPDATE valor=VALUES(valor);

-- ============================================
-- VERIFICACIÓN
-- ============================================

SELECT 'Tablas de autenticación creadas exitosamente' AS mensaje;

-- Mostrar columnas agregadas a personas
SELECT 'Columnas en tabla personas:' AS info;
SHOW COLUMNS FROM personas LIKE '%password%';
SHOW COLUMNS FROM personas LIKE '%verificado%';
SHOW COLUMNS FROM personas LIKE '%login%';

-- Mostrar columnas agregadas a clientes
SELECT 'Columnas en tabla clientes:' AS info;
SHOW COLUMNS FROM clientes LIKE '%password%';
SHOW COLUMNS FROM clientes LIKE '%verificado%';
SHOW COLUMNS FROM clientes LIKE '%login%';

-- Mostrar tablas nuevas
SELECT 'Tablas de autenticación:' AS info;
SHOW TABLES LIKE '%codigo%';
SHOW TABLES LIKE '%sesion%';
SHOW TABLES LIKE '%intento%';

SELECT '✅ Sistema de autenticación instalado correctamente' AS resultado;
