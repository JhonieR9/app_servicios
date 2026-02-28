import mysql.connector

# Conexión a BD
conexion = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Jhonier18.",
    database="profiles_cv_db"
)

cursor = conexion.cursor()

print("\n" + "="*60)
print("VERIFICACIÓN DE TABLAS EN LA BASE DE DATOS")
print("="*60 + "\n")

# 1. Mostrar todas las tablas
print("📋 TABLAS ACTUALES:")
print("-" * 60)
cursor.execute("SHOW TABLES")
tablas = cursor.fetchall()
for tabla in tablas:
    print(f"  ✓ {tabla[0]}")

print(f"\n📊 Total de tablas: {len(tablas)}\n")

# 2. Verificar tablas duplicadas específicas
print("="*60)
print("🔍 VERIFICANDO TABLAS DUPLICADAS")
print("="*60 + "\n")

tablas_a_verificar = [
    ('trabajador_categorias', 'servicios_persona'),
    ('disponibilidad_trabajador', 'disponibilidad')
]

tablas_duplicadas = []

for tabla_duplicada, tabla_correcta in tablas_a_verificar:
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = 'profiles_cv_db' 
        AND table_name = '{tabla_duplicada}'
    """)
    existe = cursor.fetchone()[0] > 0
    
    if existe:
        print(f"⚠️  DUPLICADA: '{tabla_duplicada}' existe")
        print(f"   → Debe eliminarse y usar '{tabla_correcta}' en su lugar\n")
        tablas_duplicadas.append(tabla_duplicada)
    else:
        print(f"✅ OK: '{tabla_duplicada}' no existe")
        print(f"   → Se está usando correctamente '{tabla_correcta}'\n")

# 3. Verificar tablas necesarias
print("="*60)
print("✓ VERIFICANDO TABLAS NECESARIAS")
print("="*60 + "\n")

tablas_necesarias = [
    'personas',
    'servicios_persona',
    'disponibilidad',
    'clientes',
    'categorias_servicio',
    'solicitudes_servicio',
    'calificaciones',
    'notificaciones'
]

for tabla in tablas_necesarias:
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = 'profiles_cv_db' 
        AND table_name = '{tabla}'
    """)
    existe = cursor.fetchone()[0] > 0
    
    if existe:
        # Contar registros
        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
        total = cursor.fetchone()[0]
        print(f"✅ {tabla:30} → {total} registros")
    else:
        print(f"❌ {tabla:30} → NO EXISTE")

# 4. Verificar columnas GPS en disponibilidad
print("\n" + "="*60)
print("📍 VERIFICANDO COLUMNAS GPS EN 'disponibilidad'")
print("="*60 + "\n")

cursor.execute("""
    SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'profiles_cv_db' 
    AND TABLE_NAME = 'disponibilidad'
    AND COLUMN_NAME IN ('latitud', 'longitud', 'disponible', 'ultima_actualizacion')
""")

columnas_gps = cursor.fetchall()
if columnas_gps:
    for col in columnas_gps:
        print(f"✅ {col[0]:25} → {col[1]:20} (NULL: {col[2]})")
else:
    print("⚠️  No se encontraron columnas GPS")

# 5. Eliminar tablas duplicadas si existen
if tablas_duplicadas:
    print("\n" + "="*60)
    print("🗑️  ELIMINANDO TABLAS DUPLICADAS")
    print("="*60 + "\n")
    
    for tabla in tablas_duplicadas:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {tabla}")
            conexion.commit()
            print(f"✅ Tabla '{tabla}' eliminada correctamente")
        except Exception as e:
            print(f"❌ Error al eliminar '{tabla}': {e}")
else:
    print("\n" + "="*60)
    print("✅ NO HAY TABLAS DUPLICADAS PARA ELIMINAR")
    print("="*60)

# Resumen final
print("\n" + "="*60)
print("📊 RESUMEN FINAL")
print("="*60)
print(f"✅ Base de datos limpia y lista para usar")
print(f"📋 Total de tablas: {len(tablas)}")
print(f"🗑️  Tablas duplicadas eliminadas: {len(tablas_duplicadas)}")
print("="*60 + "\n")

cursor.close()
conexion.close()
