from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from routers import clientes, trabajadores, chat, pagos
from config import DB_CONFIG, conectar_bd

app = FastAPI(title="TalentHub API", version="2.0.0")

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Incluir routers
app.include_router(clientes.router)
app.include_router(trabajadores.router)
app.include_router(chat.router)
app.include_router(pagos.router)

# ============================================
# CREAR TABLAS AL ARRANCAR (si no existen)
# ============================================

@app.on_event("startup")
def crear_tablas():
    try:
        conn = conectar_bd()
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
                (31, 'Mascotas',           'Paseo, cuidado, guardería y grooming de mascotas'),
            ]
            for id_cat, nombre, descripcion in categorias:
                cursor.execute(
                    "INSERT INTO categorias_servicio (id_categoria, nombre_categoria, descripcion, estado) VALUES (%s, %s, %s, 'activo')",
                    (id_cat, nombre, descripcion)
                )
            print(f"✅ {len(categorias)} categorías insertadas")

        # Insertar Mascotas si no existe (para BDs que ya tenían datos)
        try:
            cursor.execute("""
                INSERT IGNORE INTO categorias_servicio (id_categoria, nombre_categoria, descripcion, estado)
                VALUES (31, 'Mascotas', 'Paseo, cuidado, guardería y grooming de mascotas', 'activo')
            """)
            conn.commit()
        except Exception:
            pass

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
            ('metodo_pago',        "varchar(50) DEFAULT 'efectivo'"),
            ('codigo_confirmacion',"varchar(10) DEFAULT NULL"),
            ('codigo_inicio',      "varchar(10) DEFAULT NULL"),
            ('cotizacion_horas',   "decimal(4,1) DEFAULT NULL"),
            ('cotizacion_precio',  "decimal(10,2) DEFAULT NULL"),
            ('cotizacion_nota',    "text DEFAULT NULL"),
            ('cotizacion_fecha',   "datetime DEFAULT NULL"),
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

        # Columna verificado en correo_persona (si no existe)
        try:
            cursor.execute("ALTER TABLE correo_persona ADD COLUMN verificado tinyint(1) DEFAULT 0")
        except Exception:
            pass

        # Columnas medio_pago y banco en detalles_persona
        for col, definition in [
            ('medio_pago',          "varchar(200) DEFAULT NULL"),
            ('medio_pago_principal',"varchar(50) DEFAULT NULL"),
            ('banco',               "varchar(100) DEFAULT NULL"),
            ('tipo_cuenta',         "varchar(20) DEFAULT NULL"),
            ('numero_cuenta',       "varchar(30) DEFAULT NULL"),
            ('titular_cuenta',      "varchar(120) DEFAULT NULL"),
            ('arl',                 "varchar(100) DEFAULT NULL"),
            ('eps',                 "varchar(100) DEFAULT NULL"),
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

        # Columna tags en calificaciones (para chips descriptivos)
        try:
            cursor.execute("ALTER TABLE calificaciones ADD COLUMN tags varchar(500) DEFAULT NULL")
        except Exception:
            pass  # Ya existe

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

        # Tabla suscripciones push (Web Push / VAPID)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `push_subscriptions` (
              `id`           int NOT NULL AUTO_INCREMENT,
              `tipo_usuario` enum('trabajador','cliente') NOT NULL DEFAULT 'trabajador',
              `id_usuario`   int NOT NULL,
              `endpoint`     text NOT NULL,
              `p256dh`       text NOT NULL,
              `auth`         text NOT NULL,
              `fecha_reg`    datetime DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`),
              KEY `idx_push_usuario` (`tipo_usuario`, `id_usuario`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Tabla fotos de servicio (antes/después)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `fotos_servicio` (
              `id_foto`       int NOT NULL AUTO_INCREMENT,
              `id_solicitud`  int NOT NULL,
              `id_trabajador` int NOT NULL,
              `tipo_foto`     enum('antes','despues','progreso') DEFAULT 'progreso',
              `foto_data`     longblob NOT NULL,
              `foto_tipo`     varchar(50) DEFAULT 'image/jpeg',
              `descripcion`   varchar(200) DEFAULT NULL,
              `fecha_subida`  datetime DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`id_foto`),
              KEY `idx_foto_solicitud` (`id_solicitud`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Tabla favoritos del cliente
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `favoritos_cliente` (
              `id`            int NOT NULL AUTO_INCREMENT,
              `id_cliente`    int NOT NULL,
              `id_trabajador` int NOT NULL,
              `fecha_guardado` datetime DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`),
              UNIQUE KEY `uk_fav` (`id_cliente`, `id_trabajador`),
              KEY `idx_fav_cliente` (`id_cliente`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Tabla pagos (Wompi)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `pagos_solicitud` (
              `id`                      int NOT NULL AUTO_INCREMENT,
              `id_solicitud`            int NOT NULL,
              `id_cliente`              int NOT NULL,
              `referencia_wompi`        varchar(100) NOT NULL,
              `id_transaccion_wompi`    varchar(100) DEFAULT NULL,
              `monto`                   decimal(10,2) NOT NULL,
              `estado_wompi`            varchar(30) DEFAULT 'PENDING',
              `fecha_creacion`          datetime DEFAULT CURRENT_TIMESTAMP,
              `fecha_actualizacion`     datetime DEFAULT NULL,
              PRIMARY KEY (`id`),
              UNIQUE KEY `uk_referencia` (`referencia_wompi`),
              KEY `idx_pago_solicitud` (`id_solicitud`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Columna pago_estado en solicitudes
        try:
            cursor.execute("ALTER TABLE solicitudes_servicio ADD COLUMN pago_estado varchar(20) DEFAULT 'pendiente'")
        except Exception:
            pass

        # Columnas dispersión en pagos
        for col, definition in [
            ('dispersado',       "tinyint(1) DEFAULT 0"),
            ('fecha_dispersion', "datetime DEFAULT NULL"),
        ]:
            try:
                cursor.execute(f"ALTER TABLE pagos_solicitud ADD COLUMN {col} {definition}")
            except Exception:
                pass

        # Tabla especialidades del trabajador
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `especialidades_trabajador` (
              `id`              int NOT NULL AUTO_INCREMENT,
              `id_persona`      int NOT NULL,
              `categoria`       varchar(100) NOT NULL,
              `especialidad`    varchar(200) NOT NULL,
              `fecha_agregada`  datetime DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`),
              KEY `idx_esp_persona` (`id_persona`),
              KEY `idx_esp_categoria` (`categoria`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Tabla ciudades de servicio del trabajador
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `ciudades_servicio_trabajador` (
              `id`              int NOT NULL AUTO_INCREMENT,
              `id_persona`      int NOT NULL,
              `ciudad`          varchar(100) NOT NULL,
              `departamento`    varchar(100) DEFAULT NULL,
              `fecha_agregada`  datetime DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`),
              KEY `idx_ciudad_persona` (`id_persona`),
              KEY `idx_ciudad_nombre` (`ciudad`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Columna ciudad_nacimiento en personas
        try:
            cursor.execute("ALTER TABLE personas ADD COLUMN ciudad_nacimiento varchar(100) DEFAULT NULL")
        except Exception:
            pass

        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Tablas verificadas/creadas correctamente")
    except Exception as e:
        print(f"⚠️ Error al crear tablas: {e}")

# ============================================
# SCHEDULER — RECORDATORIOS AUTOMÁTICOS
# ============================================

def iniciar_scheduler():
    """Scheduler en background que envía recordatorios a trabajadores según su horario"""
    import threading
    import time
    from datetime import datetime, timedelta

    HORARIOS_NOTIF = {
        # id_horario: (hora_envio_hour, hora_envio_minute, mensaje)
        7:  (7, 50, "¡Buenos días! Tu horario 8am-12pm está por empezar. Activa tu disponibilidad 🟢"),
        8:  (13, 50, "¡Buenas tardes! Tu horario 2pm-6pm está por empezar. Activa tu disponibilidad 🟢"),
        9:  (17, 50, "¡Buenas noches! Tu horario 6pm-10pm está por empezar. Activa tu disponibilidad 🟢"),
        11: (7, 50, "¡Buenos días! Tu jornada 8am-6pm está por empezar. Activa tu disponibilidad 🟢"),
        12: (7, 50, "¡Buenos días! Estás en horario 8am-10pm. Activa tu disponibilidad 🟢"),
        10: (7, 50, "¡Buenos días! Estás disponible 24h. Activa tu disponibilidad si no lo has hecho 🟢"),
    }

    notificados_hoy = set()  # evitar duplicados en el mismo día

    def _loop():
        nonlocal notificados_hoy
        while True:
            try:
                # Hora Colombia (UTC-5)
                ahora = datetime.utcnow() - timedelta(hours=5)
                hora_actual = ahora.hour
                minuto_actual = ahora.minute
                dia_actual = ahora.strftime('%Y-%m-%d')

                # Resetear set de notificados cada día
                if not any(dia_actual in s for s in notificados_hoy):
                    notificados_hoy = set()

                for id_horario, (h, m, mensaje) in HORARIOS_NOTIF.items():
                    if hora_actual == h and minuto_actual == m:
                        clave = f"{dia_actual}_{id_horario}"
                        if clave in notificados_hoy:
                            continue
                        notificados_hoy.add(clave)

                        # Enviar push a trabajadores con este horario que NO están activos
                        _enviar_recordatorio(id_horario, mensaje)

            except Exception as ex:
                print(f"[SCHEDULER] Error: {ex}")

            time.sleep(60)  # revisar cada minuto

    def _enviar_recordatorio(id_horario, mensaje):
        try:
            import json

            conn = conectar_bd()
            cursor = conn.cursor(dictionary=True)

            # Buscar trabajadores con ese horario que NO tienen disponible=1
            cursor.execute("""
                SELECT DISTINCT ps.id_usuario, ps.endpoint, ps.p256dh, ps.auth
                FROM push_subscriptions ps
                INNER JOIN disponibilidad d ON ps.id_usuario = d.id_persona
                WHERE ps.tipo_usuario = 'trabajador'
                  AND d.id_horario = %s
                  AND (d.disponible = 0 OR d.disponible IS NULL)
            """, (id_horario,))
            subs = cursor.fetchall()
            cursor.close()
            conn.close()

            if not subs:
                return

            try:
                from pywebpush import webpush, WebPushException
            except ImportError:
                print("[SCHEDULER] pywebpush no instalado")
                return

            payload = json.dumps({
                "title": "🔔 TalentHub — Hora de conectarse",
                "body": mensaje,
                "url": "/trabajador/panel",
                "icon": "/static/icons/icon-192.png"
            })

            for sub in subs:
                try:
                    webpush(
                        subscription_info={
                            "endpoint": sub["endpoint"],
                            "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]}
                        },
                        data=payload,
                        vapid_private_key=VAPID_PRIVATE,
                        vapid_claims=VAPID_CLAIMS
                    )
                except Exception:
                    pass

            print(f"[SCHEDULER] ✅ Recordatorio enviado a {len(subs)} trabajadores (horario {id_horario})")
        except Exception as ex:
            print(f"[SCHEDULER] Error enviando: {ex}")

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    print("✅ Scheduler de recordatorios iniciado")

# Iniciar scheduler al arrancar
@app.on_event("startup")
def iniciar_recordatorios():
    iniciar_scheduler()

# ============================================
# PÁGINA PRINCIPAL - SOLO FORMULARIO
# ============================================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/instalar", response_class=HTMLResponse)
def instalar(request: Request):
    return templates.TemplateResponse("instalar.html", {"request": request})

@app.get("/privacidad", response_class=HTMLResponse)
def privacidad(request: Request):
    return templates.TemplateResponse("privacidad.html", {"request": request})

@app.get("/terminos", response_class=HTMLResponse)
def terminos(request: Request):
    return templates.TemplateResponse("terminos.html", {"request": request})

@app.get("/inicio", response_class=HTMLResponse)
def mostrar_solo_formulario(request: Request):
    return templates.TemplateResponse("solo_formulario.html", {"request": request})

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "TalentHub API is running"}

@app.get("/health/email-test")
def test_email(request: Request):
    """Diagnóstico de email — solo admin"""
    import os
    import requests as _req

    # Verificar admin
    token = request.cookies.get("admin_session")
    admin_secret = os.getenv("ADMIN_TOKEN", "talenthub_admin_2026_secret")
    if token != admin_secret:
        return {"error": "No autorizado"}

    resend_key = os.getenv("RESEND_API_KEY", "")
    gmail_user = os.getenv("GMAIL_USER", "")

    if not resend_key:
        return {
            "status": "error",
            "detail": "Variable RESEND_API_KEY no configurada en Railway",
            "RESEND_API_KEY_len": 0,
            "GMAIL_USER": gmail_user or "(vacío)"
        }

    from_email = "noreply@talenthubcol.com"
    to_email = gmail_user if gmail_user else "delivered@resend.dev"

    try:
        resp = _req.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": f"TalentHub <{from_email}>",
                "to": [to_email],
                "subject": "Test Email TalentHub",
                "html": "<p>Este es un email de prueba desde TalentHub en Railway.</p>"
            },
            timeout=15
        )

        if resp.status_code in (200, 201):
            return {
                "status": "ok",
                "detail": f"Email de prueba enviado a {to_email} via Resend",
                "resend_response": resp.json()
            }
        else:
            return {
                "status": "error",
                "detail": f"Resend respondió {resp.status_code}",
                "resend_error": resp.text,
                "from": from_email,
                "to": to_email
            }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e)
        }

