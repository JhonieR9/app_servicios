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


# ── Parámetros de la tarifa de servicio TalentHub ──────────────────
# La empresa quiere quedarse con MARGEN_EMPRESA netos por servicio,
# después de pagarle a Wompi su comisión. Wompi (plan 2.65% + $700 + IVA)
# cobra un % variable sobre el total + un fijo por transacción, y sobre esa
# comisión se aplica el IVA (19%). Por eso usamos las tarifas con IVA incluido.
MARGEN_EMPRESA   = 10000.0            # lo que gana TalentHub, limpio, por servicio
IVA              = 0.19              # IVA Colombia sobre la comisión de Wompi
WOMPI_PORCENTAJE = 0.0265 * (1 + IVA)  # 2.65% + IVA = 3.1535% efectivo sobre el total
WOMPI_FIJO       = 700.0 * (1 + IVA)   # $700 + IVA = $833 por transacción


def calcular_cobro(precio_servicio: float):
    """
    Dado el precio del servicio (lo que recibe el trabajador),
    calcula cuánto debe pagar el cliente para que a TalentHub le queden
    exactamente MARGEN_EMPRESA netos después de la comisión de Wompi (con IVA).

    Fórmula (despejando el total T):
        T - P - (T*%  + fijo) = margen
        T = (P + margen + fijo) / (1 - %)
    donde % y fijo ya incluyen el IVA de la comisión de Wompi.

    Devuelve un dict con el desglose para mostrar al cliente y cobrar.
    """
    P = float(precio_servicio or 0)
    total = (P + MARGEN_EMPRESA + WOMPI_FIJO) / (1 - WOMPI_PORCENTAJE)

    # Redondear el total HACIA ARRIBA a la centena (cobro "limpio" al cliente).
    # Hacia arriba y no al más cercano: así el margen nunca queda por debajo de MARGEN_EMPRESA.
    import math
    total = math.ceil(round(total, 6) / 100) * 100

    tarifa_servicio = total - P              # lo que ve el cliente como "tarifa de servicio"
    costo_wompi     = total * WOMPI_PORCENTAJE + WOMPI_FIJO
    ganancia_neta   = total - P - costo_wompi

    return {
        "precio_servicio": round(P),
        "tarifa_servicio": round(tarifa_servicio),
        "total":           round(total),
        "costo_wompi":     round(costo_wompi),
        "ganancia_neta":   round(ganancia_neta),
    }


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

        # Precio del servicio (lo que recibe el trabajador): precio_final > cotizacion_precio > 0
        precio_servicio = float(sol.get('precio_final') or sol.get('cotizacion_precio') or 0)
        if precio_servicio <= 0:
            return JSONResponse({"error": "Esta solicitud no tiene un precio acordado"}, status_code=400)

        # Tarifa de servicio = margen TalentHub (10.000) + comisión Wompi.
        # El cliente paga el TOTAL; el trabajador recibe precio_servicio completo.
        cobro = calcular_cobro(precio_servicio)
        precio = float(cobro["total"])   # lo que efectivamente se le cobra al cliente

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

        # Registrar intención de pago en BD.
        # monto_trabajador = snapshot de lo que se le debe al trabajador. Se fija ahora, junto
        # con el cobro, para que no cambie si después se modifica el precio de la solicitud.
        try:
            cursor.execute("""
                INSERT INTO pagos_solicitud
                (id_solicitud, id_cliente, referencia_wompi, monto, monto_trabajador, estado_wompi, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, 'PENDING', NOW())
            """, (id_solicitud, id_cliente, referencia, precio, precio_servicio))
        except Exception as e_col:
            # Si la columna aún no existe (migración pendiente), cae al insert anterior
            print(f"[PAGO] insert sin monto_trabajador ({e_col})")
            conexion.rollback()
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
            "precio_cop":       precio,
            # Desglose para mostrar al cliente en el checkout
            "desglose": {
                "precio_servicio": cobro["precio_servicio"],
                "tarifa_servicio": cobro["tarifa_servicio"],
                "total":           cobro["total"],
            }
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

        # Si aprobado → marcar como pagado.
        # NO sobrescribimos precio_final: ese es el valor del servicio que recibe
        # el trabajador. El total pagado por el cliente (servicio + tarifa) queda
        # registrado en pagos_solicitud.monto.
        if est == "APPROVED":
            # Si la solicitud ya tenía OTRO pago aprobado, este es un cobro duplicado:
            # hay que reembolsarlo (el panel de dispersiones solo muestra el primero).
            cursor.execute("""
                SELECT COUNT(*) AS n FROM pagos_solicitud
                WHERE id_solicitud = %s AND estado_wompi = 'APPROVED' AND id <> %s
            """, (pago['id_solicitud'], pago['id']))
            otros = cursor.fetchone()
            if otros and otros['n'] > 0:
                print(f"[PAGO] ⚠️ COBRO DUPLICADO solicitud #{pago['id_solicitud']} ref={ref} "
                      f"monto={monto} — reembolsar al cliente")

            # precio_final: si por algún motivo seguía vacío (pago hecho durante la cotización),
            # se toma de la cotización para que el trabajador no quede en $0.
            cursor.execute("""
                UPDATE solicitudes_servicio
                SET pago_estado = 'pagado',
                    precio_final = COALESCE(NULLIF(precio_final, 0), cotizacion_precio, precio_final)
                WHERE id_solicitud = %s
            """, (pago['id_solicitud'],))

            # Obtener datos para notificaciones
            cursor.execute("""
                SELECT
                    s.id_trabajador, s.titulo, s.precio_final,
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

            # Monto que recibe el trabajador = precio del servicio (no el total con tarifa)
            monto_trabajador = float(datos['precio_final']) if datos and datos.get('precio_final') else monto

            # Notificar al trabajador por push (le mostramos LO QUE RECIBE)
            try:
                if datos and datos['id_trabajador']:
                    _notificar_pago_push(
                        datos['id_trabajador'],
                        pago['id_solicitud'],
                        monto_trabajador
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
              AND (precio_final IS NULL OR precio_final = 0)
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


# ============================================
# ADMIN — PANEL DE DISPERSIONES
# ============================================

@router.get("/admin/dispersiones", response_class=HTMLResponse)
def admin_dispersiones(request: Request):
    """Panel admin para gestionar pagos pendientes de dispersar a trabajadores (solo admin)."""
    from routers.trabajadores import requiere_admin
    redir = requiere_admin(request)
    if redir:
        return redir
    return templates.TemplateResponse("trabajadores/dispersiones.html", {"request": request})


@router.post("/admin/confirmar-pago-manual")
def confirmar_pago_manual(request: Request, id_solicitud: int = Form(...)):
    """Admin marca manualmente un pago como recibido (fallback cuando el webhook falla)."""
    from routers.trabajadores import verificar_admin
    if not verificar_admin(request):
        return JSONResponse({"error": "No autorizado"}, status_code=401)
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        # Actualizar solicitud
        cursor.execute("""
            UPDATE solicitudes_servicio
            SET pago_estado = 'pagado'
            WHERE id_solicitud = %s AND estado = 'completada'
        """, (id_solicitud,))
        # Actualizar registro en pagos_solicitud (para que aparezca en dispersiones)
        cursor.execute("""
            UPDATE pagos_solicitud
            SET estado_wompi = 'APPROVED', id_transaccion_wompi = CONCAT('MANUAL-', %s),
                fecha_actualizacion = NOW()
            WHERE id_solicitud = %s
        """, (id_solicitud, id_solicitud))
        # Si no existe el registro de pago, crearlo
        cursor.execute("SELECT id FROM pagos_solicitud WHERE id_solicitud = %s LIMIT 1", (id_solicitud,))
        if not cursor.fetchone():
            cursor.execute("""
                SELECT id_cliente, precio_final FROM solicitudes_servicio
                WHERE id_solicitud = %s LIMIT 1
            """, (id_solicitud,))
            sol = cursor.fetchone()
            if sol:
                cursor.execute("""
                    INSERT INTO pagos_solicitud
                    (id_solicitud, id_cliente, referencia_wompi, monto, estado_wompi, fecha_creacion, fecha_actualizacion)
                    VALUES (%s, %s, %s, %s, 'APPROVED', NOW(), NOW())
                """, (id_solicitud, sol[0], f"MANUAL-{id_solicitud}", sol[1] or 0))
        conexion.commit()
        return JSONResponse({"ok": True, "mensaje": f"Pago de solicitud #{id_solicitud} marcado como recibido"})
    except Exception as e:
        conexion.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


@router.get("/admin/dispersiones-api")
def api_dispersiones(request: Request, tab: str = "pendientes"):
    """API: lista pagos aprobados pendientes o ya dispersados (solo admin)."""
    from routers.trabajadores import verificar_admin
    if not verificar_admin(request):
        return JSONResponse({"error": "No autorizado", "dispersiones": []}, status_code=401)

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)

        # Solo el PRIMER pago aprobado de cada solicitud es dispersable. Si el cliente pagó dos
        # veces (doble pestaña, reintento), el segundo es un cobro duplicado a reembolsar, no
        # algo que se le deba pagar otra vez al trabajador.
        unico = ("AND ps.id = (SELECT MIN(p2.id) FROM pagos_solicitud p2 "
                 "WHERE p2.id_solicitud = ps.id_solicitud AND p2.estado_wompi = 'APPROVED')")
        # Lo que se le debe al trabajador: el valor fijado al crear el pago (snapshot);
        # para pagos anteriores a ese cambio, el precio de la solicitud.
        a_pagar = "COALESCE(NULLIF(ps.monto_trabajador, 0), NULLIF(s.precio_final, 0))"

        # Stats — mismo JOIN y filtro que la lista, para que los números coincidan con lo que se ve.
        # El monto por dispersar es SOLO el valor del servicio (lo del trabajador),
        # nunca el total que pagó el cliente (que incluye la tarifa de la plataforma).
        cursor.execute(f"""
            SELECT COUNT(*)                                          AS total,
                   COALESCE(SUM(COALESCE({a_pagar}, 0)), 0)          AS monto,
                   COALESCE(SUM(CASE WHEN {a_pagar} IS NULL
                                     THEN 1 ELSE 0 END), 0)          AS sin_precio
            FROM pagos_solicitud ps
            INNER JOIN solicitudes_servicio s ON ps.id_solicitud = s.id_solicitud
            WHERE ps.estado_wompi = 'APPROVED' AND (ps.dispersado = 0 OR ps.dispersado IS NULL)
              {unico}
        """)
        st = cursor.fetchone()
        total_pend = int(st['total'] or 0)
        monto_pend = float(st['monto'] or 0)
        sin_precio = int(st['sin_precio'] or 0)
        cursor.execute(f"""
            SELECT COUNT(*) AS total
            FROM pagos_solicitud ps
            INNER JOIN solicitudes_servicio s ON ps.id_solicitud = s.id_solicitud
            WHERE ps.estado_wompi = 'APPROVED' AND ps.dispersado = 1
              {unico}
        """)
        total_disp = int(cursor.fetchone()['total'] or 0)

        # Lista según tab
        if tab == 'pagados':
            filtro = "AND ps.dispersado = 1"
            orden  = "ps.fecha_dispersion DESC"
        else:
            filtro = "AND (ps.dispersado = 0 OR ps.dispersado IS NULL)"
            orden  = "ps.fecha_creacion DESC"

        # Una sola fila por pago: el teléfono y los datos de cuenta se resumen en
        # subconsultas agrupadas para que no se dupliquen si el trabajador tiene
        # varios teléfonos o más de un registro en detalles_persona.
        cursor.execute(f"""
            SELECT
                ps.id AS id_pago,
                ps.id_solicitud,
                ps.monto,
                {a_pagar} AS monto_trabajador,
                ps.estado_wompi,
                ps.referencia_wompi,
                ps.dispersado,
                ps.fecha_dispersion,
                ps.fecha_creacion,
                ps.fecha_actualizacion,
                s.titulo,
                s.id_trabajador,
                p.nombre_completo AS nombre_trabajador,
                p.numero_documento AS documento_trabajador,
                (SELECT MIN(tp.telefono) FROM telefono_persona tp
                  WHERE tp.id_persona = p.id_persona) AS telefono_trabajador,
                dp.medio_pago, dp.medio_pago_principal, dp.banco,
                dp.tipo_cuenta, dp.numero_cuenta, dp.titular_cuenta,
                c.nombre_completo AS nombre_cliente
            FROM pagos_solicitud ps
            INNER JOIN solicitudes_servicio s ON ps.id_solicitud = s.id_solicitud
            LEFT JOIN personas p ON s.id_trabajador = p.id_persona
            LEFT JOIN (
                SELECT id_persona,
                       MAX(medio_pago)           AS medio_pago,
                       MAX(medio_pago_principal) AS medio_pago_principal,
                       MAX(banco)                AS banco,
                       MAX(tipo_cuenta)          AS tipo_cuenta,
                       MAX(numero_cuenta)        AS numero_cuenta,
                       MAX(titular_cuenta)       AS titular_cuenta
                FROM detalles_persona
                GROUP BY id_persona
            ) dp ON dp.id_persona = p.id_persona
            LEFT JOIN clientes c ON ps.id_cliente = c.id_cliente
            WHERE ps.estado_wompi = 'APPROVED' {filtro}
              {unico}
            ORDER BY {orden}
            LIMIT 300
        """)
        dispersiones = cursor.fetchall()

        from datetime import timedelta
        from decimal import Decimal
        for d in dispersiones:
            for k, v in d.items():
                if v is None:
                    d[k] = ''
                elif hasattr(v, 'isoformat'):
                    d[k] = (v - timedelta(hours=5)).strftime('%d/%m/%Y %H:%M')
                elif isinstance(v, Decimal):
                    d[k] = float(v)

        return JSONResponse({
            "dispersiones":      dispersiones,
            "total_pendientes":  total_pend,
            "monto_pendiente":   monto_pend,
            "total_dispersados": total_disp,
            "sin_precio":        sin_precio,
            "mostrando":         len(dispersiones),
        })
    except Exception as e:
        return JSONResponse({"error": str(e), "dispersiones": []}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


@router.post("/admin/marcar-dispersado")
def marcar_dispersado(request: Request, id_pago: int = Form(...)):
    """Marca un pago como dispersado al trabajador (solo admin)."""
    from routers.trabajadores import verificar_admin
    if not verificar_admin(request):
        return JSONResponse({"error": "No autorizado"}, status_code=401)

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        # Solo si todavía no estaba dispersado: evita doble clic / doble registro
        cursor.execute("""
            UPDATE pagos_solicitud
            SET dispersado = 1, fecha_dispersion = NOW()
            WHERE id = %s AND estado_wompi = 'APPROVED'
              AND (dispersado = 0 OR dispersado IS NULL)
        """, (id_pago,))
        if cursor.rowcount == 0:
            conexion.rollback()
            return JSONResponse(
                {"error": "Este pago ya estaba marcado como dispersado o no está aprobado"},
                status_code=409
            )
        conexion.commit()
        return JSONResponse({"ok": True})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


@router.post("/admin/desmarcar-dispersado")
def desmarcar_dispersado(request: Request, id_pago: int = Form(...)):
    """Revierte una dispersión marcada por error (solo admin)."""
    from routers.trabajadores import verificar_admin
    if not verificar_admin(request):
        return JSONResponse({"error": "No autorizado"}, status_code=401)

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            UPDATE pagos_solicitud
            SET dispersado = 0, fecha_dispersion = NULL
            WHERE id = %s AND dispersado = 1
        """, (id_pago,))
        if cursor.rowcount == 0:
            conexion.rollback()
            return JSONResponse({"error": "Este pago no estaba marcado como dispersado"}, status_code=409)
        conexion.commit()
        return JSONResponse({"ok": True})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conexion and conexion.is_connected():
            conexion.close()


