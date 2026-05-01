from fastapi import APIRouter, Form, Request, UploadFile, File, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import mysql.connector
from datetime import datetime, timedelta
import bcrypt
import auth  # Módulo de autenticación
from config import DB_CONFIG

router = APIRouter(prefix="/trabajador", tags=["trabajadores"])
templates = Jinja2Templates(directory="templates")

# Conexión a BD
def conectar_bd():
    return mysql.connector.connect(**DB_CONFIG)

# ============================================
# TEMPLATES - Aquí conectarás tu formulario de hoja de vida
# ============================================

@router.get("/crear_password", response_class=HTMLResponse)
def mostrar_crear_password(request: Request):
    """Pantalla para crear contraseña después del registro"""
    return templates.TemplateResponse("trabajadores/crear_password.html", {"request": request})

@router.get("/panel", response_class=HTMLResponse)
def mostrar_panel_trabajador(request: Request):
    """Panel principal del trabajador"""
    return templates.TemplateResponse("trabajadores/panel.html", {"request": request})

@router.get("/mi-perfil")
def obtener_mi_perfil(request: Request):
    """Obtiene datos del trabajador autenticado"""
    token = request.cookies.get("session_token")
    if not token:
        from fastapi.responses import JSONResponse as JR
        return JR({"error": "No autenticado"}, status_code=401)
    sesion = auth.verificar_sesion(token)
    if not sesion or sesion['tipo_usuario'] != 'trabajador':
        return JSONResponse({"error": "Sesión inválida"}, status_code=401)
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT id_persona, nombre_completo, numero_documento, ciudad FROM personas WHERE id_persona = %s", (sesion['id_usuario'],))
    trabajador = cursor.fetchone()
    cursor.close()
    conexion.close()
    return JSONResponse(trabajador or {"error": "No encontrado"})

@router.get("/registro", response_class=HTMLResponse)
def mostrar_registro_trabajador(request: Request):
    return templates.TemplateResponse("trabajadores/registro_trabajador.html", {"request": request})

