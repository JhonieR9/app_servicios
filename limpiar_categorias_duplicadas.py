import mysql.connector

HOST = "centerbeam.proxy.rlwy.net"
PORT = 32047
USER = "root"
PASSWORD = input("Password de Railway: ")
DATABASE = "railway"

conn = mysql.connector.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, database=DATABASE)
cursor = conn.cursor()

print("Limpiando categorías duplicadas...")

# Borrar TODAS las categorías
cursor.execute("DELETE FROM categorias_servicio")
conn.commit()
print("✅ Categorías borradas")

# Reiniciar el auto_increment
cursor.execute("ALTER TABLE categorias_servicio AUTO_INCREMENT = 1")
conn.commit()

# Insertar categorías limpias una sola vez
categorias = [
    (1,  'Plomería',           'Reparación de tuberías, grifos y sistemas de agua'),
    (2,  'Electricidad',       'Instalaciones eléctricas y reparaciones'),
    (3,  'Limpieza',           'Limpieza de hogares, oficinas y espacios'),
    (4,  'Carpintería',        'Muebles, puertas, ventanas y trabajos en madera'),
    (5,  'Pintura',            'Pintura de interiores y exteriores'),
    (6,  'Jardinería',         'Corte de césped, poda y mantenimiento de jardines'),
    (7,  'Cerrajería',         'Apertura de puertas y cambio de chapas'),
    (8,  'Mudanza',            'Transporte de muebles y trasteos'),
    (9,  'Construcción',       'Remodelaciones, pisos, techos y obras civiles'),
    (10, 'Vidriería',          'Instalación y reparación de vidrios'),
    (11, 'Impermeabilización', 'Sellado de filtraciones y techos'),
    (12, 'Lavandería',         'Lavado y planchado de ropa a domicilio'),
    (13, 'Control de plagas',  'Fumigación y eliminación de insectos'),
    (14, 'Tecnología',         'Reparación de computadores y redes WiFi'),
    (15, 'Electrodomésticos',  'Reparación de neveras, lavadoras y hornos'),
    (16, 'CCTV y Alarmas',     'Instalación de cámaras y sistemas de alarma'),
    (17, 'Transporte',         'Domicilios, diligencias y carga'),
    (18, 'Mecánica',           'Reparación de vehículos a domicilio'),
    (19, 'Salud',              'Enfermería, fisioterapia y cuidado en casa'),
    (20, 'Belleza',            'Corte de cabello, manicure y maquillaje'),
    (21, 'Masajes',            'Masajes terapéuticos y relajantes a domicilio'),
    (22, 'Veterinaria',        'Cuidado veterinario a domicilio'),
    (23, 'Educación',          'Clases particulares y refuerzo escolar'),
    (24, 'Idiomas',            'Clases de inglés, francés y otros idiomas'),
    (25, 'Gastronomía',        'Cocineros a domicilio, catering y alimentos'),
    (26, 'Eventos',            'Organización de fiestas y decoración'),
    (27, 'Fotografía',         'Fotografía y video para eventos'),
    (28, 'Contabilidad',       'Declaraciones de renta y asesoría fiscal'),
    (29, 'Diseño',             'Diseño gráfico, logos y publicidad'),
    (30, 'Mensajería',         'Envío de paquetes y documentos'),
]

for id_cat, nombre, desc in categorias:
    cursor.execute(
        "INSERT INTO categorias_servicio (id_categoria, nombre_categoria, descripcion, estado) VALUES (%s, %s, %s, 'activo')",
        (id_cat, nombre, desc)
    )

conn.commit()

cursor.execute("SELECT COUNT(*) FROM categorias_servicio")
total = cursor.fetchone()[0]
print(f"✅ {total} categorías insertadas correctamente")

cursor.close()
conn.close()
print("¡Listo!")
