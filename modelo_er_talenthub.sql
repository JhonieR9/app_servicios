-- ============================================================
-- MODELO ENTIDAD-RELACIÓN — TALENTHUB
-- Generado: Agosto 2026
-- Instrucciones:
--   1. DROP DATABASE IF EXISTS talenthub_modelo;
--   2. CREATE DATABASE talenthub_modelo;
--   3. USE talenthub_modelo;
--   4. Ejecutar este script completo
--   5. Database → Reverse Engineer → seleccionar talenthub_modelo
-- ============================================================

DROP DATABASE IF EXISTS talenthub_modelo;
CREATE DATABASE talenthub_modelo;
USE talenthub_modelo;

-- ════════════════════════════════════════════════════════════
-- TABLAS PRINCIPALES (sin dependencias)
-- ════════════════════════════════════════════════════════════

-- PERSONAS (Trabajadores)
CREATE TABLE `personas` (
  `id_persona` int NOT NULL AUTO_INCREMENT,
  `id_tipo_documento` int DEFAULT NULL COMMENT '1=CC,2=CE,3=PA,4=TI,5=NIT,6=PPT',
  `numero_documento` varchar(20) NOT NULL,
  `id_genero` int DEFAULT NULL COMMENT '1=Masculino,2=Femenino,3=NoBinario,4=NoDice',
  `nombre_completo` varchar(100) NOT NULL,
  `ciudad` varchar(100) DEFAULT NULL,
  `departamento` varchar(100) DEFAULT NULL,
  `codigo_dane` varchar(10) DEFAULT NULL,
  `fecha_nacimiento` date DEFAULT NULL,
  `ciudad_nacimiento` varchar(100) DEFAULT NULL,
  `nacionalidad` varchar(50) DEFAULT NULL,
  `estado` varchar(30) DEFAULT 'pendiente_revision' COMMENT 'pendiente_revision|activo|rechazado|eliminado|inactivo',
  `password_hash` varchar(255) DEFAULT NULL,
  `registrado_por` varchar(100) DEFAULT NULL,
  `fecha_registro` datetime DEFAULT CURRENT_TIMESTAMP,
  `fecha_eliminacion` datetime DEFAULT NULL,
  `intentos_fallidos` int DEFAULT 0,
  `ultimo_login` datetime DEFAULT NULL,
  PRIMARY KEY (`id_persona`),
  UNIQUE KEY `uk_documento` (`numero_documento`)
) ENGINE=InnoDB;

-- CLIENTES
CREATE TABLE `clientes` (
  `id_cliente` int NOT NULL AUTO_INCREMENT,
  `nombre_completo` varchar(100) NOT NULL,
  `estado` varchar(20) DEFAULT 'activo',
  `password_hash` varchar(255) DEFAULT NULL,
  `fecha_registro` datetime DEFAULT CURRENT_TIMESTAMP,
  `ultimo_login` datetime DEFAULT NULL,
  `intentos_fallidos` int DEFAULT 0,
  PRIMARY KEY (`id_cliente`)
) ENGINE=InnoDB;

-- CATEGORIAS DE SERVICIO (catálogo)
CREATE TABLE `categorias_servicio` (
  `id_categoria` int NOT NULL AUTO_INCREMENT,
  `nombre_categoria` varchar(100) NOT NULL,
  `descripcion` text,
  `icono` varchar(50) DEFAULT NULL,
  `estado` varchar(20) DEFAULT 'activo',
  PRIMARY KEY (`id_categoria`)
) ENGINE=InnoDB;

-- ════════════════════════════════════════════════════════════
-- TABLAS DEPENDIENTES DE PERSONAS
-- ════════════════════════════════════════════════════════════