@router.post("/crear")
async def crear_trabajador(
    request: Request,
    tipo_documento: int = Form(...),
    numero_documento: str = Form(...),
    genero: int = Form(...),
    nombre_completo: str = Form(...),
    fecha_nacimiento: str = Form(None),
    nacionalidad: str = Form(None),
    ciudad: str = Form(...),
    departamento: str = Form(None),
    codigo_dane: str = Form(...),
    celular: str = Form(...),
    correo: str = Form(None),
    habilidades_tipo: int = Form(...),
    disponibilidad: int = Form(...),
    disponibilidad_dias: int = Form(...),
    foto_identificacion: UploadFile = File(...),
    foto_antecedentes: UploadFile = File(...),
    recomendaciones_archivo: UploadFile = File(...),
    antecedentes: str = Form(None),
    recomendaciones: str = Form(None),
    acepta_terminos: str = Form(None),
    permisos_ubicacion: str = Form(None)
):
    """Crear nuevo trabajador con todos sus datos"""
    import os
    from datetime import datetime
    from werkzeug.utils import secure_filename
    
    UPLOAD_FOLDER = "static/uploads"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    conexion = None
    cursor = None
    
    try:
        # Validar que el documento no exista
        conexion = conectar_bd()
        cursor = conexion.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM personas WHERE numero_documento = %s", (numero_documento,))
        if cursor.fetchone()[0] > 0:
            return {"error": f"El documento {numero_documento} ya está registrado"}
        
        # Leer archivos en memoria (para guardar en BD)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Foto identificación
        foto_bytes = await foto_identificacion.read()
        foto_filename = f"foto_{timestamp}_{foto_identificacion.filename}"
        foto_tipo = foto_identificacion.content_type or 'image/jpeg'
        # Guardar también en disco si es posible
        try:
            foto_path = os.path.join(UPLOAD_FOLDER, foto_filename)
            with open(foto_path, "wb") as f:
                f.write(foto_bytes)
        except: pass

        # Antecedentes
        antecedentes_bytes = await foto_antecedentes.read()
        antecedentes_filename = f"antecedentes_{timestamp}_{foto_antecedentes.filename}" if foto_antecedentes.filename else None
        antecedentes_tipo = foto_antecedentes.content_type or 'application/pdf'
        try:
            if antecedentes_filename:
                ant_path = os.path.join(UPLOAD_FOLDER, antecedentes_filename)
                with open(ant_path, "wb") as f:
                    f.write(antecedentes_bytes)
        except: pass

        # Recomendaciones
        recomend_bytes = await recomendaciones_archivo.read()
        recomend_filename = f"recom_{timestamp}_{recomendaciones_archivo.filename}" if recomendaciones_archivo.filename else None
        recomend_tipo = recomendaciones_archivo.content_type or 'application/pdf'
        try:
            if recomend_filename:
                rec_path = os.path.join(UPLOAD_FOLDER, recomend_filename)
                with open(rec_path, "wb") as f:
                    f.write(recomend_bytes)
        except: pass
        
        # Iniciar transacción
        conexion.autocommit = False
        
        # 1. Insertar persona
        cursor.execute("""
            INSERT INTO personas 
            (id_tipo_documento, numero_documento, id_genero, nombre_completo, ciudad, codigo_dane, fecha_nacimiento, nacionalidad, registrado_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (tipo_documento, numero_documento, genero, nombre_completo, ciudad, codigo_dane, fecha_nacimiento, nacionalidad, nombre_completo))        
        id_persona = cursor.lastrowid
        
        # 2. Insertar teléfono
        cursor.execute("""
            INSERT INTO telefono_persona (id_persona, telefono)
            VALUES (%s, %s)
        """, (id_persona, celular))
        
        # 3. Insertar correo (opcional)
        if correo:
            cursor.execute("""
                INSERT INTO correo_persona (id_persona, correo)
                VALUES (%s, %s)
            """, (id_persona, correo))
        
        # 4. Obtener servicios del formulario
        form_data = await request.form()
        servicios_categoria = form_data.getlist('servicio_categoria[]')
        servicios_desc = form_data.getlist('habilidad_desc[]')
        servicios_exp = form_data.getlist('habilidad_exp[]')
        servicios_valor = form_data.getlist('habilidad_valor[]')
        tiene_ayudante_list = form_data.getlist('tiene_ayudante[]')
        costo_ayudante_list = form_data.getlist('costo_ayudante[]')
        
        experiencias_validas = []
        todos_servicios = []
        
        for i in range(len(servicios_desc)):
            if servicios_desc[i].strip():
                categoria = servicios_categoria[i] if i < len(servicios_categoria) else 'Otro'
                exp_valor = float(servicios_exp[i]) if servicios_exp[i] else 0
                valor_hora = float(servicios_valor[i]) if servicios_valor[i] else 0
                tiene_ayudante = int(tiene_ayudante_list[i]) if i < len(tiene_ayudante_list) else 0
                costo_ayudante = float(costo_ayudante_list[i]) if i < len(costo_ayudante_list) and costo_ayudante_list[i] and tiene_ayudante == 1 else None
                
                cursor.execute("""
                    INSERT INTO servicios_persona 
                    (id_persona, categoria, descripcion, anios_experiencia, valor_hora, tiene_ayudante, costo_ayudante)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (id_persona, categoria, servicios_desc[i].strip(), exp_valor, valor_hora, tiene_ayudante, costo_ayudante))
                
                experiencias_validas.append(exp_valor)
                todos_servicios.append(f"{categoria}: {servicios_desc[i].strip()}")
        
        # 5. Insertar experiencia general
        max_experiencia = max(experiencias_validas) if experiencias_validas else 0
        resumen_servicios = ' | '.join(todos_servicios)
        
        cursor.execute("""
            INSERT INTO experiencia_persona (id_persona, anios_experiencia, descripcion)
            VALUES (%s, %s, %s)
        """, (id_persona, int(max_experiencia), resumen_servicios))
        
        # 6. Insertar disponibilidad
        cursor.execute("""
            INSERT INTO disponibilidad (id_persona, id_horario, id_dias)
            VALUES (%s, %s, %s)
        """, (id_persona, disponibilidad, disponibilidad_dias))
        
        # 7. Insertar detalles
        acepta_terminos_val = 1 if acepta_terminos == 'on' else 0
        permisos_ubicacion_val = 1 if permisos_ubicacion == 'on' else 0
        
        cursor.execute("""
            INSERT INTO detalles_persona 
            (id_persona, id_servicio_tipo, tareas, antecedentes_pdf, foto_identificacion, 
             acepta_terminos, permisos_ubicacion, recomendaciones, recomendaciones_archivo,
             foto_identificacion_data, foto_identificacion_tipo,
             antecedentes_data, antecedentes_tipo,
             recomendaciones_data, recomendaciones_tipo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (id_persona, habilidades_tipo, resumen_servicios, antecedentes_filename, 
              foto_filename, acepta_terminos_val, permisos_ubicacion_val, 
              recomendaciones or '', recomend_filename,
              foto_bytes, foto_tipo,
              antecedentes_bytes, antecedentes_tipo,
              recomend_bytes, recomend_tipo))
        
        conexion.commit()
        
        return {
            "mensaje": f"✅ Registro exitoso: {nombre_completo} fue registrado",
            "id_persona": id_persona,
            "redirect": f"/trabajador/crear_password?id_persona={id_persona}"
        }
        
    except Exception as e:
        if conexion:
            conexion.rollback()
        import traceback
        error_detalle = traceback.format_exc()
        print(f"ERROR EN REGISTRO: {error_detalle}")
        return {"error": f"Error: {str(e)}"}
    
    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.is_connected():
            conexion.close()


# ============================================
# API ENDPOINTS
# ============================================

@router.get("/solicitudes_pendientes")
def listar_solicitudes_pendientes(id_categoria: int = None):
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    
    if id_categoria:
        sql = """
        SELECT s.*, c.nombre_completo as nombre_cliente, cat.nombre_categoria
        FROM solicitudes_servicio s
        INNER JOIN clientes c ON s.id_cliente = c.id_cliente
        INNER JOIN categorias_servicio cat ON s.id_categoria = cat.id_categoria
        WHERE s.estado = 'pendiente' AND s.id_categoria = %s
        ORDER BY s.fecha_solicitud DESC
        """
        cursor.execute(sql, (id_categoria,))
    else:
        sql = """
        SELECT s.*, c.nombre_completo as nombre_cliente, cat.nombre_categoria
        FROM solicitudes_servicio s
        INNER JOIN clientes c ON s.id_cliente = c.id_cliente
        INNER JOIN categorias_servicio cat ON s.id_categoria = cat.id_categoria
        WHERE s.estado = 'pendiente'
        ORDER BY s.fecha_solicitud DESC
        """
        cursor.execute(sql)
    
    solicitudes = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    return {"solicitudes": solicitudes}

@router.post("/solicitud/aceptar")
def aceptar_solicitud(
    id_solicitud: int = Form(...),
    id_trabajador: int = Form(...)
):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    sql = """
    UPDATE solicitudes_servicio 
    SET id_trabajador = %s, estado = 'aceptada', fecha_aceptacion = %s
    WHERE id_solicitud = %s AND estado = 'pendiente'
    """
    
    cursor.execute(sql, (id_trabajador, datetime.now(), id_solicitud))
    conexion.commit()
    
    if cursor.rowcount == 0:
        cursor.close()
        conexion.close()
        return {"error": "La solicitud ya fue aceptada o no existe"}
    
    cursor.close()
    conexion.close()
    
    return {"mensaje": "Solicitud aceptada exitosamente"}

@router.post("/servicio/iniciar")
def iniciar_servicio(id_solicitud: int = Form(...)):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    sql = """
    UPDATE solicitudes_servicio 
    SET estado = 'en_proceso', fecha_inicio = %s
    WHERE id_solicitud = %s AND estado = 'aceptada'
    """
    
    cursor.execute(sql, (datetime.now(), id_solicitud))
    conexion.commit()
    cursor.close()
    conexion.close()
    
    return {"mensaje": "Servicio iniciado"}

@router.post("/servicio/completar")
def completar_servicio(
    id_solicitud: int = Form(...),
    precio_final: float = Form(...)
):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    sql = """
    UPDATE solicitudes_servicio 
    SET estado = 'completada', fecha_finalizacion = %s, precio_final = %s
    WHERE id_solicitud = %s AND estado = 'en_proceso'
    """
    
    cursor.execute(sql, (datetime.now(), precio_final, id_solicitud))
    conexion.commit()
    cursor.close()
    conexion.close()
    
    return {"mensaje": "Servicio completado exitosamente"}

@router.get("/historial/{id_trabajador}")
def historial_trabajador(id_trabajador: int):
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT s.*, c.nombre_completo as nombre_cliente, cat.nombre_categoria
        FROM solicitudes_servicio s
        INNER JOIN clientes c ON s.id_cliente = c.id_cliente
        INNER JOIN categorias_servicio cat ON s.id_categoria = cat.id_categoria
        WHERE s.id_trabajador = %s
        ORDER BY s.fecha_solicitud DESC
    """, (id_trabajador,))
    
    historial = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    return {"historial": historial}

