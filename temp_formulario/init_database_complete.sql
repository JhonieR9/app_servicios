-- =====================================================
-- BASE DE DATOS: REGISTRO DE PROFESIONALES Y SERVICIOS
-- Versión: 2.0 - Actualizada con nomenclatura de servicios
-- =====================================================

CREATE DATABASE IF NOT EXISTS profiles_cv_db;
USE profiles_cv_db;

-- =====================================================
-- LIMPIEZA (ORDEN CORRECTO)
-- =====================================================
DROP TABLE IF EXISTS persona_servicio;
DROP TABLE IF EXISTS disponibilidad;
DROP TABLE IF EXISTS detalles_persona;
DROP TABLE IF EXISTS correo_persona;
DROP TABLE IF EXISTS telefono_persona;
DROP TABLE IF EXISTS servicios_persona;
DROP TABLE IF EXISTS experiencia_persona;
DROP TABLE IF EXISTS personas;
DROP TABLE IF EXISTS detalle_parametro;
DROP TABLE IF EXISTS parametros_generales;

-- =====================================================
-- PARAMETROS GENERALES
-- =====================================================
CREATE TABLE parametros_generales (
    id_parametro INT AUTO_INCREMENT PRIMARY KEY,
    nombre_parametro VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(100),
    INDEX idx_nombre (nombre_parametro)
);

-- =====================================================
-- DETALLE PARAMETRO
-- =====================================================
CREATE TABLE detalle_parametro (
    id_detalle INT AUTO_INCREMENT PRIMARY KEY,
    id_parametro INT NOT NULL,
    descripcion VARCHAR(80) NOT NULL,
    activo TINYINT(1) DEFAULT 1,
    FOREIGN KEY (id_parametro)
        REFERENCES parametros_generales(id_parametro)
        ON DELETE CASCADE,
    INDEX idx_parametro (id_parametro)
);

-- =====================================================
-- PERSONAS (DATOS PRINCIPALES)
-- =====================================================
CREATE TABLE personas (
    id_persona INT AUTO_INCREMENT PRIMARY KEY,
    id_tipo_documento INT NOT NULL,
    numero_documento VARCHAR(20) NOT NULL,
    id_genero INT NOT NULL,
    nombre_completo VARCHAR(80) NOT NULL,
    ciudad VARCHAR(80) NOT NULL,
    codigo_dane CHAR(5) NOT NULL,
    registrado_por VARCHAR(80) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    fecha_eliminacion TIMESTAMP NULL,
    estado ENUM('activo', 'inactivo', 'eliminado') DEFAULT 'activo',
    FOREIGN KEY (id_tipo_documento)
        REFERENCES detalle_parametro(id_detalle),
    FOREIGN KEY (id_genero)
        REFERENCES detalle_parametro(id_detalle),
    UNIQUE KEY unique_documento (numero_documento),
    INDEX idx_ciudad (ciudad),
    INDEX idx_estado (estado),
    INDEX idx_fecha (fecha_registro)
);

-- =====================================================
-- TELEFONO
-- =====================================================
CREATE TABLE telefono_persona (
    id_telefono INT AUTO_INCREMENT PRIMARY KEY,
    id_persona INT NOT NULL UNIQUE,
    telefono VARCHAR(20) NOT NULL,
    FOREIGN KEY (id_persona)
        REFERENCES personas(id_persona)
        ON DELETE CASCADE
);

-- =====================================================
-- CORREO (OPCIONAL)
-- =====================================================
CREATE TABLE correo_persona (
    id_correo INT AUTO_INCREMENT PRIMARY KEY,
    id_persona INT NOT NULL UNIQUE,
    correo VARCHAR(120),
    FOREIGN KEY (id_persona)
        REFERENCES personas(id_persona)
        ON DELETE CASCADE,
    INDEX idx_correo (correo)
);

-- =====================================================
-- EXPERIENCIA GENERAL
-- =====================================================
CREATE TABLE experiencia_persona (
    id_experiencia INT AUTO_INCREMENT PRIMARY KEY,
    id_persona INT NOT NULL UNIQUE,
    anios_experiencia INT,
    descripcion TEXT,
    FOREIGN KEY (id_persona)
        REFERENCES personas(id_persona)
        ON DELETE CASCADE
);

-- =====================================================
-- SERVICIOS OFRECIDOS (CON CATEGORÍA Y TARIFA)
-- =====================================================
CREATE TABLE servicios_persona (
    id_servicio INT AUTO_INCREMENT PRIMARY KEY,
    id_persona INT NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    descripcion TEXT NOT NULL,
    anios_experiencia DECIMAL(3,1) DEFAULT 0,
    valor_hora DECIMAL(10,2) DEFAULT 0,
    tiene_ayudante TINYINT(1) DEFAULT 0,
    costo_ayudante DECIMAL(10,2) DEFAULT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_persona)
        REFERENCES personas(id_persona)
        ON DELETE CASCADE,
    INDEX idx_persona (id_persona),
    INDEX idx_categoria (categoria),
    INDEX idx_valor (valor_hora),
    CHECK (valor_hora >= 0),
    CHECK (anios_experiencia >= 0),
    CHECK (costo_ayudante IS NULL OR costo_ayudante >= 0)
);