# ── TWA / Play Store — Digital Asset Links ──────────────────────────
@app.get("/.well-known/assetlinks.json")
def asset_links():
    """Requerido por Google para verificar el dominio en TWA (Play Store)"""
    import os, json
    from fastapi.responses import Response as _Resp
    ruta = os.path.join("static", ".well-known", "assetlinks.json")
    try:
        with open(ruta, "r") as f:
            contenido = f.read()
        return _Resp(content=contenido, media_type="application/json")
    except Exception:
        return _Resp(content="[]", media_type="application/json")

@app.get("/uploads/{filename}")
async def servir_upload(filename: str):
    """Sirve archivos desde BD cuando no existen en disco"""
    import os
    from fastapi.responses import Response, FileResponse

    # Intentar servir desde disco primero
    ruta_disco = os.path.join("static", "uploads", filename)
    if os.path.exists(ruta_disco):
        return FileResponse(ruta_disco)

    # Si no existe en disco, buscar en BD por nombre de archivo
    try:
        conn = conectar_bd()
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

# ============================================
# WEB PUSH — VAPID
# ============================================

# Claves VAPID (generadas una sola vez — NO cambiar en producción)
# Para regenerar: python -c "from cryptography..."
VAPID_PUBLIC  = "BM66qRWQGKRktcIccA8tJ3k10D6Bslu8jjQufR89ATky-v9aKXacOD9IHxaxLR9ZdOO6A7wVxudhXCrONhZoOfo"
VAPID_PRIVATE = "JyFRkexRUVZRSaX93z-_Y5H_OYSVOIGyQ3QrOJ28M9A"
VAPID_CLAIMS  = {"sub": "mailto:admin@talenthub.app"}

