import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Jhonier18.",
    database="profiles_cv_db"
)

cursor = conn.cursor()

print("=" * 60)
print("ESTRUCTURA DE LA TABLA PERSONAS")
print("=" * 60)

cursor.execute("DESCRIBE personas")
columns = cursor.fetchall()

for col in columns:
    print(f"{col[0]:<30} {col[1]:<20} {col[2]}")

print("\n" + "=" * 60)
print("ESTRUCTURA DE LA TABLA SERVICIOS_PERSONA")
print("=" * 60)

cursor.execute("DESCRIBE servicios_persona")
columns = cursor.fetchall()

for col in columns:
    print(f"{col[0]:<30} {col[1]:<20} {col[2]}")

conn.close()
