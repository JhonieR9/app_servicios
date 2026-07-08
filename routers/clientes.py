from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import math
import auth  # Módulo de autenticación
from config import DB_CONFIG, conectar_bd

router = APIRouter(prefix="/cliente", tags=["clientes"])
templates = Jinja2Templates(directory="templates")

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
    token = request.cookies.get("session_token_cliente") or request.cookies.get("session_token")
    if not token:
        return JSONResponse({"error": "No autenticado"}, status_code=401)
    sesion = auth.verificar_sesion(token)
    if not sesion or sesion['tipo_usuario'] != 'cliente':
        return JSONResponse({"error": "Sesión inválida"}, status_code=401)
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.id_cliente, c.nombre_completo,
               e.correo,
               e.verificado AS email_verificado,
               t.telefono
        FROM clientes c
        LEFT JOIN correo_cliente e ON c.id_cliente = e.id_cliente AND e.principal = 1
        LEFT JOIN telefono_cliente t ON c.id_cliente = t.id_cliente AND t.principal = 1
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
    response: Response,
    nombre_completo: str = Form(...),
    correo: str = Form(...),
    telefono: str = Form(...),
    password: str = Form(...),
    confirmar_password: str = Form(...)
):
    """Registro de cliente con contraseña y login automático"""
    if password != confirmar_password:
        return JSONResponse({"error": "Las contraseñas no coinciden"}, status_code=400)
    if len(password) < 6:
        return JSONResponse({"error": "La contraseña debe tener al menos 6 caracteres"}, status_code=400)

    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

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

        # Login automático — crear sesión
        token = auth.crear_sesion('cliente', id_cliente)
        response.set_cookie(
            key="session_token_cliente",
            value=token,
            httponly=False,
            max_age=86400 * 7,
            samesite="lax"
        )

        # Enviar código de verificación por email en background
        import threading
        codigo = auth.generar_codigo_sms()
        auth.crear_codigo_verificacion('cliente', id_cliente, telefono, 'registro')
        # Guardar código real (sobreescribir con el que vamos a enviar por email)
        conexion2 = conectar_bd()
        cursor2 = conexion2.cursor()
        from datetime import timedelta as td
        expiracion = datetime.now() + td(minutes=10)
        cursor2.execute("""
            INSERT INTO codigos_verificacion 
            (tipo_usuario, id_usuario, telefono, codigo, tipo_verificacion, fecha_expiracion)
            VALUES ('cliente', %s, %s, %s, 'registro', %s)
        """, (id_cliente, correo, codigo, expiracion))
        conexion2.commit(); cursor2.close(); conexion2.close()

        def _enviar_codigo():
            auth.enviar_codigo_verificacion_email(correo, codigo)
        threading.Thread(target=_enviar_codigo, daemon=True).start()

        nombre_corto = nombre_completo.split()[0]
        return JSONResponse({
            "mensaje": f"¡Bienvenido {nombre_corto}! Te enviamos un código de verificación a tu correo.",
            "id_cliente": id_cliente,
            "nombre": nombre_completo,
            "requiere_codigo": True,
            "redirect": f"/cliente/verificar-codigo?id={id_cliente}&correo={correo}"
        })
    except Exception as e:
        conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        cursor.close()
        conexion.close()

@router.get("/verificar-codigo", response_class=HTMLResponse)
def mostrar_verificar_codigo(request: Request):
    """Página para ingresar código de verificación"""
    return templates.TemplateResponse("clientes/verificar_codigo.html", {"request": request})

@router.post("/verificar-codigo")
def verificar_codigo_cliente(
    id_cliente: int = Form(...),
    codigo: str = Form(...)
):
    """Verifica el código de 4 dígitos enviado por email"""
    valido, mensaje = auth.verificar_codigo_sms('cliente', id_cliente, codigo)
    if valido:
        # Marcar correo como verificado
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("UPDATE correo_cliente SET verificado = 1 WHERE id_cliente = %s AND principal = 1", (id_cliente,))
        conexion.commit(); cursor.close(); conexion.close()
        return JSONResponse({"ok": True, "mensaje": "¡Correo verificado! Bienvenido a TalentHub.", "redirect": "/cliente/panel"})
    return JSONResponse({"ok": False, "error": "Código incorrecto o expirado"}, status_code=400)

@router.get("/solicitar_servicio", response_class=HTMLResponse)
def mostrar_solicitar_servicio(request: Request):
    return templates.TemplateResponse("clientes/solicitar_servicio.html", {"request": request})

@router.get("/seguimiento", response_class=HTMLResponse)
def mostrar_seguimiento(request: Request):
    return templates.TemplateResponse("clientes/seguimiento.html", {"request": request})

