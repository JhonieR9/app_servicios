import mysql.connector
import os

# Credenciales de Railway
HOST = "centerbeam.proxy.rlwy.net"
PORT = 32047
USER = "root"
DATABASE = "railway"

# Pedir contraseña
PASSWORD = input("Ingresa la password de Railway: ")

print("🚀 CONFIGURANDO BASE DE DATOS EN RAILWAY")
print("=" * 50)
print(f"Host: {HOST}")
print(f"Port: {PORT}")
print(f"Database: {DATABASE}")
print("=" * 50)

try:
    # Conectar a Railway
    print("📡 Conectando a Railway MySQL...")
    conn = mysql.connector.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        autocommit=True
    )
    
    cursor = conn.cursor()
    print("✅ Conexión exitosa")
    
    # 1. CREAR TABLAS BÁSICAS PRIMERO
    print("\n📦 Creando tablas básicas...")
    
    # Tabla personas (trabajadores)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS personas (
        id_persona INT AUTO_INCREMENT PRIMARY KEY,
        nombre_completo VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        telefono VARCHAR(20),
        ciudad VARCHAR(100),
        departamento VARCHAR(100),
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        estado ENUM('activo', 'inactivo', 'suspendido') DEFAULT 'activo',
        password_hash VARCHAR(255),
        email_verificado BOOLEAN DEFAULT FALSE,
        telefono_verificado BOOLEAN DEFAULT FALSE
    )
    """)
    print("✅ Tabla personas creada")
    
    # Tabla clientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id_cliente INT AUTO_INCREMENT PRIMARY KEY,
        nombre_completo VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        telefono VARCHAR(20),
        direccion TEXT,
        ciudad VARCHAR(100),
        departamento VARCHAR(100),
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        estado ENUM('activo', 'inactivo', 'suspendido') DEFAULT 'activo',
        password_hash VARCHAR(255),
        email_verificado BOOLEAN DEFAULT FALSE,
        telefono_verificado BOOLEAN DEFAULT FALSE,
        foto_perfil VARCHAR(255) NULL,
        fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """)
    print("✅ Tabla clientes creada")
    
    # 2. CATEGORÍAS DE SERVICIO
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias_servicio (
        id_categoria INT AUTO_INCREMENT PRIMARY KEY,
        nombre_categoria VARCHAR(100) NOT NULL,
        descripcion TEXT,
        icono VARCHAR(50),
        estado ENUM('activo', 'inactivo') DEFAULT 'activo',
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("✅ Tabla categorias_servicio creada")
    
    # Insertar categorías
    cursor.execute("SELECT COUNT(*) FROM categorias_servicio")
    if cursor.fetchone()[0] == 0:
        categorias = [
            ('Plomería', 'Reparación e instalación de tuberías y sistemas de agua', '🔧'),
            ('Electricidad', 'Instalación y reparación eléctrica', '⚡'),
            ('Limpieza', 'Servicios de limpieza para hogar y oficina', '🧹'),
            ('Carpintería', 'Trabajos en madera y muebles', '🪚'),
            ('Pintura', 'Pintura de interiores y exteriores', '🎨'),
            ('Jardinería', 'Mantenimiento de jardines y áreas verdes', '🌱'),
            ('Cerrajería', 'Servicios de cerrajería y seguridad', '🔑'),
            ('Mudanza', 'Servicios de transporte y mudanza', '📦')
        ]
        cursor.executemany(
            "INSERT INTO categorias_servicio (nombre_categoria, descripcion, icono) VALUES (%s, %s, %s)",
            categorias
        )
        print("✅ Categorías de servicio insertadas")
    
    # 3. SOLICITUDES DE SERVICIO
    cursor.execute("""
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
        tiempo_estimado INT NULL,
        notas_adicionales TEXT,
        fecha_aceptacion DATETIME NULL,
        fecha_inicio DATETIME NULL,
        fecha_finalizacion DATETIME NULL,
        motivo_cancelacion TEXT NULL,
        FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente) ON DELETE CASCADE,
        FOREIGN KEY (id_categoria) REFERENCES categorias_servicio(id_categoria),
        FOREIGN KEY (id_trabajador) REFERENCES personas(id_persona) ON DELETE SET NULL
    )
    """)
    print("✅ Tabla solicitudes_servicio creada")
    
    # 4. CALIFICACIONES
    cursor.execute("""
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
    )
    """)
    print("✅ Tabla calificaciones creada")
    
    # 5. SERVICIOS_PERSONA (reemplaza trabajador_categorias)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS servicios_persona (
        id INT AUTO_INCREMENT PRIMARY KEY,
        id_persona INT NOT NULL,
        id_categoria INT NOT NULL,
        experiencia_anos INT DEFAULT 0,
        certificado BOOLEAN DEFAULT FALSE,
        fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_persona) REFERENCES personas(id_persona) ON DELETE CASCADE,
        FOREIGN KEY (id_categoria) REFERENCES categorias_servicio(id_categoria) ON DELETE CASCADE,
        UNIQUE KEY unique_persona_categoria (id_persona, id_categoria)
    )
    """)
    print("✅ Tabla servicios_persona creada")
    
    # 6. DISPONIBILIDAD
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS disponibilidad (
        id_disponibilidad INT AUTO_INCREMENT PRIMARY KEY,
        id_persona INT NOT NULL,
        disponible BOOLEAN DEFAULT TRUE,
        latitud DECIMAL(10, 8) NULL,
        longitud DECIMAL(11, 8) NULL,
        ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (id_persona) REFERENCES personas(id_persona) ON DELETE CASCADE
    )
    """)
    print("✅ Tabla disponibilidad creada")
    
    # 7. NOTIFICACIONES
    cursor.execute("""
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
    )
    """)
    print("✅ Tabla notificaciones creada")
    
    # 8. TABLAS DE AUTENTICACIÓN
    print("\n🔐 Creando tablas de autenticación...")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS codigos_verificacion (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        codigo VARCHAR(6) NOT NULL,
        tipo ENUM('registro', 'login', 'recuperacion') NOT NULL,
        usado BOOLEAN DEFAULT FALSE,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fecha_expiracion TIMESTAMP NOT NULL,
        INDEX idx_email_codigo (email, codigo),
        INDEX idx_fecha_expiracion (fecha_expiracion)
    )
    """)
    print("✅ Tabla codigos_verificacion creada")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sesiones (
        id INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id INT NOT NULL,
        tipo_usuario ENUM('cliente', 'trabajador') NOT NULL,
        token_sesion VARCHAR(255) UNIQUE NOT NULL,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fecha_expiracion TIMESTAMP NOT NULL,
        activa BOOLEAN DEFAULT TRUE,
        ip_address VARCHAR(45),
        user_agent TEXT,
        INDEX idx_token (token_sesion),
        INDEX idx_usuario (usuario_id, tipo_usuario),
        INDEX idx_fecha_expiracion (fecha_expiracion)
    )
    """)
    print("✅ Tabla sesiones creada")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS intentos_login (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        ip_address VARCHAR(45),
        exitoso BOOLEAN DEFAULT FALSE,
        fecha_intento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_email_fecha (email, fecha_intento),
        INDEX idx_ip_fecha (ip_address, fecha_intento)
    )
    """)
    print("✅ Tabla intentos_login creada")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS configuracion_seguridad (
        id INT AUTO_INCREMENT PRIMARY KEY,
        clave VARCHAR(100) UNIQUE NOT NULL,
        valor VARCHAR(500) NOT NULL,
        descripcion TEXT,
        fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """)
    print("✅ Tabla configuracion_seguridad creada")
    
    # Insertar configuración de seguridad
    cursor.execute("SELECT COUNT(*) FROM configuracion_seguridad")
    if cursor.fetchone()[0] == 0:
        config_seguridad = [
            ('sms_verificacion_activa', 'false', 'Activar/desactivar verificación SMS'),
            ('max_intentos_login', '5', 'Máximo número de intentos de login'),
            ('tiempo_bloqueo_minutos', '15', 'Tiempo de bloqueo tras exceder intentos'),
            ('longitud_minima_password', '6', 'Longitud mínima de contraseña'),
            ('admin_password', 'admin123', 'Contraseña del administrador')
        ]
        cursor.executemany(
            "INSERT INTO configuracion_seguridad (clave, valor, descripcion) VALUES (%s, %s, %s)",
            config_seguridad
        )
        print("✅ Configuración de seguridad insertada")
    
    # 9. VERIFICAR TABLAS CREADAS
    cursor.execute("SHOW TABLES")
    tablas = cursor.fetchall()
    print(f"\n🎉 ¡BASE DE DATOS CONFIGURADA!")
    print(f"✅ {len(tablas)} tablas creadas:")
    for tabla in tablas:
        print(f"   - {tabla[0]}")
    
    print(f"\n🌐 Tu aplicación está lista en:")
    print(f"   https://web-production-191f4.up.railway.app")
    print(f"   Formulario: https://web-production-191f4.up.railway.app/trabajador/registro")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()

print("\n✅ Script completado")