-- =====================================================
-- DISPONIBILIDAD
-- =====================================================
CREATE TABLE disponibilidad (
    id_disp INT AUTO_INCREMENT PRIMARY KEY,
    id_persona INT NOT NULL UNIQUE,
    id_horario INT NOT NULL,
    id_dias INT NOT NULL,
    FOREIGN KEY (id_persona)
        REFERENCES personas(id_persona)
        ON DELETE CASCADE,
    FOREIGN KEY (id_horario)
        REFERENCES detalle_parametro(id_detalle),
    FOREIGN KEY (id_dias)
        REFERENCES detalle_parametro(id_detalle)
);

-- =====================================================
-- DETALLES PERSONA (DOCUMENTOS Y ARCHIVOS)
-- =====================================================
CREATE TABLE detalles_persona (
    id_detalle_persona INT AUTO_INCREMENT PRIMARY KEY,
    id_persona INT NOT NULL UNIQUE,
    id_servicio_tipo INT,
    tareas TEXT,
    antecedentes_pdf VARCHAR(255),
    foto_identificacion VARCHAR(255),
    acepta_terminos TINYINT(1) DEFAULT 0,
    permisos_ubicacion TINYINT(1) DEFAULT 0,
    recomendaciones TEXT,
    recomendaciones_archivo VARCHAR(255),
    FOREIGN KEY (id_persona)
        REFERENCES personas(id_persona)
        ON DELETE CASCADE,
    FOREIGN KEY (id_servicio_tipo)
        REFERENCES detalle_parametro(id_detalle)
);

-- =====================================================
-- NOTA: La tabla persona_servicio fue eliminada
-- Ahora se usa servicios_persona para gestionar los servicios
-- =====================================================

-- =====================================================
-- MÓDULO DE CLIENTES
-- =====================================================

-- Tabla principal de clientes
CREATE TABLE clientes (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    id_tipo_documento INT NOT NULL,
    numero_documento VARCHAR(20) NOT NULL,
    nombre_completo VARCHAR(80) NOT NULL,
    pais VARCHAR(50) NOT NULL DEFAULT 'Colombia',
    departamento VARCHAR(50) NOT NULL,
    ciudad VARCHAR(80) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    estado ENUM('activo', 'inactivo', 'bloqueado') DEFAULT 'activo',
    FOREIGN KEY (id_tipo_documento)
        REFERENCES detalle_parametro(id_detalle),
    UNIQUE KEY unique_documento_cliente (numero_documento),
    INDEX idx_ciudad_cliente (ciudad),
    INDEX idx_estado_cliente (estado),
    INDEX idx_fecha_cliente (fecha_registro)
);

-- Teléfono del cliente
CREATE TABLE telefono_cliente (
    id_telefono_cliente INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    tipo_telefono ENUM('celular', 'fijo') DEFAULT 'celular',
    principal TINYINT(1) DEFAULT 1,
    FOREIGN KEY (id_cliente)
        REFERENCES clientes(id_cliente)
        ON DELETE CASCADE,
    INDEX idx_cliente_telefono (id_cliente)
);

-- Correo del cliente
CREATE TABLE correo_cliente (
    id_correo_cliente INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    correo VARCHAR(120) NOT NULL,
    verificado TINYINT(1) DEFAULT 0,
    principal TINYINT(1) DEFAULT 1,
    FOREIGN KEY (id_cliente)
        REFERENCES clientes(id_cliente)
        ON DELETE CASCADE,
    INDEX idx_cliente_correo (id_cliente),
    INDEX idx_correo (correo)
);

-- Direcciones del cliente (puede tener múltiples)
CREATE TABLE direcciones_cliente (
    id_direccion INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    direccion_completa TEXT NOT NULL,
    ciudad VARCHAR(80) NOT NULL,
    departamento VARCHAR(50) NOT NULL,
    codigo_postal VARCHAR(10),
    referencia TEXT,
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    principal TINYINT(1) DEFAULT 0,
    FOREIGN KEY (id_cliente)
        REFERENCES clientes(id_cliente)
        ON DELETE CASCADE,
    INDEX idx_cliente_direccion (id_cliente),
    INDEX idx_ciudad_direccion (ciudad)
);

