import mysql.connector

# Conexión
conexion = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Jhonier18.",
    database="profiles_cv_db"
)

cursor = conexion.cursor()

print("\n" + "="*60)
print("INSTALANDO SISTEMA DE AUTENTICACIÓN")
print("="*60 + "\n")

# 1. Agregar columnas a personas
print("1. Agregando columnas a tabla personas...")
try:
    cursor.execute("""
        ALTER TABLE personas 
        ADD COLUMN password_hash VARCHAR(255),
        ADD COLUMN telefono_verificado TINYINT(1) DEFAULT 0,
        ADD COLUMN correo_verificado TINYINT(1) DEFAULT 0,
        ADD COLUMN ultimo_login DATETIME,
        ADD COLUMN intentos_fallidos INT DEFAULT 0,
        ADD COLUMN bloqueado_hasta DATETIME
    """)
    conexion.commit()
    print("   ✅ Columnas agregadas a personas")
except Exception as e:
    print(f"   ⚠️  {e}")

# 2. Agregar columnas a clientes
print("\n2. Agregando columnas a tabla clientes...")
try:
    cursor.execute("""
        ALTER TABLE clientes 
        ADD COLUMN password_hash VARCHAR(255),
        ADD COLUMN telefono_verificado TINYINT(1) DEFAULT 0,
        ADD COLUMN correo_verificado TINYINT(1) DEFAULT 0,
        ADD COLUMN ultimo_login DATETIME,
        ADD COLUMN intentos_fallidos INT DEFAULT 0,
        ADD COLUMN bloqueado_hasta DATETIME
    """)
    conexion.commit()
    print("   ✅ Columnas agregadas a clientes")
except Exception as e:
    print(f"   ⚠️  {e}")

# 3. Crear tabla de códigos de verificación
print("\n3. Creando tabla codigos_verificacion...")
try:
    cursor.execute("""
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
            INDEX idx_codigo (codigo)
        )
    """)
    conexion.commit()
    print("   ✅ Tabla codigos_verificacion creada")
except Exception as e:
    print(f"   ⚠️  {e}")

# 4. Crear tabla de sesiones
print("\n4. Creando tabla sesiones...")
try:
    cursor.execute("""
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
        )
    """)
    conexion.commit()
    print("   ✅ Tabla sesiones creada")
except Exception as e:
    print(f"   ⚠️  {e}")

# 5. Crear tabla de intentos de login
print("\n5. Creando tabla intentos_login...")
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS intentos_login (
            id_intento INT PRIMARY KEY AUTO_INCREMENT,
            tipo_usuario ENUM('trabajador', 'cliente', 'admin') NOT NULL,
            correo VARCHAR(255),
            ip_address VARCHAR(45),
            exitoso TINYINT(1) NOT NULL,
            mensaje TEXT,
            fecha_intento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_correo (correo)
        )
    """)
    conexion.commit()
    print("   ✅ Tabla intentos_login creada")
except Exception as e:
    print(f"   ⚠️  {e}")

# 6. Crear tabla de configuración
print("\n6. Creando tabla configuracion_seguridad...")
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracion_seguridad (
            id_config INT PRIMARY KEY AUTO_INCREMENT,
            clave VARCHAR(100) UNIQUE NOT NULL,
            valor TEXT NOT NULL,
            descripcion TEXT,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        INSERT INTO configuracion_seguridad (clave, valor, descripcion) VALUES
        ('max_intentos_login', '5', 'Máximo de intentos de login'),
        ('tiempo_bloqueo_minutos', '30', 'Tiempo de bloqueo en minutos'),
        ('duracion_sesion_horas', '24', 'Duración de sesión en horas'),
        ('longitud_codigo_sms', '6', 'Longitud del código SMS'),
        ('expiracion_codigo_minutos', '10', 'Expiración código SMS'),
        ('requiere_verificacion_sms', '1', 'Requiere verificación SMS')
        ON DUPLICATE KEY UPDATE valor=VALUES(valor)
    """)
    conexion.commit()
    print("   ✅ Tabla configuracion_seguridad creada")
except Exception as e:
    print(f"   ⚠️  {e}")

print("\n" + "="*60)
print("✅ SISTEMA DE AUTENTICACIÓN INSTALADO")
print("="*60 + "\n")

cursor.close()
conexion.close()
