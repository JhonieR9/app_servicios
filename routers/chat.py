from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from config import DB_CONFIG
import mysql.connector
from datetime import datetime

router = APIRouter(prefix="/chat", tags=["chat"])
templates = Jinja2Templates(directory="templates")

def conectar_bd():
    return mysql.connector.connect(**DB_CONFIG)

# ── Página de chat ────────────────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
def mostrar_chat(request: Request):
    return templates.TemplateResponse("clientes/chat.html", {"request": request})

# ── Info de la solicitud para el header del chat ──────────────────
@router.get("/info")
def info_chat(id_solicitud: int, tipo: str = "cliente", id_usuario: int = 0):
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.titulo, s.estado, s.id_cliente, s.id_trabajador,
                   c.nombre_completo AS nombre_cliente,
                   p.nombre_completo AS nombre_trabajador
            FROM solicitudes_servicio s
            LEFT JOIN clientes c ON s.id_cliente = c.id_cliente
            LEFT JOIN personas p ON s.id_trabajador = p.id_persona
            WHERE s.id_solicitud = %s
        """, (id_solicitud,))
        sol = cursor.fetchone()
        if not sol:
            return JSONResponse({"error": "No encontrada"}, status_code=404)

        # La contraparte depende de quién consulta
        if tipo == "cliente":
            contraparte = sol["nombre_trabajador"] or "Trabajador"
        else:
            contraparte = sol["nombre_cliente"] or "Cliente"

        return JSONResponse({
            "titulo":     sol["titulo"] or "",
            "estado":     sol["estado"] or "",
            "contraparte": contraparte
        })
    finally:
        conexion.close()

# ── Listar mensajes (con paginación por id) ───────────────────────
@router.get("/mensajes")
def listar_mensajes(id_solicitud: int, desde_id: int = 0):
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.id_mensaje, m.tipo_remitente, m.id_remitente,
                   m.mensaje, m.leido, m.fecha_envio,
                   COALESCE(c.nombre_completo, p.nombre_completo, 'Sistema') AS nombre_remitente
            FROM mensajes_chat m
            LEFT JOIN clientes c  ON m.tipo_remitente = 'cliente'   AND m.id_remitente = c.id_cliente
            LEFT JOIN personas p  ON m.tipo_remitente = 'trabajador' AND m.id_remitente = p.id_persona
            WHERE m.id_solicitud = %s AND m.id_mensaje > %s
            ORDER BY m.id_mensaje ASC
            LIMIT 100
        """, (id_solicitud, desde_id))
        mensajes = cursor.fetchall()
        # Formatear fechas en Python (evitar problemas con DATE_FORMAT)
        from datetime import timedelta
        for m in mensajes:
            if m.get('fecha_envio') and hasattr(m['fecha_envio'], 'strftime'):
                # Ajustar a hora Colombia (UTC-5)
                hora_col = m['fecha_envio'] - timedelta(hours=5)
                m['fecha_envio'] = hora_col.strftime('%Y-%m-%d %H:%M')
            elif m.get('fecha_envio'):
                m['fecha_envio'] = str(m['fecha_envio'])
            else:
                m['fecha_envio'] = ''
        return JSONResponse({"mensajes": mensajes})
    except Exception as e:
        return JSONResponse({"error": str(e), "mensajes": []}, status_code=500)
    finally:
        conexion.close()