@router.get("/seguimiento_api")
def api_seguimiento(id: int):
    """Retorna el estado actual de una solicitud con datos del trabajador"""
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.id_solicitud, s.titulo, s.estado, s.ciudad, s.departamento,
                   s.fecha_solicitud, s.fecha_aceptacion, s.fecha_inicio, s.fecha_finalizacion,
                   s.id_trabajador, s.precio_final, s.id_categoria, s.codigo_confirmacion,
                   COALESCE(cat.nombre_categoria, s.titulo, CONCAT('Categoría ', s.id_categoria), 'Servicio') as nombre_categoria,
                   TIMESTAMPDIFF(MINUTE, s.fecha_solicitud, NOW()) as minutos_pendiente
            FROM solicitudes_servicio s
            LEFT JOIN categorias_servicio cat ON s.id_categoria = cat.id_categoria
            WHERE s.id_solicitud = %s
        """, (id,))
        sol = cursor.fetchone()
        if not sol:
            return JSONResponse({"error": "No encontrada"}, status_code=404)

        # Guardar minutos_pendiente antes de serializar fechas
        minutos_pendiente = int(sol.get('minutos_pendiente') or 0)
        sol['minutos_pendiente'] = minutos_pendiente

        from datetime import timedelta
        for k in ['fecha_solicitud','fecha_aceptacion','fecha_inicio','fecha_finalizacion']:
            if sol.get(k) and hasattr(sol[k], 'isoformat'):
                sol[k] = (sol[k] - timedelta(hours=5)).strftime('%d/%m %H:%M')
            elif not sol.get(k):
                sol[k] = None

        # Serializar precio
        if sol.get('precio_final') is not None:
            sol['precio_final'] = float(sol['precio_final'])

        # Garantizar que campos string no sean None
        for k in ['titulo', 'estado', 'ciudad', 'departamento', 'nombre_categoria']:
            if sol.get(k) is None:
                sol[k] = ''

        if sol.get('id_trabajador'):
            cursor.execute("""
                SELECT p.nombre_completo, tp.telefono
                FROM personas p
                LEFT JOIN telefono_persona tp ON p.id_persona = tp.id_persona
                WHERE p.id_persona = %s
            """, (sol['id_trabajador'],))
            trab = cursor.fetchone()
            if trab:
                sol['trabajador'] = {
                    'nombre':   trab['nombre_completo'] or '',
                    'telefono': str(trab['telefono'] or '')
                }

        return JSONResponse(sol)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()

@router.get("/mis_solicitudes", response_class=HTMLResponse)
def mostrar_mis_solicitudes(request: Request):
    return templates.TemplateResponse("clientes/mis_solicitudes.html", {"request": request})

@router.get("/mis_solicitudes_api")
def listar_mis_solicitudes_cliente(request: Request, id_cliente: int = None):
    """API para obtener solicitudes de un cliente con datos del trabajador"""
    conexion = conectar_bd()
    if not conexion:
        return JSONResponse({"error": "Error de conexión", "solicitudes": []}, status_code=500)
    try:
        cursor = conexion.cursor(dictionary=True)
        if not id_cliente:
            token = request.cookies.get("session_token_cliente") or request.cookies.get("session_token")
            if token:
                sesion = auth.verificar_sesion(token)
                if sesion and sesion.get('tipo_usuario') == 'cliente':
                    id_cliente = sesion['id_usuario']
        if not id_cliente:
            return JSONResponse({"solicitudes": []})

        cursor.execute("""
            SELECT s.id_solicitud, s.titulo, s.descripcion, s.estado,
                   s.ciudad, s.departamento, s.direccion_servicio,
                   s.fecha_solicitud, s.fecha_aceptacion, s.fecha_finalizacion,
                   s.id_trabajador,
                   cat.nombre_categoria,
                   p.nombre_completo  AS nombre_trabajador,
                   tp.telefono        AS telefono_trabajador,
                   cp.correo          AS correo_trabajador,
                   (SELECT ROUND(AVG(c2.puntuacion),1) FROM calificaciones c2 WHERE c2.id_trabajador = p.id_persona) AS calificacion_trabajador,
                   TIMESTAMPDIFF(MINUTE, s.fecha_solicitud, NOW()) AS minutos_pendiente
            FROM solicitudes_servicio s
            LEFT JOIN categorias_servicio cat ON s.id_categoria  = cat.id_categoria
            LEFT JOIN personas p              ON s.id_trabajador = p.id_persona
            LEFT JOIN telefono_persona tp     ON p.id_persona    = tp.id_persona
            LEFT JOIN correo_persona cp       ON p.id_persona    = cp.id_persona
            WHERE s.id_cliente = %s
            ORDER BY s.fecha_solicitud DESC
        """, (id_cliente,))

        solicitudes = cursor.fetchall()
        from datetime import timedelta
        for s in solicitudes:
            for k, v in s.items():
                if hasattr(v, 'isoformat'):
                    s[k] = (v - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M')
                elif v is None:
                    s[k] = ''
                elif hasattr(v, '__float__'):
                    s[k] = float(v)
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
    id_trabajador: str = Form(None),   # string para manejar '' sin error
    metodo_pago: str = Form("efectivo")
):
    # Convertir id_trabajador a int si viene con valor
    id_trab = None
    if id_trabajador and str(id_trabajador).strip():
        try:
            id_trab = int(id_trabajador)
        except (ValueError, TypeError):
            id_trab = None

    # Intentar obtener id_cliente desde la sesión si no viene en el form
    if not id_cliente:
        token = request.cookies.get("session_token_cliente") or request.cookies.get("session_token")
        if token:
            import auth as auth_module
            sesion = auth_module.verificar_sesion(token)
            if sesion and sesion.get('tipo_usuario') == 'cliente':
                id_cliente = sesion['id_usuario']
        if not id_cliente:
            return JSONResponse({"error": "Debes iniciar sesión para solicitar un servicio"}, status_code=401)
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
        # Buscar nombre real de la categoría en BD
        cursor2 = conexion.cursor(dictionary=True)
        cursor2.execute("SELECT nombre_categoria FROM categorias_servicio WHERE id_categoria = %s LIMIT 1", (id_categoria,))
        cat_row = cursor2.fetchone()
        if cat_row:
            nombre_cat = cat_row['nombre_categoria']
        cursor2.close()

        cursor.execute("""
            INSERT IGNORE INTO categorias_servicio (id_categoria, nombre_categoria, estado)
            VALUES (%s, %s, 'activo')
        """, (id_categoria, nombre_cat))
        conexion.commit()

        # Si se seleccionó un trabajador específico, asignarlo pero dejar en pendiente
        # El trabajador debe aceptar o rechazar
        if id_trab:
            sql = """
            INSERT INTO solicitudes_servicio 
            (id_cliente, id_categoria, id_trabajador, titulo, descripcion, direccion_servicio, 
             ciudad, departamento, fecha_programada, metodo_pago, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pendiente')
            """
            cursor.execute(sql, (
                id_cliente, id_categoria, id_trab, titulo, descripcion, direccion_servicio,
                ciudad, departamento, fecha_programada if fecha_programada else None,
                metodo_pago or 'efectivo'
            ))
        else:
            sql = """
            INSERT INTO solicitudes_servicio 
            (id_cliente, id_categoria, titulo, descripcion, direccion_servicio, 
             ciudad, departamento, fecha_programada, metodo_pago, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pendiente')
            """
            cursor.execute(sql, (
                id_cliente, id_categoria, titulo, descripcion, direccion_servicio,
                ciudad, departamento, fecha_programada if fecha_programada else None,
                metodo_pago or 'efectivo'
            ))
        conexion.commit()
        id_solicitud = cursor.lastrowid

        # Ya NO se acepta automáticamente — el trabajador decide
        # Obtener nombre real del cliente para la notificación
        nombre_cliente_notif = str(id_cliente)
        try:
            cursor_nc = conexion.cursor(dictionary=True)
            cursor_nc.execute(
                "SELECT nombre_completo FROM clientes WHERE id_cliente = %s LIMIT 1",
                (id_cliente,)
            )
            row_nc = cursor_nc.fetchone()
            if row_nc and row_nc.get('nombre_completo'):
                nombre_cliente_notif = row_nc['nombre_completo']
            cursor_nc.close()
        except Exception:
            pass

        # Notificar por email a trabajadores con esa categoría (en background)
        try:
            import threading
            def _notificar(nombre_cli=nombre_cliente_notif):
                try:
                    import os
                    from config import conectar_bd as _conectar
                    conn2 = _conectar()
                    cur2  = conn2.cursor(dictionary=True)
                    # Buscar trabajadores activos con esa categoría y correo registrado
                    cur2.execute("""
                        SELECT DISTINCT p.id_persona, p.nombre_completo,
                               cp.correo, p.ciudad
                        FROM personas p
                        INNER JOIN servicios_persona sp ON p.id_persona = sp.id_persona
                        INNER JOIN correo_persona cp    ON p.id_persona = cp.id_persona
                        LEFT JOIN  disponibilidad d     ON p.id_persona = d.id_persona
                        WHERE sp.id_categoria = %s
                          AND (p.estado = 'activo' OR p.estado IS NULL)
                          AND (d.disponible = 1 OR d.disponible IS NULL)
                        LIMIT 20
                    """, (id_categoria,))
                    trabajadores_notif = cur2.fetchall()
                    cur2.close(); conn2.close()

                    base_url = os.getenv("APP_URL", "https://web-production-191f4.up.railway.app")
                    for t in trabajadores_notif:
                        auth.notificar_nueva_solicitud(
                            correo_trabajador = t['correo'],
                            nombre_trabajador = t['nombre_completo'],
                            nombre_cliente    = nombre_cli,
                            categoria         = nombre_cat,
                            descripcion       = descripcion or '',
                            ciudad            = ciudad or '',
                            id_solicitud      = id_solicitud,
                            base_url          = base_url
                        )
                    # Push notifications nativas
                    try:
                        import main as _main
                        _main.enviar_push_trabajadores(
                            id_categoria    = id_categoria,
                            nombre_categoria = nombre_cat,
                            titulo_notif    = f"🔔 Nueva solicitud: {nombre_cat}",
                            cuerpo          = f"{nombre_cli} en {ciudad or 'tu zona'} — {(descripcion or '')[:80]}",
                            url_destino     = "/trabajador/panel"
                        )
                    except Exception as _pe:
                        print(f"[PUSH] No se pudo enviar: {_pe}")
                except Exception as ex:
                    print(f"[NOTIF] Error en hilo: {ex}")
            threading.Thread(target=_notificar, daemon=True).start()
        except Exception:
            pass

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
        SELECT s.id_solicitud, s.titulo, s.estado, s.ciudad, s.departamento,
               s.fecha_solicitud, s.fecha_finalizacion,
               cat.nombre_categoria
        FROM solicitudes_servicio s
        LEFT JOIN categorias_servicio cat ON s.id_categoria = cat.id_categoria
        WHERE s.id_cliente = %s
        ORDER BY s.fecha_solicitud DESC
    """, (id_cliente,))
    historial = cursor.fetchall()
    for h in historial:
        for k, v in h.items():
            if hasattr(v, 'isoformat'): h[k] = str(v)
            elif v is None: h[k] = ''
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
    WHERE id_solicitud = %s AND estado IN ('pendiente', 'aceptada', 'en_proceso')
    """
    
    cursor.execute(sql, (motivo, id_solicitud))
    conexion.commit()
    afectadas = cursor.rowcount
    cursor.close()
    conexion.close()
    
    if afectadas == 0:
        return JSONResponse({"error": "No se pudo cancelar — la solicitud ya está completada o cancelada"}, status_code=400)
    return {"mensaje": "Solicitud cancelada"}

@router.post("/solicitud/completar")
def completar_solicitud_cliente(
    id_solicitud: int = Form(...),
    fecha_local: str = Form(...)   # El cliente envía su hora local: "2026-05-14T15:30:00"
):
    """Solo el cliente puede marcar un servicio como completado"""
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    try:
        # Verificar que la solicitud existe y está en proceso
        cursor.execute("""
            SELECT id_solicitud, id_cliente, id_trabajador, estado
            FROM solicitudes_servicio
            WHERE id_solicitud = %s
        """, (id_solicitud,))
        sol = cursor.fetchone()

        if not sol:
            return JSONResponse({"error": "Solicitud no encontrada"}, status_code=404)
        if sol['estado'] not in ('aceptada', 'en_proceso'):
            return JSONResponse({"error": f"No se puede completar una solicitud en estado '{sol['estado']}'"}, status_code=400)

        # Guardar la hora local del cliente (no la del servidor)
        cursor.execute("""
            UPDATE solicitudes_servicio
            SET estado = 'completada', fecha_finalizacion = %s
            WHERE id_solicitud = %s
        """, (fecha_local, id_solicitud))
        conexion.commit()

        return JSONResponse({
            "mensaje": "¡Servicio completado! Gracias por usar TalentHub.",
            "id_solicitud": id_solicitud,
            "id_trabajador": sol['id_trabajador']
        })
    except Exception as e:
        conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        cursor.close()
        conexion.close()


@router.post("/calificar")
def calificar_servicio(
    id_solicitud: int = Form(...),
    id_cliente: int = Form(...),
    id_trabajador: int = Form(0),
    puntuacion: int = Form(...),
    comentario: str = Form(None),
    tags: str = Form(None)
):
    if puntuacion < 1 or puntuacion > 5:
        return {"error": "La puntuación debe estar entre 1 y 5"}

    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    # Si no viene id_trabajador, obtenerlo de la solicitud
    if not id_trabajador:
        cursor.execute("SELECT id_trabajador FROM solicitudes_servicio WHERE id_solicitud = %s", (id_solicitud,))
        sol = cursor.fetchone()
        id_trabajador = sol['id_trabajador'] if sol and sol['id_trabajador'] else 0

    if not id_trabajador:
        return JSONResponse({"error": "No se encontró el trabajador"}, status_code=400)

    # Validar que exista una solicitud completada entre este cliente y este trabajador
    cursor.execute("""
        SELECT id_solicitud FROM solicitudes_servicio
        WHERE id_solicitud = %s
          AND id_cliente = %s
          AND id_trabajador = %s
          AND estado = 'completada'
        LIMIT 1
    """, (id_solicitud, id_cliente, id_trabajador))
    if not cursor.fetchone():
        cursor.close()
        conexion.close()
        return JSONResponse(
            {"error": "Solo puedes calificar un servicio que hayas completado con este trabajador"},
            status_code=403
        )

    # Evitar calificación duplicada
    cursor.execute("""
        SELECT id_calificacion FROM calificaciones
        WHERE id_solicitud = %s AND id_cliente = %s
    """, (id_solicitud, id_cliente))
    if cursor.fetchone():
        cursor.close()
        conexion.close()
        return JSONResponse({"mensaje": "Ya calificaste este servicio"})

    cursor.execute("""
        INSERT INTO calificaciones
        (id_solicitud, id_cliente, id_trabajador, tipo_calificacion, puntuacion, comentario, tags)
        VALUES (%s, %s, %s, 'cliente_a_trabajador', %s, %s, %s)
    """, (id_solicitud, id_cliente, id_trabajador, puntuacion, comentario, tags))
    conexion.commit()
    cursor.close()
    conexion.close()

    return {"mensaje": "¡Gracias por tu calificación!"}


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
    radio: float = 30.0,
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
            # Obtener calificación promedio
            cursor.execute("""
                SELECT AVG(puntuacion) as promedio, COUNT(*) as total
                FROM calificaciones
                WHERE id_trabajador = %s
            """, (trabajador['id_persona'],))
            cal = cursor.fetchone()
            calificacion = round(float(cal['promedio']), 1) if cal and cal['promedio'] else 0
            total_cal = int(cal['total']) if cal else 0

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
                
                # Calificación promedio
                cursor.execute("""
                    SELECT ROUND(AVG(puntuacion),1) as promedio, COUNT(*) as total
                    FROM calificaciones WHERE id_trabajador = %s
                """, (trabajador['id_persona'],))
                cal = cursor.fetchone()
                calificacion = float(cal['promedio']) if cal and cal['promedio'] else 0
                total_cal = int(cal['total']) if cal else 0

                trabajadores_cercanos.append({
                    "id": int(trabajador['id_persona']),
                    "nombre": str(trabajador['nombre_completo']),
                    "telefono": str(trabajador.get('telefono') or 'N/A'),
                    "experiencia": experiencia,
                    "categoria": servicios[0]['categoria'] if servicios else 'General',
                    "tarifa": float(servicios[0].get('valor_hora') or 0) if servicios else 0,
                    "servicios": servicios,
                    "latitud": float(trabajador_lat),
                    "longitud": float(trabajador_lng),
                    "distancia": float(round(distancia, 2)),
                    "tiene_gps_real": bool(trabajador.get('latitud') and trabajador.get('longitud')),
                    "calificacion": calificacion,
                    "total_calificaciones": total_cal
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
# EDITAR PERFIL Y BAJA - CLIENTES
# ============================================

@router.post("/perfil/editar")
def editar_perfil_cliente(
    request: Request,
    nombre:   str = Form(None),
    telefono: str = Form(None),
    correo:   str = Form(None)
):
    """Permite al cliente actualizar sus datos"""
    token = request.cookies.get("session_token_cliente") or request.cookies.get("session_token")
    if not token:
        return JSONResponse({"error": "No autenticado"}, status_code=401)
    sesion = auth.verificar_sesion(token)
    if not sesion or sesion['tipo_usuario'] != 'cliente':
        return JSONResponse({"error": "Sesión inválida"}, status_code=401)

    id_cliente = sesion['id_usuario']
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()

        if nombre:
            cursor.execute("UPDATE clientes SET nombre_completo = %s WHERE id_cliente = %s", (nombre, id_cliente))

        if telefono:
            cursor.execute("SELECT 1 FROM telefono_cliente WHERE id_cliente = %s AND principal = 1 LIMIT 1", (id_cliente,))
            if cursor.fetchone():
                cursor.execute("UPDATE telefono_cliente SET telefono = %s WHERE id_cliente = %s AND principal = 1", (telefono, id_cliente))
            else:
                cursor.execute("INSERT INTO telefono_cliente (id_cliente, telefono, tipo_telefono, principal) VALUES (%s, %s, 'celular', 1)", (id_cliente, telefono))

        if correo:
            cursor.execute("SELECT 1 FROM correo_cliente WHERE id_cliente = %s AND principal = 1 LIMIT 1", (id_cliente,))
            if cursor.fetchone():
                cursor.execute("UPDATE correo_cliente SET correo = %s WHERE id_cliente = %s AND principal = 1", (correo, id_cliente))
            else:
                cursor.execute("INSERT INTO correo_cliente (id_cliente, correo, verificado, principal) VALUES (%s, %s, 0, 1)", (id_cliente, correo))

        conexion.commit()
        return JSONResponse({"mensaje": "Datos actualizados correctamente"})
    except Exception as e:
        conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()

@router.post("/baja")
def dar_de_baja_cliente(
    request: Request,
    id_cliente: int = Form(None)
):
    """Desactiva la cuenta del cliente (soft delete)"""
    token = request.cookies.get("session_token_cliente") or request.cookies.get("session_token")
    if not token:
        return JSONResponse({"error": "No autenticado"}, status_code=401)
    sesion = auth.verificar_sesion(token)
    if not sesion or sesion['tipo_usuario'] != 'cliente':
        return JSONResponse({"error": "Sesión inválida"}, status_code=401)

    id_real = sesion['id_usuario']
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        cursor.execute("UPDATE clientes SET estado = 'inactivo' WHERE id_cliente = %s", (id_real,))
        conexion.commit()
        return JSONResponse({"mensaje": "Cuenta desactivada"})
    except Exception as e:
        conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
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
        
        # Verificar si requiere verificación SMS (tabla puede no existir)
        requiere_sms = False
        try:
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
        except Exception:
            requiere_sms = False
        
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
                "nombre": nombre,
                "telefono": str(cliente.get('telefono') or ''),
                "correo": cliente.get('correo', ''),
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
            key="session_token_cliente",
            value=token,
            httponly=False,
            max_age=86400,
            samesite="lax"
        )
        
        return JSONResponse({
            "mensaje": "Verificación exitosa",
            "redirect": "/cliente/panel"
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
    response.delete_cookie("session_token_cliente")
    response.delete_cookie("session_token")  # por compatibilidad
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

# ============================================
# RECUPERACIÓN DE CONTRASEÑA - CLIENTES
# ============================================

@router.get("/recuperar", response_class=HTMLResponse)
def mostrar_recuperar_cliente(request: Request):
    """Página para solicitar recuperación de contraseña"""
    return templates.TemplateResponse("clientes/recuperar_password.html", {"request": request})

@router.post("/recuperar/solicitar")
async def solicitar_recuperacion_cliente(request: Request, correo: str = Form(...)):
    """Genera token y envía email de recuperación"""
    try:
        token = auth.crear_token_recuperacion('cliente', correo)
        if token:
            base_url = str(request.base_url).rstrip('/')
            # Enviar en background para no bloquear la respuesta
            import threading
            def _enviar():
                auth.enviar_email_recuperacion(correo, token, 'cliente', base_url)
            threading.Thread(target=_enviar, daemon=True).start()
        # Siempre responder igual — no revelar si el correo existe o no
        return JSONResponse({"mensaje": "Si el correo está registrado, recibirás un enlace en breve."})
    except Exception as e:
        import traceback; traceback.print_exc()
        return JSONResponse({"error": f"Error interno: {str(e)}"}, status_code=500)

@router.get("/recuperar/nueva-password", response_class=HTMLResponse)
def mostrar_nueva_password_cliente(request: Request, token: str = ""):
    """Página para ingresar la nueva contraseña"""
    datos = auth.verificar_token_recuperacion(token) if token else None
    if not datos:
        return templates.TemplateResponse("clientes/recuperar_password.html", {
            "request": request,
            "error_token": "El enlace es inválido o ya expiró. Solicita uno nuevo."
        })
    return templates.TemplateResponse("clientes/nueva_password.html", {
        "request": request, "token": token
    })

@router.post("/recuperar/nueva-password")
async def guardar_nueva_password_cliente(
    token: str = Form(...),
    password: str = Form(...),
    confirmar_password: str = Form(...)
):
    """Guarda la nueva contraseña del cliente"""
    if password != confirmar_password:
        return JSONResponse({"error": "Las contraseñas no coinciden"}, status_code=400)
    if len(password) < 6:
        return JSONResponse({"error": "Mínimo 6 caracteres"}, status_code=400)
    ok = auth.consumir_token_recuperacion(token, password)
    if not ok:
        return JSONResponse({"error": "El enlace es inválido o ya expiró"}, status_code=400)
    return JSONResponse({"mensaje": "Contraseña actualizada correctamente", "redirect": "/cliente/login"})

@router.get("/recuperar/verificar-correo")
def verificar_correo_cliente(correo: str):
    """Verifica si un correo está registrado como cliente (para validación en tiempo real)"""
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.id_cliente FROM clientes c
            INNER JOIN correo_cliente ec ON c.id_cliente = ec.id_cliente
            WHERE ec.correo = %s AND c.estado = 'activo'
            LIMIT 1
        """, (correo,))
        existe = cursor.fetchone() is not None
        return JSONResponse({"existe": existe})
    except Exception as e:
        return JSONResponse({"existe": False, "error": str(e)})
    finally:
        if conexion and conexion.is_connected():
            conexion.close()