@router.get("/disponibles/{id_categoria}")
def trabajadores_disponibles(id_categoria: int):
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT 
            p.id_persona,
            p.nombre_completo,
            p.ciudad,
            tc.experiencia_anos,
            tc.certificado,
            COALESCE(vtc.calificacion_promedio, 0) as calificacion,
            vtc.servicios_completados
        FROM personas p
        INNER JOIN trabajador_categorias tc ON p.id_persona = tc.id_trabajador
        LEFT JOIN vista_trabajadores_calificacion vtc ON p.id_persona = vtc.id_trabajador
        LEFT JOIN disponibilidad_trabajador dt ON p.id_persona = dt.id_trabajador
        WHERE tc.id_categoria = %s 
        AND p.estado = 'activo'
        AND (dt.disponible = 1 OR dt.disponible IS NULL)
        ORDER BY vtc.calificacion_promedio DESC
    """, (id_categoria,))
    
    trabajadores = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    return {"trabajadores": trabajadores}

@router.post("/disponibilidad/actualizar")
def actualizar_disponibilidad(
    id_trabajador: int = Form(...),
    disponible: bool = Form(...),
    latitud: float = Form(None),
    longitud: float = Form(None)
):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    cursor.execute("""
        SELECT id_disponibilidad FROM disponibilidad_trabajador 
        WHERE id_trabajador = %s
    """, (id_trabajador,))
    
    existe = cursor.fetchone()
    
    if existe:
        sql = """
        UPDATE disponibilidad_trabajador 
        SET disponible = %s, latitud = %s, longitud = %s
        WHERE id_trabajador = %s
        """
        cursor.execute(sql, (disponible, latitud, longitud, id_trabajador))
    else:
        sql = """
        INSERT INTO disponibilidad_trabajador 
        (id_trabajador, disponible, latitud, longitud)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (id_trabajador, disponible, latitud, longitud))
    
    conexion.commit()
    cursor.close()
    conexion.close()
    
    return {"mensaje": "Disponibilidad actualizada"}


# ============================================
# AUTENTICACIÓN Y ADMINISTRACIÓN
# ============================================

