"""
Módulo de Pagos — TalentHub
Integración con Wompi (Colombia)
Docs: https://docs.wompi.co/docs/colombia/
"""
from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from config import DB_CONFIG, conectar_bd
import os, hashlib, hmac, json
from datetime import datetime

router = APIRouter(prefix="/pago", tags=["pagos"])
templates = Jinja2Templates(directory="templates")

# ── Claves Wompi (configurar en Railway) ──────────────────────────
def get_wompi_keys():
    pub  = os.getenv("WOMPI_PUBLIC_KEY",  "pub_test_xxxxx")   # reemplazar con clave real
    priv = os.getenv("WOMPI_PRIVATE_KEY", "priv_test_xxxxx")  # reemplazar con clave real
    evt  = os.getenv("WOMPI_EVENT_KEY",   "")                 # para validar webhooks
    intg = os.getenv("WOMPI_INTEGRITY_KEY", "")               # para firma de integridad
    is_prod = os.getenv("WOMPI_PRODUCTION", "false").lower() == "true"
    base_url = (
        "https://production.wompi.co/v1"
        if is_prod else
        "https://sandbox.wompi.co/v1"
    )
    return pub, priv, evt, base_url, intg


# ============================================
# CREAR TRANSACCIÓN — cliente inicia el pago
# ============================================

@router.post("/crear")
async def crear_pago(
    request: Request,
    id_solicitud: int  = Form(...),
    id_cliente:   int  = Form(None)
):
    """
    Genera un link/widget de pago Wompi para una solicitud con precio acordado.
    Retorna los datos necesarios para abrir el widget en el frontend.
    """
    # Obtener id_cliente desde sesión si no viene
    if not id_cliente:
        import auth as _auth
        token = request.cookies.get("session_token_cliente") or request.cookies.get("session_token")
        if token:
            sesion = _auth.verificar_sesion(token)
            if sesion and sesion['tipo_usuario'] == 'cliente':
                id_cliente = sesion['id_usuario']
    if not id_cliente:
        return JSONResponse({"error": "No autenticado"}, status_code=401)

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)

        # Verificar solicitud y precio
        cursor.execute("""
            SELECT s.id_solicitud, s.titulo, s.estado,
                   s.precio_final, s.cotizacion_precio, s.id_cliente,
                   c.nombre_completo AS nombre_cliente,
                   ec.correo AS correo_cliente
            FROM solicitudes_servicio s
            LEFT JOIN clientes c  ON s.id_cliente = c.id_cliente
            LEFT JOIN correo_cliente ec ON c.id_cliente = ec.id_cliente AND ec.principal = 1
            WHERE s.id_solicitud = %s AND s.id_cliente = %s
            LIMIT 1
        """, (id_solicitud, id_cliente))
        sol = cursor.fetchone()

        if not sol:
            return JSONResponse({"error": "Solicitud no encontrada"}, status_code=404)

        # Precio a cobrar: precio_final > cotizacion_precio > 0
        precio = float(sol.get('precio_final') or sol.get('cotizacion_precio') or 0)
        if precio <= 0:
            return JSONResponse({"error": "Esta solicitud no tiene un precio acordado"}, status_code=400)

        if sol['estado'] not in ('aceptada', 'en_proceso', 'cotizacion_enviada', 'completada'):
            return JSONResponse(
                {"error": f"Solo se puede pagar una solicitud aceptada (estado actual: {sol['estado']})"},
                status_code=400
            )

        # Verificar si ya tiene un pago APROBADO (no bloquear si solo está pendiente)
        cursor.execute("""
            SELECT id, estado_wompi FROM pagos_solicitud
            WHERE id_solicitud = %s AND estado_wompi = 'APPROVED'
            LIMIT 1
        """, (id_solicitud,))
        pago_existente = cursor.fetchone()
        if pago_existente:
            return JSONResponse({
                "error": "Esta solicitud ya tiene un pago aprobado"
            }, status_code=400)

        pub_key, _, _, _, intg_key = get_wompi_keys()
        base_url_app = os.getenv("APP_URL", "https://web-production-191f4.up.railway.app")

        # Referencia única para esta transacción
        referencia = f"TH-{id_solicitud}-{id_cliente}-{int(datetime.now().timestamp())}"
        monto_cents = int(precio * 100)

        # Calcular firma de integridad (SHA256)
        import hashlib
        cadena = f"{referencia}{monto_cents}COP{intg_key}"
        firma_integridad = hashlib.sha256(cadena.encode()).hexdigest() if intg_key else ""

        # Registrar intención de pago en BD
        cursor.execute("""
            INSERT INTO pagos_solicitud
            (id_solicitud, id_cliente, referencia_wompi, monto, estado_wompi, fecha_creacion)
            VALUES (%s, %s, %s, %s, 'PENDING', NOW())
        """, (id_solicitud, id_cliente, referencia, precio))
        conexion.commit()

        # Datos para el widget de Wompi (frontend)
        return JSONResponse({
            "ok": True,
            "public_key":       pub_key,
            "monto_cents":      monto_cents,
            "referencia":       referencia,
            "firma_integridad": firma_integridad,
            "descripcion":      sol['titulo'] or f"Servicio TalentHub #{id_solicitud}",
            "correo":           sol.get('correo_cliente') or '',
            "nombre":           sol.get('nombre_cliente') or '',
            "redirect_url":     f"{base_url_app}/pago/resultado?id_solicitud={id_solicitud}",
            "precio_cop":       precio
        })

    except Exception as e:
        if conexion: conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