# ============================================
# CHAT DIRECTO — crear solicitud y abrir chat
# ============================================

@router.post("/iniciar-chat")
async def iniciar_chat_directo(
    id_cliente:    int = Form(...),
    id_trabajador: int = Form(...),
    categoria:     str = Form("Servicio general"),
    mensaje_inicial: str = Form(None)
):
    """
    Crea una solicitud pendiente y un mensaje inicial en el chat.
    Retorna el id_solicitud para redirigir al chat.
    """
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)

        # Datos del trabajador
        cursor.execute("""
            SELECT p.nombre_completo, tp.telefono
            FROM personas p
            LEFT JOIN telefono_persona tp ON p.id_persona = tp.id_persona
            WHERE p.id_persona = %s LIMIT 1
        """, (id_trabajador,))
        trabajador = cursor.fetchone()
        if not trabajador:
            return JSONResponse({"error": "Trabajador no encontrado"}, status_code=404)

        # Datos del cliente
        cursor.execute("""
            SELECT c.nombre_completo FROM clientes c WHERE c.id_cliente = %s LIMIT 1
        """, (id_cliente,))
        cliente = cursor.fetchone()
        nombre_cliente = cliente['nombre_completo'] if cliente else 'Cliente'

        # Buscar id_categoria
        cursor.execute("""
            SELECT id_categoria FROM categorias_servicio
            WHERE nombre_categoria = %s LIMIT 1
        """, (categoria,))
        cat = cursor.fetchone()
        id_categoria = cat['id_categoria'] if cat else None

        # Crear solicitud
        titulo = f"{categoria} - {trabajador['nombre_completo']}"
        cursor.execute("""
            INSERT INTO solicitudes_servicio
            (id_cliente, id_trabajador, id_categoria, titulo, descripcion, estado, fecha_solicitud)
            VALUES (%s, %s, %s, %s, %s, 'pendiente', NOW())
        """, (id_cliente, id_trabajador, id_categoria, titulo,
              mensaje_inicial or f"Solicitud de {nombre_cliente}"))
        id_solicitud = cursor.lastrowid

        # Mensaje de sistema
        cursor.execute("""
            INSERT INTO mensajes_chat
            (id_solicitud, tipo_remitente, id_remitente, mensaje, fecha_envio, leido)
            VALUES (%s, 'sistema', 0, %s, NOW(), 0)
        """, (id_solicitud,
              f"💬 {nombre_cliente} inició una conversación sobre {categoria}"))

        # Mensaje inicial del cliente si lo escribió
        if mensaje_inicial and mensaje_inicial.strip():
            cursor.execute("""
                INSERT INTO mensajes_chat
                (id_solicitud, tipo_remitente, id_remitente, mensaje, fecha_envio, leido)
                VALUES (%s, 'cliente', %s, %s, NOW(), 0)
            """, (id_solicitud, id_cliente, mensaje_inicial.strip()))

        conexion.commit()

        # Notificar al trabajador específico por email
        try:
            import threading, os
            correo_t = None
            cur_email = conexion.cursor(dictionary=True) if conexion.is_connected() else None
            if cur_email:
                cur_email.execute(
                    "SELECT correo FROM correo_persona WHERE id_persona = %s LIMIT 1",
                    (id_trabajador,)
                )
                row = cur_email.fetchone()
                correo_t = row['correo'] if row else None
                cur_email.close()

            if correo_t:
                base_url = os.getenv("APP_URL", "https://talenthub.up.railway.app")
                def _notif():
                    auth.notificar_nueva_solicitud(
                        correo_trabajador = correo_t,
                        nombre_trabajador = trabajador['nombre_completo'],
                        nombre_cliente    = nombre_cliente,
                        categoria         = categoria,
                        descripcion       = mensaje_inicial or '',
                        ciudad            = '',
                        id_solicitud      = id_solicitud,
                        base_url          = base_url
                    )
                threading.Thread(target=_notif, daemon=True).start()
        except Exception as ex:
            print(f"[NOTIF] Error chat directo: {ex}")

        return JSONResponse({
            "ok": True,
            "id_solicitud": id_solicitud,
            "redirect": f"/chat/?id_solicitud={id_solicitud}&tipo=cliente&id_usuario={id_cliente}"
        })
    except Exception as e:
        if conexion: conexion.rollback()
        import traceback; traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()

