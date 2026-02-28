-- ============================================
-- SISTEMA DE AUTENTICACIÓN - VERSIÓN CORREGIDA
-- Base de datos: profiles_cv_db
-- ============================================

USE profiles_cv_db;

-- ============================================
-- 1. AGREGAR COLUMNAS DE AUTENTICACIÓN A PERSONAS
-- ============================================

ALTER TABLE personas 
ADD COLUMN password_hash VARCHAR(255) AFTER estado,
ADD COLUMN telefono_verificado TINYINT(1) DEFAULT 0 AFTER password_hash,
ADD COLUMN correo_verificado TINYINT(1) DEFAULT 0 AFTER telefono_verificado,
ADD COLUMN ultimo_login DATETIME AFTER correo_verificado,
ADD COLUMN intentos_fallidos INT DEFAULT 0 AFTER ultimo_login,
ADD COLUMN bloqueado_hasta DATETIME AFTER intentos_fallidos;

-- ============================================
-- 2. AGREGAR COLUMNAS DE AUTENTICACIÓN A CLIENTES
-- ============================================

ALTER TABLE clientes 
ADD COLUMN password_hash VARCHAR(255) AFTER estado,
ADD COLUMN telefono_verificado TINYINT(1) DEFAULT 0 AFTER password_hash,
ADD COLUMN correo_verificado TINYINT(1) DEFAULT 0 AFTER telefono_verificado,
ADD COLUMN ultimo_login DATETIME AFTER correo_verificado,
ADD COLUMN intentos_fallidos INT DEFAULT 0 AFTER ultimo_login,
ADD COLUMN bloqueado_hasta DATETIME AFTER intentos_fallidos;

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
    fecha_uso TIMESTAMP NULL
);

CREATE INDEX idx_telefono_codigo ON codigos_verificacion(telefono);
CREATE INDEX idx_codigo_verificacion ON codigos_verificacion(codigo);

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
    activa TINYINT(1) DEFAULT 1
);

CREATE INDEX idx_token_sesion ON sesiones(token);
CREATE INDEX idx_usuario_sesion ON sesiones(tipo_usuario, id_usuario);

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
    fecha_intento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_correo_intento ON intentos_login(correo);

-- ============================================
-- 6. CONFIGURACIÓN DE SEGURIDAD
-- ============================================

CREATE TABLE IF NOT EXISTS configuracion_seguridad (
    id_config INT PRIMARY KEY AUTO_INCREMENT,
    clave VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT NOT NULL,
    descripcion TEXT,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO configuracion_seguridad (clave, valor, descripcion) VALUES
('max_intentos_login', '5', 'Máximo de intentos de login antes de bloquear'),
('tiempo_bloqueo_minutos', '30', 'Tiempo de bloqueo en minutos'),
('duracion_sesion_horas', '24', 'Duración de la sesión en horas'),
('longitud_codigo_sms', '6', 'Longitud del código SMS'),
('expiracion_codigo_minutos', '10', 'Expiración del código SMS en minutos'),
('requiere_verificacion_sms', '1', 'Requiere verificación SMS')
ON DUPLICATE KEY UPDATE valor=VALUES(valor);

SELECT '✅ Sistema de autenticación instalado correctamente' AS resultado;
