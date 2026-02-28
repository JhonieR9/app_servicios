import mysql.connector

print("=" * 60)
print("LIMPIANDO TODAS LAS TABLAS")
print("=" * 60)

# Conectar a la base de datos
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Jhonier18.",
    database="profiles_cv_db"
)

cursor = conn.cursor()

try:
    # Desactivar verificación de claves foráneas temporalmente
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    
    # Lista de tablas a limpiar
    tablas = [
        # Tablas de trabajadores/personas
        'servicios_persona',
        'telefono_persona',
        'correo_persona',
        'experiencia_persona',
        'detalles_persona',
        'disponibilidad',
        'personas',
        
        # Tablas de clientes
        'correo_cliente',
        'telefono_cliente',
        'direcciones_cliente',
        'clientes',
        
        # Tablas de servicios
        'calificaciones',
        'notificaciones',
        'solicitudes_servicio',
        
        # Tablas de autenticación
        'codigos_verificacion',
        'sesiones',
        'intentos_login'
    ]
    
    for tabla in tablas:
        try:
            cursor.execute(f"TRUNCATE TABLE {tabla}")
            print(f"✅ Tabla '{tabla}' limpiada")
        except Exception as e:
            print(f"⚠️  Tabla '{tabla}': {str(e)}")
    
    # Reactivar verificación de claves foráneas
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    
    conn.commit()
    print("\n" + "=" * 60)
    print("✅ TODAS LAS TABLAS HAN SIDO LIMPIADAS")
    print("=" * 60)
    print("\nNOTA: Las categorías de servicio NO fueron eliminadas")
    print("Puedes registrar nuevos trabajadores desde cero")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()
