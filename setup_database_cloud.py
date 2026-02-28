"""
Script para configurar la base de datos en Railway (o cualquier servidor en la nube)
"""
import mysql.connector
from config import DB_CONFIG
import os

print("=" * 60)
print("CONFIGURANDO BASE DE DATOS EN LA NUBE")
print("=" * 60)

# Mostrar configuración (sin password)
print(f"\nHost: {DB_CONFIG['host']}")
print(f"User: {DB_CONFIG['user']}")
print(f"Database: {DB_CONFIG['database']}")
print(f"Port: {DB_CONFIG['port']}")

try:
    # Conectar a MySQL
    print("\n📡 Conectando a MySQL...")
    conexion = mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        port=DB_CONFIG['port']
    )
    cursor = conexion.cursor()
    print("✅ Conexión exitosa")
    
    # Crear base de datos si no existe
    print(f"\n📦 Creando base de datos '{DB_CONFIG['database']}'...")
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
    cursor.execute(f"USE {DB_CONFIG['database']}")
    print("✅ Base de datos lista")
    
    # Leer y ejecutar scripts SQL
    scripts = [
        'database_mvp.sql',
        'database_auth_fix.sql',
        'database_gps_fix.sql'
    ]
    
    for script in scripts:
        if os.path.exists(script):
            print(f"\n📄 Ejecutando {script}...")
            with open(script, 'r', encoding='utf-8') as f:
                sql_content = f.read()
                
                # Dividir por comandos (separados por ;)
                commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
                
                for cmd in commands:
                    try:
                        cursor.execute(cmd)
                    except mysql.connector.Error as e:
                        # Ignorar errores de tablas que ya existen
                        if "already exists" not in str(e).lower():
                            print(f"   ⚠️  {e}")
                
                conexion.commit()
                print(f"✅ {script} ejecutado")
        else:
            print(f"⚠️  {script} no encontrado")
    
    # Verificar tablas creadas
    print("\n📊 Verificando tablas...")
    cursor.execute("SHOW TABLES")
    tablas = cursor.fetchall()
    print(f"✅ {len(tablas)} tablas creadas:")
    for tabla in tablas:
        print(f"   - {tabla[0]}")
    
    # Verificar categorías de servicio
    print("\n🏷️  Verificando categorías de servicio...")
    cursor.execute("SELECT COUNT(*) FROM categorias_servicio")
    count = cursor.fetchone()[0]
    print(f"✅ {count} categorías disponibles")
    
    print("\n" + "=" * 60)
    print("✅ BASE DE DATOS CONFIGURADA CORRECTAMENTE")
    print("=" * 60)
    print("\n🚀 Tu aplicación está lista para usar")
    print(f"📝 Formulario: https://tu-app.railway.app/trabajador/registro")
    print(f"👤 Admin: https://tu-app.railway.app/trabajador/admin/login")
    
except mysql.connector.Error as e:
    print(f"\n❌ Error: {e}")
    print("\n💡 Verifica:")
    print("   1. Las credenciales de la base de datos")
    print("   2. Que la base de datos esté corriendo")
    print("   3. Las variables de entorno en Railway")
except Exception as e:
    print(f"\n❌ Error inesperado: {e}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conexion' in locals():
        conexion.close()
