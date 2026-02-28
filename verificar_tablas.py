import mysql.connector

conexion = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Jhonier18.",
    database="profiles_cv_db"
)

cursor = conexion.cursor()
cursor.execute("SHOW TABLES")
tablas = cursor.fetchall()

print("📋 Tablas existentes en profiles_cv_db:")
for tabla in tablas:
    print(f"  - {tabla[0]}")

cursor.close()
conexion.close()
