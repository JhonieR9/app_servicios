from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from config import conectar_bd
import os

router = APIRouter(prefix="/psicologa", tags=["psicologa"])
templates = Jinja2Templates(directory="templates")

# Credenciales de la psicóloga (configurables por env vars)
PSICO_PASSWORD = os.getenv("PSICO_PASSWORD", "psico2026")
PSICO_TOKEN = os.getenv("PSICO_TOKEN", "talenthub_psico_2026_secret")


def verificar_psicologa(request: Request) -> bool:
    """Verifica si la request tiene sesión de psicóloga válida"""
    token = request.cookies.get("psico_session")
    return token == PSICO_TOKEN


# ============================================
# LOGIN
# ============================================

@router.get("/login", response_class=HTMLResponse)
def mostrar_login(request: Request):
    return templates.TemplateResponse("trabajadores/psicologa_login.html", {"request": request})


@router.post("/login")
async def login_psicologa(password: str = Form(...)):
    """Login de la psicóloga"""
    if password == PSICO_PASSWORD:
        resp = JSONResponse({"success": True, "mensaje": "Inicio de sesión exitoso"})
        resp.set_cookie(
            key="psico_session",
            value=PSICO_TOKEN,
            httponly=True,
            max_age=86400 * 7,
            samesite="lax"
        )
        return resp
    return JSONResponse({"success": False, "error": "Contraseña incorrecta"}, status_code=401)


@router.get("/logout")
def logout_psicologa():
    resp = RedirectResponse(url="/", status_code=302)
    resp.delete_cookie("psico_session")
    return resp


# ============================================
# PANEL PRINCIPAL
# ============================================

@router.get("/panel", response_class=HTMLResponse)
def mostrar_panel(request: Request):
    if not verificar_psicologa(request):
        return RedirectResponse(url="/psicologa/login", status_code=302)
    return templates.TemplateResponse("trabajadores/psicologa_panel.html", {"request": request})


@router.get("/hoja-de-vida/{id_persona}", response_class=HTMLResponse)
def mostrar_hoja_de_vida(request: Request, id_persona: int):
    """Vista de la hoja de vida completa (estilo formulario de registro)"""
    if not verificar_psicologa(request):
        return RedirectResponse(url="/psicologa/login", status_code=302)
    return templates.TemplateResponse("trabajadores/psicologa_hv.html", {"request": request, "id_persona": id_persona})


# ============================================
# API: LISTAR PENDIENTES DE REVISIÓN
# ============================================