# ============================================
# RECIBO / COMPROBANTE DE PAGO (imprimible → PDF)
# ============================================

@router.get("/recibo", response_class=HTMLResponse)
def recibo_pago(request: Request, id_solicitud: int = 0):
    """Muestra un comprobante imprimible del pago aprobado (solo el cliente dueño o un admin)."""
    from datetime import timedelta
    import auth as _auth
    from routers.trabajadores import verificar_admin

    # Quién pide el recibo: el cliente logueado o un administrador
    token = request.cookies.get("session_token_cliente") or request.cookies.get("session_token")
    sesion = _auth.verificar_sesion(token) if token else None
    id_cliente_sesion = sesion['id_usuario'] if (sesion and sesion.get('tipo_usuario') == 'cliente') else None
    es_admin = verificar_admin(request)
    if not id_cliente_sesion and not es_admin:
        return RedirectResponse(url="/cliente/login", status_code=302)

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.referencia_wompi, p.id_transaccion_wompi, p.monto, p.monto_trabajador,
                   p.estado_wompi, p.fecha_actualizacion, p.fecha_creacion,
                   s.titulo, s.id_cliente, s.id_trabajador,
                   s.precio_final, s.cotizacion_precio,
                   cat.nombre_categoria,
                   cl.nombre_completo AS nombre_cliente,
                   tr.nombre_completo AS nombre_trabajador
            FROM pagos_solicitud p
            INNER JOIN solicitudes_servicio s ON p.id_solicitud = s.id_solicitud
            LEFT JOIN categorias_servicio cat ON s.id_categoria = cat.id_categoria
            LEFT JOIN clientes cl ON s.id_cliente = cl.id_cliente
            LEFT JOIN personas tr ON s.id_trabajador = tr.id_persona
            WHERE p.id_solicitud = %s AND p.estado_wompi = 'APPROVED'
            ORDER BY p.id ASC
            LIMIT 1
        """, (id_solicitud,))
        pago = cursor.fetchone()
        cursor.close()

        # Un cliente solo ve SUS recibos; si no es suyo respondemos igual que si no existiera
        if pago and not es_admin and pago.get('id_cliente') != id_cliente_sesion:
            pago = None

        if not pago:
            return HTMLResponse(
                "<div style='font-family:sans-serif;text-align:center;padding:60px'>"
                "<h2>Recibo no disponible</h2>"
                "<p>No encontramos un pago aprobado para esta solicitud.</p>"
                "<a href='/cliente/panel'>Volver al panel</a></div>",
                status_code=404,
            )

        def _fmt(v):
            try:
                return f"{int(float(v or 0)):,}".replace(",", ".")
            except Exception:
                return "0"

        total_pagado    = float(pago['monto'] or 0)
        # Valor del servicio: el fijado al crear el pago; para pagos anteriores, el de la solicitud
        precio_servicio = float(pago.get('monto_trabajador') or pago.get('precio_final') or pago.get('cotizacion_precio') or 0)
        tarifa_servicio = max(0, total_pagado - precio_servicio)

        monto_fmt    = _fmt(total_pagado)
        servicio_fmt = _fmt(precio_servicio)
        tarifa_fmt   = _fmt(tarifa_servicio)

        # Fecha de pago en hora Colombia (UTC-5)
        fecha_src = pago.get("fecha_actualizacion") or pago.get("fecha_creacion")
        if fecha_src and hasattr(fecha_src, "strftime"):
            fecha_pago = (fecha_src - timedelta(hours=5)).strftime("%d/%m/%Y %I:%M %p")
        else:
            fecha_pago = ""

        return templates.TemplateResponse("clientes/recibo_pago.html", {
            "request":           request,
            "id_solicitud":      id_solicitud,
            "monto_fmt":         monto_fmt,
            "servicio_fmt":      servicio_fmt,
            "tarifa_fmt":        tarifa_fmt,
            "titulo":            pago.get("titulo") or "Servicio",
            "categoria":         pago.get("nombre_categoria") or "",
            "nombre_trabajador": pago.get("nombre_trabajador") or "",
            "nombre_cliente":    pago.get("nombre_cliente") or "",
            "fecha_pago":        fecha_pago,
            "referencia":        pago.get("referencia_wompi") or "",
            "id_transaccion":    pago.get("id_transaccion_wompi") or "",
        })
    except Exception as e:
        print(f"[RECIBO] Error solicitud #{id_solicitud}: {e}")
        return HTMLResponse(
            "<div style='font-family:sans-serif;text-align:center;padding:60px'>"
            "<h2>No pudimos generar el recibo</h2><p>Intenta de nuevo en unos minutos.</p></div>",
            status_code=500,
        )
    finally:
        if conexion and conexion.is_connected():
            conexion.close()