# Contraseña de administrador simple (cambiar en producción)
ADMIN_PASSWORD = "admin123"

@router.get("/admin/login", response_class=HTMLResponse)
def mostrar_admin_login(request: Request):
    return templates.TemplateResponse("trabajadores/admin_login.html", {"request": request})

@router.post("/admin/login")
async def admin_login(password: str = Form(...)):
    """Login de administrador"""
    try:
        # Verificar contraseña directamente (para desarrollo)
        if password == ADMIN_PASSWORD:
            return JSONResponse({
                "success": True,
                "mensaje": "Inicio de sesión exitoso"
            })
        else:
            return JSONResponse({
                "success": False,
                "error": "Contraseña incorrecta"
            }, status_code=401)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"Error al verificar contraseña: {str(e)}"
        }, status_code=500)

@router.get("/admin/logout")
def admin_logout():
    """Cerrar sesión de administrador"""
    return RedirectResponse(url="/", status_code=302)

@router.get("/registros", response_class=HTMLResponse)
def ver_registros(request: Request):
    """Página para ver todos los registros (requiere autenticación en producción)"""
    # TODO: Agregar middleware de autenticación
    return templates.TemplateResponse("trabajadores/registros.html", {"request": request})

@router.get("/registros/test")
def test_registros():
    """Endpoint de prueba simple"""
    conexion = conectar_bd()
    if not conexion:
        return {"error": "No se pudo conectar a la base de datos"}
    
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total FROM personas")
        total = cursor.fetchone()
        
        cursor.execute("SELECT * FROM personas LIMIT 5")
        registros = cursor.fetchall()
        
        # Convertir fechas a string
        for reg in registros:
            if reg.get('fecha_registro'):
                reg['fecha_registro'] = str(reg['fecha_registro'])
        
        return {
            "total": total['total'],
            "registros": registros,
            "mensaje": "Conexión exitosa"
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

@router.get("/registros/listar")
def listar_registros():
    """API para obtener todos los registros de trabajadores"""
    conexion = conectar_bd()
    if not conexion:
        return JSONResponse({"error": "Error de conexión", "registros": []}, status_code=500)
    
    try:
        cursor = conexion.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                p.id_persona,
                p.numero_documento,
                p.nombre_completo,
                p.ciudad,
                p.departamento,
                p.codigo_dane,
                p.id_genero,
                p.fecha_nacimiento,
                p.nacionalidad,
                p.fecha_registro,
                p.estado
            FROM personas p
            WHERE p.estado = 'activo' OR p.estado IS NULL
            ORDER BY p.id_persona DESC
        """)
        
        registros = cursor.fetchall()
        
        generos = {1: 'Masculino', 2: 'Femenino', 3: 'Otro', 4: 'Masculino', 5: 'Femenino', 6: 'Otro'}
        horarios = {7: '8am-12pm', 8: '2pm-6pm', 9: '6pm-10pm', 10: '24 horas'}
        dias = {11: 'Entre Semana', 12: 'Toda la Semana'}

        for reg in registros:
            for key, value in reg.items():
                if value is None:
                    reg[key] = ''
                elif hasattr(value, 'isoformat'):
                    reg[key] = value.isoformat()
                elif isinstance(value, (int, float)):
                    reg[key] = float(value) if isinstance(value, float) else int(value)
                else:
                    reg[key] = str(value)

            # Género desde id_genero
            id_gen = reg.get('id_genero', 0)
            reg['genero'] = generos.get(int(id_gen) if id_gen else 0, 'N/A')
            reg['tipo_documento'] = 'CC'
            reg['telefono'] = 'N/A'
            reg['correo'] = ''
            reg['anios_experiencia'] = 0
            reg['servicio_tipo'] = 'N/A'
            reg['foto_identificacion'] = ''
            reg['antecedentes_pdf'] = ''
            reg['recomendaciones'] = ''
            reg['recomendaciones_archivo'] = ''
            reg['horario'] = 'N/A'
            reg['dias_disponibles'] = 'N/A'
            reg['servicios'] = []
            reg['registrado_por'] = 'Sistema'

            try:
                cursor.execute("SELECT telefono FROM telefono_persona WHERE id_persona = %s LIMIT 1", (reg['id_persona'],))
                tel = cursor.fetchone()
                if tel: reg['telefono'] = str(tel['telefono'])

                cursor.execute("SELECT correo FROM correo_persona WHERE id_persona = %s LIMIT 1", (reg['id_persona'],))
                email = cursor.fetchone()
                if email: reg['correo'] = str(email['correo'])

                cursor.execute("""
                    SELECT foto_identificacion, antecedentes_pdf, recomendaciones, recomendaciones_archivo,
                           (foto_identificacion_data IS NOT NULL AND LENGTH(foto_identificacion_data) > 0) as tiene_foto,
                           (antecedentes_data IS NOT NULL AND LENGTH(antecedentes_data) > 0) as tiene_ant,
                           (recomendaciones_data IS NOT NULL AND LENGTH(recomendaciones_data) > 0) as tiene_rec
                    FROM detalles_persona WHERE id_persona = %s LIMIT 1
                """, (reg['id_persona'],))
                detalles = cursor.fetchone()
                if detalles:
                    reg['foto_identificacion'] = str(detalles.get('foto_identificacion') or '')
                    reg['antecedentes_pdf'] = str(detalles.get('antecedentes_pdf') or '')
                    reg['recomendaciones'] = str(detalles.get('recomendaciones') or '')
                    reg['recomendaciones_archivo'] = str(detalles.get('recomendaciones_archivo') or '')
                    # URLs para servir desde BD
                    if detalles.get('tiene_foto'):
                        reg['foto_identificacion_url'] = f"/trabajador/archivo/{reg['id_persona']}/foto"
                    if detalles.get('tiene_ant'):
                        reg['antecedentes_url'] = f"/trabajador/archivo/{reg['id_persona']}/antecedentes"
                    if detalles.get('tiene_rec'):
                        reg['recomendaciones_url'] = f"/trabajador/archivo/{reg['id_persona']}/recomendaciones"

                # Disponibilidad
                cursor.execute("SELECT id_horario, id_dias FROM disponibilidad WHERE id_persona = %s LIMIT 1", (reg['id_persona'],))
                disp = cursor.fetchone()
                if disp:
                    reg['horario'] = horarios.get(disp.get('id_horario'), 'N/A')
                    reg['dias_disponibles'] = dias.get(disp.get('id_dias'), 'N/A')

                cursor.execute("""
                    SELECT categoria, descripcion, anios_experiencia, valor_hora, tiene_ayudante, costo_ayudante
                    FROM servicios_persona WHERE id_persona = %s
                """, (reg['id_persona'],))
                servicios = cursor.fetchall()

                max_exp = 0
                servicios_proc = []
                for serv in servicios:
                    sp = {}
                    for k, v in serv.items():
                        if hasattr(v, '__float__'): sp[k] = float(v)
                        elif v is None: sp[k] = 0 if k in ['valor_hora','anios_experiencia','tiene_ayudante','costo_ayudante'] else ''
                        else: sp[k] = v
                    servicios_proc.append(sp)
                    if sp.get('anios_experiencia', 0) > max_exp:
                        max_exp = sp['anios_experiencia']

                reg['servicios'] = servicios_proc
                reg['anios_experiencia'] = int(max_exp)
                if servicios_proc:
                    reg['servicio_tipo'] = servicios_proc[0]['categoria']

            except Exception as ex:
                print(f"Error datos adicionales persona {reg['id_persona']}: {ex}")
                pass
        
        return JSONResponse({"registros": registros})
        
    except Exception as e:
        import traceback
        print(f"Error en /registros/listar: {traceback.format_exc()}")
        return JSONResponse({"error": str(e), "registros": []}, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

@router.get("/dashboard", response_class=HTMLResponse)
def mostrar_dashboard(request: Request):
    """Dashboard principal del administrador"""
    return templates.TemplateResponse("trabajadores/dashboard.html", {"request": request})

@router.get("/estadisticas")
def obtener_estadisticas():
    """API para obtener estadísticas completas del dashboard"""
    conexion = conectar_bd()
    if not conexion:
        return JSONResponse({"error": "Error de conexión"}, status_code=500)
    
    try:
        cursor = conexion.cursor(dictionary=True)
        
        # Totales generales
        cursor.execute("SELECT COUNT(*) as total FROM personas WHERE estado = 'activo' OR estado IS NULL")
        total_activos = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM personas WHERE estado = 'eliminado'")
        total_eliminados = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM personas")
        total_todos = cursor.fetchone()['total']

        # Registros hoy
        cursor.execute("SELECT COUNT(*) as total FROM personas WHERE DATE(fecha_registro) = CURDATE()")
        row = cursor.fetchone()
        registros_hoy = row['total'] if row else 0

        # Registros esta semana
        cursor.execute("SELECT COUNT(*) as total FROM personas WHERE fecha_registro >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
        row = cursor.fetchone()
        registros_semana = row['total'] if row else 0

        # Por categoría de servicio
        cursor.execute("""
            SELECT categoria, COUNT(*) as total 
            FROM servicios_persona 
            GROUP BY categoria 
            ORDER BY total DESC
            LIMIT 10
        """)
        por_categoria = cursor.fetchall()

        # Por ciudad (top 10)
        cursor.execute("""
            SELECT ciudad, COUNT(*) as total 
            FROM personas 
            WHERE (estado = 'activo' OR estado IS NULL) AND ciudad IS NOT NULL AND ciudad != ''
            GROUP BY ciudad 
            ORDER BY total DESC
            LIMIT 10
        """)
        por_ciudad = cursor.fetchall()

        # Por departamento (top 10)
        cursor.execute("""
            SELECT departamento, COUNT(*) as total 
            FROM personas 
            WHERE (estado = 'activo' OR estado IS NULL) AND departamento IS NOT NULL AND departamento != ''
            GROUP BY departamento 
            ORDER BY total DESC
            LIMIT 10
        """)
        por_departamento = cursor.fetchall()

        # Registros por mes (últimos 6 meses)
        cursor.execute("""
            SELECT DATE_FORMAT(fecha_registro, '%Y-%m') as mes, COUNT(*) as total
            FROM personas
            WHERE fecha_registro >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
            GROUP BY mes ORDER BY mes ASC
        """)
        por_mes = cursor.fetchall()

        # Tarifa promedio
        cursor.execute("SELECT AVG(valor_hora) as promedio FROM servicios_persona WHERE valor_hora > 0")
        row = cursor.fetchone()
        tarifa_promedio = float(row['promedio']) if row and row['promedio'] else 0

        # Últimos 5 registros
        cursor.execute("""
            SELECT p.id_persona, p.nombre_completo, p.ciudad, p.departamento,
                   p.fecha_registro,
                   GROUP_CONCAT(DISTINCT sp.categoria SEPARATOR ', ') as servicios
            FROM personas p
            LEFT JOIN servicios_persona sp ON p.id_persona = sp.id_persona
            WHERE p.estado = 'activo' OR p.estado IS NULL
            GROUP BY p.id_persona
            ORDER BY p.id_persona DESC
            LIMIT 5
        """)
        ultimos_registros = cursor.fetchall()
        for r in ultimos_registros:
            if r.get('fecha_registro'):
                r['fecha_registro'] = str(r['fecha_registro'])

        return JSONResponse({
            "total_activos": total_activos,
            "total_eliminados": total_eliminados,
            "total_todos": total_todos,
            "registros_hoy": registros_hoy,
            "registros_semana": registros_semana,
            "tarifa_promedio": tarifa_promedio,
            "por_categoria": por_categoria,
            "por_ciudad": por_ciudad,
            "por_departamento": por_departamento,
            "por_mes": por_mes,
            "ultimos_registros": ultimos_registros
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()

@router.post("/eliminar")
async def eliminar_registro(id_persona: int = Form(...)):
    """Eliminar registro (soft delete)"""
    conexion = conectar_bd()
    if not conexion:
        return JSONResponse({"error": "Error de conexión"}, status_code=500)
    
    try:
        cursor = conexion.cursor()
        
        cursor.execute("""
            UPDATE personas 
            SET estado = 'eliminado', fecha_eliminacion = %s
            WHERE id_persona = %s
        """, (datetime.now(), id_persona))
        
        conexion.commit()
        
        return JSONResponse({"mensaje": "✅ Registro eliminado exitosamente"})
        
    except Exception as e:
        conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()

@router.get("/exportar-excel")
def exportar_excel():
    """Exportar registros a Excel (placeholder)"""
    return JSONResponse({
        "mensaje": "Funcionalidad de exportación en desarrollo",
        "nota": "Requiere instalar openpyxl o xlsxwriter"
    })

@router.get("/archivo/{id_persona}/{tipo}")
def servir_archivo(id_persona: int, tipo: str):
    """Sirve archivos guardados en la base de datos"""
    from fastapi.responses import Response as FastResponse
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        campos = {
            'foto': ('foto_identificacion_data', 'foto_identificacion_tipo'),
            'antecedentes': ('antecedentes_data', 'antecedentes_tipo'),
            'recomendaciones': ('recomendaciones_data', 'recomendaciones_tipo'),
        }
        if tipo not in campos:
            return JSONResponse({"error": "Tipo inválido"}, status_code=400)
        
        col_data, col_tipo = campos[tipo]
        cursor.execute(f"SELECT {col_data}, {col_tipo} FROM detalles_persona WHERE id_persona = %s LIMIT 1", (id_persona,))
        row = cursor.fetchone()
        
        if not row or not row[col_data]:
            return JSONResponse({"error": "Archivo no encontrado"}, status_code=404)
        
        content_type = row[col_tipo] or 'application/octet-stream'
        return FastResponse(content=bytes(row[col_data]), media_type=content_type)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


# ============================================
# GEOLOCALIZACIÓN Y DISPONIBILIDAD
# ============================================

@router.get("/disponibilidad", response_class=HTMLResponse)
def mostrar_disponibilidad(request: Request):
    """Página para que trabajadores activen/desactiven su disponibilidad"""
    return templates.TemplateResponse("trabajadores/mi_disponibilidad.html", {"request": request})

@router.get("/disponibilidad/estado")
def obtener_estado_disponibilidad(id_trabajador: int):
    """Obtiene el estado actual de disponibilidad del trabajador"""
    conexion = conectar_bd()
    if not conexion:
        return JSONResponse({"error": "Error de conexión"}, status_code=500)
    
    try:
        cursor = conexion.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT disponible, latitud, longitud, ultima_actualizacion
            FROM disponibilidad
            WHERE id_persona = %s
            LIMIT 1
        """, (id_trabajador,))
        
        result = cursor.fetchone()
        
        if result:
            # Convertir Decimal a float
            if result.get('latitud'):
                result['latitud'] = float(result['latitud'])
            if result.get('longitud'):
                result['longitud'] = float(result['longitud'])
            if result.get('ultima_actualizacion'):
                result['ultima_actualizacion'] = result['ultima_actualizacion'].isoformat()
            
            return JSONResponse(result)
        else:
            return JSONResponse({"disponible": False})
            
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

