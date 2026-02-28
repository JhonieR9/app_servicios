import mysql.connector
import bcrypt
import time

def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

try:
    print("Conectando a MySQL...")
    conexion = mysql.connector.connect(
        host="localhost", user="root",
        password="Jhonier18.", database="profiles_cv_db",
        autocommit=False
    )
    cursor = conexion.cursor()
    
    # Limpiar datos anteriores
    print("Limpiando datos de prueba anteriores...")
    cursor.execute("DELETE FROM correo_cliente WHERE correo = 'cliente@test.com'")
    cursor.execute("DELETE FROM correo_persona WHERE correo = 'trabajador@test.com'")
    cursor.execute("DELETE FROM clientes WHERE numero_documento = '1234567890'")
    cursor.execute("DELETE FROM personas WHERE numero_documento = '9876543210'")
    conexion.commit()
    time.sleep(1)
    
    print("Creando cliente...")
    cursor.execute("INSERT INTO clientes (id_tipo_documento, numero_documento, nombre_completo, pais, departamento, ciudad, fecha_registro, estado) VALUES (1, '1234567890', 'Juan Pérez', 'Colombia', 'Valle del Cauca', 'Cali', NOW(), 'activo')")
    conexion.commit()
    id_cliente = cursor.lastrowid
    
    cursor.execute("INSERT INTO correo_cliente (id_cliente, correo, verificado, principal) VALUES (%s, 'cliente@test.com', 1, 1)", (id_cliente,))
    cursor.execute("INSERT INTO telefono_cliente (id_cliente, telefono, tipo_telefono, principal) VALUES (%s, '3001234567', 'celular', 1)", (id_cliente,))
    
    password_hash = hash_password("cliente123")
    cursor.execute("UPDATE clientes SET password_hash = %s WHERE id_cliente = %s", (password_hash, id_cliente))
    conexion.commit()
    print("✅ Cliente: cliente@test.com / cliente123")
    
    print("Creando trabajador...")
    cursor.execute("INSERT INTO personas (id_tipo_documento, numero_documento, nombre_completo, pais, departamento, ciudad, estado) VALUES (1, '9876543210', 'Carlos Rodríguez', 'Colombia', 'Valle del Cauca', 'Cali', 'activo')")
    conexion.commit()
    id_persona = cursor.lastrowid
    
    cursor.execute("INSERT INTO correo_persona (id_persona, correo, verificado, principal) VALUES (%s, 'trabajador@test.com', 1, 1)", (id_persona,))
    cursor.execute("INSERT INTO servicios_persona (id_persona, categoria, descripcion, valor_hora, anios_experiencia) VALUES (%s, 'Plomería', 'Servicio', 25000, 5)", (id_persona,))
    cursor.execute("INSERT INTO disponibilidad (id_persona, disponible, latitud, longitud, ultima_actualizacion) VALUES (%s, 1, 3.431608, -76.522041, NOW())", (id_persona,))
    
    password_hash = hash_password("trabajador123")
    cursor.execute("UPDATE personas SET password_hash = %s WHERE id_persona = %s", (password_hash, id_persona))
    conexion.commit()
    print("✅ Trabajador: trabajador@test.com / trabajador123")
    
    cursor.execute("INSERT INTO configuracion_seguridad (clave, valor) VALUES ('requiere_verificacion_sms', '0') ON DUPLICATE KEY UPDATE valor = '0'")
    conexion.commit()
    
    cursor.close()
    conexion.close()
    
    print("\n" + "="*50)
    print("✅ DATOS DE PRUEBA CREADOS")
    print("="*50)
    print("\n🚀 Ejecuta: uvicorn main:app --host 0.0.0.0 --port 8000")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 Solución:")
    print("1. Cierra todas las terminales con uvicorn")
    print("2. Abre MySQL Workbench y ejecuta: FLUSH TABLES;")
    print("3. Intenta de nuevo")