-- =====================================================
-- INSERTAR PARÁMETROS GENERALES
-- =====================================================
INSERT INTO parametros_generales (nombre_parametro, descripcion) VALUES
('tipo_documento', 'Tipos de documentos de identidad'),
('genero', 'Géneros disponibles'),
('horario', 'Horarios de disponibilidad'),
('dias_disponibles', 'Días de la semana disponibles'),
('servicio_tipo', 'Tipo de servicios ofrecidos'),
('departamento', 'Departamentos de Colombia');

-- =====================================================
-- INSERTAR DETALLES DE PARÁMETROS
-- =====================================================

-- Tipos de documento
INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Cédula de Ciudadanía'
FROM parametros_generales WHERE nombre_parametro = 'tipo_documento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Cédula de Extranjería'
FROM parametros_generales WHERE nombre_parametro = 'tipo_documento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Pasaporte'
FROM parametros_generales WHERE nombre_parametro = 'tipo_documento';

-- Géneros
INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Masculino'
FROM parametros_generales WHERE nombre_parametro = 'genero';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Femenino'
FROM parametros_generales WHERE nombre_parametro = 'genero';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Otro'
FROM parametros_generales WHERE nombre_parametro = 'genero';

-- Horarios
INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, '8am-12pm'
FROM parametros_generales WHERE nombre_parametro = 'horario';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, '2pm-6pm'
FROM parametros_generales WHERE nombre_parametro = 'horario';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, '6pm-10pm'
FROM parametros_generales WHERE nombre_parametro = 'horario';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, '24 horas'
FROM parametros_generales WHERE nombre_parametro = 'horario';

-- Días disponibles
INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Entre Semana (Lunes-Viernes)'
FROM parametros_generales WHERE nombre_parametro = 'dias_disponibles';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Toda la Semana'
FROM parametros_generales WHERE nombre_parametro = 'dias_disponibles';

-- Tipos de servicios
INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Un servicio principal'
FROM parametros_generales WHERE nombre_parametro = 'servicio_tipo';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Varios servicios'
FROM parametros_generales WHERE nombre_parametro = 'servicio_tipo';

-- Departamentos de Colombia
INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Amazonas'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Antioquia'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Arauca'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Atlántico'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Bolívar'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Boyacá'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Caldas'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Caquetá'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Casanare'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Cauca'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Cesar'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Chocó'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Córdoba'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Cundinamarca'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Guainía'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Guaviare'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Huila'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'La Guajira'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Magdalena'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Meta'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Nariño'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Norte de Santander'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Putumayo'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Quindío'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Risaralda'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'San Andrés y Providencia'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Santander'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Sucre'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Tolima'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Valle del Cauca'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Vaupés'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Vichada'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

INSERT INTO detalle_parametro (id_parametro, descripcion)
SELECT id_parametro, 'Bogotá D.C.'
FROM parametros_generales WHERE nombre_parametro = 'departamento';

-- =====================================================
-- VISTAS ÚTILES
-- =====================================================

-- Vista completa de profesionales con sus servicios
CREATE OR REPLACE VIEW vista_profesionales AS
SELECT 
    p.id_persona,
    p.nombre_completo,
    p.numero_documento,
    p.ciudad,
    p.codigo_dane,
    p.registrado_por,
    p.fecha_registro,
    p.estado,
    td.descripcion AS tipo_documento,
    g.descripcion AS genero,
    tp.telefono,
    cp.correo,
    GROUP_CONCAT(DISTINCT sp.categoria SEPARATOR ', ') AS categorias_servicios,
    COUNT(DISTINCT sp.id_servicio) AS total_servicios,
    MIN(sp.valor_hora) AS tarifa_minima,
    MAX(sp.valor_hora) AS tarifa_maxima,
    AVG(sp.valor_hora) AS tarifa_promedio
FROM personas p
LEFT JOIN detalle_parametro td ON p.id_tipo_documento = td.id_detalle
LEFT JOIN detalle_parametro g ON p.id_genero = g.id_detalle
LEFT JOIN telefono_persona tp ON p.id_persona = tp.id_persona
LEFT JOIN correo_persona cp ON p.id_persona = cp.id_persona
LEFT JOIN servicios_persona sp ON p.id_persona = sp.id_persona
GROUP BY p.id_persona;

-- =====================================================
-- COMENTARIOS FINALES
-- =====================================================
-- Base de datos optimizada con:
-- ✓ Nomenclatura actualizada (servicios en lugar de habilidades)
-- ✓ Índices para búsquedas rápidas
-- ✓ Validaciones con CHECK constraints
-- ✓ Campo registrado_por para auditoría
-- ✓ Campos de fecha de actualización
-- ✓ Estado activo/inactivo
-- ✓ Vista para consultas complejas
-- ✓ Unique constraint en número de documento