@app.get("/push/vapid-public")
def get_vapid_public():
    """Devuelve la clave pública VAPID para que el frontend la use al suscribirse."""
    return {"publicKey": VAPID_PUBLIC}

@app.post("/push/subscribe")
async def push_subscribe(request: Request):
    """Guarda o actualiza la suscripción push de un usuario."""
    from fastapi.responses import JSONResponse as _JSON
    import json
    try:
        body = await request.json()
        tipo_usuario = body.get("tipo_usuario", "trabajador")
        id_usuario   = int(body.get("id_usuario", 0))
        endpoint     = body.get("endpoint", "")
        p256dh       = body.get("keys", {}).get("p256dh", "")
        auth         = body.get("keys", {}).get("auth", "")

        if not endpoint or not p256dh or not auth or not id_usuario:
            return _JSON({"error": "Datos incompletos"}, status_code=400)

        conn   = conectar_bd()
        cursor = conn.cursor()
        # Borrar suscripciones anteriores del mismo usuario en este dispositivo
        cursor.execute("""
            DELETE FROM push_subscriptions
            WHERE tipo_usuario = %s AND id_usuario = %s AND endpoint = %s
        """, (tipo_usuario, id_usuario, endpoint))
        cursor.execute("""
            INSERT INTO push_subscriptions (tipo_usuario, id_usuario, endpoint, p256dh, auth)
            VALUES (%s, %s, %s, %s, %s)
        """, (tipo_usuario, id_usuario, endpoint, p256dh, auth))
        conn.commit()
        cursor.close(); conn.close()
        return _JSON({"ok": True})
    except Exception as e:
        return _JSON({"error": str(e)}, status_code=500)

