import mysql.connector

# Credenciales de Railway
HOST = "centerbeam.proxy.rlwy.net"
PORT = 32047
USER = "root"
PASSWORD = input("Ingresa la password de Railway: ")
DATABASE = "railway"

print("Conectando a Railway MySQL...")

try:
    conn = mysql.connector.connect(
        host=HOST, port=PORT, user=USER,
        password=PASSWORD, database=DATABASE
    )
    cursor = conn.cursor()
    print("✅ Conexión exitosa\n")

    # Todas las categorías necesarias
    categorias = [
        # Hogar y construcción
        ('Plomería',        'Reparación de tuberías, grifos, baños y sistemas de agua'),
        ('Electricidad',    'Instalaciones eléctricas, reparaciones y mantenimiento'),
        ('Carpintería',     'Muebles, puertas, ventanas y trabajos en madera'),
        ('Pintura',         'Pintura de interiores, exteriores e impermeabilización'),
        ('Construcción',    'Remodelaciones, pisos, techos y obras civiles'),
        ('Cerrajería',      'Apertura de puertas, cambio de chapas y seguridad'),
        ('Vidriería',       'Instalación y reparación de vidrios y ventanas'),
        ('Impermeabilización', 'Sellado de filtraciones y techos'),

        # Limpieza y mantenimiento
        ('Limpieza',        'Limpieza de hogares, oficinas y espacios comerciales'),
        ('Lavandería',      'Lavado y planchado de ropa a domicilio'),
        ('Control de plagas','Fumigación y eliminación de insectos y roedores'),
        ('Jardinería',      'Corte de césped, poda, diseño y mantenimiento de jardines'),

        # Tecnología
        ('Tecnología',      'Reparación de computadores, redes WiFi e instalaciones'),
        ('Electrodomésticos','Reparación de neveras, lavadoras, hornos y más'),
        ('CCTV y Alarmas',  'Instalación de cámaras de seguridad y sistemas de alarma'),

        # Transporte y mudanza
        ('Mudanza',         'Transporte de muebles y trasteos locales'),
        ('Transporte',      'Domicilios, diligencias y transporte de carga'),
        ('Mecánica',        'Reparación de vehículos a domicilio'),

        # Salud y bienestar
        ('Salud',           'Enfermería, fisioterapia y cuidado en casa'),
        ('Belleza',         'Corte de cabello, manicure, maquillaje y más'),
        ('Masajes',         'Masajes terapéuticos y relajantes a domicilio'),
        ('Veterinaria',     'Cuidado y atención veterinaria a domicilio'),

        # Educación
        ('Educación',       'Clases particulares, refuerzo escolar y tutorías'),
        ('Idiomas',         'Clases de inglés, francés y otros idiomas'),

        # Gastronomía y eventos
        ('Gastronomía',     'Cocineros a domicilio, catering y preparación de alimentos'),
        ('Eventos',         'Organización de fiestas, decoración y animación'),
        ('Fotografía',      'Fotografía y video para eventos y sesiones'),

        # Otros servicios
        ('Contabilidad',    'Declaraciones de renta, contabilidad y asesoría fiscal'),
        ('Diseño',          'Diseño gráfico, logos y material publicitario'),
        ('Mensajería',      'Envío de paquetes y documentos en la ciudad'),
    ]

    # Verificar cuáles ya existen
    cursor.execute("SELECT nombre_categoria FROM categorias_servicio")
    existentes = {row[0] for row in cursor.fetchall()}
    print(f"Categorías existentes: {len(existentes)}")

    agregadas = 0
    for nombre, descripcion in categorias:
        if nombre not in existentes:
            cursor.execute("""
                INSERT INTO categorias_servicio (nombre_categoria, descripcion, estado)
                VALUES (%s, %s, 'activo')
            """, (nombre, descripcion))
            print(f"  ✅ Agregada: {nombre}")
            agregadas += 1
        else:
            print(f"  ⏭️  Ya existe: {nombre}")

    conn.commit()

    # Verificar total
    cursor.execute("SELECT COUNT(*) FROM categorias_servicio WHERE estado = 'activo'")
    total = cursor.fetchone()[0]

    print(f"\n{'='*50}")
    print(f"✅ {agregadas} categorías nuevas agregadas")
    print(f"📊 Total de categorías activas: {total}")
    print(f"{'='*50}")

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals(): conn.close()
