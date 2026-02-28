"""Configura la base de datos desde cero"""
import mysql.connector

print("Conectando a MySQL...")
conexion = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Jhonier18."
)
cursor = conexion.cursor()

print("Creando base de datos...")
cursor.execute("CREATE DATABASE IF NOT EXISTS profiles_cv_db")
cursor.execute("USE profiles_cv_db")
conexion.commit()

print("Ejecutando database_mvp.sql...")
with open('database_mvp.sql', 'r', encoding='utf-8') as f:
    sql = f.read()
    for statement in sql.split(';'):
        if statement.strip():
            try:
                cursor.execute(statement)
            except Exception as e:
                print(f"Advertencia: {e}")

print("Ejecutando database_auth_fix.sql...")
with open('database_auth_fix.sql', 'r', encoding='utf-8') as f:
    sql = f.read()
    for statement in sql.split(';'):
        if statement.strip():
            try:
                cursor.execute(statement)
            except Exception as e:
                print(f"Advertencia: {e}")

print("Ejecutando database_gps_fix.sql...")
with open('database_gps_fix.sql', 'r', encoding='utf-8') as f:
    sql = f.read()
    for statement in sql.split(';'):
        if statement.strip():
            try:
                cursor.execute(statement)
            except Exception as e:
                print(f"Advertencia: {e}")

conexion.commit()
cursor.close()
conexion.close()

print("\n✅ Base de datos configurada!")
print("Ahora ejecuta: python crear_datos_prueba.py")