@router.get("/pendientes")
def listar_pendientes(request: Request):
    """Lista trabajadores pendientes de revisión psicológica"""
    if not verificar_psicologa(request):
        return JSONResponse({"error": "No autorizado"}, status_code=401)

    conexion = conectar_bd()
    if not conexion:
        return JSONResponse({"error": "Error de conexión", "trabajadores": []}, status_code=500)

    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                p.id_persona, p.nombre_completo, p.numero_documento, p.ciudad,
                p.departamento, p.fecha_nacimiento, p.nacionalidad, p.fecha_registro,
                tp.telefono, cp.correo,
                COALESCE(dp.nivel_estudio, '') as nivel_estudio,
                COALESCE(dp.arl, '') as arl,
                COALESCE(dp.eps, '') as eps,
                dp.foto_identificacion,
                (dp.foto_identificacion_data IS NOT NULL AND LENGTH(dp.foto_identificacion_data) > 0) as tiene_foto,
                (dp.antecedentes_data IS NOT NULL AND LENGTH(dp.antecedentes_data) > 0) as tiene_antecedentes,
                (dp.recomendaciones_data IS NOT NULL AND LENGTH(dp.recomendaciones_data) > 0) as tiene_recomendaciones,
                (dp.certificado_estudio_data IS NOT NULL AND LENGTH(dp.certificado_estudio_data) > 0) as tiene_certificado
            FROM personas p
            LEFT JOIN telefono_persona tp ON p.id_persona = tp.id_persona
            LEFT JOIN correo_persona cp ON p.id_persona = cp.id_persona
            LEFT JOIN detalles_persona dp ON p.id_persona = dp.id_persona
            WHERE p.estado = 'pendiente_revision'
            ORDER BY p.fecha_registro DESC
        """)
        trabajadores = cursor.fetchall()

        for t in trabajadores:
            for k, v in t.items():
                if v is None:
                    t[k] = ''
                elif hasattr(v, 'isoformat'):
                    t[k] = v.strftime('%Y-%m-%d') if k == 'fecha_nacimiento' else v.strftime('%Y-%m-%d %H:%M')

            # Agregar URLs de documentos
            if t.get('tiene_foto'):
                t['foto_url'] = f"/trabajador/archivo/{t['id_persona']}/foto"
            if t.get('tiene_antecedentes'):
                t['antecedentes_url'] = f"/trabajador/archivo/{t['id_persona']}/antecedentes"
            if t.get('tiene_recomendaciones'):
                t['recomendaciones_url'] = f"/trabajador/archivo/{t['id_persona']}/recomendaciones"
            if t.get('tiene_certificado'):
                t['certificado_url'] = f"/trabajador/archivo/{t['id_persona']}/certificado_estudio"

            # Servicios del trabajador
            cursor.execute("""
                SELECT categoria, descripcion, valor_hora, anios_experiencia
                FROM servicios_persona WHERE id_persona = %s
            """, (t['id_persona'],))
            servicios = cursor.fetchall()
            for s in servicios:
                for k, v in s.items():
                    if v is None: s[k] = ''
                    elif hasattr(v, '__float__'): s[k] = float(v)
            t['servicios'] = servicios

        return JSONResponse({"trabajadores": trabajadores})

    except Exception as e:
        return JSONResponse({"error": str(e), "trabajadores": []}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


# ============================================
# API: APROBAR TRABAJADOR
# ============================================

@router.get("/detalle/{id_persona}")
def detalle_trabajador(request: Request, id_persona: int):
    """Devuelve TODOS los datos de un trabajador para la vista tipo formulario"""
    if not verificar_psicologa(request):
        return JSONResponse({"error": "No autorizado"}, status_code=401)

    conexion = conectar_bd()
    if not conexion:
        return JSONResponse({"error": "Error de conexión"}, status_code=500)

    try:
        cursor = conexion.cursor(dictionary=True)
        # Datos básicos de la persona
        cursor.execute("""
            SELECT 
                p.id_persona, p.nombre_completo, p.numero_documento, p.ciudad,
                p.departamento, p.fecha_nacimiento, p.nacionalidad, p.fecha_registro,
                p.id_tipo_documento, p.id_genero, p.codigo_dane, p.ciudad_nacimiento, p.estado,
                tp.telefono, cp.correo
            FROM personas p
            LEFT JOIN telefono_persona tp ON p.id_persona = tp.id_persona
            LEFT JOIN correo_persona cp ON p.id_persona = cp.id_persona
            WHERE p.id_persona = %s
        """, (id_persona,))
        t = cursor.fetchone()
        if not t:
            return JSONResponse({"error": "No encontrado"}, status_code=404)

        for k, v in t.items():
            if v is None: t[k] = ''
            elif hasattr(v, 'isoformat'): t[k] = v.strftime('%Y-%m-%d')

        # Detalles (query separada para evitar duplicados con JOIN)
        cursor.execute("""
            SELECT nivel_estudio, arl, eps, recomendaciones,
                   medio_pago, medio_pago_principal, banco, tipo_cuenta,
                   numero_cuenta, titular_cuenta,
                   (foto_identificacion_data IS NOT NULL AND LENGTH(foto_identificacion_data) > 0) as tiene_foto,
                   (antecedentes_data IS NOT NULL AND LENGTH(antecedentes_data) > 0) as tiene_antecedentes,
                   (recomendaciones_data IS NOT NULL AND LENGTH(recomendaciones_data) > 0) as tiene_recomendaciones,
                   (certificado_estudio_data IS NOT NULL AND LENGTH(certificado_estudio_data) > 0) as tiene_certificado,
                   (foto_perfil_data IS NOT NULL AND LENGTH(foto_perfil_data) > 0) as tiene_foto_perfil
            FROM detalles_persona WHERE id_persona = %s
            ORDER BY (nivel_estudio IS NOT NULL AND nivel_estudio != '') DESC,
                     (foto_identificacion_data IS NOT NULL) DESC
            LIMIT 1
        """, (id_persona,))
        detalles = cursor.fetchone()
        if detalles:
            for k, v in detalles.items():
                if v is None: t[k] = ''
                else: t[k] = v
        else:
            t['nivel_estudio'] = ''
            t['arl'] = ''
            t['eps'] = ''
            t['recomendaciones'] = ''
            t['medio_pago'] = ''
            t['medio_pago_principal'] = ''
            t['banco'] = ''
            t['tipo_cuenta'] = ''
            t['numero_cuenta'] = ''
            t['titular_cuenta'] = ''
            t['tiene_foto'] = 0
            t['tiene_antecedentes'] = 0
            t['tiene_recomendaciones'] = 0
            t['tiene_certificado'] = 0

        # Mapear tipo doc y genero
        TIPOS_DOC = {1: 'CC', 2: 'CE', 3: 'PA', 4: 'TI', 5: 'NIT', 6: 'PPT'}
        GENEROS = {1: 'Masculino', 2: 'Femenino', 3: 'No binario', 4: 'Prefiero no decir'}
        t['tipo_documento_texto'] = TIPOS_DOC.get(t.get('id_tipo_documento'), str(t.get('id_tipo_documento', '')))
        t['genero_texto'] = GENEROS.get(t.get('id_genero'), str(t.get('id_genero', '')))

        # URLs documentos
        if t.get('tiene_foto'):
            t['foto_url'] = f"/trabajador/archivo/{id_persona}/foto"
        if t.get('tiene_antecedentes'):
            t['antecedentes_url'] = f"/trabajador/archivo/{id_persona}/antecedentes"
        if t.get('tiene_recomendaciones'):
            t['recomendaciones_url'] = f"/trabajador/archivo/{id_persona}/recomendaciones"
        if t.get('tiene_certificado'):
            t['certificado_url'] = f"/trabajador/archivo/{id_persona}/certificado_estudio"
        if t.get('tiene_foto_perfil'):
            t['foto_perfil_url'] = f"/trabajador/archivo/{id_persona}/perfil"

        # Servicios
        cursor.execute("""
            SELECT categoria, descripcion, valor_hora, anios_experiencia, tiene_ayudante, costo_ayudante
            FROM servicios_persona WHERE id_persona = %s
        """, (id_persona,))
        servicios = cursor.fetchall()
        for s in servicios:
            for k, v in s.items():
                if v is None: s[k] = ''
                elif hasattr(v, '__float__'): s[k] = float(v)
        t['servicios'] = servicios

        # Disponibilidad
        cursor.execute("SELECT id_horario, id_dias FROM disponibilidad WHERE id_persona = %s LIMIT 1", (id_persona,))
        disp = cursor.fetchone()
        HORARIOS = {7: 'Mañanas (8am-12pm)', 8: 'Tardes (2pm-6pm)', 9: 'Noches (6pm-10pm)', 10: '24 horas', 11: 'Jornada completa (8am-6pm)', 12: 'Jornada extendida (8am-10pm)'}
        DIAS = {1: 'Lunes a Viernes', 2: 'Lunes a Sábado', 3: 'Lunes a Domingo', 4: 'Fines de semana', 5: 'Días específicos', 11: 'Entre semana', 12: 'Toda la semana'}
        t['horario'] = HORARIOS.get(disp['id_horario'], '') if disp else ''
        t['dias'] = DIAS.get(disp['id_dias'], '') if disp else ''

        # Ciudades de servicio
        cursor.execute("SELECT ciudad FROM ciudades_servicio_trabajador WHERE id_persona = %s ORDER BY ciudad", (id_persona,))
        ciudades = cursor.fetchall()
        t['ciudades_servicio'] = [c['ciudad'] for c in ciudades] if ciudades else []

        # Referencias personales
        cursor.execute("SELECT nombre, celular, correo, descripcion FROM referencias_personales WHERE id_persona = %s", (id_persona,))
        refs = cursor.fetchall()
        for r in refs:
            for k, v in r.items():
                if v is None: r[k] = ''
        t['referencias'] = refs

        return JSONResponse(t)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()

@router.post("/aprobar")
def aprobar_trabajador(request: Request, id_persona: int = Form(...)):
    """La psicóloga aprueba al trabajador — pasa a estado 'activo'"""
    if not verificar_psicologa(request):
        return JSONResponse({"error": "No autorizado"}, status_code=401)

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        
        # Obtener datos para notificar
        cursor.execute("""
            SELECT p.nombre_completo, cp.correo
            FROM personas p
            LEFT JOIN correo_persona cp ON p.id_persona = cp.id_persona
            WHERE p.id_persona = %s
        """, (id_persona,))
        trabajador = cursor.fetchone()
        
        cursor.execute("""
            UPDATE personas SET estado = 'activo', motivo_rechazo = NULL WHERE id_persona = %s AND estado = 'pendiente_revision'
        """, (id_persona,))
        if cursor.rowcount == 0:
            return JSONResponse({"error": "Trabajador no encontrado o ya aprobado"}, status_code=400)
        conexion.commit()
        
        # Enviar email de aprobación
        if trabajador and trabajador.get('correo'):
            try:
                import threading
                import auth as _auth
                nombre = trabajador.get('nombre_completo', 'Profesional')
                correo = trabajador['correo']
                
                def _enviar():
                    html = f"""<div style="font-family:Arial;max-width:480px;margin:0 auto;padding:20px">
                        <div style="text-align:center;margin-bottom:20px">
                            <div style="font-size:3rem">🎉</div>
                            <h2 style="color:#16a34a;margin:10px 0">¡Felicidades, {nombre.split()[0]}!</h2>
                        </div>
                        <p style="color:#374151;font-size:0.95rem;line-height:1.7">Tu hoja de vida ha sido <strong style="color:#16a34a">aprobada</strong> por nuestro equipo de revisión.</p>
                        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:16px;margin:16px 0;text-align:center">
                            <p style="margin:0;font-size:1rem;font-weight:700;color:#166534">✅ Ya puedes recibir solicitudes de servicio</p>
                        </div>
                        <p style="color:#64748b;font-size:0.88rem">Ingresa a tu cuenta, activa tu disponibilidad y empieza a conectar con clientes.</p>
                        <p style="color:#94a3b8;font-size:0.8rem;margin-top:20px">— Equipo TalentHub</p>
                    </div>"""
                    _auth._enviar_gmail(correo, "🎉 ¡Tu perfil fue aprobado! - TalentHub", html)
                
                threading.Thread(target=_enviar, daemon=True).start()
            except Exception as e_mail:
                print(f"[PSICO] Error email aprobación: {e_mail}")
        
        return JSONResponse({"ok": True, "mensaje": "✅ Trabajador aprobado — ya puede recibir solicitudes"})
    except Exception as e:
        if conexion: conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


# ============================================
# API: RECHAZAR TRABAJADOR
# ============================================

@router.post("/rechazar")
def rechazar_trabajador(request: Request, id_persona: int = Form(...), motivo: str = Form(None)):
    """La psicóloga rechaza al trabajador con motivo"""
    if not verificar_psicologa(request):
        return JSONResponse({"error": "No autorizado"}, status_code=401)

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        
        # Obtener datos del trabajador para notificar
        cursor.execute("""
            SELECT p.nombre_completo, cp.correo
            FROM personas p
            LEFT JOIN correo_persona cp ON p.id_persona = cp.id_persona
            WHERE p.id_persona = %s
        """, (id_persona,))
        trabajador = cursor.fetchone()
        
        cursor.execute("""
            UPDATE personas SET estado = 'rechazado', motivo_rechazo = %s WHERE id_persona = %s AND estado = 'pendiente_revision'
        """, (motivo or '', id_persona))
        if cursor.rowcount == 0:
            return JSONResponse({"error": "Trabajador no encontrado"}, status_code=400)
        conexion.commit()
        
        # Notificar al trabajador por email si tiene correo
        if trabajador and trabajador.get('correo') and motivo:
            try:
                import threading
                import auth as _auth
                nombre = trabajador.get('nombre_completo', 'Profesional')
                correo = trabajador['correo']
                
                def _enviar():
                    html = f"""<div style="font-family:Arial;max-width:480px;margin:0 auto;padding:20px">
                        <h2 style="color:#dc2626">Resultado de la revisión de tu perfil</h2>
                        <p>Hola <strong>{nombre.split()[0]}</strong>,</p>
                        <p>Lamentamos informarte que tu hoja de vida no fue aprobada por nuestro equipo de revisión.</p>
                        <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:16px;margin:16px 0">
                            <strong style="color:#dc2626">Motivo:</strong><br>
                            <p style="margin:8px 0 0;color:#374151">{motivo}</p>
                        </div>
                        <p style="color:#64748b;font-size:0.9rem">Si deseas corregir la información, puedes volver a registrarte o contactarnos para más detalles.</p>
                        <p style="color:#94a3b8;font-size:0.8rem;margin-top:20px">— Equipo TalentHub</p>
                    </div>"""
                    _auth._enviar_gmail(correo, "Resultado de revisión - TalentHub", html)
                
                threading.Thread(target=_enviar, daemon=True).start()
            except Exception as e_mail:
                print(f"[PSICO] Error enviando email rechazo: {e_mail}")
        
        return JSONResponse({"ok": True, "mensaje": "❌ Trabajador rechazado — se le notificó el motivo"})
    except Exception as e:
        if conexion: conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


# ============================================
# API: LISTAR APROBADOS
# ============================================

@router.post("/devolver-revision")
def devolver_a_revision(request: Request, id_persona: int = Form(...)):
    """Devuelve un trabajador rechazado o activo al estado pendiente_revision"""
    if not verificar_psicologa(request):
        return JSONResponse({"error": "No autorizado"}, status_code=401)

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            UPDATE personas SET estado = 'pendiente_revision'
            WHERE id_persona = %s AND estado IN ('rechazado', 'activo')
        """, (id_persona,))
        if cursor.rowcount == 0:
            return JSONResponse({"error": "No encontrado o ya está pendiente"}, status_code=400)
        conexion.commit()
        return JSONResponse({"ok": True, "mensaje": "🔄 Devuelto a revisión"})
    except Exception as e:
        if conexion: conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