# ============================================
# WEBHOOK — Wompi notifica resultado del pago
# ============================================

@router.post("/wompi-webhook")
async def wompi_webhook(request: Request):
    """
    Wompi llama a este endpoint cuando una transacción cambia de estado.
    Actualiza el pago y la solicitud en BD.
    """
    try:
        body = await request.body()
        data = json.loads(body)

        # Validar firma del evento (si WOMPI_EVENT_KEY está configurada)
        _, _, evt_key, _, _ = get_wompi_keys()
        if evt_key:
            firma_recibida  = request.headers.get("x-event-checksum", "")
            firma_calculada = hmac.new(evt_key.encode(), body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(firma_recibida, firma_calculada):
                return JSONResponse({"error": "Firma inválida"}, status_code=401)
                return JSONResponse({"error": "Firma inválida"}, status_code=401)

        evento = data.get("event", "")
        if evento != "transaction.updated":
            return JSONResponse({"ok": True, "ignorado": True})

        txn  = data.get("data", {}).get("transaction", {})
        ref  = txn.get("reference", "")
        est  = txn.get("status", "")        # APPROVED, DECLINED, VOIDED, ERROR
        txn_id = txn.get("id", "")
        monto = int(txn.get("amount_in_cents", 0)) / 100

        conexion = conectar_bd()
        cursor   = conexion.cursor(dictionary=True)

        # Buscar pago por referencia
        cursor.execute("""
            SELECT id, id_solicitud, id_cliente FROM pagos_solicitud
            WHERE referencia_wompi = %s LIMIT 1
        """, (ref,))
        pago = cursor.fetchone()

        if not pago:
            cursor.close(); conexion.close()
            return JSONResponse({"ok": True, "nota": "Referencia no encontrada"})

        # Actualizar estado del pago
        cursor.execute("""
            UPDATE pagos_solicitud
            SET estado_wompi = %s, id_transaccion_wompi = %s,
                fecha_actualizacion = NOW()
            WHERE id = %s
        """, (est, txn_id, pago['id']))

        # Si aprobado → actualizar solicitud
        if est == "APPROVED":
            cursor.execute("""
                UPDATE solicitudes_servicio
                SET pago_estado = 'pagado', precio_final = %s
                WHERE id_solicitud = %s
            """, (monto, pago['id_solicitud']))

            # Obtener datos para notificaciones
            cursor.execute("""
                SELECT
                    s.id_trabajador, s.titulo,
                    c.nombre_completo  AS nombre_cliente,
                    ec.correo          AS correo_cliente,
                    p.nombre_completo  AS nombre_trabajador,
                    ep.correo          AS correo_trabajador
                FROM solicitudes_servicio s
                LEFT JOIN clientes c    ON s.id_cliente   = c.id_cliente
                LEFT JOIN correo_cliente ec ON c.id_cliente = ec.id_cliente AND ec.principal = 1
                LEFT JOIN personas p    ON s.id_trabajador = p.id_persona
                LEFT JOIN correo_persona ep ON p.id_persona = ep.id_persona AND ep.principal = 1
                WHERE s.id_solicitud = %s
                LIMIT 1
            """, (pago['id_solicitud'],))
            datos = cursor.fetchone()

            # Notificar al trabajador por push
            try:
                if datos and datos['id_trabajador']:
                    _notificar_pago_push(
                        datos['id_trabajador'],
                        pago['id_solicitud'],
                        monto
                    )
            except: pass

            # Enviar emails de confirmación (cliente + trabajador)
            try:
                import auth as _auth
                base_url = os.getenv("APP_URL", "https://web-production-191f4.up.railway.app")
                if datos and datos.get('correo_cliente') and datos.get('correo_trabajador'):
                    import threading
                    threading.Thread(
                        target=_auth.enviar_email_confirmacion_pago,
                        args=(
                            datos['correo_cliente'],
                            datos['nombre_cliente'] or 'Cliente',
                            datos['titulo'] or f'Servicio #{pago["id_solicitud"]}',
                            monto,
                            ref,
                            pago['id_solicitud'],
                            datos['correo_trabajador'],
                            datos['nombre_trabajador'] or 'Profesional',
                            base_url,
                        ),
                        daemon=True
                    ).start()
                    print(f"[PAGO] ✅ Emails de confirmación enviados — solicitud #{pago['id_solicitud']}")
            except Exception as e_mail:
                print(f"[PAGO] ⚠️ Error enviando emails: {e_mail}")

        conexion.commit()
        cursor.close(); conexion.close()
        return JSONResponse({"ok": True})

    except Exception as e:
        print(f"[WEBHOOK] Error: {e}")
        return JSONResponse({"ok": True})   # Siempre 200 para que Wompi no reintente


# ============================================
# PÁGINA DE RESULTADO (redirect_url de Wompi)
# ============================================

@router.get("/resultado", response_class=HTMLResponse)
def resultado_pago(request: Request, id_solicitud: int = 0):
    """Página que muestra el resultado del pago al cliente."""
    return templates.TemplateResponse("clientes/resultado_pago.html", {
        "request":      request,
        "id_solicitud": id_solicitud
    })


@router.post("/establecer-precio")
async def establecer_precio(
    request: Request,
    id_solicitud: int  = Form(...),
    precio_final: float = Form(...)
):
    """Permite establecer el precio final cuando no viene de cotización."""
    import auth as _auth
    token = request.cookies.get("session_token_cliente") or request.cookies.get("session_token")
    if not token:
        return JSONResponse({"error": "No autenticado"}, status_code=401)
    sesion = _auth.verificar_sesion(token)
    if not sesion or sesion['tipo_usuario'] != 'cliente':
        return JSONResponse({"error": "No autorizado"}, status_code=403)

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            UPDATE solicitudes_servicio
            SET precio_final = %s
            WHERE id_solicitud = %s AND id_cliente = %s
              AND precio_final IS NULL OR precio_final = 0
        """, (precio_final, id_solicitud, sesion['id_usuario']))
        conexion.commit()
        return JSONResponse({"ok": True})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


@router.get("/estado")
def estado_pago(id_solicitud: int):
    """Consulta el estado del pago de una solicitud."""
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT estado_wompi, monto, fecha_actualizacion
            FROM pagos_solicitud
            WHERE id_solicitud = %s
            ORDER BY fecha_creacion DESC LIMIT 1
        """, (id_solicitud,))
        pago = cursor.fetchone()
        if not pago:
            return JSONResponse({"estado": "sin_pago", "pagado": False})
        from datetime import timedelta
        if pago.get('fecha_actualizacion') and hasattr(pago['fecha_actualizacion'], 'isoformat'):
            pago['fecha_actualizacion'] = (pago['fecha_actualizacion'] - timedelta(hours=5)).strftime('%d/%m %H:%M')
        pago['pagado'] = pago['estado_wompi'] == 'APPROVED'
        if pago.get('monto'): pago['monto'] = float(pago['monto'])
        return JSONResponse(pago)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


# ============================================
# HELPER — notificar pago al trabajador
# ============================================

def _notificar_pago_push(id_trabajador: int, id_solicitud: int, monto: float):
    import threading, json
    def _push():
        try:
            from config import conectar_bd as _c
            from pywebpush import webpush, WebPushException
            import main as _m
            conn = _c()
            cur  = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT endpoint, p256dh, auth FROM push_subscriptions
                WHERE tipo_usuario = 'trabajador' AND id_usuario = %s
            """, (id_trabajador,))
            subs = cur.fetchall()
            cur.close(); conn.close()
            payload = json.dumps({
                "title": "💰 ¡Pago recibido!",
                "body":  f"El cliente pagó ${monto:,.0f} por el servicio #{id_solicitud}",
                "url":   f"/trabajador/solicitudes_pendientes_panel",
                "icon":  "/static/icons/icon-192.png"
            })
            for sub in subs:
                try:
                    webpush(
                        subscription_info={"endpoint": sub["endpoint"], "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]}},
                        data=payload,
                        vapid_private_key=_m.VAPID_PRIVATE,
                        vapid_claims=_m.VAPID_CLAIMS
                    )
                except: pass
        except: pass
    threading.Thread(target=_push, daemon=True).start()