# ============================================
# VERIFICACIÓN DE EMAIL
# ============================================

@router.get("/verificar-email", response_class=HTMLResponse)
def verificar_email_cliente(request: Request, token: str = ""):
    """Verifica el email del cliente desde el link del correo"""
    if not token:
        return templates.TemplateResponse("verificacion_email.html", {
            "request": request, "exito": False,
            "mensaje": "Enlace inválido. Asegúrate de copiar el link completo del correo.",
            "redirect": "/cliente/login"
        })
    datos = auth.verificar_email_token(token)
    if datos:
        return templates.TemplateResponse("verificacion_email.html", {
            "request": request, "exito": True,
            "mensaje": "¡Tu correo ha sido verificado exitosamente! Ya puedes usar todas las funciones de TalentHub.",
            "redirect": "/cliente/login"
        })
    return templates.TemplateResponse("verificacion_email.html", {
        "request": request, "exito": False,
        "mensaje": "El enlace es inválido o ya expiró. Inicia sesión para solicitar uno nuevo.",
        "redirect": "/cliente/login"
    })

@router.post("/reenviar-verificacion")
async def reenviar_verificacion_cliente(request: Request, id_cliente: int = None):
    """Reenvía el email de verificación al cliente — acepta sesión o id_cliente directo"""
    import os

    # Intentar obtener id desde sesión
    if not id_cliente:
        token = request.cookies.get("session_token_cliente") or request.cookies.get("session_token")
        if token:
            sesion = auth.verificar_sesion(token)
            if sesion and sesion['tipo_usuario'] == 'cliente':
                id_cliente = sesion['id_usuario']

    # Intentar desde body JSON
    if not id_cliente:
        try:
            body = await request.json()
            id_cliente = body.get("id_cliente")
        except Exception:
            pass

    if not id_cliente:
        return JSONResponse({"error": "No autenticado"}, status_code=401)

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT ec.correo, ec.verificado, c.nombre_completo
            FROM correo_cliente ec
            INNER JOIN clientes c ON ec.id_cliente = c.id_cliente
            WHERE ec.id_cliente = %s AND ec.principal = 1 LIMIT 1
        """, (id_cliente,))
        row = cursor.fetchone()
        if not row:
            return JSONResponse({"error": "No se encontró correo registrado"}, status_code=404)
        if row['verificado']:
            return JSONResponse({"mensaje": "Tu correo ya está verificado."})

        base_url = os.getenv("APP_URL", "https://web-production-191f4.up.railway.app")
        # Lanzar en background para no bloquear la respuesta
        import threading
        resultado = [False]
        def _enviar():
            resultado[0] = auth.enviar_email_bienvenida(
                row['correo'], row['nombre_completo'], 'cliente', id_cliente, base_url
            )
        t = threading.Thread(target=_enviar, daemon=True)
        t.start()
        t.join(timeout=15)  # esperar máximo 15s
        if resultado[0]:
            return JSONResponse({"mensaje": f"Correo de verificación reenviado a {row['correo']}"})
        else:
            return JSONResponse({"error": "No se pudo enviar el correo. Revisa GMAIL_USER y GMAIL_PASS en Railway."}, status_code=500)
    except Exception as e:
        import traceback; traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()

@router.get("/buscar")
def buscar_cliente(nombre: str = "", correo: str = ""):
    """Busca clientes por nombre o correo — para uso admin"""
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        if correo:
            cursor.execute("""
                SELECT c.id_cliente, c.nombre_completo, ec.correo, c.fecha_registro
                FROM clientes c
                LEFT JOIN correo_cliente ec ON c.id_cliente = ec.id_cliente
                WHERE ec.correo LIKE %s
                LIMIT 10
            """, (f"%{correo}%",))
        else:
            cursor.execute("""
                SELECT c.id_cliente, c.nombre_completo, ec.correo, c.fecha_registro
                FROM clientes c
                LEFT JOIN correo_cliente ec ON c.id_cliente = ec.id_cliente
                WHERE c.nombre_completo LIKE %s
                LIMIT 10
            """, (f"%{nombre}%",))
        resultados = cursor.fetchall()
        for r in resultados:
            for k, v in r.items():
                if hasattr(v, 'isoformat'): r[k] = str(v)
                elif v is None: r[k] = ''
        return JSONResponse({"clientes": resultados})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()

@router.get("/debug/solicitudes-recientes")
def debug_solicitudes_recientes():
    """Diagnóstico: últimas 10 solicitudes con id_cliente y nombre"""
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.id_solicitud, s.id_cliente, s.estado, s.titulo,
                   s.fecha_solicitud,
                   c.nombre_completo as nombre_cliente
            FROM solicitudes_servicio s
            LEFT JOIN clientes c ON s.id_cliente = c.id_cliente
            ORDER BY s.id_solicitud DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        for r in rows:
            for k, v in r.items():
                if hasattr(v, 'isoformat'): r[k] = str(v)
                elif v is None: r[k] = ''
        return JSONResponse({"solicitudes": rows})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()

# ============================================
# FAVORITOS — guardar/quitar/listar trabajadores favoritos
# ============================================

@router.post("/favorito/toggle")
async def toggle_favorito(
    request: Request,
    id_trabajador: int = Form(...),
    id_cliente: int = Form(None)
):
    """Agrega o quita un trabajador de favoritos del cliente"""
    # Obtener id_cliente desde sesión si no viene en el form
    if not id_cliente:
        token = request.cookies.get("session_token_cliente") or request.cookies.get("session_token")
        if token:
            sesion = auth.verificar_sesion(token)
            if sesion and sesion['tipo_usuario'] == 'cliente':
                id_cliente = sesion['id_usuario']
    if not id_cliente:
        return JSONResponse({"error": "No autenticado"}, status_code=401)

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        # Verificar si ya es favorito
        cursor.execute("""
            SELECT id FROM favoritos_cliente
            WHERE id_cliente = %s AND id_trabajador = %s
        """, (id_cliente, id_trabajador))
        existente = cursor.fetchone()

        if existente:
            # Quitar de favoritos
            cursor.execute("""
                DELETE FROM favoritos_cliente
                WHERE id_cliente = %s AND id_trabajador = %s
            """, (id_cliente, id_trabajador))
            conexion.commit()
            return JSONResponse({"ok": True, "favorito": False, "mensaje": "Eliminado de favoritos"})
        else:
            # Agregar a favoritos
            cursor.execute("""
                INSERT INTO favoritos_cliente (id_cliente, id_trabajador)
                VALUES (%s, %s)
            """, (id_cliente, id_trabajador))
            conexion.commit()
            return JSONResponse({"ok": True, "favorito": True, "mensaje": "Guardado en favoritos ❤️"})
    except Exception as e:
        conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


@router.get("/favoritos")
def listar_favoritos(request: Request, id_cliente: int = None):
    """Lista los trabajadores favoritos del cliente con datos completos"""
    if not id_cliente:
        token = request.cookies.get("session_token_cliente") or request.cookies.get("session_token")
        if token:
            sesion = auth.verificar_sesion(token)
            if sesion and sesion['tipo_usuario'] == 'cliente':
                id_cliente = sesion['id_usuario']
    if not id_cliente:
        return JSONResponse({"favoritos": []})

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                p.id_persona,
                p.nombre_completo,
                p.ciudad,
                tp.telefono,
                f.fecha_guardado,
                ROUND(AVG(cal.puntuacion), 1) AS calificacion,
                COUNT(cal.id_calificacion)    AS total_resenas,
                GROUP_CONCAT(DISTINCT sp.categoria ORDER BY sp.categoria SEPARATOR ', ') AS categorias
            FROM favoritos_cliente f
            INNER JOIN personas p    ON f.id_trabajador = p.id_persona
            LEFT JOIN telefono_persona tp ON p.id_persona = tp.id_persona
            LEFT JOIN calificaciones cal  ON p.id_persona = cal.id_trabajador
            LEFT JOIN servicios_persona sp ON p.id_persona = sp.id_persona
            WHERE f.id_cliente = %s
              AND (p.estado = 'activo' OR p.estado IS NULL)
            GROUP BY p.id_persona, p.nombre_completo, p.ciudad, tp.telefono, f.fecha_guardado
            ORDER BY f.fecha_guardado DESC
        """, (id_cliente,))
        favoritos = cursor.fetchall()

        from datetime import timedelta
        for fav in favoritos:
            for k, v in fav.items():
                if v is None:
                    fav[k] = '' if k not in ('calificacion', 'total_resenas') else 0
                elif hasattr(v, 'isoformat'):
                    fav[k] = (v - timedelta(hours=5)).strftime('%d/%m/%Y')
                elif hasattr(v, '__float__'):
                    fav[k] = float(v)

        return JSONResponse({"favoritos": favoritos})
    except Exception as e:
        return JSONResponse({"error": str(e), "favoritos": []}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


@router.get("/favorito/check")
def check_favorito(id_cliente: int, id_trabajador: int):
    """Verifica si un trabajador es favorito de un cliente"""
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT id FROM favoritos_cliente
            WHERE id_cliente = %s AND id_trabajador = %s
        """, (id_cliente, id_trabajador))
        return JSONResponse({"favorito": cursor.fetchone() is not None})
    except Exception as e:
        return JSONResponse({"favorito": False})
    finally:
        if conexion and conexion.is_connected():
            conexion.close()