@router.get("/rechazados")
def listar_rechazados(request: Request):
    """Lista trabajadores rechazados"""
    if not verificar_psicologa(request):
        return JSONResponse({"error": "No autorizado"}, status_code=401)

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.id_persona, p.nombre_completo, p.numero_documento, p.ciudad, p.fecha_registro,
                   tp.telefono
            FROM personas p
            LEFT JOIN telefono_persona tp ON p.id_persona = tp.id_persona
            WHERE p.estado = 'rechazado'
            ORDER BY p.fecha_registro DESC LIMIT 50
        """)
        trabajadores = cursor.fetchall()
        for t in trabajadores:
            for k, v in t.items():
                if v is None: t[k] = ''
                elif hasattr(v, 'isoformat'): t[k] = v.strftime('%Y-%m-%d %H:%M')
        return JSONResponse({"trabajadores": trabajadores})
    except Exception as e:
        return JSONResponse({"error": str(e), "trabajadores": []}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()

@router.get("/aprobados")
def listar_aprobados(request: Request):
    """Lista trabajadores ya aprobados por la psicóloga"""
    if not verificar_psicologa(request):
        return JSONResponse({"error": "No autorizado"}, status_code=401)

    conexion = conectar_bd()
    if not conexion:
        return JSONResponse({"error": "Error de conexión", "trabajadores": []}, status_code=500)

    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                p.id_persona, p.nombre_completo, p.numero_documento, p.ciudad,
                p.departamento, p.fecha_registro,
                tp.telefono,
                dp.nivel_estudio
            FROM personas p
            LEFT JOIN telefono_persona tp ON p.id_persona = tp.id_persona
            LEFT JOIN detalles_persona dp ON p.id_persona = dp.id_persona
            WHERE p.estado = 'activo'
            ORDER BY p.fecha_registro DESC
            LIMIT 100
        """)
        trabajadores = cursor.fetchall()

        for t in trabajadores:
            for k, v in t.items():
                if v is None:
                    t[k] = ''
                elif hasattr(v, 'isoformat'):
                    t[k] = v.strftime('%Y-%m-%d') if k == 'fecha_nacimiento' else v.strftime('%Y-%m-%d %H:%M')

        return JSONResponse({"trabajadores": trabajadores})

    except Exception as e:
        return JSONResponse({"error": str(e), "trabajadores": []}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()
