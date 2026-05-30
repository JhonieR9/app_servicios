from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from routers import clientes, trabajadores, chat

app = FastAPI(title="TalentHub API", version="1.0.0")

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Incluir routers
app.include_router(clientes.router)
app.include_router(trabajadores.router)
app.include_router(chat.router)

# ============================================
# CREAR TABLAS AL ARRANCAR (si no existen)
# ============================================

@app.on_event("startup")
def crear_tablas():
    try:
        import mysql.connector
        from config import DB_CONFIG
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `categorias_servicio` (
              `id_categoria` int NOT NULL AUTO_INCREMENT,
              `nombre_categoria` varchar(100) NOT NULL,
              `descripcion` text,
              `icono` varchar(50) DEFAULT NULL,
              `estado` varchar(20) DEFAULT 'activo',
              PRIMARY KEY (`id_categoria`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Solo insertar si la tabla está vacía para evitar duplicados
        cursor.execute("SELECT COUNT(*) FROM categorias_servicio")
        count = cursor.fetchone()[0]
        
        if count == 0:
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
            for id_cat, nombre, descripcion in categorias:
                cursor.execute(
                    "INSERT INTO categorias_servicio (id_categoria, nombre_categoria, descripcion, estado) VALUES (%s, %s, %s, 'activo')",
                    (id_cat, nombre, descripcion)
                )
            print(f"✅ {len(categorias)} categorías insertadas")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `solicitudes_servicio` (
              `id_solicitud`        int NOT NULL AUTO_INCREMENT,
              `id_cliente`          int DEFAULT NULL,
              `id_categoria`        int DEFAULT NULL,
              `id_trabajador`       int DEFAULT NULL,
              `titulo`              varchar(255) DEFAULT NULL,
              `descripcion`         text,
              `direccion_servicio`  text,
              `ciudad`              varchar(100) DEFAULT NULL,
              `departamento`        varchar(100) DEFAULT NULL,
              `fecha_programada`    datetime DEFAULT NULL,
              `estado`              varchar(50) DEFAULT 'pendiente',
              `fecha_solicitud`     datetime DEFAULT CURRENT_TIMESTAMP,
              `fecha_aceptacion`    datetime DEFAULT NULL,
              `fecha_inicio`        datetime DEFAULT NULL,
              `fecha_finalizacion`  datetime DEFAULT NULL,
              `precio_final`        decimal(10,2) DEFAULT NULL,
              `motivo_cancelacion`  text,
              PRIMARY KEY (`id_solicitud`),
              KEY `idx_sol_estado`    (`estado`),
              KEY `idx_sol_cliente`   (`id_cliente`),
              KEY `idx_sol_categoria` (`id_categoria`),
              KEY `idx_sol_trabajador`(`id_trabajador`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Agregar columnas faltantes si la tabla ya existía sin ellas
        for col, definition in [
            ('id_trabajador',      'int DEFAULT NULL AFTER id_categoria'),
            ('fecha_aceptacion',   'datetime DEFAULT NULL'),
            ('fecha_inicio',       'datetime DEFAULT NULL'),
            ('fecha_finalizacion', 'datetime DEFAULT NULL'),
            ('precio_final',       'decimal(10,2) DEFAULT NULL'),
        ]:
            try:
                cursor.execute(f"ALTER TABLE solicitudes_servicio ADD COLUMN {col} {definition}")
            except Exception:
                pass  # Ya existe

        # Columnas GPS en disponibilidad
        for col, definition in [
            ('disponible',          'tinyint(1) DEFAULT 0'),
            ('latitud',             'decimal(10,8) DEFAULT NULL'),
            ('longitud',            'decimal(11,8) DEFAULT NULL'),
            ('ultima_actualizacion','datetime DEFAULT NULL'),
        ]:
            try:
                cursor.execute(f"ALTER TABLE disponibilidad ADD COLUMN {col} {definition}")
            except Exception:
                pass  # Ya existe

        # Columna password_hash en personas (para login trabajador)
        try:
            cursor.execute("ALTER TABLE personas ADD COLUMN password_hash varchar(255) DEFAULT NULL")
        except Exception:
            pass

        # Columnas medio_pago y banco en detalles_persona
        for col, definition in [
            ('medio_pago',    "varchar(50) DEFAULT NULL"),
            ('banco',         "varchar(100) DEFAULT NULL"),
            ('tipo_cuenta',   "varchar(20) DEFAULT NULL"),
            ('numero_cuenta', "varchar(30) DEFAULT NULL"),
            ('titular_cuenta',"varchar(120) DEFAULT NULL"),
        ]:
            try:
                cursor.execute(f"ALTER TABLE detalles_persona ADD COLUMN {col} {definition}")
            except Exception:
                pass

        # Tabla calificaciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `calificaciones` (
              `id_calificacion`   int NOT NULL AUTO_INCREMENT,
              `id_solicitud`      int DEFAULT NULL,
              `id_cliente`        int DEFAULT NULL,
              `id_trabajador`     int DEFAULT NULL,
              `tipo_calificacion` varchar(50) DEFAULT 'cliente_a_trabajador',
              `puntuacion`        int DEFAULT NULL,
              `comentario`        text,
              `fecha_calificacion` datetime DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`id_calificacion`),
              KEY `idx_cal_trabajador` (`id_trabajador`),
              KEY `idx_cal_solicitud`  (`id_solicitud`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Tabla tokens de recuperación de contraseña
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `tokens_recuperacion` (
              `id_token`      int NOT NULL AUTO_INCREMENT,
              `tipo_usuario`  enum('trabajador','cliente') NOT NULL,
              `id_usuario`    int NOT NULL,
              `correo`        varchar(255) NOT NULL,
              `token`         varchar(100) NOT NULL,
              `usado`         tinyint(1) DEFAULT 0,
              `fecha_expiracion` datetime NOT NULL,
              `fecha_creacion`   datetime DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`id_token`),
              UNIQUE KEY `uk_token` (`token`),
              KEY `idx_token_usuario` (`tipo_usuario`, `id_usuario`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Tabla chat interno
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `mensajes_chat` (
              `id_mensaje`      int NOT NULL AUTO_INCREMENT,
              `id_solicitud`    int NOT NULL,
              `tipo_remitente`  enum('cliente','trabajador','sistema') NOT NULL,
              `id_remitente`    int DEFAULT NULL,
              `mensaje`         text NOT NULL,
              `leido`           tinyint(1) DEFAULT 0,
              `fecha_envio`     datetime DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`id_mensaje`),
              KEY `idx_chat_solicitud` (`id_solicitud`),
              KEY `idx_chat_fecha`     (`fecha_envio`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Tablas verificadas/creadas correctamente")
    except Exception as e:
        print(f"⚠️ Error al crear tablas: {e}")

# ============================================
# PÁGINA PRINCIPAL - SOLO FORMULARIO
# ============================================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/instalar", response_class=HTMLResponse)
def instalar(request: Request):
    return templates.TemplateResponse("instalar.html", {"request": request})

@app.get("/inicio", response_class=HTMLResponse)
def mostrar_solo_formulario(request: Request):
    return templates.TemplateResponse("solo_formulario.html", {"request": request})

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "TalentHub API is running"}

@app.get("/uploads/{filename}")
async def servir_upload(filename: str):
    """Sirve archivos desde BD cuando no existen en disco"""
    import os
    import mysql.connector
    from fastapi.responses import Response, FileResponse
    from config import DB_CONFIG

    # Intentar servir desde disco primero
    ruta_disco = os.path.join("static", "uploads", filename)
    if os.path.exists(ruta_disco):
        return FileResponse(ruta_disco)

    # Si no existe en disco, buscar en BD por nombre de archivo
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Buscar en detalles_persona por nombre de archivo
        cursor.execute("""
            SELECT 
                foto_identificacion, foto_identificacion_data, foto_identificacion_tipo,
                antecedentes_pdf, antecedentes_data, antecedentes_tipo,
                recomendaciones_archivo, recomendaciones_data, recomendaciones_tipo
            FROM detalles_persona
            WHERE foto_identificacion = %s 
               OR antecedentes_pdf = %s 
               OR recomendaciones_archivo = %s
            LIMIT 1
        """, (filename, filename, filename))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            if row['foto_identificacion'] == filename and row['foto_identificacion_data']:
                return Response(content=bytes(row['foto_identificacion_data']),
                               media_type=row['foto_identificacion_tipo'] or 'image/jpeg')
            if row['antecedentes_pdf'] == filename and row['antecedentes_data']:
                return Response(content=bytes(row['antecedentes_data']),
                               media_type=row['antecedentes_tipo'] or 'application/pdf')
            if row['recomendaciones_archivo'] == filename and row['recomendaciones_data']:
                return Response(content=bytes(row['recomendaciones_data']),
                               media_type=row['recomendaciones_tipo'] or 'application/pdf')
    except Exception as e:
        print(f"Error sirviendo archivo {filename}: {e}")

    from fastapi.responses import JSONResponse
    return JSONResponse({"error": "Archivo no encontrado"}, status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
