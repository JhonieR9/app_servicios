from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import mysql.connector
from datetime import datetime
import math
import auth  # Módulo de autenticación
from config import DB_CONFIG

router = APIRouter(prefix="/cliente", tags=["clientes"])
templates = Jinja2Templates(directory="templates")

# Conexión a BD
def conectar_bd():
    """
    Establece conexión con la base de datos MySQL.
    
    Returns:
        Connection: Objeto de conexión a MySQL
    """
    return mysql.connector.connect(**DB_CONFIG)

def calcular_distancia(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en kilómetros entre dos coordenadas GPS usando la fórmula de Haversine.
    
    Args:
        lat1 (float): Latitud del punto 1
        lon1 (float): Longitud del punto 1
        lat2 (float): Latitud del punto 2
        lon2 (float): Longitud del punto 2
    
    Returns:
        float: Distancia en kilómetros (redondeada a 2 decimales)
    
    Example:
        >>> calcular_distancia(4.7110, -74.0721, 4.6097, -74.0817)
        11.34
    """
    R = 6371  # Radio de la Tierra en kilómetros
    
    # Convertir grados a radianes
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    # Fórmula de Haversine
    a = (math.sin(dlat/2) * math.sin(dlat/2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2) * math.sin(dlon/2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distancia = R * c
    
    return round(distancia, 2)

# ============================================
# TEMPLATES
# ============================================

@router.get("/mi-perfil")
def obtener_mi_perfil_cliente(request: Request):
    """Obtiene datos del cliente autenticado"""
    token = request.cookies.get("session_token")
    if not token:
        return JSONResponse({"error": "No autenticado"}, status_code=401)
    sesion = auth.verificar_sesion(token)
    if not sesion or sesion['tipo_usuario'] != 'cliente':
        return JSONResponse({"error": "Sesión inválida"}, status_code=401)
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.id_cliente, c.nombre_completo, e.correo
        FROM clientes c
        LEFT JOIN correo_cliente e ON c.id_cliente = e.id_cliente
        WHERE c.id_cliente = %s
    """, (sesion['id_usuario'],))
    cliente = cursor.fetchone()
    cursor.close()
    conexion.close()
    return JSONResponse(cliente or {"error": "No encontrado"})

@router.get("/panel", response_class=HTMLResponse)
def mostrar_panel_cliente(request: Request):
    """Panel principal del cliente"""
    return templates.TemplateResponse("clientes/panel.html", {"request": request})

@router.get("/registro", response_class=HTMLResponse)
def mostrar_formulario(request: Request):
    return templates.TemplateResponse("clientes/registro_cliente.html", {"request": request})

@router.post("/registro")
async def registrar_cliente(
    nombre_completo: str = Form(...),
    correo: str = Form(...),
    telefono: str = Form(...),
    password: str = Form(...),
    confirmar_password: str = Form(...)
):
    """Registro de cliente con contraseña"""
    if password != confirmar_password:
        return JSONResponse({"error": "Las contraseñas no coinciden"}, status_code=400)
    if len(password) < 6:
        return JSONResponse({"error": "La contraseña debe tener al menos 6 caracteres"}, status_code=400)

    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    # Verificar correo único
    cursor.execute("SELECT id_cliente FROM correo_cliente WHERE correo = %s", (correo,))
    if cursor.fetchone():
        cursor.close()
        conexion.close()
        return JSONResponse({"error": "Este correo ya está registrado"}, status_code=400)

    try:
        password_hash = auth.hash_password(password)
        cursor.execute("""
            INSERT INTO clientes (nombre_completo, estado, password_hash, fecha_registro)
            VALUES (%s, 'activo', %s, NOW())
        """, (nombre_completo, password_hash))
        conexion.commit()
        id_cliente = cursor.lastrowid

        cursor.execute("INSERT INTO correo_cliente (id_cliente, correo, verificado, principal) VALUES (%s, %s, 0, 1)", (id_cliente, correo))
        cursor.execute("INSERT INTO telefono_cliente (id_cliente, telefono, tipo_telefono, principal) VALUES (%s, %s, 'celular', 1)", (id_cliente, telefono))
        conexion.commit()

        return JSONResponse({"mensaje": "Cuenta creada exitosamente", "id_cliente": id_cliente})
    except Exception as e:
        conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        cursor.close()
        conexion.close()

@router.get("/solicitar_servicio", response_class=HTMLResponse)
def mostrar_solicitar_servicio(request: Request):
    return templates.TemplateResponse("clientes/solicitar_servicio.html", {"request": request})

