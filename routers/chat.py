from fastapi import APIRouter, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, Response
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
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO mensajes_chat
                (id_solicitud, tipo_remitente, id_remitente, mensaje, fecha_envio, leido)
            VALUES (%s, %s, %s, %s, %s, 0)
        """, (id_solicitud, tipo_remitente, id_remitente, mensaje.strip(), datetime.now()))
        conexion.commit()
        id_msg = cursor.lastrowid

        # ── Enviar push notification al destinatario (en background) ──
        import threading
        def _notificar_push():
            try:
                import json, os
                conn2 = conectar_bd()
                cur2  = conn2.cursor(dictionary=True)

                # Determinar destinatario
                cur2.execute("""
                    SELECT id_cliente, id_trabajador FROM solicitudes_servicio
                    WHERE id_solicitud = %s LIMIT 1
                """, (id_solicitud,))
                sol = cur2.fetchone()
                if not sol:
                    cur2.close(); conn2.close(); return

                # Obtener nombre del remitente
                if tipo_remitente == 'cliente':
                    cur2.execute("SELECT nombre_completo FROM clientes WHERE id_cliente = %s", (id_remitente,))
                    row = cur2.fetchone()
                    nombre_remitente = row['nombre_completo'] if row else 'Cliente'
                    # Notificar al trabajador
                    tipo_dest = 'trabajador'
                    id_dest   = sol['id_trabajador']
                else:
                    cur2.execute("SELECT nombre_completo FROM personas WHERE id_persona = %s", (id_remitente,))
                    row = cur2.fetchone()
                    nombre_remitente = row['nombre_completo'] if row else 'Trabajador'
                    # Notificar al cliente
                    tipo_dest = 'cliente'
                    id_dest   = sol['id_cliente']

                if not id_dest:
                    cur2.close(); conn2.close(); return

                # Buscar suscripciones push del destinatario
                cur2.execute("""
                    SELECT endpoint, p256dh, auth FROM push_subscriptions
                    WHERE tipo_usuario = %s AND id_usuario = %s
                """, (tipo_dest, id_dest))
                subs = cur2.fetchall()
                cur2.close(); conn2.close()

                if not subs:
                    return

                try:
                    from pywebpush import webpush, WebPushException
                except ImportError:
                    return

                from main import VAPID_PRIVATE, VAPID_CLAIMS
                texto_corto = mensaje.strip()[:80]
                payload = json.dumps({
                    "title": f"💬 {nombre_remitente}",
                    "body":  texto_corto,
                    "url":   f"/chat/?id_solicitud={id_solicitud}&tipo={tipo_dest}&id_usuario={id_dest}",
                    "icon":  "/static/icons/icon-192.png"
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
                    except WebPushException as ex:
                        if ex.response and ex.response.status_code in (404, 410):
                            try:
                                c3 = conectar_bd(); cur3 = c3.cursor()
                                cur3.execute("DELETE FROM push_subscriptions WHERE endpoint = %s", (sub["endpoint"],))
                                c3.commit(); cur3.close(); c3.close()
                            except: pass
                    except: pass
            except Exception as ex:
                print(f"[CHAT PUSH] Error: {ex}")

        threading.Thread(target=_notificar_push, daemon=True).start()

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


# ── Subir foto (antes/después/progreso) ───────────────────────────
@router.post("/foto/subir")
async def subir_foto_chat(
    id_solicitud:  int = Form(...),
    id_usuario:    int = Form(...),
    tipo_usuario:  str = Form("trabajador"),
    tipo_foto:     str = Form("progreso"),   # 'antes', 'despues', 'progreso'
    descripcion:   str = Form(None),
    foto: UploadFile = File(...)
):
    """Subir una foto del servicio (trabajador o cliente)"""
    if tipo_foto not in ('antes', 'despues', 'progreso'):
        tipo_foto = 'progreso'

    foto_bytes = await foto.read()
    foto_tipo = foto.content_type or 'image/jpeg'

    # Limitar tamaño (5MB)
    if len(foto_bytes) > 5 * 1024 * 1024:
        return JSONResponse({"error": "La foto no puede pesar más de 5MB"}, status_code=400)

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO fotos_servicio (id_solicitud, id_trabajador, tipo_foto, foto_data, foto_tipo, descripcion)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (id_solicitud, id_usuario, tipo_foto, foto_bytes, foto_tipo, descripcion))
        conexion.commit()
        id_foto = cursor.lastrowid

        # También enviar como mensaje en el chat
        etiqueta = {'antes': '📷 Foto ANTES', 'despues': '📷 Foto DESPUÉS', 'progreso': '📷 Foto'}
        msg_texto = etiqueta.get(tipo_foto, '📷 Foto')
        if descripcion:
            msg_texto += f': {descripcion}'
        msg_texto += f' [foto:{id_foto}]'

        tipo_rem = tipo_usuario if tipo_usuario in ('cliente', 'trabajador') else 'trabajador'
        cursor.execute("""
            INSERT INTO mensajes_chat (id_solicitud, tipo_remitente, id_remitente, mensaje, fecha_envio, leido)
            VALUES (%s, %s, %s, %s, %s, 0)
        """, (id_solicitud, tipo_rem, id_usuario, msg_texto, datetime.now()))
        conexion.commit()

        return JSONResponse({"ok": True, "id_foto": id_foto})
    except Exception as e:
        conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        conexion.close()

# ── Ver foto por ID ───────────────────────────────────────────────
@router.get("/foto/{id_foto}")
def ver_foto(id_foto: int):
    """Sirve una foto del servicio por su ID"""
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT foto_data, foto_tipo FROM fotos_servicio WHERE id_foto = %s", (id_foto,))
        foto = cursor.fetchone()
        if not foto or not foto['foto_data']:
            return JSONResponse({"error": "Foto no encontrada"}, status_code=404)
        return Response(content=bytes(foto['foto_data']), media_type=foto['foto_tipo'] or 'image/jpeg')
    finally:
        conexion.close()

# ── Listar fotos de una solicitud ─────────────────────────────────
@router.get("/fotos/{id_solicitud}")
def listar_fotos(id_solicitud: int):
    """Lista todas las fotos de un servicio"""
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT id_foto, tipo_foto, descripcion, fecha_subida
            FROM fotos_servicio
            WHERE id_solicitud = %s
            ORDER BY fecha_subida ASC
        """, (id_solicitud,))
        fotos = cursor.fetchall()
        from datetime import timedelta
        for f in fotos:
            if f.get('fecha_subida') and hasattr(f['fecha_subida'], 'strftime'):
                f['fecha_subida'] = (f['fecha_subida'] - timedelta(hours=5)).strftime('%d/%m %H:%M')
            f['url'] = f'/chat/foto/{f["id_foto"]}'
        return JSONResponse({"fotos": fotos})
    finally:
        conexion.close()
