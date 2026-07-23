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
                dp.nivel_estudio, dp.arl, dp.eps,
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
                    t[k] = v.strftime('%Y-%m-%d %H:%M')

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

@router.post("/aprobar")
def aprobar_trabajador(request: Request, id_persona: int = Form(...)):
    """La psicóloga aprueba al trabajador — pasa a estado 'activo'"""
    if not verificar_psicologa(request):
        return JSONResponse({"error": "No autorizado"}, status_code=401)

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            UPDATE personas SET estado = 'activo' WHERE id_persona = %s AND estado = 'pendiente_revision'
        """, (id_persona,))
        if cursor.rowcount == 0:
            return JSONResponse({"error": "Trabajador no encontrado o ya aprobado"}, status_code=400)
        conexion.commit()
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
    """La psicóloga rechaza al trabajador"""
    if not verificar_psicologa(request):
        return JSONResponse({"error": "No autorizado"}, status_code=401)

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            UPDATE personas SET estado = 'rechazado' WHERE id_persona = %s AND estado = 'pendiente_revision'
        """, (id_persona,))
        if cursor.rowcount == 0:
            return JSONResponse({"error": "Trabajador no encontrado"}, status_code=400)
        conexion.commit()
        return JSONResponse({"ok": True, "mensaje": "❌ Trabajador rechazado"})
    except Exception as e:
        if conexion: conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


# ============================================
# API: LISTAR APROBADOS
# ============================================

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
                    t[k] = v.strftime('%Y-%m-%d %H:%M')

        return JSONResponse({"trabajadores": trabajadores})

    except Exception as e:
        return JSONResponse({"error": str(e), "trabajadores": []}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()
