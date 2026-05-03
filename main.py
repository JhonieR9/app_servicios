from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from routers import clientes, trabajadores

app = FastAPI(title="TalentHub API", version="1.0.0")

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Incluir routers
app.include_router(clientes.router)
app.include_router(trabajadores.router)

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

        categorias = [
            (1,'Plomería'),(2,'Electricidad'),(3,'Limpieza'),(4,'Carpintería'),
            (5,'Pintura'),(6,'Jardinería'),(7,'Mecánica'),(8,'Tecnología'),
            (9,'Construcción'),(10,'Educación'),(11,'Salud'),(12,'Belleza'),
            (13,'Gastronomía'),(14,'Transporte')
        ]
        for id_cat, nombre in categorias:
            cursor.execute(
                "INSERT IGNORE INTO categorias_servicio (id_categoria, nombre_categoria, estado) VALUES (%s, %s, 'activo')",
                (id_cat, nombre)
            )

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
