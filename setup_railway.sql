-- ============================================
-- SCRIPT PARA CREAR TABLAS FALTANTES EN RAILWAY
-- Ejecutar en la consola MySQL de Railway
-- ============================================

-- 1. Categorías de servicio
CREATE TABLE IF NOT EXISTS `categorias_servicio` (
  `id_categoria` int NOT NULL AUTO_INCREMENT,
  `nombre_categoria` varchar(100) NOT NULL,
  `descripcion` text,
  `icono` varchar(50) DEFAULT NULL,
  `estado` varchar(20) DEFAULT 'activo',
  PRIMARY KEY (`id_categoria`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insertar las 14 categorías
INSERT IGNORE INTO `categorias_servicio` (id_categoria, nombre_categoria, estado) VALUES
(1,  'Plomería',     'activo'),
(2,  'Electricidad', 'activo'),
(3,  'Limpieza',     'activo'),
(4,  'Carpintería',  'activo'),
(5,  'Pintura',      'activo'),
(6,  'Jardinería',   'activo'),
(7,  'Mecánica',     'activo'),
(8,  'Tecnología',   'activo'),
(9,  'Construcción', 'activo'),
(10, 'Educación',    'activo'),
(11, 'Salud',        'activo'),
(12, 'Belleza',      'activo'),
(13, 'Gastronomía',  'activo'),
(14, 'Transporte',   'activo');

-- 2. Solicitudes de servicio
CREATE TABLE IF NOT EXISTS `solicitudes_servicio` (
  `id_solicitud`        int NOT NULL AUTO_INCREMENT,
  `id_cliente`          int DEFAULT NULL,
  `id_categoria`        int DEFAULT NULL,
  `id_trabajador`       int DEFAULT NULL,
  `titulo`              varchar(255) DEFAULT NULL,
  `descripcion`         text,
  `direccion_servicio`  text,
  `ciudad`              varchar(100) DEFAULT NULL,
  `departamento`        varchar(100) DEFAULT NULL,
  `fecha_programada`    datetime DEFAULT NULL,
  `estado`              varchar(50) DEFAULT 'pendiente',
  `fecha_solicitud`     datetime DEFAULT CURRENT_TIMESTAMP,
  `fecha_aceptacion`    datetime DEFAULT NULL,
  `fecha_inicio`        datetime DEFAULT NULL,
  `fecha_finalizacion`  datetime DEFAULT NULL,
  `precio_final`        decimal(10,2) DEFAULT NULL,
  `motivo_cancelacion`  text,
  PRIMARY KEY (`id_solicitud`),
  KEY `idx_solicitud_estado`    (`estado`),
  KEY `idx_solicitud_cliente`   (`id_cliente`),
  KEY `idx_solicitud_categoria` (`id_categoria`),
  KEY `idx_solicitud_trabajador`(`id_trabajador`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