@app.post("/push/unsubscribe")
async def push_unsubscribe(request: Request):
    """Elimina la suscripción push de un usuario."""
    from fastapi.responses import JSONResponse as _JSON
    try:
        body     = await request.json()
        endpoint = body.get("endpoint", "")
        if not endpoint:
            return _JSON({"error": "endpoint requerido"}, status_code=400)
        conn   = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM push_subscriptions WHERE endpoint = %s", (endpoint,))
        conn.commit()
        cursor.close(); conn.close()
        return _JSON({"ok": True})
    except Exception as e:
        return _JSON({"error": str(e)}, status_code=500)


def enviar_push_trabajadores(id_categoria: int, nombre_categoria: str, titulo_notif: str, cuerpo: str, url_destino: str = "/trabajador/panel"):
    """
    Envía notificación push a todos los trabajadores suscritos
    que tengan esa categoría de servicio.
    Acepta tanto el id como el nombre de la categoría porque servicios_persona
    guarda el texto (ej. 'Carpintería'), no el id numérico.
    """
    import threading
    def _enviar():
        try:
            import json
            try:
                from pywebpush import webpush, WebPushException
            except ImportError:
                print("[PUSH] pywebpush no instalado — omitiendo push")
                return

            conn   = conectar_bd()
            cursor = conn.cursor(dictionary=True)

            # servicios_persona.categoria es texto, no id
            cursor.execute("""
                SELECT DISTINCT ps.endpoint, ps.p256dh, ps.auth
                FROM push_subscriptions ps
                INNER JOIN servicios_persona sp ON ps.id_usuario = sp.id_persona
                WHERE ps.tipo_usuario = 'trabajador'
                  AND sp.categoria = %s
            """, (nombre_categoria,))
            suscripciones = cursor.fetchall()
            cursor.close(); conn.close()

            if not suscripciones:
                print(f"[PUSH] Sin suscripciones para categoría '{nombre_categoria}'")
                return

            payload = json.dumps({
                "title": titulo_notif,
                "body":  cuerpo,
                "url":   url_destino,
                "icon":  "/static/icons/icon-192.png",
                "badge": "/static/icons/icon-192.png"
            })

            for sub in suscripciones:
                try:
                    webpush(
                        subscription_info={
                            "endpoint": sub["endpoint"],
                            "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]}
                        },
                        data=payload,
                        vapid_private_key=VAPID_PRIVATE,
                        vapid_claims=VAPID_CLAIMS
                    )
                    print(f"[PUSH] ✅ Enviado a endpoint ...{sub['endpoint'][-20:]}")
                except WebPushException as ex:
                    # Suscripción expirada o inválida — limpiar
                    if ex.response and ex.response.status_code in (404, 410):
                        try:
                            conn2   = conectar_bd()
                            cur2    = conn2.cursor()
                            cur2.execute("DELETE FROM push_subscriptions WHERE endpoint = %s", (sub["endpoint"],))
                            conn2.commit(); cur2.close(); conn2.close()
                            print(f"[PUSH] Suscripción expirada eliminada")
                        except Exception: pass
                    else:
                        print(f"[PUSH] WebPushException: {ex}")
                except Exception as ex:
                    print(f"[PUSH] Error general: {ex}")
        except Exception as ex:
            print(f"[PUSH] Error hilo: {ex}")
    threading.Thread(target=_enviar, daemon=True).start()