-- DETALLES_PERSONA (documentos, archivos, medios de pago)
CREATE TABLE `detalles_persona` (
  `id_detalle` int NOT NULL AUTO_INCREMENT,
  `id_persona` int NOT NULL,
  `id_servicio_tipo` int DEFAULT NULL,
  `tareas` text,
  `foto_identificacion` varchar(255) DEFAULT NULL,
  `foto_identificacion_data` longblob,
  `foto_identificacion_tipo` varchar(50) DEFAULT NULL,
  `antecedentes_pdf` varchar(255) DEFAULT NULL,
  `antecedentes_data` longblob,
  `antecedentes_tipo` varchar(50) DEFAULT NULL,
  `recomendaciones` text,
  `recomendaciones_archivo` varchar(255) DEFAULT NULL,
  `recomendaciones_data` longblob,
  `recomendaciones_tipo` varchar(50) DEFAULT NULL,
  `certificado_estudio` varchar(255) DEFAULT NULL,
  `certificado_estudio_data` longblob,
  `certificado_estudio_tipo` varchar(50) DEFAULT NULL,
  `foto_perfil_data` longblob,
  `foto_perfil_tipo` varchar(50) DEFAULT NULL,
  `nivel_estudio` varchar(50) DEFAULT NULL,
  `acepta_terminos` tinyint(1) DEFAULT 0,
  `permisos_ubicacion` tinyint(1) DEFAULT 0,
  `medio_pago` varchar(200) DEFAULT NULL,
  `medio_pago_principal` varchar(50) DEFAULT NULL,
  `banco` varchar(100) DEFAULT NULL,
  `tipo_cuenta` varchar(20) DEFAULT NULL,
  `numero_cuenta` varchar(30) DEFAULT NULL,
  `titular_cuenta` varchar(120) DEFAULT NULL,
  `arl` varchar(100) DEFAULT NULL,
  `eps` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_detalle`),
  KEY `idx_det_persona` (`id_persona`),
  CONSTRAINT `fk_detalles_persona` FOREIGN KEY (`id_persona`) REFERENCES `personas` (`id_persona`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- TELEFONO_PERSONA
CREATE TABLE `telefono_persona` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_persona` int NOT NULL,
  `telefono` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_tel_persona` (`id_persona`),
  CONSTRAINT `fk_tel_persona` FOREIGN KEY (`id_persona`) REFERENCES `personas` (`id_persona`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- CORREO_PERSONA
CREATE TABLE `correo_persona` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_persona` int NOT NULL,
  `correo` varchar(255) DEFAULT NULL,
  `verificado` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_correo_persona` (`id_persona`),
  CONSTRAINT `fk_correo_persona` FOREIGN KEY (`id_persona`) REFERENCES `personas` (`id_persona`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- SERVICIOS_PERSONA
CREATE TABLE `servicios_persona` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_persona` int NOT NULL,
  `categoria` varchar(100) NOT NULL,
  `descripcion` text,
  `valor_hora` decimal(10,2) DEFAULT NULL,
  `anios_experiencia` decimal(4,1) DEFAULT NULL,
  `tiene_ayudante` tinyint(1) DEFAULT 0,
  `costo_ayudante` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_serv_persona` (`id_persona`),
  CONSTRAINT `fk_serv_persona` FOREIGN KEY (`id_persona`) REFERENCES `personas` (`id_persona`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- DISPONIBILIDAD
CREATE TABLE `disponibilidad` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_persona` int NOT NULL,
  `id_horario` int DEFAULT NULL,
  `id_dias` int DEFAULT NULL,
  `disponible` tinyint(1) DEFAULT 0,
  `latitud` decimal(10,8) DEFAULT NULL,
  `longitud` decimal(11,8) DEFAULT NULL,
  `ultima_actualizacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_disp_persona` (`id_persona`),
  CONSTRAINT `fk_disp_persona` FOREIGN KEY (`id_persona`) REFERENCES `personas` (`id_persona`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- CIUDADES_SERVICIO_TRABAJADOR
CREATE TABLE `ciudades_servicio_trabajador` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_persona` int NOT NULL,
  `ciudad` varchar(100) NOT NULL,
  `departamento` varchar(100) DEFAULT NULL,
  `fecha_agregada` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_ciudad_persona` (`id_persona`),
  CONSTRAINT `fk_ciudad_persona` FOREIGN KEY (`id_persona`) REFERENCES `personas` (`id_persona`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ESPECIALIDADES_TRABAJADOR
CREATE TABLE `especialidades_trabajador` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_persona` int NOT NULL,
  `categoria` varchar(100) NOT NULL,
  `especialidad` varchar(200) NOT NULL,
  `fecha_agregada` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_esp_persona` (`id_persona`),
  CONSTRAINT `fk_esp_persona` FOREIGN KEY (`id_persona`) REFERENCES `personas` (`id_persona`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- REFERENCIAS_PERSONALES
CREATE TABLE `referencias_personales` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_persona` int NOT NULL,
  `nombre` varchar(120) NOT NULL,
  `celular` varchar(15) NOT NULL,
  `correo` varchar(150) DEFAULT NULL,
  `descripcion` varchar(200) DEFAULT NULL,
  `fecha_agregada` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_ref_persona` (`id_persona`),
  CONSTRAINT `fk_ref_persona` FOREIGN KEY (`id_persona`) REFERENCES `personas` (`id_persona`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ════════════════════════════════════════════════════════════
-- TABLAS DEPENDIENTES DE CLIENTES
-- ════════════════════════════════════════════════════════════

-- CORREO_CLIENTE
CREATE TABLE `correo_cliente` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_cliente` int NOT NULL,
  `correo` varchar(255) NOT NULL,
  `verificado` tinyint(1) DEFAULT 0,
  `principal` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `idx_correo_cliente` (`id_cliente`),
  CONSTRAINT `fk_correo_cliente` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id_cliente`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- TELEFONO_CLIENTE
CREATE TABLE `telefono_cliente` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_cliente` int NOT NULL,
  `telefono` varchar(20) NOT NULL,
  `tipo_telefono` varchar(20) DEFAULT 'celular',
  `principal` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `idx_tel_cliente` (`id_cliente`),
  CONSTRAINT `fk_tel_cliente` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id_cliente`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- FAVORITOS_CLIENTE
CREATE TABLE `favoritos_cliente` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_cliente` int NOT NULL,
  `id_trabajador` int NOT NULL,
  `fecha_guardado` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_fav` (`id_cliente`, `id_trabajador`),
  KEY `idx_fav_cliente` (`id_cliente`),
  KEY `idx_fav_trabajador` (`id_trabajador`),
  CONSTRAINT `fk_fav_cliente` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id_cliente`) ON DELETE CASCADE,
  CONSTRAINT `fk_fav_trabajador` FOREIGN KEY (`id_trabajador`) REFERENCES `personas` (`id_persona`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ════════════════════════════════════════════════════════════
-- TABLAS DE NEGOCIO (dependen de personas + clientes + categorias)
-- ════════════════════════════════════════════════════════════

-- SOLICITUDES_SERVICIO
CREATE TABLE `solicitudes_servicio` (
  `id_solicitud` int NOT NULL AUTO_INCREMENT,
  `id_cliente` int DEFAULT NULL,
  `id_categoria` int DEFAULT NULL,
  `id_trabajador` int DEFAULT NULL,
  `titulo` varchar(255) DEFAULT NULL,
  `descripcion` text,
  `direccion_servicio` text,
  `ciudad` varchar(100) DEFAULT NULL,
  `departamento` varchar(100) DEFAULT NULL,
  `fecha_programada` datetime DEFAULT NULL,
  `estado` varchar(50) DEFAULT 'pendiente' COMMENT 'pendiente|cotizacion_enviada|aceptada|en_proceso|completada|cancelada',
  `metodo_pago` varchar(50) DEFAULT 'digital',
  `fecha_solicitud` datetime DEFAULT CURRENT_TIMESTAMP,
  `fecha_aceptacion` datetime DEFAULT NULL,
  `fecha_inicio` datetime DEFAULT NULL,
  `fecha_finalizacion` datetime DEFAULT NULL,
  `precio_final` decimal(10,2) DEFAULT NULL,
  `pago_estado` varchar(20) DEFAULT 'pendiente' COMMENT 'pendiente|pagado',
  `codigo_inicio` varchar(10) DEFAULT NULL,
  `codigo_confirmacion` varchar(10) DEFAULT NULL,
  `cotizacion_horas` decimal(4,1) DEFAULT NULL,
  `cotizacion_precio` decimal(10,2) DEFAULT NULL,
  `cotizacion_nota` text,
  `cotizacion_fecha` datetime DEFAULT NULL,
  `motivo_cancelacion` text,
  PRIMARY KEY (`id_solicitud`),
  KEY `idx_sol_cliente` (`id_cliente`),
  KEY `idx_sol_categoria` (`id_categoria`),
  KEY `idx_sol_trabajador` (`id_trabajador`),
  KEY `idx_sol_estado` (`estado`),
  CONSTRAINT `fk_sol_cliente` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id_cliente`) ON DELETE SET NULL,
  CONSTRAINT `fk_sol_categoria` FOREIGN KEY (`id_categoria`) REFERENCES `categorias_servicio` (`id_categoria`) ON DELETE SET NULL,
  CONSTRAINT `fk_sol_trabajador` FOREIGN KEY (`id_trabajador`) REFERENCES `personas` (`id_persona`) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ════════════════════════════════════════════════════════════
-- TABLAS DEPENDIENTES DE SOLICITUDES
-- ════════════════════════════════════════════════════════════

-- MENSAJES_CHAT
CREATE TABLE `mensajes_chat` (
  `id_mensaje` int NOT NULL AUTO_INCREMENT,
  `id_solicitud` int NOT NULL,
  `tipo_remitente` enum('cliente','trabajador','sistema') NOT NULL,
  `id_remitente` int DEFAULT NULL,
  `mensaje` text NOT NULL,
  `leido` tinyint(1) DEFAULT 0,
  `fecha_envio` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_mensaje`),
  KEY `idx_chat_solicitud` (`id_solicitud`),
  KEY `idx_chat_fecha` (`fecha_envio`),
  CONSTRAINT `fk_chat_solicitud` FOREIGN KEY (`id_solicitud`) REFERENCES `solicitudes_servicio` (`id_solicitud`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- PAGOS_SOLICITUD (Wompi)
CREATE TABLE `pagos_solicitud` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_solicitud` int NOT NULL,
  `id_cliente` int NOT NULL,
  `referencia_wompi` varchar(100) NOT NULL,
  `id_transaccion_wompi` varchar(100) DEFAULT NULL,
  `monto` decimal(10,2) NOT NULL,
  `estado_wompi` varchar(30) DEFAULT 'PENDING' COMMENT 'PENDING|APPROVED|DECLINED|VOIDED|ERROR',
  `dispersado` tinyint(1) DEFAULT 0,
  `fecha_dispersion` datetime DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT CURRENT_TIMESTAMP,
  `fecha_actualizacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_referencia` (`referencia_wompi`),
  KEY `idx_pago_solicitud` (`id_solicitud`),
  KEY `idx_pago_cliente` (`id_cliente`),
  CONSTRAINT `fk_pago_solicitud` FOREIGN KEY (`id_solicitud`) REFERENCES `solicitudes_servicio` (`id_solicitud`) ON DELETE CASCADE,
  CONSTRAINT `fk_pago_cliente` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id_cliente`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- CALIFICACIONES
CREATE TABLE `calificaciones` (
  `id_calificacion` int NOT NULL AUTO_INCREMENT,
  `id_solicitud` int DEFAULT NULL,
  `id_cliente` int DEFAULT NULL,
  `id_trabajador` int DEFAULT NULL,
  `tipo_calificacion` varchar(50) DEFAULT 'cliente_a_trabajador',
  `puntuacion` int DEFAULT NULL COMMENT '1 a 5 estrellas',
  `comentario` text,
  `tags` varchar(500) DEFAULT NULL,
  `fecha_calificacion` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_calificacion`),
  KEY `idx_cal_solicitud` (`id_solicitud`),
  KEY `idx_cal_trabajador` (`id_trabajador`),
  KEY `idx_cal_cliente` (`id_cliente`),
  CONSTRAINT `fk_cal_solicitud` FOREIGN KEY (`id_solicitud`) REFERENCES `solicitudes_servicio` (`id_solicitud`) ON DELETE SET NULL,
  CONSTRAINT `fk_cal_trabajador` FOREIGN KEY (`id_trabajador`) REFERENCES `personas` (`id_persona`) ON DELETE SET NULL,
  CONSTRAINT `fk_cal_cliente` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id_cliente`) ON DELETE SET NULL
) ENGINE=InnoDB;

-- FOTOS_SERVICIO
CREATE TABLE `fotos_servicio` (
  `id_foto` int NOT NULL AUTO_INCREMENT,
  `id_solicitud` int NOT NULL,
  `id_trabajador` int NOT NULL,
  `tipo_foto` enum('antes','despues','progreso') DEFAULT 'progreso',
  `foto_data` longblob NOT NULL,
  `foto_tipo` varchar(50) DEFAULT 'image/jpeg',
  `descripcion` varchar(200) DEFAULT NULL,
  `fecha_subida` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_foto`),
  KEY `idx_foto_solicitud` (`id_solicitud`),
  KEY `idx_foto_trabajador` (`id_trabajador`),
  CONSTRAINT `fk_foto_solicitud` FOREIGN KEY (`id_solicitud`) REFERENCES `solicitudes_servicio` (`id_solicitud`) ON DELETE CASCADE,
  CONSTRAINT `fk_foto_trabajador` FOREIGN KEY (`id_trabajador`) REFERENCES `personas` (`id_persona`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ════════════════════════════════════════════════════════════
-- TABLAS DE SISTEMA (autenticación, notificaciones)
-- ════════════════════════════════════════════════════════════

-- SESIONES
CREATE TABLE `sesiones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tipo_usuario` enum('trabajador','cliente') NOT NULL,
  `id_usuario` int NOT NULL,
  `token` varchar(100) NOT NULL,
  `activa` tinyint(1) DEFAULT 1,
  `ip_address` varchar(50) DEFAULT NULL,
  `user_agent` text,
  `fecha_creacion` datetime DEFAULT CURRENT_TIMESTAMP,
  `fecha_expiracion` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_token` (`token`),
  KEY `idx_sesion_usuario` (`tipo_usuario`, `id_usuario`)
) ENGINE=InnoDB;

-- PUSH_SUBSCRIPTIONS
CREATE TABLE `push_subscriptions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tipo_usuario` enum('trabajador','cliente') NOT NULL DEFAULT 'trabajador',
  `id_usuario` int NOT NULL,
  `endpoint` text NOT NULL,
  `p256dh` text NOT NULL,
  `auth` text NOT NULL,
  `fecha_reg` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_push_usuario` (`tipo_usuario`, `id_usuario`)
) ENGINE=InnoDB;

-- TOKENS_RECUPERACION
CREATE TABLE `tokens_recuperacion` (
  `id_token` int NOT NULL AUTO_INCREMENT,
  `tipo_usuario` enum('trabajador','cliente') NOT NULL,
  `id_usuario` int NOT NULL,
  `correo` varchar(255) NOT NULL,
  `token` varchar(100) NOT NULL,
  `usado` tinyint(1) DEFAULT 0,
  `fecha_expiracion` datetime NOT NULL,
  `fecha_creacion` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_token`),
  UNIQUE KEY `uk_token_rec` (`token`),
  KEY `idx_token_usuario` (`tipo_usuario`, `id_usuario`)
) ENGINE=InnoDB;
