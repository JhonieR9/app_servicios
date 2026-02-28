import mysql.connector

# Credenciales de Railway (las que vimos antes)
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
    
    # Leer y ejecutar scripts SQL
    scripts = ['database_mvp.sql', 'database_auth_fix.sql', 'database_gps_fix.sql']
    
    for script in scripts:
        print(f"\n📄 Ejecutando {script}...")
        try:
            with open(script, 'r', encoding='utf-8') as f:
                sql_content = f.read()
                
                # Dividir por comandos
                commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
                
                for cmd in commands:
                    try:
                        cursor.execute(cmd)
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            print(f"   ⚠️  {e}")
                
                conn.commit()
                print(f"✅ {script} ejecutado")
        except FileNotFoundError:
            print(f"⚠️  {script} no encontrado")
    
    # Verificar tablas
    cursor.execute("SHOW TABLES")
    tablas = cursor.fetchall()
    print(f"\n✅ {len(tablas)} tablas creadas:")
    for tabla in tablas:
        print(f"   - {tabla[0]}")
    
    print("\n🎉 ¡Base de datos configurada correctamente!")
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()