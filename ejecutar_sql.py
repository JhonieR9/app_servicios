import mysql.connector

# Conexión a MySQL
conexion = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Jhonier18.",
    database="profiles_cv_db",
    autocommit=False
)

cursor = conexion.cursor()

# Leer el archivo SQL
with open('database_mvp.sql', 'r', encoding='utf-8') as file:
    sql_script = file.read()

# Dividir por statement considerando delimitadores
statements = []
current_statement = []
in_delimiter = False

for line in sql_script.split('\n'):
    line = line.strip()
    
    # Ignorar comentarios y líneas vacías
    if not line or line.startswith('--'):
        continue
    
    current_statement.append(line)
    
    # Si termina con ; es fin de statement
    if line.endswith(';'):
        full_statement = ' '.join(current_statement)
        statements.append(full_statement)
        current_statement = []

# Ejecutar cada statement
errores = 0
exitosos = 0

for i, statement in enumerate(statements, 1):
    if statement.strip():
        try:
            cursor.execute(statement)
            conexion.commit()
            exitosos += 1
            # Mostrar solo primeras palabras del statement
            preview = ' '.join(statement.split()[:5])
            print(f"✅ [{i}] {preview}...")
        except Exception as e:
            errores += 1
            preview = ' '.join(statement.split()[:8])
            print(f"⚠️ [{i}] Error: {str(e)[:80]}")
            print(f"   Statement: {preview}...")

cursor.close()
conexion.close()

print(f"\n{'='*50}")
print(f"🎉 Proceso completado")
print(f"✅ Exitosos: {exitosos}")
print(f"⚠️ Errores: {errores}")
print(f"{'='*50}")
