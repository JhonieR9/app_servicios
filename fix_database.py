"""Solución rápida - Crea todo desde cero"""
import mysql.connector

print("🔧 Conectando a MySQL...")
try:
    # Conectar sin especificar base de datos
    conexion = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Jhonier18."
    )
    cursor = conexion.cursor()
    
    # Eliminar bases de datos con nombres incorrectos
    print("🗑️ Limpiando bases de datos antiguas...")
    cursor.execute("DROP DATABASE IF EXISTS profiles_cv_dv")
    cursor.execute("DROP DATABASE IF EXISTS profiles_cv_db")
    
    # Crear base de datos correcta
    print("📦 Creando base de datos profiles_cv_db...")
    cursor.execute("CREATE DATABASE profiles_cv_db")
    cursor.execute("USE profiles_cv_db")
    
    print("✅ Base de datos creada!")
    print("\n📋 Ahora ejecuta en orden:")
    print("1. python setup_database.py")
    print("2. python crear_datos_prueba.py")
    
    cursor.close()
    conexion.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
