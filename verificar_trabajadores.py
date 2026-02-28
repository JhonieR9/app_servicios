import mysql.connector

# Conectar a la base de datos
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Jhonier18.",
    database="profiles_cv_db"
)

cursor = conn.cursor(dictionary=True)

# Verificar trabajadores
print("=" * 60)
print("TRABAJADORES EN LA BASE DE DATOS")
print("=" * 60)

cursor.execute("""
    SELECT id_persona, nombre_completo, ciudad, estado 
    FROM personas 
    ORDER BY id_persona DESC 
    LIMIT 10
""")

trabajadores = cursor.fetchall()

if not trabajadores:
    print("\n❌ NO HAY TRABAJADORES EN LA BASE DE DATOS")
else:
    print(f"\n✅ Total encontrados: {len(trabajadores)}\n")
    for t in trabajadores:
        estado = t.get('estado') or 'NULL'
        print(f"ID: {t['id_persona']}")
        print(f"Nombre: {t['nombre_completo']}")
        print(f"Ciudad: {t['ciudad']}")
        print(f"Estado: {estado}")
        
        # Verificar servicios
        cursor.execute("""
            SELECT categoria, valor_hora 
            FROM servicios_persona 
            WHERE id_persona = %s
        """, (t['id_persona'],))
        servicios = cursor.fetchall()
        
        if servicios:
            print(f"Servicios: {len(servicios)}")
            for s in servicios:
                print(f"  - {s['categoria']}: ${s['valor_hora']}")
        else:
            print("Servicios: Ninguno")
        
        print("-" * 60)

# Verificar estadísticas
print("\n" + "=" * 60)
print("ESTADÍSTICAS")
print("=" * 60)

cursor.execute("SELECT COUNT(*) as total FROM personas")
total_todos = cursor.fetchone()['total']
print(f"Total personas (todos): {total_todos}")

cursor.execute("SELECT COUNT(*) as total FROM personas WHERE estado = 'activo'")
total_activos = cursor.fetchone()['total']
print(f"Total personas (activos): {total_activos}")

cursor.execute("SELECT COUNT(*) as total FROM personas WHERE estado IS NULL")
total_null = cursor.fetchone()['total']
print(f"Total personas (estado NULL): {total_null}")

cursor.execute("SELECT COUNT(*) as total FROM servicios_persona")
total_servicios = cursor.fetchone()['total']
print(f"Total servicios registrados: {total_servicios}")

conn.close()
print("\n✅ Verificación completada")