# ── Enviar mensaje ────────────────────────────────────────────────
@router.post("/enviar")
def enviar_mensaje(
    id_solicitud:  int  = Form(...),
    tipo_remitente: str = Form(...),   # 'cliente' | 'trabajador'
    id_remitente:  int  = Form(...),
    mensaje:       str  = Form(...)
):
    if not mensaje.strip():
        return JSONResponse({"error": "Mensaje vacío"}, status_code=400)
    if tipo_remitente not in ("cliente", "trabajador"):
        return JSONResponse({"error": "Tipo inválido"}, status_code=400)

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO mensajes_chat
                (id_solicitud, tipo_remitente, id_remitente, mensaje, fecha_envio, leido)
            VALUES (%s, %s, %s, %s, %s, 0)
        """, (id_solicitud, tipo_remitente, id_remitente, mensaje.strip(), datetime.now()))
        conexion.commit()
        id_msg = cursor.lastrowid
        return JSONResponse({"ok": True, "id_mensaje": id_msg})
    except Exception as e:
        conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        conexion.close()

# ── Marcar mensajes como leídos ───────────────────────────────────
@router.post("/leer")
def marcar_leidos(
    id_solicitud:   int = Form(...),
    tipo_receptor:  str = Form(...)    # quien está leyendo
):
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        # Marcar como leídos los mensajes del otro
        otro = "trabajador" if tipo_receptor == "cliente" else "cliente"
        cursor.execute("""
            UPDATE mensajes_chat
            SET leido = 1
            WHERE id_solicitud = %s AND tipo_remitente = %s AND leido = 0
        """, (id_solicitud, otro))
        conexion.commit()
        return JSONResponse({"ok": True})
    finally:
        conexion.close()

# ── Contar mensajes no leídos (para badge) ────────────────────────
@router.get("/no-leidos")
def contar_no_leidos(id_solicitud: int, tipo_receptor: str):
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        otro = "trabajador" if tipo_receptor == "cliente" else "cliente"
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM mensajes_chat
            WHERE id_solicitud = %s AND tipo_remitente = %s AND leido = 0
        """, (id_solicitud, otro))
        row = cursor.fetchone()
        return JSONResponse({"no_leidos": row["total"] if row else 0})
    finally:
        conexion.close()

# ── Vista admin: todos los chats ─────────────────────────────────
@router.get("/admin", response_class=HTMLResponse)
def admin_chats(request: Request):
    """Panel admin para monitorear todos los chats activos"""
    return templates.TemplateResponse("trabajadores/admin_chats.html", {"request": request})

@router.get("/admin/listar")
def listar_todos_chats(buscar: str = "", estado: str = ""):
    """Lista todas las conversaciones para el admin"""
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        where = "WHERE 1=1"
        params = []
        if estado:
            where += " AND s.estado = %s"
            params.append(estado)
        if buscar:
            where += " AND (c.nombre_completo LIKE %s OR p.nombre_completo LIKE %s OR s.titulo LIKE %s)"
            params += [f"%{buscar}%", f"%{buscar}%", f"%{buscar}%"]

        cursor.execute(f"""
            SELECT
                s.id_solicitud,
                s.titulo,
                s.estado,
                s.fecha_solicitud,
                c.nombre_completo  AS nombre_cliente,
                p.nombre_completo  AS nombre_trabajador,
                cat.nombre_categoria,
                (SELECT COUNT(*) FROM mensajes_chat m WHERE m.id_solicitud = s.id_solicitud) AS total_mensajes,
                (SELECT COUNT(*) FROM mensajes_chat m WHERE m.id_solicitud = s.id_solicitud AND m.leido = 0) AS no_leidos,
                (SELECT m2.mensaje FROM mensajes_chat m2
                 WHERE m2.id_solicitud = s.id_solicitud
                 ORDER BY m2.id_mensaje DESC LIMIT 1) AS ultimo_mensaje,
                (SELECT m3.fecha_envio FROM mensajes_chat m3
                 WHERE m3.id_solicitud = s.id_solicitud
                 ORDER BY m3.id_mensaje DESC LIMIT 1) AS ultima_actividad
            FROM solicitudes_servicio s
            LEFT JOIN clientes c   ON s.id_cliente   = c.id_cliente
            LEFT JOIN personas p   ON s.id_trabajador = p.id_persona
            LEFT JOIN categorias_servicio cat ON s.id_categoria = cat.id_categoria
            {where}
            ORDER BY ultima_actividad DESC, s.fecha_solicitud DESC
            LIMIT 100
        """, params)
        chats = cursor.fetchall()
        for ch in chats:
            for k, v in ch.items():
                if v is None:
                    ch[k] = ''
                elif hasattr(v, 'isoformat'):
                    from datetime import timedelta
                    ch[k] = (v - timedelta(hours=5)).strftime('%d/%m %H:%M')
        return JSONResponse({"chats": chats})
    except Exception as e:
        return JSONResponse({"error": str(e), "chats": []}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()
