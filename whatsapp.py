"""
WhatsApp Business API - Integración con Meta Cloud API
Envía notificaciones por WhatsApp a trabajadores y clientes.

Variables de entorno necesarias en Railway:
  WA_TOKEN       = Token de acceso permanente de Meta
  WA_PHONE_ID    = Phone Number ID de WhatsApp Business
"""
import os
import requests
import json

WA_TOKEN = os.getenv("WA_TOKEN", "")
WA_PHONE_ID = os.getenv("WA_PHONE_ID", "")
WA_API_URL = f"https://graph.facebook.com/v20.0/{WA_PHONE_ID}/messages"


def _formatear_telefono(telefono: str) -> str:
    """Convierte un teléfono colombiano al formato internacional (57XXXXXXXXXX)"""
    tel = str(telefono).strip().replace(" ", "").replace("-", "").replace("+", "")
    # Si ya tiene 57 al inicio y 12 dígitos
    if tel.startswith("57") and len(tel) == 12:
        return tel
    # Si tiene 10 dígitos (formato colombiano sin código país)
    if len(tel) == 10 and tel.startswith("3"):
        return "57" + tel
    # Si tiene 7 dígitos (fijo)
    if len(tel) == 7:
        return "57" + tel
    return tel


def enviar_whatsapp(telefono: str, mensaje: str) -> dict:
    """
    Envía un mensaje de texto libre por WhatsApp.
    Solo funciona si el usuario ha enviado un mensaje en las últimas 24h (ventana de servicio).
    Para mensajes fuera de ventana, usar enviar_plantilla().
    """
    if not WA_TOKEN or not WA_PHONE_ID:
        print("[WA] No configurado — WA_TOKEN o WA_PHONE_ID vacíos")
        return {"error": "WhatsApp no configurado"}

    tel_formatted = _formatear_telefono(telefono)

    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": tel_formatted,
        "type": "text",
        "text": {"body": mensaje}
    }

    try:
        res = requests.post(WA_API_URL, headers=headers, json=payload, timeout=10)
        data = res.json()
        if res.status_code == 200:
            print(f"[WA] ✅ Mensaje enviado a {tel_formatted}")
        else:
            print(f"[WA] ❌ Error {res.status_code}: {data}")
        return data
    except Exception as e:
        print(f"[WA] ❌ Excepción: {e}")
        return {"error": str(e)}


def enviar_plantilla(telefono: str, plantilla: str, parametros: list = None) -> dict:
    """
    Envía un mensaje de plantilla aprobada por Meta.
    Esto funciona SIEMPRE (no necesita ventana de 24h).
    
    Args:
        telefono: Número del destinatario
        plantilla: Nombre de la plantilla aprobada en Meta
        parametros: Lista de strings para los {{1}}, {{2}}, etc.
    """
    if not WA_TOKEN or not WA_PHONE_ID:
        print("[WA] No configurado — WA_TOKEN o WA_PHONE_ID vacíos")
        return {"error": "WhatsApp no configurado"}

    tel_formatted = _formatear_telefono(telefono)

    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json"
    }

    # Construir componentes de la plantilla
    components = []
    if parametros:
        params_body = [{"type": "text", "text": str(p)} for p in parametros]
        components.append({
            "type": "body",
            "parameters": params_body
        })

    payload = {
        "messaging_product": "whatsapp",
        "to": tel_formatted,
        "type": "template",
        "template": {
            "name": plantilla,
            "language": {"code": "es"},
            "components": components
        }
    }

    try:
        res = requests.post(WA_API_URL, headers=headers, json=payload, timeout=10)
        data = res.json()
        if res.status_code == 200:
            print(f"[WA] ✅ Plantilla '{plantilla}' enviada a {tel_formatted}")
        else:
            print(f"[WA] ❌ Error plantilla {res.status_code}: {data}")
        return data
    except Exception as e:
        print(f"[WA] ❌ Excepción: {e}")
        return {"error": str(e)}


# ── Funciones helper para los eventos de TalentHub ──────────────────

def notificar_nueva_solicitud(telefono: str, nombre_trabajador: str, categoria: str, ciudad: str, cliente: str):
    """Notifica al trabajador que tiene una nueva solicitud"""
    mensaje = (
        f"🔔 *Nueva solicitud en TalentHub*\n\n"
        f"Hola {nombre_trabajador}, tienes una nueva solicitud:\n\n"
        f"📋 *{categoria}*\n"
        f"📍 {ciudad}\n"
        f"👤 Cliente: {cliente}\n\n"
        f"Abre TalentHub para aceptar ➡️\n"
        f"https://talenthubcol.com/trabajador/panel"
    )
    return enviar_whatsapp(telefono, mensaje)


def notificar_cotizacion_aceptada(telefono: str, nombre_trabajador: str, precio: str, titulo: str):
    """Notifica al trabajador que su cotización fue aceptada"""
    mensaje = (
        f"✅ *¡Cotización aceptada!*\n\n"
        f"Hola {nombre_trabajador}, el cliente aceptó tu cotización:\n\n"
        f"📋 {titulo}\n"
        f"💰 ${precio}\n\n"
        f"¡Coordina con el cliente para iniciar! 💪\n"
        f"https://talenthubcol.com/trabajador/panel"
    )
    return enviar_whatsapp(telefono, mensaje)


def notificar_recordatorio(telefono: str, nombre: str, titulo: str, fecha: str, es_trabajador: bool = True):
    """Envía recordatorio 24h antes del servicio programado"""
    if es_trabajador:
        mensaje = (
            f"📅 *Recordatorio — Servicio mañana*\n\n"
            f"Hola {nombre}, te recordamos que tienes:\n\n"
            f"📋 *{titulo}*\n"
            f"🕐 {fecha}\n\n"
            f"¡No olvides confirmar tu asistencia!\n"
            f"https://talenthubcol.com/trabajador/panel"
        )
    else:
        mensaje = (
            f"📅 *Recordatorio — Servicio mañana*\n\n"
            f"Hola {nombre}, tu servicio es mañana:\n\n"
            f"📋 *{titulo}*\n"
            f"🕐 {fecha}\n\n"
            f"¡Prepárate! El profesional llegará a la hora acordada.\n"
            f"https://talenthubcol.com/cliente/mis_solicitudes"
        )
    return enviar_whatsapp(telefono, mensaje)


def notificar_servicio_completado(telefono: str, nombre_cliente: str, titulo: str, precio: str):
    """Notifica al cliente que el servicio se completó"""
    mensaje = (
        f"🎉 *Servicio completado*\n\n"
        f"Hola {nombre_cliente}, tu servicio fue realizado:\n\n"
        f"📋 {titulo}\n"
        f"💰 Total: ${precio}\n\n"
        f"¡Califica al profesional! ⭐\n"
        f"https://talenthubcol.com/cliente/mis_solicitudes"
    )
    return enviar_whatsapp(telefono, mensaje)


def notificar_pago_recibido(telefono: str, nombre_trabajador: str, monto: str, titulo: str):
    """Notifica al trabajador que recibió un pago"""
    mensaje = (
        f"💰 *¡Pago recibido!*\n\n"
        f"Hola {nombre_trabajador}, te pagaron:\n\n"
        f"📋 {titulo}\n"
        f"💵 ${monto}\n\n"
        f"El dinero será dispersado a tu cuenta registrada.\n"
        f"¡Gracias por tu trabajo! 🙌"
    )
    return enviar_whatsapp(telefono, mensaje)