@router.post("/disponibilidad/actualizar")
async def actualizar_disponibilidad(
    id_trabajador: int = Form(...),
    disponible: bool = Form(...),
    latitud: float = Form(None),
    longitud: float = Form(None)
):
    """Actualiza la disponibilidad y ubicación del trabajador"""
    conexion = conectar_bd()
    if not conexion:
        return JSONResponse({"error": "Error de conexión"}, status_code=500)
    
    try:
        cursor = conexion.cursor()
        
        # Verificar si ya existe registro
        cursor.execute("""
            SELECT id_disponibilidad FROM disponibilidad
            WHERE id_persona = %s
            LIMIT 1
        """, (id_trabajador,))
        
        existe = cursor.fetchone()
        
        if existe:
            # Actualizar
            cursor.execute("""
                UPDATE disponibilidad
                SET disponible = %s, latitud = %s, longitud = %s,
                    ultima_actualizacion = NOW()
                WHERE id_persona = %s
            """, (disponible, latitud, longitud, id_trabajador))
        else:
            # Insertar nuevo
            cursor.execute("""
                INSERT INTO disponibilidad (id_persona, disponible, latitud, longitud)
                VALUES (%s, %s, %s, %s)
            """, (id_trabajador, disponible, latitud, longitud))
        
        conexion.commit()
        
        return JSONResponse({
            "mensaje": "Disponibilidad actualizada correctamente",
            "disponible": disponible,
            "latitud": latitud,
            "longitud": longitud
        })
        
    except Exception as e:
        conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