@router.get("/mis_solicitudes", response_class=HTMLResponse)
def mostrar_mis_solicitudes(request: Request):
    return templates.TemplateResponse("clientes/mis_solicitudes.html", {"request": request})

@router.get("/mis_solicitudes_api")
def listar_mis_solicitudes_cliente(id_cliente: int = None):
    """API para obtener solicitudes de un cliente"""
    conexion = conectar_bd()
    if not conexion:
        return JSONResponse({"error": "Error de conexión", "solicitudes": []}, status_code=500)
    try:
        cursor = conexion.cursor(dictionary=True)
        if id_cliente:
            cursor.execute("""
                SELECT s.id_solicitud, s.titulo, s.descripcion, s.estado,
                       s.ciudad, s.departamento, s.fecha_solicitud,
                       cat.nombre_categoria
                FROM solicitudes_servicio s
                LEFT JOIN categorias_servicio cat ON s.id_categoria = cat.id_categoria
                WHERE s.id_cliente = %s
                ORDER BY s.fecha_solicitud DESC
            """, (id_cliente,))
        else:
            return JSONResponse({"solicitudes": []})
        solicitudes = cursor.fetchall()
        from datetime import timedelta
        for s in solicitudes:
            for k, v in s.items():
                if hasattr(v, 'isoformat'):
                    s[k] = (v - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M')
                elif v is None:
                    s[k] = ''
        return JSONResponse({"solicitudes": solicitudes})
    except Exception as e:
        return JSONResponse({"error": str(e), "solicitudes": []}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


# ============================================
# API ENDPOINTS
# ============================================

@router.post("/crear")
def crear_cliente(
    nombre_completo: str = Form(...),
    numero_documento: str = Form(...),
    pais: str = Form(...),
    departamento: str = Form(...),
    ciudad: str = Form(...),
    correo: str = Form(...),
    telefono: str = Form(...),
    direccion_completa: str = Form(...),
    codigo_postal: str = Form(...)
):
    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql_cliente = """
    INSERT INTO clientes 
    (id_tipo_documento, numero_documento, nombre_completo, pais, departamento, ciudad, fecha_registro, estado)
    VALUES (1, %s, %s, %s, %s, %s, %s, 'activo')
    """

    cursor.execute(sql_cliente, (
        numero_documento, nombre_completo, pais, departamento, ciudad, datetime.now()
    ))
    conexion.commit()
    id_cliente = cursor.lastrowid

    # Insertar correo
    cursor.execute("""
        INSERT INTO correo_cliente (id_cliente, correo, verificado, principal)
        VALUES (%s, %s, 0, 1)
    """, (id_cliente, correo))
    conexion.commit()

    # Insertar teléfono
    cursor.execute("""
        INSERT INTO telefono_cliente (id_cliente, telefono, tipo_telefono, principal)
        VALUES (%s, %s, 'celular', 1)
    """, (id_cliente, telefono))
    conexion.commit()

    # Insertar dirección
    cursor.execute("""
        INSERT INTO direcciones_cliente (id_cliente, direccion_completa, ciudad, departamento, codigo_postal)
        VALUES (%s, %s, %s, %s, %s)
    """, (id_cliente, direccion_completa, ciudad, departamento, codigo_postal))
    conexion.commit()

    cursor.close()
    conexion.close()

    return {"mensaje": "Cliente creado correctamente", "id_cliente": id_cliente}

@router.get("/categorias")
def listar_categorias():
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT id_categoria, nombre_categoria, descripcion, icono 
        FROM categorias_servicio 
        WHERE estado = 'activo'
    """)
    
    categorias = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    return {"categorias": categorias}

@router.post("/solicitud/crear")
def crear_solicitud(
    request: Request,
    id_cliente: int = Form(None),
    id_categoria: int = Form(...),
    titulo: str = Form(...),
    descripcion: str = Form(...),
    direccion_servicio: str = Form(...),
    ciudad: str = Form(...),
    departamento: str = Form(...),
    fecha_programada: str = Form(None),
    id_trabajador: int = Form(None)
):
    # Intentar obtener id_cliente desde la sesión si no viene en el form
    if not id_cliente:
        token = request.cookies.get("session_token_cliente") or request.cookies.get("session_token")
        if token:
            import auth as auth_module
            sesion = auth_module.verificar_sesion(token)
            if sesion and sesion.get('tipo_usuario') == 'cliente':
                id_cliente = sesion['id_usuario']
        if not id_cliente:
            id_cliente = 1  # fallback para pruebas sin login
    # Mapa de id_categoria → nombre (igual que en el frontend)
    CATEGORIAS = {
        1: 'Plomería', 2: 'Electricidad', 3: 'Limpieza', 4: 'Carpintería',
        5: 'Pintura', 6: 'Jardinería', 7: 'Mecánica', 8: 'Tecnología',
        9: 'Construcción', 10: 'Educación', 11: 'Salud', 12: 'Belleza',
        13: 'Gastronomía', 14: 'Transporte'
    }

    conexion = conectar_bd()
    cursor = conexion.cursor()

    try:
        # Asegurar que la categoría existe en la tabla
        nombre_cat = CATEGORIAS.get(id_categoria, 'Otro')
        cursor.execute("""
            INSERT IGNORE INTO categorias_servicio (id_categoria, nombre_categoria, estado)
            VALUES (%s, %s, 'activo')
        """, (id_categoria, nombre_cat))
        conexion.commit()

        sql = """
        INSERT INTO solicitudes_servicio 
        (id_cliente, id_categoria, titulo, descripcion, direccion_servicio, 
         ciudad, departamento, fecha_programada, estado)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pendiente')
        """
        cursor.execute(sql, (
            id_cliente, id_categoria, titulo, descripcion, direccion_servicio,
            ciudad, departamento, fecha_programada if fecha_programada else None
        ))
        conexion.commit()
        id_solicitud = cursor.lastrowid

        # Ya NO se acepta automáticamente — el trabajador decide
        return {"mensaje": "Solicitud creada exitosamente", "id_solicitud": id_solicitud}

    except Exception as e:
        conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        cursor.close()
        conexion.close()

@router.get("/historial/{id_cliente}")
def historial_cliente(id_cliente: int):
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT * FROM vista_historial_cliente
        WHERE id_cliente = %s
        ORDER BY fecha_solicitud DESC
    """, (id_cliente,))
    
    historial = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    return {"historial": historial}

@router.post("/solicitud/cancelar")
def cancelar_solicitud(
    id_solicitud: int = Form(...),
    motivo: str = Form(...)
):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    sql = """
    UPDATE solicitudes_servicio 
    SET estado = 'cancelada', motivo_cancelacion = %s
    WHERE id_solicitud = %s AND estado IN ('pendiente', 'aceptada')
    """
    
    cursor.execute(sql, (motivo, id_solicitud))
    conexion.commit()
    cursor.close()
    conexion.close()
    
    return {"mensaje": "Solicitud cancelada"}

@router.post("/calificar")
def calificar_servicio(
    id_solicitud: int = Form(...),
    id_cliente: int = Form(...),
    id_trabajador: int = Form(...),
    puntuacion: int = Form(...),
    comentario: str = Form(None)
):
    if puntuacion < 1 or puntuacion > 5:
        return {"error": "La puntuación debe estar entre 1 y 5"}
    
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    sql = """
    INSERT INTO calificaciones 
    (id_solicitud, id_cliente, id_trabajador, tipo_calificacion, puntuacion, comentario)
    VALUES (%s, %s, %s, 'cliente_a_trabajador', %s, %s)
    """
    
    cursor.execute(sql, (id_solicitud, id_cliente, id_trabajador, puntuacion, comentario))
    conexion.commit()
    cursor.close()
    conexion.close()
    
    return {"mensaje": "Calificación registrada exitosamente"}


# ============================================
# GEOLOCALIZACIÓN
# ============================================

@router.get("/mapa", response_class=HTMLResponse)
def mostrar_mapa(request: Request):
    """Muestra lista visual de trabajadores cercanos."""
    import os
    mapbox_token = os.getenv("MAPBOX_TOKEN", "pk.eyJ1IjoiamhvbmllcmNlc3BlZGVzMTItIiwiYSI6ImNtb25qeGJ1dTBtNGoycnB2NWZtb3V1ZDcifQ.oWycZCkDrln9HOGRaWT8Xg")
    return templates.TemplateResponse("clientes/mapa_simple.html", {"request": request, "mapbox_token": mapbox_token})

@router.get("/trabajadores-cercanos")
def obtener_trabajadores_cercanos(
    lat: float,
    lng: float,
    radio: float = 10.0,
    categoria: str = ""
):
    """
    Obtiene trabajadores cercanos usando GPS real de la base de datos.
    
    Args:
        lat: Latitud del cliente
        lng: Longitud del cliente
        radio: Radio de búsqueda en km
        categoria: Categoría de servicio (opcional)
    """
    conexion = conectar_bd()
    if not conexion:
        return JSONResponse({"error": "Error de conexión", "trabajadores": []}, status_code=500)
    
    try:
        cursor = conexion.cursor(dictionary=True)
        
        # Obtener trabajadores disponibles con ubicación GPS
        cursor.execute("""
            SELECT 
                p.id_persona,
                p.nombre_completo,
                p.ciudad,
                tp.telefono,
                ep.anios_experiencia,
                d.latitud,
                d.longitud,
                d.disponible,
                d.ultima_actualizacion
            FROM personas p
            LEFT JOIN telefono_persona tp ON p.id_persona = tp.id_persona
            LEFT JOIN experiencia_persona ep ON p.id_persona = ep.id_persona
            LEFT JOIN disponibilidad d ON p.id_persona = d.id_persona
            WHERE (p.estado = 'activo' OR p.estado IS NULL)
            AND (d.disponible = 1 OR d.disponible IS NULL)
        """)
        
        trabajadores = cursor.fetchall()
        trabajadores_cercanos = []
        
        for trabajador in trabajadores:
            # Obtener servicios del trabajador
            cursor.execute("""
                SELECT categoria, descripcion, valor_hora, anios_experiencia
                FROM servicios_persona
                WHERE id_persona = %s
            """, (trabajador['id_persona'],))
            servicios = cursor.fetchall()
            
            # Filtrar por categoría si se especifica
            if categoria:
                servicios = [s for s in servicios if s['categoria'] == categoria]
                if not servicios:
                    continue
            
            # Convertir TODOS los Decimals a float o int
            for serv in servicios:
                for key, value in serv.items():
                    if value is not None and hasattr(value, '__float__'):  # Es Decimal
                        serv[key] = float(value)
                    elif value is None:
                        serv[key] = 0 if key in ['valor_hora', 'anios_experiencia'] else ''
            
            # Obtener ubicación GPS real o generar una cercana
            if trabajador.get('latitud') and trabajador.get('longitud'):
                # Usar ubicación real de la base de datos
                trabajador_lat = float(trabajador['latitud'])
                trabajador_lng = float(trabajador['longitud'])
            else:
                # Si no tiene GPS, generar ubicación aleatoria cerca del cliente
                import random
                offset_lat = random.uniform(-0.05, 0.05)  # ~5km
                offset_lng = random.uniform(-0.05, 0.05)
                trabajador_lat = lat + offset_lat
                trabajador_lng = lng + offset_lng
            
            # Calcular distancia
            distancia = calcular_distancia(lat, lng, trabajador_lat, trabajador_lng)
            
            # Filtrar por radio
            if distancia <= radio:
                # Convertir experiencia a int si es necesario
                experiencia = trabajador.get('anios_experiencia', 0)
                if experiencia and hasattr(experiencia, '__float__'):
                    experiencia = int(float(experiencia))
                elif not experiencia:
                    experiencia = 0
                
                trabajadores_cercanos.append({
                    "id": int(trabajador['id_persona']),
                    "nombre": str(trabajador['nombre_completo']),
                    "telefono": str(trabajador.get('telefono') or 'N/A'),
                    "experiencia": experiencia,
                    "categoria": servicios[0]['categoria'] if servicios else 'General',
                    "servicios": servicios,
                    "latitud": float(trabajador_lat),
                    "longitud": float(trabajador_lng),
                    "distancia": float(round(distancia, 2)),
                    "tiene_gps_real": bool(trabajador.get('latitud') and trabajador.get('longitud'))
                })
        
        # Ordenar por distancia
        trabajadores_cercanos.sort(key=lambda x: x['distancia'])
        
        return JSONResponse({"trabajadores": trabajadores_cercanos})
        
    except Exception as e:
        import traceback
        print(f"Error: {traceback.format_exc()}")
        return JSONResponse({"error": str(e), "trabajadores": []}, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


# ============================================
# AUTENTICACIÓN - LOGIN Y VERIFICACIÓN
# ============================================

@router.get("/login", response_class=HTMLResponse)
def mostrar_login_cliente(request: Request):
    """Muestra página de login para clientes"""
    return templates.TemplateResponse("clientes/login.html", {"request": request})

@router.post("/login")
async def login_cliente(
    response: Response,
    correo: str = Form(...),
    password: str = Form(...)
):
    """Endpoint de login para clientes"""
    try:
        exitoso, cliente, mensaje = auth.autenticar_cliente(correo, password)
        
        if not exitoso:
            return JSONResponse(
                {"error": mensaje},
                status_code=401
            )
        
        # Verificar si requiere verificación SMS
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT valor FROM configuracion_seguridad
            WHERE clave = 'requiere_verificacion_sms'
        """)
        config = cursor.fetchone()
        requiere_sms = config and config['valor'] == '1'
        
        cursor.close()
        conexion.close()
        
        if requiere_sms and cliente.get('telefono'):
            codigo = auth.crear_codigo_verificacion(
                'cliente',
                cliente['id_cliente'],
                cliente['telefono'],
                'login'
            )
            
            auth.enviar_sms(cliente['telefono'], codigo)
            
            return JSONResponse({
                "requiere_verificacion_sms": True,
                "id_cliente": cliente['id_cliente'],
                "mensaje": "Código enviado a tu teléfono"
            })
        else:
            token = auth.crear_sesion('cliente', cliente['id_cliente'])
            
            response.set_cookie(
                key="session_token_cliente",
                value=token,
                httponly=False,
                max_age=86400,
                samesite="lax"
            )
            
            nombre = cliente.get('nombre_completo', 'Cliente')
            return JSONResponse({
                "requiere_verificacion_sms": False,
                "id_cliente": cliente['id_cliente'],
                "mensaje": "Login exitoso",
                "redirect": f"/cliente/panel?nombre={nombre}&id={cliente['id_cliente']}"
            })
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Error en el servidor: {str(e)}"},
            status_code=500
        )

@router.post("/verificar-sms")
async def verificar_sms_cliente(
    response: Response,
    id_cliente: int = Form(...),
    codigo: str = Form(...)
):
    """Verifica el código SMS y crea la sesión"""
    try:
        valido, mensaje = auth.verificar_codigo_sms('cliente', id_cliente, codigo)
        
        if not valido:
            return JSONResponse(
                {"error": mensaje},
                status_code=400
            )
        
        token = auth.crear_sesion('cliente', id_cliente)
        
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            max_age=86400,
            samesite="lax"
        )
        
        return JSONResponse({
            "mensaje": "Verificación exitosa",
            "redirect": "/cliente/dashboard"
        })
        
    except Exception as e:
        return JSONResponse(
            {"error": f"Error: {str(e)}"},
            status_code=500
        )

@router.post("/reenviar-codigo")
async def reenviar_codigo_cliente(id_cliente: int = Form(...)):
    """Reenvía el código SMS"""
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT t.telefono
            FROM telefono_cliente t
            WHERE t.id_cliente = %s
            LIMIT 1
        """, (id_cliente,))
        
        result = cursor.fetchone()
        cursor.close()
        conexion.close()
        
        if not result:
            return JSONResponse(
                {"error": "No se encontró teléfono registrado"},
                status_code=404
            )
        
        codigo = auth.crear_codigo_verificacion(
            'cliente',
            id_cliente,
            result['telefono'],
            'login'
        )
        
        auth.enviar_sms(result['telefono'], codigo)
        
        return JSONResponse({"mensaje": "Código reenviado"})
        
    except Exception as e:
        return JSONResponse(
            {"error": f"Error: {str(e)}"},
            status_code=500
        )

@router.get("/logout")
def logout_cliente(response: Response):
    """Cierra la sesión del cliente"""
    response.delete_cookie("session_token")
    return RedirectResponse(url="/", status_code=302)

@router.post("/configurar-password")
async def configurar_password_cliente(
    id_cliente: int = Form(...),
    password: str = Form(...),
    confirmar_password: str = Form(...)
):
    """Configura la contraseña de un cliente recién registrado"""
    try:
        if password != confirmar_password:
            return JSONResponse(
                {"error": "Las contraseñas no coinciden"},
                status_code=400
            )
        
        if len(password) < 6:
            return JSONResponse(
                {"error": "La contraseña debe tener al menos 6 caracteres"},
                status_code=400
            )
        
        auth.configurar_password_cliente(id_cliente, password)
        
        return JSONResponse({
            "mensaje": "Contraseña configurada correctamente",
            "redirect": "/cliente/login"
        })
        
    except Exception as e:
        return JSONResponse(
            {"error": f"Error: {str(e)}"},
            status_code=500
        )
