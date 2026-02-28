import mysql.connector

# Credenciales de Railway
HOST = "centerbeam.proxy.rlwy.net"
PORT = 32047
USER = "root"
PASSWORD = input("Ingresa la password de Railway: ")
DATABASE = "railway"

print("Conectando a Railway MySQL...")

try:
    conn = mysql.connector.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE
    )
    
    cursor = conn.cursor()
    print("✅ Conexión exitosa")
    
    # Crear solo las tablas esenciales para el formulario
    tablas_sql = [
        # Tabla de personas (trabajadores)
        """
        CREATE TABLE IF NOT EXISTS personas (
            id_persona INT AUTO_INCREMENT PRIMARY KEY,
            numero_documento VARCHAR(50) NOT NULL,
            nombre_completo VARCHAR(255) NOT NULL,
            ciudad VARCHAR(100),
            estado VARCHAR(20) DEFAULT 'activo'
        )
        """,
        
        # Tabla de teléfonos
        """
        CREATE TABLE IF NOT EXISTS telefono_persona (
            id_telefono INT AUTO_INCREMENT PRIMARY KEY,
            id_persona INT,
            telefono VARCHAR(20),
            FOREIGN KEY (id_persona) REFERENCES personas(id_persona)
        )
        """,
        
        # Tabla de correos
        """
        CREATE TABLE IF NOT EXISTS correo_persona (
            id_correo INT AUTO_INCREMENT PRIMARY KEY,
            id_persona INT,
            correo VARCHAR(255),
            FOREIGN KEY (id_persona) REFERENCES personas(id_persona)
        )
        """,
        
        # Tabla de servicios
        """
        CREATE TABLE IF NOT EXISTS servicios_persona (
            id_servicio INT AUTO_INCREMENT PRIMARY KEY,
            id_persona INT,
            categoria VARCHAR(100),
            descripcion TEXT,
            valor_hora DECIMAL(10,2),
            anios_experiencia INT,
            FOREIGN KEY (id_persona) REFERENCES personas(id_persona)
        )
        """,
        
        # Tabla de categorías
        """
        CREATE TABLE IF NOT EXISTS categorias_servicio (
            id_categoria INT AUTO_INCREMENT PRIMARY KEY,
            nombre_categoria VARCHAR(100) NOT NULL,
            descripcion TEXT,
            estado VARCHAR(20) DEFAULT 'activo'
        )
        """
    ]
    
    # Ejecutar creación de tablas
    for i, sql in enumerate(tablas_sql, 1):
        print(f"📄 Creando tabla {i}/5...")
        cursor.execute(sql)
        conn.commit()
    
    # Insertar categorías básicas
    print("📄 Insertando categorías de servicio...")
    categorias = [
        ('Plomería', 'Servicios de fontanería y tuberías'),
        ('Electricidad', 'Instalaciones y reparaciones eléctricas'),
        ('Limpieza', 'Servicios de limpieza y aseo'),
        ('Carpintería', 'Trabajos en madera y muebles'),
        ('Pintura', 'Pintura de interiores y exteriores'),
        ('Jardinería', 'Cuidado de jardines y plantas'),
        ('Cerrajería', 'Servicios de cerrajería y seguridad'),
        ('Mudanza', 'Servicios de mudanza y transporte')
    ]
    
    for nombre, desc in categorias:
        cursor.execute("""
            INSERT IGNORE INTO categorias_servicio (nombre_categoria, descripcion)
            VALUES (%s, %s)
        """, (nombre, desc))
    
    conn.commit()
    
    # Verificar tablas
    cursor.execute("SHOW TABLES")
    tablas = cursor.fetchall()
    print(f"\n✅ {len(tablas)} tablas creadas:")
    for tabla in tablas:
        print(f"   - {tabla[0]}")
    
    print("\n🎉 ¡Base de datos básica configurada!")
    print("📝 El formulario de registro ya puede funcionar")
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()