@router.get("/eliminados", response_class=HTMLResponse)
def ver_eliminados(request: Request):
    """Página de papelera de registros eliminados"""
    return templates.TemplateResponse("trabajadores/eliminados.html", {"request": request})

@router.get("/eliminados/listar")
def listar_eliminados():
    """API para obtener registros eliminados"""
    conexion = conectar_bd()
    if not conexion:
        return JSONResponse({"error": "Error de conexión"}, status_code=500)
    
    try:
        cursor = conexion.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT p.id_persona, p.numero_documento, p.nombre_completo, p.ciudad, 
                   p.fecha_eliminacion, p.departamento,
                   tp.telefono
            FROM personas p
            LEFT JOIN telefono_persona tp ON p.id_persona = tp.id_persona
            WHERE p.estado = 'eliminado'
            ORDER BY p.fecha_eliminacion DESC
        """)
        
        registros = cursor.fetchall()
        
        # Serializar fechas
        for r in registros:
            for k, v in r.items():
                if hasattr(v, 'isoformat'):
                    r[k] = v.isoformat()
                elif v is None:
                    r[k] = ''
            r['tipo_documento'] = 'CC'
        
        registros = cursor.fetchall()
        
        cursor.execute("SELECT COUNT(*) as total FROM personas WHERE estado = 'eliminado'")
        total = cursor.fetchone()['total']
        
        return JSONResponse({
            "registros": registros,
            "total": total
        })
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()

@router.post("/restaurar")
async def restaurar_registro(id_persona: int = Form(...)):
    """Restaurar un registro eliminado"""
    conexion = conectar_bd()
    if not conexion:
        return JSONResponse({"error": "Error de conexión"}, status_code=500)
    
    try:
        cursor = conexion.cursor()
        
        cursor.execute("""
            UPDATE personas 
            SET estado = 'activo', fecha_eliminacion = NULL
            WHERE id_persona = %s
        """, (id_persona,))
        
        conexion.commit()
        
        return JSONResponse({"mensaje": "✅ Registro restaurado exitosamente"})
        
    except Exception as e:
        conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()

@router.post("/eliminar-permanente")
async def eliminar_permanente(id_persona: int = Form(...)):
    """Eliminar registro permanentemente de la base de datos"""
    import os
    
    conexion = conectar_bd()
    if not conexion:
        return JSONResponse({"error": "Error de conexión"}, status_code=500)
    
    try:
        cursor = conexion.cursor()
        
        # Obtener archivos antes de eliminar
        cursor.execute("""
            SELECT foto_identificacion, antecedentes_pdf, recomendaciones_archivo 
            FROM detalles_persona 
            WHERE id_persona = %s
        """, (id_persona,))
        
        archivos = cursor.fetchone()
        
        # Eliminar permanentemente
        cursor.execute("DELETE FROM personas WHERE id_persona = %s", (id_persona,))
        conexion.commit()
        
        # Eliminar archivos físicos
        if archivos:
            UPLOAD_FOLDER = "static/uploads"
            for archivo in archivos:
                if archivo:
                    archivo_path = os.path.join(UPLOAD_FOLDER, archivo)
                    if os.path.exists(archivo_path):
                        os.remove(archivo_path)
        
        return JSONResponse({"mensaje": "✅ Registro eliminado permanentemente"})
        
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
def mostrar_login_trabajador(request: Request):
    """Muestra página de login para trabajadores"""
    return templates.TemplateResponse("trabajadores/login.html", {"request": request})

@router.post("/login")
async def login_trabajador(
    response: Response,
    numero_documento: str = Form(...),
    password: str = Form(...)
):
    """Login de trabajador con número de documento + contraseña"""
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, tp.telefono
            FROM personas p
            LEFT JOIN telefono_persona tp ON p.id_persona = tp.id_persona
            WHERE p.numero_documento = %s AND (p.estado = 'activo' OR p.estado IS NULL)
            LIMIT 1
        """, (numero_documento,))
        trabajador = cursor.fetchone()
        cursor.close()
        conexion.close()

        if not trabajador:
            return JSONResponse({"error": "Documento no registrado"}, status_code=401)
        if not trabajador.get('password_hash'):
            return JSONResponse({"error": "Debes crear tu contraseña primero", "redirect": f"/trabajador/crear_password?id_persona={trabajador['id_persona']}"}, status_code=401)
        if not auth.verificar_password(password, trabajador['password_hash']):
            return JSONResponse({"error": "Contraseña incorrecta"}, status_code=401)

        token = auth.crear_sesion('trabajador', trabajador['id_persona'])
        response.set_cookie(key="session_token", value=token, httponly=True, max_age=86400, samesite="lax")

        return JSONResponse({"mensaje": f"Bienvenido, {trabajador['nombre_completo'].split()[0]}", "redirect": "/trabajador/panel"})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    """
    Endpoint de login para trabajadores
    Verifica credenciales y opcionalmente envía código SMS
    """
    try:
        # Autenticar trabajador
        exitoso, trabajador, mensaje = auth.autenticar_trabajador(correo, password)
        
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
        
        if requiere_sms and trabajador.get('telefono'):
            # Generar y enviar código SMS
            codigo = auth.crear_codigo_verificacion(
                'trabajador',
                trabajador['id_persona'],
                trabajador['telefono'],
                'login'
            )
            
            # Enviar SMS (simulado por ahora)
            auth.enviar_sms(trabajador['telefono'], codigo)
            
            return JSONResponse({
                "requiere_verificacion_sms": True,
                "id_trabajador": trabajador['id_persona'],
                "mensaje": "Código enviado a tu teléfono"
            })
        else:
            # Login directo sin SMS
            token = auth.crear_sesion('trabajador', trabajador['id_persona'])
            
            # Guardar token en cookie
            response.set_cookie(
                key="session_token",
                value=token,
                httponly=True,
                max_age=86400,  # 24 horas
                samesite="lax"
            )
            
            return JSONResponse({
                "requiere_verificacion_sms": False,
                "mensaje": "Login exitoso",
                "redirect": "/trabajador/disponibilidad"
            })
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Error en el servidor: {str(e)}"},
            status_code=500
        )