# ============================================
# MANEJO DE ERRORES PERSONALIZADOS
# ============================================

from fastapi.exceptions import HTTPException as FastAPIHTTPException
from starlette.requests import Request as StarletteRequest
from starlette.responses import HTMLResponse as StarletteHTML

@app.exception_handler(404)
async def not_found_handler(request: StarletteRequest, exc: FastAPIHTTPException):
    html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Página no encontrada - TalentHub</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #0a0a0f;
            min-height: 100vh;
            display: flex; align-items: center; justify-content: center;
            padding: 20px;
        }
        .bg {
            position: fixed; inset: 0; pointer-events: none;
            background:
                radial-gradient(ellipse 70% 50% at 20% 20%, rgba(99,102,241,0.12) 0%, transparent 60%),
                radial-gradient(ellipse 60% 50% at 80% 80%, rgba(139,92,246,0.1) 0%, transparent 60%);
        }
        .card {
            position: relative; z-index: 1;
            background: #111118;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 24px;
            padding: 48px 32px;
            width: 100%; max-width: 440px;
            text-align: center;
            box-shadow: 0 32px 64px rgba(0,0,0,0.5);
        }
        .error-num {
            font-size: 5rem; font-weight: 900; line-height: 1;
            background: linear-gradient(135deg, #a5b4fc, #67e8f9);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }
        .icon { font-size: 2.5rem; margin-bottom: 16px; display: block; }
        h2 { color: #f1f5f9; font-size: 1.3rem; font-weight: 700; margin-bottom: 10px; }
        p { color: #64748b; font-size: 0.9rem; line-height: 1.6; margin-bottom: 32px; }
        .btns { display: flex; flex-direction: column; gap: 10px; }
        .btn {
            padding: 14px 24px; border-radius: 12px; font-weight: 700;
            font-size: 0.9rem; text-decoration: none; display: block;
            transition: all 0.2s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
            color: white; box-shadow: 0 4px 16px rgba(99,102,241,0.35);
        }
        .btn-primary:hover { transform: translateY(-2px); color: white; }
        .btn-secondary {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            color: #94a3b8;
        }
        .btn-secondary:hover { background: rgba(255,255,255,0.08); color: #f1f5f9; }
    </style>
</head>
<body>
<div class="bg"></div>
<div class="card">
    <span class="icon">🔍</span>
    <div class="error-num">404</div>
    <h2>Página no encontrada</h2>
    <p>La ruta que buscas no existe o fue movida.<br>Verifica el enlace o regresa a un lugar seguro.</p>
    <div class="btns">
        <a href="/" class="btn btn-primary"><i class="bi bi-house-fill"></i> Ir al inicio</a>
        <a href="javascript:history.back()" class="btn btn-secondary">← Volver atrás</a>
    </div>
</div>
</body>
</html>"""
    return StarletteHTML(content=html, status_code=404)

@app.exception_handler(500)
async def server_error_handler(request: StarletteRequest, exc: Exception):
    html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error del servidor - TalentHub</title>
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'Segoe UI',sans-serif; background:#0a0a0f; min-height:100vh;
               display:flex; align-items:center; justify-content:center; padding:20px; }
        .card { background:#111118; border:1px solid rgba(255,255,255,0.08); border-radius:24px;
                padding:48px 32px; width:100%; max-width:440px; text-align:center;
                box-shadow:0 32px 64px rgba(0,0,0,0.5); }
        .error-num { font-size:5rem; font-weight:900; line-height:1;
                     background:linear-gradient(135deg,#fca5a5,#f87171);
                     -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:8px; }
        h2 { color:#f1f5f9; font-size:1.3rem; font-weight:700; margin-bottom:10px; }
        p { color:#64748b; font-size:0.9rem; line-height:1.6; margin-bottom:32px; }
        .btn { padding:14px 24px; border-radius:12px; font-weight:700; font-size:0.9rem;
               text-decoration:none; display:block; background:rgba(255,255,255,0.04);
               border:1px solid rgba(255,255,255,0.08); color:#94a3b8; transition:all 0.2s; }
        .btn:hover { background:rgba(255,255,255,0.08); color:#f1f5f9; }
    </style>
</head>
<body>
<div class="card">
    <div style="font-size:2.5rem;margin-bottom:16px">⚠️</div>
    <div class="error-num">500</div>
    <h2>Error interno del servidor</h2>
    <p>Algo salió mal de nuestro lado. Estamos trabajando para solucionarlo.<br>Intenta de nuevo en unos minutos.</p>
    <a href="/" class="btn">← Volver al inicio</a>
</div>
</body>
</html>"""
    return StarletteHTML(content=html, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