@router.post("/verificar-sms")
async def verificar_sms_trabajador(
    response: Response,
    id_trabajador: int = Form(...),
    codigo: str = Form(...)
):
    """Verifica el código SMS y crea la sesión"""
    try:
        valido, mensaje = auth.verificar_codigo_sms('trabajador', id_trabajador, codigo)
        
        if not valido:
            return JSONResponse(
                {"error": mensaje},
                status_code=400
            )
        
        # Crear sesión
        token = auth.crear_sesion('trabajador', id_trabajador)
        
        # Guardar token en cookie
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            max_age=86400,
            samesite="lax"
        )
        
        return JSONResponse({
            "mensaje": "Verificación exitosa",
            "redirect": "/trabajador/disponibilidad"
        })
        
    except Exception as e:
        return JSONResponse(
            {"error": f"Error: {str(e)}"},
            status_code=500
        )

@router.post("/reenviar-codigo")
async def reenviar_codigo_trabajador(id_trabajador: int = Form(...)):
    """Reenvía el código SMS"""
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)
        
        # Obtener teléfono del trabajador
        cursor.execute("""
            SELECT t.telefono
            FROM telefono_persona t
            WHERE t.id_persona = %s
            LIMIT 1
        """, (id_trabajador,))
        
        result = cursor.fetchone()
        cursor.close()
        conexion.close()
        
        if not result:
            return JSONResponse(
                {"error": "No se encontró teléfono registrado"},
                status_code=404
            )
        
        # Generar nuevo código
        codigo = auth.crear_codigo_verificacion(
            'trabajador',
            id_trabajador,
            result['telefono'],
            'login'
        )
        
        # Enviar SMS
        auth.enviar_sms(result['telefono'], codigo)
        
        return JSONResponse({"mensaje": "Código reenviado"})
        
    except Exception as e:
        return JSONResponse(
            {"error": f"Error: {str(e)}"},
            status_code=500
        )

@router.get("/logout")
def logout_trabajador(response: Response):
    """Cierra la sesión del trabajador"""
    response.delete_cookie("session_token")
    return RedirectResponse(url="/", status_code=302)

@router.post("/configurar-password")
async def configurar_password_trabajador(
    id_persona: int = Form(...),
    password: str = Form(...),
    confirmar_password: str = Form(...)
):
    """Configura la contraseña de un trabajador recién registrado"""
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
        
        auth.configurar_password_trabajador(id_persona, password)
        
        return JSONResponse({
            "mensaje": "Contraseña configurada correctamente",
            "redirect": "/trabajador/login"
        })
        
    except Exception as e:
        return JSONResponse(
            {"error": f"Error: {str(e)}"},
            status_code=500
        )
